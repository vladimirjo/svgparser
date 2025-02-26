from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector
    from xmlvalidator import XmlValidator

    from .doctype import Doctype
    from .includeignore import IncludeIgnore
    from .tag import Tag

from dtd.defattr import DefAttrDefaultsEnum
from dtd.defattr import DefAttrTypeEnum
from dtd.defattr import DtdAttributeDefinition
from errorcollector import CritErr


class Attlist:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.parent: Doctype | IncludeIgnore | XmlValidator | Tag | None = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.element_name: Token | None = None
        self.attr_defs: list[DtdAttributeDefinition] = []
        self.verify_start()
        self.verify_end()
        self.verify_and_get_element()
        if self.element_name is None:
            return
        self.get_definitions()

    def __repr__(self):
        if self.element_name is None:
            return "Attlist"
        return f"Attlist: {self.element_name.chars}"

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!ATTLIST"):
            self.err.add(self.tokens[0], CritErr.ELEMENT_MISSING_START_SEQUENCE)
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)
            return
        self.end -= 1

    def verify_and_get_element(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[0], CritErr.ELEMENT_NAME_MISSING, -1)
            self.valid = False
            return
        self.element_name = self.tokens[self.current]
        if not self.element_name.is_xmlname():
            self.err.add(self.element_name, CritErr.XMLNAME_ERROR)
        self.current += 1

    def get_attribute_name(self) -> Token | None:
        if self.current > self.end:
            return None
        name_pos = self.current
        self.current += 1
        attr_name = self.tokens[name_pos]
        if not attr_name.is_xmlname():
            self.err.add(attr_name, CritErr.XMLNAME_ERROR)
        return attr_name

    def get_attr_type(self) -> DefAttrTypeEnum | None:
        if self.current > self.end:
            return None
        if self.tokens[self.current] == "CDATA":
            self.current += 1
            return DefAttrTypeEnum.CDATA
        if self.tokens[self.current] == "NMTOKEN":
            self.current += 1
            return DefAttrTypeEnum.NMTOKEN
        if self.tokens[self.current] == "NMTOKENS":
            self.current += 1
            return DefAttrTypeEnum.NMTOKENS
        if self.tokens[self.current] == "ENTITY":
            self.current += 1
            return DefAttrTypeEnum.ENTITY
        if self.tokens[self.current] == "ENTITIES":
            self.current += 1
            return DefAttrTypeEnum.ENTITIES
        if self.tokens[self.current] == "ID":
            self.current += 1
            return DefAttrTypeEnum.ID
        if self.tokens[self.current] == "IDREF":
            self.current += 1
            return DefAttrTypeEnum.IDREF
        if self.tokens[self.current] == "IDREFS":
            self.current += 1
            return DefAttrTypeEnum.IDREFS
        if self.tokens[self.current] == "NOTATION":
            self.current += 1
            return DefAttrTypeEnum.NOTATION
        if self.tokens[self.current] == "(":
            self.current += 1
            return DefAttrTypeEnum.ENUM
        self.err.add(self.tokens[self.current], CritErr.ATTLIST_TYPE_NOT_RECOGNIZED)
        return None

    def get_attr_enum(self) -> list[Token] | None:
        enum_tokens: list[Token] = []
        is_last_token_pipe = True
        while self.current <= self.end and self.tokens[self.current] != ")":
            if self.tokens[self.current] == "|" and is_last_token_pipe:
                self.err.add(self.tokens[self.current], CritErr.ATTLIST_ENUM_SEQ_PIPE)
                self.current += 1
                continue
            if self.tokens[self.current] != "|" and not is_last_token_pipe:
                self.err.add(self.tokens[self.current], CritErr.ATTLIST_ENUM_PIPE_SEPARATION)
                self.current += 1
                continue
            if self.tokens[self.current] == "|" and not is_last_token_pipe:
                self.current += 1
                is_last_token_pipe = True
                continue
            if self.tokens[self.current] != "|" and is_last_token_pipe:
                if not self.tokens[self.current].is_nmtoken():
                    self.err.add(self.tokens[self.current], CritErr.NMTOKEN_ERROR)
                enum_tokens.append(self.tokens[self.current])
                self.current += 1
                is_last_token_pipe = False
                continue
        if self.tokens[self.current] == ")":
            self.current += 1
        for enum_token in enum_tokens:
            if enum_tokens.count(enum_token) > 1:
                self.err.add(enum_token, CritErr.ATTLIST_ENUM_DUPLICATE_TAGS)
        if len(enum_tokens) < 1:
            return None
        return enum_tokens

    def get_attr_default(self) -> DefAttrDefaultsEnum | None:
        if self.current > self.end:
            return None
        if self.tokens[self.current] == "#REQUIRED":
            self.current += 1
            return DefAttrDefaultsEnum.REQUIRED
        if self.tokens[self.current] == "#IMPLIED":
            self.current += 1
            return DefAttrDefaultsEnum.IMPLIED
        if self.tokens[self.current] == "#FIXED":
            self.current += 1
            return DefAttrDefaultsEnum.FIXED
        if self.tokens[self.current].is_quotes():
            return DefAttrDefaultsEnum.OPTIONAL
        self.err.add(self.tokens[self.current], CritErr.ATTLIST_DEFAULT_NOT_RECOGNIZED)
        return None

    def get_attr_literal(self) -> Token | None:
        if self.current > self.end:
            return None
        quotes_in_use = self.tokens[self.current]
        self.current += 1
        if self.current > self.end:
            return None
        attr_default = self.tokens[self.current]
        self.current += 1
        if self.current > self.end:
            return attr_default
        if quotes_in_use.chars == self.tokens[self.current].chars:
            self.current += 1
        return attr_default

    def get_definitions(self) -> None:
        while self.current <= self.end:
            attr_name = self.get_attribute_name()
            if attr_name is None:
                return
            attr_type = self.get_attr_type()
            if attr_type is None:
                return
            attr_enum: list[Token] | None = None
            if attr_type == DefAttrTypeEnum.ENUM:
                attr_enum = self.get_attr_enum()
            attr_default = self.get_attr_default()
            if attr_default is None:
                return
            attr_literal: Token | None = None
            if attr_default == DefAttrDefaultsEnum.OPTIONAL or attr_default == DefAttrDefaultsEnum.FIXED:
                attr_literal = self.get_attr_literal()
            self.attr_defs.append(DtdAttributeDefinition(attr_name, attr_type, attr_enum, attr_default, attr_literal))
