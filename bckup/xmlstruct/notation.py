from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector
    from bckup.xmlvalidator import XmlValidator

    from .doctype import Doctype
    from .includeignore import IncludeIgnore
    from .tag import Tag

from errorcollector import CritErr


class Notation:
    def __init__(self, tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: Doctype | IncludeIgnore | XmlValidator | Tag | None = None
        self.notation: Token | None = None
        self.value: Token | None = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_notation()
        self.verify_and_get_value()
        self.check_trailing()

    def __repr__(self):
        if self.notation is None:
            return "Notation"
        if self.value is None:
            return f"Notation: {self.notation.chars}"
        return f"Notation: {self.notation.chars} {self.value.chars}"

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!NOTATION"):
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_START_SEQUENCE)
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            self.err.add(self.tokens[self.end], CritErr.DTD_NOTATION_MISSING_RIGHT_BRACKET, -1)
            return
        self.end -= 1

    def verify_and_get_notation(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_NAME, -1)
        else:
            self.element = self.tokens[self.current]
            if not self.element.is_xmlname():
                self.err.add(self.element, CritErr.XMLNAME_ERROR)
            self.current += 1

    def verify_and_get_value(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_VALUE, -1)
            return
        # The left quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_VALUE_LEFT_QUOTE)
        # The notation value
        if self.current > self.end or self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_VALUE)
            return
        else:
            self.substitute_text = self.tokens[self.current]
            self.current += 1
        # The right quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_VALUE_RIGHT_QUOTE)

    def check_trailing(self) -> None:
        if self.current <= self.end:
            self.err.add(self.tokens[0], CritErr.INVALID_TRAILING_SEQUENCE, -1)
