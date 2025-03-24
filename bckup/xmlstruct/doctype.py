from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector
    from bckup.xmlvalidator import XmlValidator

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


class Doctype:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: XmlValidator | Tag | None = None
        self.rootname: Token | None = None
        self.extern_system: Token | None = None
        self.extern_public: Token | None = None
        self.intern_declarations_closed = True
        self.closed = False
        self.children: list[Element | Attlist | Entity | Notation | IncludeIgnore | Comment | Instructions] = []
        self.verify_start()
        self.verify_end()
        self.verify_and_get_root()
        self.optional_verify_and_get_extern_dtd()
        self.optional_verify_and_get_intern_dtd()
        self.check_trailing()

    def __repr__(self):
        if self.rootname is None:
            return "Doctype"
        return f"Doctype: {self.rootname.chars}"

    def get_active_includeignore(self) -> IncludeIgnore | None:
        if len(self.children) == 0:
            return None
        active_includeignore: IncludeIgnore | None = None
        if isinstance(self.children[-1], IncludeIgnore) and not self.children[-1].closed:
            active_includeignore = self.children[-1]
        else:
            return active_includeignore
        while len(active_includeignore.children) > 0:
            if (
                isinstance(active_includeignore.children[-1], IncludeIgnore)
                and not active_includeignore.children[-1].closed
            ):
                active_includeignore = active_includeignore.children[-1]
            else:
                break
        return active_includeignore

    def is_ending(self, text: ParsedText) -> bool:
        if text.content is None:
            return False
        first_stop = text.content.search_preceded_by_whitespace("]")
        if first_stop < 0:
            return False
        second_stop = text.content.search_preceded_by_whitespace(">", first_stop)
        if second_stop < 0:
            return False
        text.content.remove_length_from_left(second_stop)
        return True

    def is_element_added_to_doctype(
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
        from .comment import Comment
        from .element import Element
        from .entity import Entity
        from .includeignore import IncludeIgnore
        from .instructions import Instructions
        from .notation import Notation
        from .parsedtext import ParsedText
        from .cdata import CData
        from .tag import Tag
        from .xmldecl import XmlDeclaration

        if self.closed:
            return False
        if len(self.children) > 0 and isinstance(self.children[-1], IncludeIgnore):
            if self.children[-1].is_element_added_to_includeignore(element):
                return True
        if isinstance(
            element,
            (
                Element,
                Attlist,
                Entity,
                Notation,
                IncludeIgnore,
                Comment,
                Instructions,
            ),
        ):
            element.parent = self
            self.children.append(element)
            return True
        if isinstance(element, ParsedText) and self.is_ending(element):
            self.closed = True
            return True
        self.err.add(self.tokens[0], CritErr.DOCTYPE_NOT_CLOSED)
        if isinstance(element, CData):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_CDATA_IN_TREE)
        if isinstance(element, Tag):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_TAG_IN_TREE)
        if isinstance(element, ParsedText):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_PARSED_TEXT_IN_TREE)
        if isinstance(element, Doctype):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_DOCTYPE_IN_TREE)
        if isinstance(element, XmlDeclaration):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_XML_DECLARATION_IN_TREE)
        return False

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!DOCTYPE"):
            self.err.add(self.tokens[0], CritErr.DOCTYPE_MISSING_START_SEQUENCE)
        self.current += 1
        return

    def verify_end(self) -> None:
        if self.tokens[self.end].match(">"):
            self.closed = True
            self.end -= 1
            return

    def verify_and_get_root(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[0], CritErr.DOCTYPE_MISSING_ROOT_CLOSING)
            return
        self.rootname = self.tokens[self.current]
        if not self.rootname.is_xmlname():
            self.err.add(self.rootname, CritErr.XMLNAME_ERROR)
        self.current += 1

    def optional_verify_and_get_extern_dtd(self) -> None:
        if self.current > self.end:
            return
        if self.tokens[self.current].match("SYSTEM"):
            self.current += 1
            self.extern_system = self.verify_and_get_quotes_value("System identifier")
        elif self.tokens[self.current].match("PUBLIC"):
            self.current += 1
            self.extern_public = self.verify_and_get_quotes_value("Public identifier")
            self.extern_system = self.verify_and_get_quotes_value("System identifier")

    def verify_and_get_quotes_value(self, identifier: str) -> Token | None:
        quotes_value: None | Token = None
        if self.current > self.end:
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_VALUE,
                -1,
                {identifier: identifier},
            )
            return
        # The left quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_LEFT_QUOTE,
                0,
                {identifier: identifier},
            )
        # The quotes value
        if self.current > self.end or self.tokens[self.current].is_quotes():
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_VALUE,
                0,
                {identifier: identifier},
            )
            return
        else:
            quotes_value = self.tokens[self.current]
            self.current += 1
        # The right quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_RIGHT_QUOTE,
                0,
                {identifier: identifier},
            )
        return quotes_value

    def optional_verify_and_get_intern_dtd(self) -> None:
        if self.current > self.end:
            return
        if self.tokens[self.current].match("["):
            self.current += 1
            self.intern_declarations_closed = False
        else:
            self.err.add(self.tokens[self.current], CritErr.DOCTYPE_INVALID_INTERNAL_DEF_START)
            return

        if self.current > self.end:
            return
        if self.tokens[self.current].match("]"):
            self.current += 1
            self.intern_declarations_closed = True
        else:
            self.err.add(self.tokens[self.current], CritErr.DOCTYPE_INVALID_INTERNAL_DEF_END)
            return

    def check_trailing(self) -> None:
        if self.current <= self.end:
            self.err.add(self.tokens[0], CritErr.INVALID_TRAILING_SEQUENCE)
