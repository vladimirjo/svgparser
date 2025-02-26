from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector
    from xmlvalidator import XmlValidator

    from .doctype import Doctype
    from .includeignore import IncludeIgnore
    from .tag import Tag

from errorcollector import CritErr


class Element:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: Doctype | IncludeIgnore | XmlValidator | Tag | None = None
        self.element: Token | None = None
        self.definition_tokens: list[Token] | None = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_element()
        self.verify_and_get_definition_tokens()

    def __repr__(self):
        if self.element is None:
            return "Element"
        return f"Element: {self.element.chars}"

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!ELEMENT"):
            self.err.add(self.tokens[0], CritErr.DTD_ELEMENT_MISSING_START_SEQUENCE)
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            self.err.add(self.tokens[self.end], CritErr.DTD_ELEMENT_MISSING_RIGHT_BRACKET)
            return
        self.end -= 1

    def verify_and_get_element(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[0], CritErr.DTD_ELEMENT_MISSING_NAME, -1)
            return
        self.element = self.tokens[self.current]
        if not self.element.is_xmlname():
            self.err.add(self.element, CritErr.XMLNAME_ERROR)
        self.current += 1

    def verify_and_get_definition_tokens(self) -> None:
        self.definition_tokens = self.tokens[self.current : self.end + 1]
