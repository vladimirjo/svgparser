from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector
    from bckup.xmlvalidator import XmlValidator
    from .tag import Tag

from errorcollector import CritErr


class CData:
    def __init__(
        self,
        element_tokens: list[Token],
        error_collector: ErrorCollector,
    ) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: XmlValidator | Tag | None = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_content()

    def __repr__(self):
        if self.content is None:
            return "Empty Cdata"
        return f"Cdata: {self.content.chars}"

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<![CDATA["):
            self.current += 1
            return
        self.err.add(self.tokens[0], CritErr.ELEMENT_MISSING_START_SEQUENCE)

    def verify_end(self) -> None:
        if self.current == self.end:
            self.err.add(self.tokens[-1], CritErr.ELEMENT_MISSING_END_SEQUENCE)
        if self.tokens[self.end].match("]]>"):
            self.end -= 1
            return
        if self.err is not None:
            self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE)

    def verify_and_get_content(self) -> None:
        if self.current > self.end:
            if self.err is not None:
                self.err.add(self.tokens[self.current], CritErr.ELEMENT_EMPTY)
            return
        if len(self.tokens[self.current : self.end]) > 1:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_INVALID)
            return
        self.content = self.tokens[self.current]
        self.current += 1
