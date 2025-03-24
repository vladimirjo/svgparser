from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .xmlcharref import XmlCharRef
    from .xmlchars import XmlChars


class XmlChar:
    def __init__(self, char: str, buffer_slot: int, buffer_pos: int, entity_id: int) -> None:
        self.strchars = char
        self.buffer_slot = buffer_slot
        self.buffer_pos = buffer_pos
        self.entity_id: int = entity_id

    def add_entity_id(self, entity_id: int) -> None:
        self.entity_id = entity_id

    def copy_with_new_entity_id(self, new_entity_id: int) -> XmlChar:
        return XmlChar(self.strchars, self.buffer_slot, self.buffer_pos, new_entity_id)

    def __repr__(self) -> str:
        return self.strchars

    def __hash__(self):
        return hash(self.strchars)

    def __eq__(self, chars: str | XmlChars | XmlChar | XmlCharRef) -> bool:
        from .xmlcharref import XmlCharRef
        from .xmlchars import XmlChars

        if isinstance(chars, XmlChars | XmlChar | XmlCharRef):
            return self.strchars == chars.strchars
        if isinstance(chars, str):
            return self.strchars == chars
        return False
