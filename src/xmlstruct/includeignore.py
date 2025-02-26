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
    from .instructions import Instructions
    from .notation import Notation
    from .parsedtext import ParsedText
    from .tag import Tag
    from .xmldecl import XmlDeclaration

from errorcollector import CritErr


class IncludeIgnore:
    def __init__(self, tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.include: bool = False
        self.closed: bool = False
        self.parent: Doctype | IncludeIgnore | XmlValidator | Tag | None = None
        self.children: list[Element | Attlist | Entity | Notation | IncludeIgnore | Comment | Instructions] = []
        self.verify_start()
        self.verify_end()
        self.verify_conditional()
        self.verify_begin_section()
        self.check_trailing()

    def __repr__(self):
        if self.include:
            return "Include"
        return "Ignore"

    # def get_active_includeignore(self) -> None | IncludeIgnore:
    #     if len(self.children) == 0:
    #         return None
    #     active_includeignore: None | IncludeIgnore = None
    #     if isinstance(self.children[-1], IncludeIgnore) and not self.children[-1].closed:
    #         active_includeignore = self.children[-1]
    #     else:
    #         return active_includeignore
    #     while len(active_includeignore.children) > 0:
    #         if (
    #             isinstance(active_includeignore.children[-1], IncludeIgnore)
    #             and not active_includeignore.children[-1].closed
    #         ):
    #             active_includeignore = active_includeignore.children[-1]
    #         else:
    #             break
    #     return active_includeignore

    def is_ending(self, text: ParsedText) -> bool:
        if text.content is None:
            return False
        length_to_remove = text.content.search_preceded_by_whitespace("]]>")
        if length_to_remove < 0:
            return False
        text.content.remove_length_from_left(length_to_remove)
        return True

    def is_element_added_to_includeignore(
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
        from .cdata import CData
        from .comment import Comment
        from .doctype import Doctype
        from .element import Element
        from .entity import Entity
        from .instructions import Instructions
        from .notation import Notation
        from .parsedtext import ParsedText
        from .tag import Tag
        from .xmldecl import XmlDeclaration

        if self.closed:
            return False
        if len(self.children) > 0 and isinstance(self.children[-1], IncludeIgnore):
            if self.children[-1].is_element_added_to_includeignore(element):
                return True
        # if self.current_includeignore is not None:
        #     if isinstance(element, IncludeIgnore):
        #         self.current_includeignore.children.append(element)
        #         element.parent = self.current_includeignore
        #         self.current_includeignore = element
        #     elif isinstance(
        #         element,
        #         (
        #             Element,
        #             Attlist,
        #             Entity,
        #             Notation,
        #             IncludeIgnore,
        #             Comment,
        #             Instructions,
        #         ),
        #     ):
        #         self.current_includeignore.children.append(element)
        #         return True
        #     elif isinstance(element, ParsedText) and self.is_ending(element):
        #         self.current_includeignore.closed = True
        #         self.current_includeignore = self.current_includeignore.parent
        #         return True
        #     else:
        #         if self.error_collector is not None:
        #             self.error_collector.add_token_start(self.tokens[0], "Dtd conditional was not properly closed.")
        #             if isinstance(element, CData):
        #                 self.error_collector.add_token_start(
        #                     element.tokens[0], "Cdata cannot be added to Doctype tree."
        #                 )
        #             if isinstance(element, Attribute):
        #                 self.error_collector.add_token_start(element.name, "Attribute cannot be added to Doctype tree.")
        #             if isinstance(element, Tag):
        #                 self.error_collector.add_token_start(element.tokens[0], "Tag cannot be added to Doctype tree.")
        #             if isinstance(element, ParsedText):
        #                 self.error_collector.add_token_start(
        #                     element.tokens[0], "Parsed text cannot be added to Doctype tree."
        #                 )
        #             if isinstance(element, XmlDeclaration):
        #                 self.error_collector.add_token_start(
        #                     element.tokens[0], "Xml declaration cannot be added to Doctype tree."
        #                 )
        #         return False
        # if isinstance(element, IncludeIgnore):
        #     element.parent = self
        #     self.children.append(element)
        #     return True
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
        self.err.add(self.tokens[0], CritErr.INCLUDEIGNORE_NOT_CLOSED)
        if isinstance(element, CData):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_CDATA_IN_TREE)
        if isinstance(element, Tag):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_TAG_IN_TREE)
        if isinstance(element, ParsedText):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_PARSED_TEXT_IN_TREE)
        if isinstance(element, Doctype):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_DOCTYPE_IN_TREE)
        if isinstance(element, XmlDeclaration):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_XML_DECLARATION_IN_TREE)
        return False

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!["):
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_MISSING_START_SEQUENCE)
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match("]]>"):
            return
        self.closed = True
        self.end -= 1

    def verify_conditional(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_MISSING_CONDITION)
        if self.tokens[self.current].match("INCLUDE"):
            self.include = True
            self.current += 1
        elif self.tokens[self.current].match("IGNORE"):
            self.current += 1
        else:
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_CONDITION_NOT_RECOGNIZED)

    def verify_begin_section(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_CONDITION_START_MISSING)
        if not self.tokens[self.current].match("["):
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_CONDITION_START_NOT_RECOGNIZED)
        self.current += 1

    def check_trailing(self) -> None:
        if self.current <= self.end:
            self.err.add(self.tokens[0], CritErr.INVALID_TRAILING_SEQUENCE, -1)
