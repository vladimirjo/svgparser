from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from buffer import Token


if TYPE_CHECKING:
    pass

from enum import Enum
from enum import auto


class DefAttrDefaultsEnum(Enum):
    REQUIRED = auto()
    IMPLIED = auto()
    OPTIONAL = auto()
    FIXED = auto()


class DefAttrTypeEnum(Enum):
    CDATA = auto()
    NMTOKEN = auto()
    NMTOKENS = auto()
    ENUM = auto()
    ENTITY = auto()
    ENTITIES = auto()
    ID = auto()
    IDREF = auto()
    IDREFS = auto()
    NOTATION = auto()


@dataclass
class DtdAttributeDefinition:
    attr_name: Token
    attr_type: DefAttrTypeEnum
    attr_enum: list[Token] | None
    attr_default: DefAttrDefaultsEnum
    attr_literal: Token | None
