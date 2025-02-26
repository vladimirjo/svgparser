from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector
    from xmlvalidator import XmlValidator

    from .attlist import Attlist
    from .cdata import CData
    from .comment import Comment
    from .doctype import Doctype
    from .element import Element
    from .entity import Entity
    from .includeignore import IncludeIgnore
    from .instructions import Instructions
    from .notation import Notation
    from .parsedtext import ParsedText
    from .tag import Tag
    from .xmldecl import XmlDeclaration

from errorcollector import CritErr
from .attr import Attribute


class Tag:
    def __init__(
        self,
        element_tokens: list[Token],
        error_collector: ErrorCollector,
    ) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.name: Token | None = None
        self.closed = False
        self.parent: XmlValidator | Tag | None = None
        self.children: list[
            Tag
            | CData
            | Comment
            | Doctype
            | Element
            | Attlist
            | Notation
            | Entity
            | IncludeIgnore
            | Instructions
            | ParsedText
            | XmlDeclaration
        ] = []
        self.attributes: list[Attribute] = []
        self.current = 0
        self.end = len(self.tokens) - 1
        self.verify_start()
        self.verify_end()
        self.parse_tagname()
        self.parse_attributes()

    def __repr__(self):
        if self.name is None:
            return "Empty Tag"
        return f"Tag: {self.name.chars}"

    def is_element_added_to_tag(
        self,
        element: Tag
        | CData
        | Comment
        | Doctype
        | Element
        | Attlist
        | Notation
        | Entity
        | IncludeIgnore
        | Instructions
        | ParsedText
        | XmlDeclaration,
    ) -> bool:
        from .attlist import Attlist
        from .doctype import Doctype
        from .comment import Comment
        from .element import Element
        from .entity import Entity
        from .includeignore import IncludeIgnore
        from .instructions import Instructions
        from .notation import Notation
        from .parsedtext import ParsedText
        from .cdata import CData
        from .xmldecl import XmlDeclaration

        if self.closed:
            return False
        if len(self.children) > 0 and isinstance(self.children[-1], Doctype):
            if self.children[-1].is_element_added_to_doctype(element):
                return True
        if len(self.children) > 0 and isinstance(self.children[-1], IncludeIgnore):
            if self.children[-1].is_element_added_to_includeignore(element):
                return True
        if len(self.children) > 0 and isinstance(self.children[-1], Tag):
            if self.children[-1].is_element_added_to_tag(element):
                return True
        if isinstance(
            element,
            (
                CData,
                Comment,
                Instructions,
                Tag,
            ),
        ):
            element.parent = self
            self.children.append(element)
            return True
        if isinstance(element, ParsedText):
            element.parent = self
            self.children.append(element)
            element.add_to_tree = False
            return True

        if isinstance(element, Doctype):
            self.err.add(element.tokens[0], CritErr.TAG_DOCTYPE_IN_TREE)
        if isinstance(element, Attlist):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_ATTLIST_IN_TREE)
        if isinstance(element, Element):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_ELEMENT_IN_TREE)
        if isinstance(element, Entity):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_ENTITY_IN_TREE)
        if isinstance(element, Notation):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_NOTATION_IN_TREE)
        if isinstance(element, IncludeIgnore):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_INCLUDEIGNORE_IN_TREE)
        if isinstance(element, XmlDeclaration):
            self.err.add(element.tokens[0], CritErr.TAG_XML_DECLARATION_IN_TREE)
        element.parent = self
        self.children.append(element)
        return False

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<"):
            self.current += 1
            return
        self.err.add(self.tokens[0], CritErr.ELEMENT_MISSING_START_SEQUENCE)

    def verify_end(self) -> None:
        if self.current == self.end:
            self.err.add(self.tokens[-1], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)
            return
        if self.tokens[self.end].match(">"):
            self.end -= 1
            return
        if self.tokens[self.end].match("/>"):
            self.closed = True
            self.end -= 1
            return
        if self.tokens[self.end].endswith(">"):
            self.end -= 1
            self.err.add(self.tokens[-1], CritErr.ELEMENT_WRONG_END_SEQUENCE, -1)
            return
        self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)

    def close_tag(self, closing_tagname: str) -> bool:
        if self.name is None:
            return False
        if self.name.chars.strip() == closing_tagname.strip():
            self.closed = True
            return True
        return False

    def parse_tagname(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[0], CritErr.ELEMENT_NAME_MISSING)
            return
        self.name = self.tokens[self.current]
        if not self.name.is_xmlname():
            self.err.add(self.name, CritErr.XMLNAME_ERROR)
        self.current += 1

    def parse_attribute_value(self) -> None | Token:
        attribute_value: Token | None = None
        if not self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_NOT_IN_QUOTES)
        else:
            self.current += 1
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING)
            return
        if self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING)
            return
        attribute_value = self.tokens[self.current]
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_NOT_IN_QUOTES)
            return attribute_value
        self.current += 1
        if not self.tokens[self.current].is_quotes():
            self.err.add(attribute_value, CritErr.ELEMENT_VALUE_NOT_IN_QUOTES, -1)
        return attribute_value

    def parse_attributes(self) -> None:
        attribute: None | Attribute = None
        while self.current < self.end:
            if self.tokens[self.current].match("="):
                if attribute is None:
                    self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING_NAME)
                    self.current += 1
                    continue
                self.current += 1
                attribute_value = self.parse_attribute_value()
                if attribute_value is not None:
                    # verify_content_or_attribute_value(attribute_value, self.err)
                    attribute.value = attribute_value
                self.current += 1
                continue
            attribute = Attribute(self.tokens[self.current], self, self.err)
            self.attributes.append(attribute)
            self.current += 1
