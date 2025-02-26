from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector
    from xmlvalidator import XmlValidator

    from .tag import Tag

from errorcollector import CritErr


class ParsedText:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.parent: XmlValidator | Tag | None = None
        self.content: Token | None = None
        self.add_to_tree: bool = True
        self.get_content()

    def is_empty(self) -> bool:
        if self.content is None:
            return True
        if len(self.content.chars) == 0:
            return True
        if self.content.chars.isspace():
            return True
        return False

    def get_content(self) -> None:
        if len(self.tokens) > 1:
            self.err.add(self.tokens[0], CritErr.ELEMENT_INVALID)
            return
        self.content = self.tokens[0]

    def verify_content(self) -> None:
        if self.content is None:
            self.err.add(self.tokens[0], CritErr.ELEMENT_INVALID)
            return
        # verify_content_or_attribute_value(self.content, self.err)

    def __repr__(self):
        if self.content is None:
            return "Empty ParsedText"
        return f"ParsedText: {self.content.chars.strip()}"
