from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .xmlchar import XmlChar
    from .xmlchars import XmlChars


class XmlCharRef:
    def __init__(self, strchars: str, *xmlchars: XmlCharRef | XmlChar) -> None:
        self.strchars = strchars
        self.xmlchars: list[XmlChar | XmlCharRef] = []
        entity_id = xmlchars[0].entity_id
        for xmlchar in xmlchars:
            if entity_id != xmlchar.entity_id:
                raise ValueError()
            self.xmlchars.append(xmlchar)
        self.entity_id: int = entity_id

    def add_entity_id(self, entity_id: int) -> None:
        self.entity_id = entity_id

    def copy_with_new_entity_id(self, new_entity_id: int) -> XmlCharRef:
        new_xmlchars: list[XmlChar | XmlCharRef] = [
            xmlchar.copy_with_new_entity_id(new_entity_id) for xmlchar in self.xmlchars
        ]
        return XmlCharRef(self.strchars, *new_xmlchars)

    def __repr__(self) -> str:
        return self.strchars

    def __hash__(self):
        return hash(self.strchars)

    def __eq__(self, chars: str | XmlChars | XmlChar | XmlCharRef) -> bool:
        from .xmlchar import XmlChar
        from .xmlchars import XmlChars

        if isinstance(chars, XmlChars | XmlChar | XmlCharRef):
            return self.strchars == chars.strchars
        if isinstance(chars, str):
            return self.strchars == chars
        return False
