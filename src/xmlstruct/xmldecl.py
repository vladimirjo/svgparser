from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector
    from xmlvalidator import XmlValidator

    from .tag import Tag

from errorcollector import CritErr

from .attr import Attribute


class XmlDeclaration:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: XmlValidator | Tag | None = None
        self.attributes: list[Attribute] = []
        self.verify_start()
        self.verify_end()
        self.parse_attributes()
        self.verify_xml_declaration()

    def __repr__(self):
        return "XmlDeclaration"

    def verify_xml_declaration(self) -> None:
        if not (self.tokens[0].buffer_slot == 0 and self.tokens[0].buffer_pointer == 0):
            self.err.add(self.tokens[0], CritErr.XMLDECL_NOT_FIRST_LINE)
        if len(self.attributes) >= 1:
            self.verify_attribute_version(self.attributes[0])
        if len(self.attributes) >= 2:
            self.verify_attribute_encoding(self.attributes[1])
        if len(self.attributes) >= 3:
            self.verify_attribute_standalone(self.attributes[2])
        if len(self.attributes) > 3:
            self.err.add(self.attributes[3].name, CritErr.XMLDECL_OVER_THREE_ATTRS)

    def verify_attribute_version(self, attribute: Attribute) -> None:
        if not attribute.name.match("version"):
            self.err.add(attribute.name, CritErr.XMLDECL_FIRST_ATTR_WRONG)
            return
        if attribute.value is None:
            self.err.add(attribute.name, CritErr.XMLDECL_FIRST_ATTR_MISSING_VALUE, -1)
            return
        if not attribute.value.match("1.0"):
            self.err.add(attribute.value, CritErr.XMLDECL_FIRST_ATTR_NOT_VALID_VALUE)
            return

    def verify_attribute_encoding(self, attribute: Attribute) -> None:
        if not attribute.name.match("encoding"):
            self.err.add(attribute.name, CritErr.XMLDECL_SECOND_ATTR_WRONG)
            return
        if attribute.value is None:
            self.err.add(attribute.name, CritErr.XMLDECL_SECOND_ATTR_MISSING_VALUE, -1)
            return
        if attribute.value.chars not in {"UTF-8", "UTF-16"}:
            self.err.add(attribute.value, CritErr.XMLDECL_SECOND_ATTR_NOT_VALID_VALUE)
            return

    def verify_attribute_standalone(self, attribute: Attribute) -> None:
        if not attribute.name.match("standalone"):
            self.err.add(attribute.name, CritErr.XMLDECL_THIRD_ATTR_WRONG)
            return
        if attribute.value is None:
            self.err.add(attribute.name, CritErr.XMLDECL_THIRD_ATTR_MISSING_VALUE, -1)
            return
        if attribute.value.chars not in {"yes", "no"}:
            self.err.add(attribute.value, CritErr.XMLDECL_THIRD_ATTR_NOT_VALID_VALUE)
            return

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<?xml"):
            self.current += 1
            return
        self.err.add(self.tokens[0], CritErr.ELEMENT_WRONG_START_SEQUENCE)

    def verify_end(self) -> None:
        if self.current == self.end:
            self.err.add(self.tokens[-1], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)
            return
        if self.tokens[self.end].match("?>"):
            self.end -= 1
            return
        if self.tokens[self.end].endswith(">"):
            self.end -= 1
            self.err.add(self.tokens[-1], CritErr.ELEMENT_WRONG_END_SEQUENCE, -1)
            return
        self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)

    def parse_attribute_value(self) -> None | Token:
        attribute_value: Token | None = None
        if not self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_NOT_IN_QUOTES)
        else:
            self.current += 1
        if self.current == self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING)
            return
        if self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING)
            return
        attribute_value = self.tokens[self.current]
        if self.current == self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_NOT_IN_QUOTES)
            return attribute_value
        self.current += 1
        if not self.tokens[self.current].is_quotes():
            self.err.add(attribute_value, CritErr.ELEMENT_VALUE_NOT_IN_QUOTES, -1)
        return attribute_value

    def parse_attributes(self) -> None:
        attribute: Attribute | None = None
        while self.current < self.end:
            if self.tokens[self.current].match("="):
                if attribute is None:
                    self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING_NAME)
                    self.current += 1
                    continue
                self.current += 1
                attribute_value = self.parse_attribute_value()
                if attribute_value is not None:
                    # verify_content_or_attribute_value(attribute_value, self.err)
                    attribute.value = attribute_value
                self.current += 1
                continue
            attribute = Attribute(self.tokens[self.current], self, self.err)
            self.attributes.append(attribute)
            self.current += 1
