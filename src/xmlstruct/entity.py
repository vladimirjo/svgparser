from __future__ import annotations

from enum import Enum
from enum import auto
from typing import TYPE_CHECKING

from errcl import CritErr


if TYPE_CHECKING:
    from dtd.dtdcore import Dtd
    from errcl import ErrorCollector
    from xmltokens import XmlProccesor
    from xmlvalidator import XmlValidator

    from .doctype import Doctype
    from .includeignore import IncludeIgnore
    from .tag import Tag

from xmltokens import XmlChars


class EntityType(Enum):
    INTERNAL = auto()
    EXTERNAL_SYSTEM = auto()
    EXTERNAL_PUBLIC = auto()


class Entity:
    def __init__(
        self,
        proc: XmlProccesor,
        parent: Tag | Doctype | IncludeIgnore | XmlValidator,
        dtd: Dtd,
        err: ErrorCollector,
    ) -> None:
        self.proc = proc
        self.dtd = dtd
        self.parent = parent
        self.err = err
        self.tokens: list[XmlChars] = []
        self.startseq = XmlChars()
        self.endseq = XmlChars()
        self.is_pent: bool = False
        self.name = XmlChars()
        self.internal_value= XmlChars()
        self.entity_type: EntityType | None = None
        self.value = XmlChars()
        self.
        self.is_syslit: bool = False
        self.public_value: XmlChars | None = None
        self.system_value: XmlChars | None = None
        self.is_ndata: bool = False
        self.ndata_value: XmlChars | None = None
        self.undef_trail: list[XmlChars] = []

    def parse_startseq(self) -> XmlChars:
        startseq = self.proc.read(0, len("<!ENTITY"))
        if startseq is None:
            raise ValueError()
        self.proc.move(len("<!ENTITY"))
        return startseq

    def check_integrity(self) -> None:
        if self.name is None:
            self.err.add(self.startseq, CritErr.ELEMENT_INVALID)
            return
        if self.entity_type is None:
            self.err.add(self.startseq, CritErr.ELEMENT_INVALID)
            return
        if self.endseq is None:
            self.err.add(self.startseq, CritErr.ELEMENT_INVALID)

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
                self.err.add(self.name, CritErr.XMLNAME_ERROR)
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
