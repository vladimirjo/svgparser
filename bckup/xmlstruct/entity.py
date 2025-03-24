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


class Entity:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: Doctype | IncludeIgnore | XmlValidator | Tag | None = None
        self.name: Token | None = None
        self.intern_value: Token | None = None
        self.extern_system: Token | None = None
        self.extern_public: Token | None = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_name()
        self.verify_and_get_entity_type()

    def __repr__(self):
        if self.name is None:
            return "Entity"
        return f"Entity: {self.name.chars}"

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!ENTITY"):
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_MISSING_START_SEQUENCE)
        else:
            self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)
        else:
            self.end -= 1

    def verify_and_get_name(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_NAME_MISSING, -1)
        else:
            self.name = self.tokens[self.current]
            if not self.name.is_xmlname():
                self.err.add(self.name, CritErr.XMLNAME_ERROR)
            self.current += 1

    def verify_and_get_entity_type(self) -> None:
        if self.current > self.end:
            self.intern_value = self.verify_and_get_quotes_value("Entity substition")
            return
        if self.tokens[self.current].match("SYSTEM"):
            self.current += 1
            self.extern_system = self.verify_and_get_quotes_value("System identifier")
        elif self.tokens[self.current].match("PUBLIC"):
            self.current += 1
            self.extern_public = self.verify_and_get_quotes_value("Public identifier")
            self.extern_system = self.verify_and_get_quotes_value("System identifier")
        else:
            self.intern_value = self.verify_and_get_quotes_value("Entity substition")

    def verify_and_get_quotes_value(self, identifier: str) -> None | Token:
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
        if self.current > self.end and not self.tokens[self.current].is_quotes():
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
