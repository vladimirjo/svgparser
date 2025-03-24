from __future__ import annotations

from typing import TYPE_CHECKING

from errorcollector import ValidErr


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector
    from bckup.xmlvalidator import CData
    from bckup.xmlvalidator import ParsedText
    from bckup.xmlvalidator import Tag
    from dtd.defattr import DtdAttributeDefinition


from .defattr import DefAttrDefaultsEnum
from .defattr import DefAttrTypeEnum
from .defelem import DefElemAny
from .defelem import DefElemDefined
from .defelem import DefElemEmpty
from .defelem import DefElemMixed
from .valelem import ValElemTree


class DtdCData:
    def __init__(self, content: Token) -> None:
        self.content = content

    def get_token(self) -> Token:
        return self.content


class DtdTag:
    def __init__(self, name: Token) -> None:
        self.name: Token = name
        self.child_elements: list[DtdTag | DtdCData] = []
        self.attrs: list[DtdAttr] = []

    def get_token(self) -> Token:
        return self.name


class DtdAttr:
    def __init__(self, parent_tag: DtdTag, name: Token, value: Token) -> None:
        self.parent_tag = parent_tag
        self.name = name
        self.value = value


class DtdCore:
    def __init__(
        self,
        error_collector: ErrorCollector,
        root: Token | None = None,
    ) -> None:
        self.err = error_collector
        self.root = root
        self.element_definitions: dict[Token, DefElemDefined | DefElemMixed | DefElemAny | DefElemEmpty] = {}
        # self.attr_defs[element_name][attr_name]
        self.attr_defs: dict[Token, dict[Token, DtdAttributeDefinition]] = {}
        self.attr_ids: set[Token] = set()

    def define_element(
        self,
        element_name: Token,
        tokens: list[Token],
    ) -> None:
        if element_name in self.element_definitions:
            self.err.add(element_name, ValidErr.ELEMENT_ALREADY_DEFINED)
            return
        if len(tokens) == 0:
            self.err.add(element_name, ValidErr.ELEMENT_NO_DEFINITION)
            return
        if len(tokens) == 1 and tokens[0] == "ANY":
            self.element_definitions[element_name] = DefElemAny()
            return
        if len(tokens) == 1 and tokens[0] == "EMPTY":
            self.element_definitions[element_name] = DefElemEmpty()
            return
        for token in tokens:
            if token == "#PCDATA":
                mixed_content = DefElemMixed(tokens, self.err)
                if mixed_content.is_definition_valid:
                    self.element_definitions[element_name] = mixed_content
                return
        self.element_definitions[element_name] = DefElemDefined(tokens)

    def validate_parsed_element_with_element_definitions(
        self, parsed_element: Token, parsed_child_elements: list[Tag | CData | ParsedText]
    ) -> None:
        if parsed_element not in self.element_definitions:
            self.err.add(parsed_element, ValidErr.UNDEFINED_ELEMENT)
            return
        element_definition = self.element_definitions[parsed_element]
        #######################################################
        # convert child elements in mixed content elements
        mixed_content_elements: list[DtdTag | DtdCData] = []
        for child_element in parsed_child_elements:
            if isinstance(child_element, Tag) and child_element.name is not None:
                mixed_content_elements.append(DtdTag(child_element.name))
            if isinstance(child_element, CData | ParsedText) and child_element.content is not None:
                if len(mixed_content_elements) > 0 and isinstance(mixed_content_elements[-1], DtdCData):
                    mixed_content_elements[-1].content.add_token(child_element.content)
                else:
                    mixed_content_elements.append(DtdCData(child_element.content))
        #######################################################
        if isinstance(element_definition, DefElemAny):
            return
        if isinstance(element_definition, DefElemEmpty):
            return
        if isinstance(element_definition, DefElemMixed):
            element_definition.validate_elements(mixed_content_elements)
            return
        if isinstance(element_definition, DefElemDefined):
            tree = ValElemTree(element_definition, self.err)
            non_mixed_child_elements: list[Token] = []
            for child_element in mixed_content_elements:
                if isinstance(child_element, DtdCData):
                    self.err.add(child_element.content, ValidErr.NO_PARSED_TEXT_IN_CONTENT)
                    continue
                non_mixed_child_elements.append(child_element.name)
            tree.validate_elements(non_mixed_child_elements)
            return
        return

    def define_attlist(self, element_name: Token, attr_defs: list[DtdAttributeDefinition]) -> None:
        for attr_def in attr_defs:
            if element_name in self.attr_defs:
                if attr_def.attr_name in self.attr_defs[element_name]:
                    pass
                    # error
                else:
                    self.attr_defs[element_name][attr_def.attr_name] = attr_def
            else:
                self.attr_defs[element_name] = {attr_def.attr_name: attr_def}

    def validate_parsed_element_and_attribute_with_attr_defs(
        self,
        element_name: Token,
        attr_name: Token,
        attr_value: Token,
    ) -> None:
        if element_name not in self.attr_defs:
            pass
            # error
            return
        if attr_name not in self.attr_defs[element_name]:
            pass
            # error attribute not defined
            return
        attr_type = self.attr_defs[element_name][attr_name].attr_type
        if attr_type == DefAttrTypeEnum.CDATA:
            # parse data to convey the xml specification:
            # https://www.w3.org/TR/xml/#AVNormalize
            return
        if attr_type == DefAttrTypeEnum.ID:
            # check to see if a value is of type xlmname
            if attr_value in self.attr_ids:
                pass
                # error id already registered
            else:
                self.attr_ids.add(attr_value)
            return
        if attr_type == DefAttrTypeEnum.IDREF:
            # check to see if a value is of type xlmname
            if attr_value not in self.attr_ids:
                pass
                # error not found sa registered ids
        if attr_type == DefAttrTypeEnum.IDREFS:
            # get tokens from the attribute value
            # check to see if a all values is of type xlmname
            if attr_value not in self.attr_ids:
                pass
                # error not found sa registered ids
        # if attr_type == DefAttrTypeEnum.ENUM:
