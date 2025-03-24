from __future__ import annotations

from enum import Enum
from enum import auto
from typing import TYPE_CHECKING

from errcl import CritErr


if TYPE_CHECKING:
    from errcl import ErrorCollector as ErrCl
    from xmltokens import XmlChars
    from xmltokens import XmlMarkup


class EntityType(Enum):
    INTERNAL = auto()
    EXTERNAL_SYSTEM = auto()
    EXTERNAL_PUBLIC = auto()


class Entity:
    def __init__(self, startseq: XmlMarkup, errcl: ErrCl) -> None:
        self.startseq: XmlMarkup = startseq
        self.tokens: list[XmlChars] = []
        self.tokens.append(startseq.xmlchars)
        self.errcl = errcl
        self.parent = None
        self.is_finished = False
        self.is_pent: bool | None = None
        self.name: XmlChars | None = None
        self.is_syslit: bool = False
        self.entity_type: EntityType | None = None
        self.internal_value: XmlChars | None = None
        self.public_value: XmlChars | None = None
        self.system_value: XmlChars | None = None
        self.is_ndata: bool = False
        self.ndata_value: XmlChars | None = None
        self.undef_trail: list[XmlChars] = []

    def check_integrity(self) -> None:
        if self.name is None:
            self.errcl.add(self.startseq, CritErr.ELEMENT_INVALID)
            return
        if self.entity_type is None:
            self.errcl.add(self.startseq, CritErr.ELEMENT_INVALID)
            return
        if self.endseq is None:
            self.errcl.add(self.startseq, CritErr.ELEMENT_INVALID)

    def add_quotes(self, quotes: XmlMarkup) -> None:


    def can_xmlchars_be_added(self, xmlchars: XmlChars) -> bool:
        if self.is_finished:
            return False
        if xmlchars == "<":
            self.is_finished = True
            return False
        if xmlchars == ">":
            self.is_finished = True
            return True
        if self.is_pent is None:
            if xmlchars == "%":
                self.is_pent = True
                return True
            self.is_pent = False
        if self.name is None:
            self.name = xmlchars
            if not self.name.is_xmlname():
                self.errcl.add(self.name, CritErr.XMLNAME_ERROR)
            return True
        if self.entity_type is None:
            if xmlchars == "SYSTEM":
                self.is_syslit = True
                self.entity_type = EntityType.EXTERNAL_SYSTEM
                return True
            if xmlchars == "PUBLIC":
                self.is_syslit = True
                self.entity_type = EntityType.EXTERNAL_PUBLIC
                return True
            self.entity_type = EntityType.INTERNAL
        if self.entity_type == EntityType.INTERNAL and self.internal_value is None:
            self.internal_value = xmlchars.strip_quotes()
            return True
        if self.entity_type == EntityType.EXTERNAL_SYSTEM and self.system_value is None:
            self.is_syslit = False
            self.system_value = xmlchars.strip_quotes()
            return True
        if self.entity_type == EntityType.EXTERNAL_PUBLIC:
            if self.public_value is None:
                self.public_value = xmlchars.strip_quotes()
                return True
            if self.system_value is None:
                self.is_syslit = False
                self.system_value = xmlchars.strip_quotes()
                return True
        if not self.is_pent and xmlchars == "NDATA":
            self.is_ndata = True
            return True
        if self.is_ndata and self.ndata_value is None:
            self.ndata_value = xmlchars
            return True
        return False
