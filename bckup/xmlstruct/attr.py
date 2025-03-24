from __future__ import annotations

from typing import TYPE_CHECKING

from errorcollector import CritErr


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector

    from .tag import Tag
    from .xmldecl import XmlDeclaration


class Attribute:
    def __init__(
        self,
        name_token: Token,
        parent: None | Tag | XmlDeclaration,
        error_collector: ErrorCollector,
    ) -> None:
        self.name = name_token
        self.parent = parent
        self.err = error_collector
        if not self.name.is_xmlname():
            self.err.add(self.name, CritErr.XMLNAME_ERROR)
        self.value: None | Token = None

    def add_value(self, value_token: Token) -> None:
        self.value = value_token

    def __repr__(self):
        return f"Attribute: {self.name.chars}"
