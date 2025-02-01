from __future__ import annotations

from typing import TYPE_CHECKING
import copy


if TYPE_CHECKING:
    from buffer_controller import Token
    from xmlvalidator import ErrorCollector
    from xmlvalidator import ValidatorAttribute
    from xmlvalidator import ValidatorCData
    from xmlvalidator import ValidatorParsedText
    from xmlvalidator import ValidatorTag

from enum import Enum
from enum import auto
from enum import unique


@unique
class ElementDefinitionsModifier(Enum):
    ONLY_ONE_TIME = auto()
    ZERO_OR_ONE_TIMES = auto()
    ONE_OR_MORE_TIMES = auto()
    ZERO_OR_MORE_TIMES = auto()


@unique
class ElementDefinitionsOrder(Enum):
    SINGLE_ELEMENT = auto()
    SEQUENCE = auto()
    CHOICE = auto()


# @unique
# class ElementDefinitionsType(Enum):
#     EMPTY = auto()
#     ANY = auto()
#     DEFINED = auto()


@unique
class AttributeDefinitonsDefaults(Enum):
    IMPLIED = auto()
    REQUIRED = auto()
    FIXED = auto()
    LITERAL = auto()


@unique
class AttributeDefinitionsType(Enum):
    CDATA = auto()
    NMTOKEN = auto()
    NMTOKENS = auto()
    ENUMERATION = auto()
    ENTITY = auto()
    ENTITIES = auto()
    ID = auto()
    IDREF = auto()
    IDREFS = auto()
    NOTATION = auto()


class CdataElement:
    def __init__(self, content: Token) -> None:
        self.content = content


class TagElement:
    def __init__(self, name: Token) -> None:
        self.name: Token = name
        self.child_elements: list[TagElement | CdataElement] = []
        self.attrs: list[AttrElement] = []


class AttrElement:
    def __init__(self, parent_tag: TagElement, name: Token, value: Token) -> None:
        self.parent_tag = parent_tag
        self.name = name
        self.value = value


class ElementDefinitionsAny:
    def validate(self, tag: ValidatorTag) -> bool:
        return True


class ElementDefinitionsEmpty:
    def validate(self, tag: ValidatorTag) -> bool:
        if len(tag.children) != 0:
            return False
        return True


class ElementDefinitionsDefined:
    def __init__(self, tokens: list[Token], parent: None | ElementDefinitionsDefined = None) -> None:
        self.tokens = tokens
        self.parent = parent
        self.is_definition_valid: bool = True
        self.modifier: ElementDefinitionsModifier = self.get_modifier()
        self.strip_paranthesis()
        if not self.is_definition_valid:
            return
        self.active_path = True
        self.used = 0
        # self.carry_child_element_to_next_definition = False
        self.order: ElementDefinitionsOrder = ElementDefinitionsOrder.SINGLE_ELEMENT
        self.child_definitions: list[ElementDefinitionsDefined] = []
        self.target: Token | None = None
        self.parse_tokens()

    def __repr__(self) -> str:
        text = ""
        for index, token in enumerate(self.tokens):
            if index == len(self.tokens) - 1:
                text += token.chars
            else:
                text += token.chars + " "
        return text

    def get_modifier(self) -> ElementDefinitionsModifier:
        if self.tokens[-1] == ("?"):
            self.tokens.pop(-1)
            return ElementDefinitionsModifier.ZERO_OR_ONE_TIMES
        if self.tokens[-1] == ("+"):
            self.tokens.pop(-1)
            return ElementDefinitionsModifier.ONE_OR_MORE_TIMES
        if self.tokens[-1] == ("*"):
            self.tokens.pop(-1)
            return ElementDefinitionsModifier.ZERO_OR_MORE_TIMES
        return ElementDefinitionsModifier.ONLY_ONE_TIME

    def strip_paranthesis(self) -> None:
        if self.tokens[0] == ("("):
            if self.tokens[-1] != (")"):
                self.mark_definition_as_invalid()
                return
            else:
                self.tokens.pop(0)
                self.tokens.pop(-1)

    def mark_definition_as_invalid(self) -> None:
        if self.parent is not None:
            self.parent.mark_definition_as_invalid()
        self.is_definition_valid = False

    def parse_tokens(self) -> None:
        if len(self.tokens) == 1:
            self.target = self.tokens[0]
            ##########################################################
            # check if a target is a valid name to se if it needs to be deactivated
            ##########################################################
            return
        accumulator: list[Token] = []
        i = 0
        nested_elements = 0
        while i < len(self.tokens):
            if self.tokens[i] == "," and nested_elements == 0:
                if self.order == ElementDefinitionsOrder.SINGLE_ELEMENT:
                    self.order = ElementDefinitionsOrder.SEQUENCE
                if self.order == ElementDefinitionsOrder.CHOICE:
                    ##################################################
                    # what about collecting errors while parsing definitions?
                    ##################################################
                    self.mark_definition_as_invalid()
                    return
                if len(accumulator) > 0:
                    child_definition = ElementDefinitionsDefined(tokens=accumulator, parent=self)
                    self.child_definitions.append(child_definition)
                    accumulator = []
                i += 1
                continue
            if self.tokens[i] == "|" and nested_elements == 0:
                if self.order == ElementDefinitionsOrder.SINGLE_ELEMENT:
                    self.order = ElementDefinitionsOrder.CHOICE
                if self.order == ElementDefinitionsOrder.SEQUENCE:
                    self.mark_definition_as_invalid()
                    return
                if len(accumulator) > 0:
                    child_definition = ElementDefinitionsDefined(accumulator, self)
                    self.child_definitions.append(child_definition)
                    accumulator = []
                i += 1
                continue
            if self.tokens[i] == "(":
                nested_elements += 1
            if self.tokens[i] == ")":
                nested_elements -= 1
            accumulator.append(self.tokens[i])
            i += 1
        if len(accumulator) > 0:
            child_definition = ElementDefinitionsDefined(accumulator, self)
            self.child_definitions.append(child_definition)


class ElementDefinitionsDefinedValidator:
    def __init__(self, declared_element_tree: ElementDefinitionsDefined) -> None:
        self.declared_element_tree = declared_element_tree

    def check_modifier_when_found(self, edd: ElementDefinitionsDefined) -> bool:
        match edd.modifier:
            case ElementDefinitionsModifier.ONLY_ONE_TIME:
                edd.active_path = False
                if edd.used > 1:
                    return False
                return True
            case ElementDefinitionsModifier.ONE_OR_MORE_TIMES:
                edd.active_path = True
                return True
            case ElementDefinitionsModifier.ZERO_OR_MORE_TIMES:
                edd.active_path = True
                return True
            case ElementDefinitionsModifier.ZERO_OR_ONE_TIMES:
                if edd.used > 1:
                    edd.active_path = False
                    return False
                edd.active_path = True
                return True

    def check_modifier_when_not_found(self, edd: ElementDefinitionsDefined) -> bool:
        edd.active_path = False
        match edd.modifier:
            case ElementDefinitionsModifier.ONLY_ONE_TIME:
                pass
            # case ElementDefinitionsModifier.ONE_OR_MORE_TIMES:
            #     if edd.used >= 1:
            #         edd.carry_child_element_to_next_definition = True
            # case ElementDefinitionsModifier.ZERO_OR_MORE_TIMES:
            #     if edd.used >= 0:
            #         edd.carry_child_element_to_next_definition = True
            # case ElementDefinitionsModifier.ZERO_OR_ONE_TIMES:
            #     if edd.used == 0 or edd.used == 1:
            #         edd.carry_child_element_to_next_definition = True
            # case _:
            #     raise ValueError()
        return False

    def are_child_definitions_deactivated(self, edd: ElementDefinitionsDefined) -> bool:
        result = True
        for child in edd.child_definitions:
            if child.active_path:
                result = False
                break
        return result

    def is_child_element_used(self, edd: ElementDefinitionsDefined) -> bool:
        match edd.modifier:
            case ElementDefinitionsModifier.ONLY_ONE_TIME:
                if edd.used == 1:
                    return True
                return False
            case ElementDefinitionsModifier.ONE_OR_MORE_TIMES:
                if edd.used >= 1:
                    return True
                return False
            case ElementDefinitionsModifier.ZERO_OR_MORE_TIMES:
                return True
            case ElementDefinitionsModifier.ZERO_OR_ONE_TIMES:
                if edd.used == 0 or edd.used == 1:
                    return True
                return False

    def is_search_criteria_met(self, edd: ElementDefinitionsDefined) -> bool:
        if len(edd.child_definitions) == 0:
            return self.is_child_element_used(edd)
            # return self.is_active_path_modifier_met_after_search(edd)
        # SEQUENCE OR CHOICE
        i = 0
        result = False
        while i < len(edd.child_definitions):
            if edd.order == ElementDefinitionsOrder.SINGLE_ELEMENT or edd.order == ElementDefinitionsOrder.SEQUENCE:
                if not self.is_search_criteria_met(edd.child_definitions[i]):
                    result = False
                    break
                result = True
                i += 1
                continue
            if edd.order == ElementDefinitionsOrder.CHOICE:
                if self.is_search_criteria_met(edd.child_definitions[i]):
                    result = result or True
                else:
                    result = result or False
                i += 1
                continue
        return result

    def reset_active_path(self, edd: ElementDefinitionsDefined) -> None:
        if len(edd.child_definitions) == 0:
            edd.active_path = True
            edd.used = 0
            return
        for child_definition in edd.child_definitions:
            self.reset_active_path(child_definition)

    def is_target_modifier_met_before_search(self, edd: ElementDefinitionsDefined) -> bool:
        match edd.modifier:
            case ElementDefinitionsModifier.ONLY_ONE_TIME:
                if edd.used == 1:
                    return False
                return True
            case ElementDefinitionsModifier.ONE_OR_MORE_TIMES:
                return True
            case ElementDefinitionsModifier.ZERO_OR_MORE_TIMES:
                return True
            case ElementDefinitionsModifier.ZERO_OR_ONE_TIMES:
                if edd.used > 1:
                    return False
                return True

    def is_active_path_modifier_met_after_search(self, edd: ElementDefinitionsDefined) -> bool:
        match edd.modifier:
            case ElementDefinitionsModifier.ONLY_ONE_TIME:
                if edd.used == 1:
                    return False
                return True
            case ElementDefinitionsModifier.ONE_OR_MORE_TIMES:
                if edd.used == 0:
                    return True
                return False
            case ElementDefinitionsModifier.ZERO_OR_MORE_TIMES:
                return True
            case ElementDefinitionsModifier.ZERO_OR_ONE_TIMES:
                if edd.used < 1:
                    return True
                return False

    def is_target(self, edd: ElementDefinitionsDefined) -> bool:
        if len(edd.child_definitions) == 0:
            return True
        return False

    def is_child_element_match_with_target(self, child_element: Token, edd: ElementDefinitionsDefined) -> bool:
        if edd.target == child_element and self.is_target_modifier_met_before_search(edd):
            edd.used += 1
            edd.active_path = False
            return True
        else:
            edd.active_path = False
            return False

    def get_active_child_element_path(self, edd: ElementDefinitionsDefined) -> None | ElementDefinitionsDefined:
        self.reopen_transit_before_match(edd)
        for child_edd in edd.child_definitions:
            if child_edd.active_path:
                return child_edd
        return None

    def reopen_transit_before_match(self, edd: ElementDefinitionsDefined) -> None:
        if edd.order == ElementDefinitionsOrder.SINGLE_ELEMENT:
            return
        if edd.order == ElementDefinitionsOrder.SEQUENCE:
            if not self.is_active_path_modifier_met_after_search(edd.child_definitions[-1]):
                self.reset_active_path(edd)
        return

    def close_transit_after_mismatch(self, edd: ElementDefinitionsDefined) -> None:
        if edd.order == ElementDefinitionsOrder.SINGLE_ELEMENT:
            return
        if edd.order == ElementDefinitionsOrder.SEQUENCE:
            is_closed = True
            for child_definition in edd.child_definitions:
                if child_definition.active_path:
                    is_closed = False
                    return
        return

    def is_element_match_with_definition(self, child_element: Token, edd: ElementDefinitionsDefined) -> bool:
        # FOUND TARGET
        if self.is_target(edd):
            return self.is_child_element_match_with_target(child_element, edd)

        # SEQUENCE OR CHOICE
        is_match: bool = False
        active_child_element_path = self.get_active_child_element_path(edd)
        while active_child_element_path is not None:
            is_match = self.is_element_match_with_definition(child_element, active_child_element_path)
            if is_match:
                edd.used += 1
                return True
            else:
                self.close_transit_after_mismatch(edd)
            active_child_element_path = self.get_active_child_element_path(edd)
        return False

    def validate_parsed_element_with_element_definitions(self, parsed_child_elements: list[Token]) -> bool:
        i = 0
        while i < len(parsed_child_elements):
            self.is_element_match_with_definition(parsed_child_elements[i], self.declared_element_tree)

            i += 1
        return self.is_search_criteria_met(self.declared_element_tree)


class Dtd:
    def __init__(
        self,
        root: Token | None = None,
        error_collector: None | ErrorCollector = None,
    ) -> None:
        self.error_collector = error_collector
        self.root = root
        self.element_definitions: dict[
            Token, ElementDefinitionsDefined | ElementDefinitionsAny | ElementDefinitionsEmpty
        ] = {}
        # ATTRIBUTE
        # self.attribute_ids: set = set()
        # self.attribute_definitions: dict[str, AttributeDeclaration] = {}

    def define_element(
        self,
        element_name: Token,
        tokens: list[Token],
    ) -> None:
        if element_name in self.element_definitions:
            if self.error_collector is not None:
                self.error_collector.add_token_start(element_name, "Element is defined already.")
            return
        if len(tokens) == 0:
            if self.error_collector is not None:
                self.error_collector.add_token_start(element_name, "Element does not have any definitions.")
            return
        if len(tokens) == 1 and tokens[0] == "ANY":
            self.element_definitions[element_name] = ElementDefinitionsAny()
            return
        if len(tokens) == 1 and tokens[0] == "EMPTY":
            self.element_definitions[element_name] = ElementDefinitionsEmpty()
            return
        self.element_definitions[element_name] = ElementDefinitionsDefined(tokens)

    def validate_parsed_element_with_element_definitions(
        self, parsed_element: Token, parsed_child_elements: list[Token]
    ) -> bool:
        if parsed_element not in self.element_definitions:
            if self.error_collector is not None:
                self.error_collector.add_token_start(parsed_element, "Element is not defined.")
            return False
        element_definition = self.element_definitions[parsed_element]
        if isinstance(element_definition, ElementDefinitionsAny):
            return False
        if isinstance(element_definition, ElementDefinitionsEmpty):
            return False
        if isinstance(element_definition, ElementDefinitionsDefined):
            edd = copy.deepcopy(element_definition)
            eddvalidator = ElementDefinitionsDefinedValidator(edd)
            return eddvalidator.validate_parsed_element_with_element_definitions(parsed_child_elements)
        if self.error_collector is not None:
            self.error_collector.add_token_start(parsed_element, "Element is registered with invalid defintion.")
        return False

    ######################################
    # def define_attribute(self, element_name: str, tokens: list[str]) -> None:
    #     if element_name in self.attribute_definitions:
    #         attr_decl = self.attribute_definitions[element_name]
    #         attr_decl.add_declaration(tokens)
    #     attr_decl = AttributeDeclaration(self, tokens)
    #     self.attribute_definitions[element_name] = attr_decl

    # def compare_defined_attribute(self, element: str, attrs: list[tuple[str, str]]) -> None:
    #     if element not in self.attribute_definitions:
    #         raise ValueError("Element does not have defined attributes.")
    #     self.attribute_definitions[element].compare(attrs)


# class AttributeValue:
#     def __init__(
#         self,
#         dtd: Dtd,
#         attr_type: AttributeDefinitionsType,
#         default: AttributeDefinitonsDefaults,
#         enum_values: None | list[str],
#         fixed_value: None | str,
#         literal_value: None | str,
#     ) -> None:
#         self.dtd = dtd
#         self.attr_type = attr_type
#         self.default = default
#         self.enum_values = enum_values
#         self.fixed_value = fixed_value
#         self.literal = literal_value

#     def is_nmtoken(self, value: str) -> bool:
#         for char in value:
#             if not char.isalnum() and char not in {"-", "_", ":", "."}:
#                 return False
#         return True

#     def is_xml_name(self, value: str) -> bool:
#         if len(value) >= 1:
#             first_char = value[0]
#             if not first_char.isalpha() and not first_char == "_":
#                 return False
#         if len(value) >= 2:
#             for char in value[1:]:
#                 if not char.isalnum() and char not in {"-", "_", ":", "."}:
#                     return False
#         return True

#     def is_nmtokens(self, value: str) -> bool:
#         tokens = value.split()
#         for token in tokens:
#             if not self.is_nmtoken(token):
#                 return False
#         return True

#     def is_enum_value(self, value: str) -> bool:
#         if self.enum_values is None:
#             raise ValueError("Enum values must be present.")
#         if value not in self.enum_values:
#             return False
#         return True

#     def is_id(self, value: str) -> bool:
#         if not self.is_xml_name(value):
#             print("Not xml name.")
#             return False
#         if value in self.dtd.attribute_ids:
#             print("Value exists already.")
#             return False
#         self.dtd.attribute_ids.add(value)
#         return True

#     def is_id_ref(self, value: str) -> bool:
#         if not self.is_xml_name(value):
#             print("Not xml name.")
#             return False
#         if value not in self.dtd.attribute_ids:
#             return False
#         return True

#     def is_id_refs(self, value: str) -> bool:
#         tokens = value.split()
#         for token in tokens:
#             if not self.is_id_ref(token):
#                 return False
#         return True

#     def check_value(self, attr_value: str) -> bool:
#         match self.attr_type:
#             case AttributeDefinitionsType.CDATA:
#                 return True
#             case AttributeDefinitionsType.NMTOKEN:
#                 return self.is_nmtoken(attr_value)
#             case AttributeDefinitionsType.NMTOKENS:
#                 return self.is_nmtokens(attr_value)
#             case AttributeDefinitionsType.ENUMERATION:
#                 return self.is_enum_value(attr_value)
#             case AttributeDefinitionsType.ID:
#                 return self.is_id(attr_value)
#             case AttributeDefinitionsType.IDREF:
#                 return self.is_id_ref(attr_value)
#             case AttributeDefinitionsType.IDREFS:
#                 return self.is_id_refs(attr_value)


# class AttributeDeclaration:
#     def __init__(self, dtd: Dtd, tokens: list[str]) -> None:
#         self.dtd = dtd
#         self.tokens: list[list[str]] = []
#         self.tokens.append(tokens)
#         self.pointer = 0
#         self.attributes: dict[str, AttributeValue] = {}
#         self.parse_tokens()

#     def next(self) -> None:
#         self.pointer += 1

#     def current(self) -> str:
#         return self.tokens[-1][self.pointer]

#     def has_next_value(self) -> bool:
#         if self.pointer < len(self.tokens[-1]):
#             return True
#         return False

#     def compare(self, attrs: list[tuple[str, str]]) -> bool:
#         attr_defs = self.get_all_attr_definitions()
#         for attr in attrs:
#             attr_name = attr[0]
#             attr_value = attr[1]
#             if attr_name not in self.attributes:
#                 print("Attribute not defined.")
#             self.attributes[attr_name].check_value(attr_value)

#     def add_declaration(self, tokens: list[str]) -> None:
#         self.tokens.append(tokens)
#         self.pointer = 0
#         self.parse_tokens()

#     def get_all_attr_definitions(self) -> dict[str, int]:
#         attr_defs: dict[str, int] = {}
#         for attr in self.attributes:
#             attr_defs[attr] = 0
#         return attr_defs

#     def get_attr_type(self) -> AttributeDefinitionsType:
#         match self.current():
#             case "CDATA":
#                 return AttributeDefinitionsType.CDATA
#             case "NMTOKEN":
#                 return AttributeDefinitionsType.NMTOKEN
#             case "NMTOKENS":
#                 return AttributeDefinitionsType.NMTOKENS
#             case "(":
#                 return AttributeDefinitionsType.ENUMERATION
#             case "ENTITY":
#                 return AttributeDefinitionsType.ENTITY
#             case "ENTITIES":
#                 return AttributeDefinitionsType.ENTITIES
#             case "ID":
#                 return AttributeDefinitionsType.ID
#             case "IDREF":
#                 return AttributeDefinitionsType.IDREF
#             case "IDREFS":
#                 return AttributeDefinitionsType.IDREFS
#             case "NOTATION":
#                 return AttributeDefinitionsType.NOTATION
#             case _:
#                 raise ValueError("Unrecognized attribute type.")

#     def parse_enumeration(self) -> list[str]:
#         if self.current() != "(":
#             raise ValueError("Enum values must be enclosed in parentheses.")
#         self.next()
#         enum_value: str = ""
#         values: list[str] = []
#         is_enum_closed = False
#         while self.has_next_value():
#             if self.current() == ")":
#                 is_enum_closed = True
#                 break
#             if self.current() == "|":
#                 if enum_value == "":
#                     raise ValueError("Enumeration must first begin with a value.")
#                 values.append(enum_value)
#                 enum_value = ""
#                 self.next()
#                 continue
#             self.verify_nmtoken(self.current())
#             if enum_value != "":
#                 raise ValueError("All enum values must be comma separated.")
#             enum_value = self.current()
#             self.next()
#             continue
#         if not is_enum_closed:
#             raise ValueError("Enum values must be enclosed in")
#         if enum_value != "":
#             values.append(enum_value)
#         return values

#     def get_attr_defaults(self) -> AttributeDefinitonsDefaults:
#         if self.current() == "#IMPLIED":
#             return AttributeDefinitonsDefaults.IMPLIED
#         if self.current() == "#REQUIRED":
#             return AttributeDefinitonsDefaults.REQUIRED
#         if self.current() == "#FIXED":
#             return AttributeDefinitonsDefaults.FIXED
#         if self.current() in QUOTES:
#             return AttributeDefinitonsDefaults.LITERAL
#         raise ValueError("Unrecognized attribute default.")

#     def get_literal_or_fixed_value(self) -> str:
#         if self.current() not in QUOTES:
#             raise ValueError("Value must be enclosed in quotes.")
#         quote_in_use = self.current()
#         self.next()
#         if not self.has_next_value():
#             raise ValueError("Value not found.")
#         return_value = self.current()
#         self.next()
#         if not self.has_next_value():
#             raise ValueError("Value must be enclosed in quotes.")
#         if self.current() != quote_in_use:
#             raise ValueError("Ending quote must match the start quote.")
#         return return_value

#     def verify_nmtoken(self, value: str) -> None:
#         for char in value:
#             if not char.isalnum() and char not in {"-", "_", ":", "."}:
#                 raise ValueError(f"Character {char} is not allowed as NMTOKEN value.")

#     def parse_tokens(self) -> None:
#         while self.has_next_value():
#             attr_name = self.current()
#             self.next()
#             attr_type = self.get_attr_type()
#             enum_values: None | list[str] = None
#             if attr_type == AttributeDefinitionsType.ENUMERATION:
#                 enum_values = self.parse_enumeration()
#             self.next()
#             if not self.has_next_value():
#                 break
#             defaults = self.get_attr_defaults()
#             fixed_value: None | str = None
#             if not self.has_next_value():
#                 break
#             if defaults == AttributeDefinitonsDefaults.FIXED:
#                 self.next()
#                 if not self.has_next_value():
#                     break
#                 fixed_value = self.get_literal_or_fixed_value()
#             literal_value: None | str = None
#             if not self.has_next_value():
#                 break
#             if defaults == AttributeDefinitonsDefaults.LITERAL:
#                 literal_value = self.get_literal_or_fixed_value()
#             attr_value = AttributeValue(self.dtd, attr_type, defaults, enum_values, fixed_value, literal_value)
#             self.attributes[attr_name] = attr_value
#             self.next()
#             continue


# section_tokens = ["(", "(", "#PCDATA", "|", "title", ")", ",", "(", "paragraph", "|", "image", ")", "*", ")"]

# complex_tokens = [
#     "(",  # Start of the entire group
#     "(",  # Start of choice: element1 or the nested sequence
#     "element1",
#     "|",  # Choice operator
#     "(",  # Start of sequence: element2, ...
#     "element2",
#     ",",  # Sequence operator
#     "(",  # Start of choice: element3 or the nested sequence
#     "element3",
#     "|",  # Choice operator
#     "(",  # Start of nested sequence: element4, element5*
#     "element4",
#     ",",  # Sequence operator
#     "element5",
#     "*",  # Zero or more occurrences of element5
#     ")",
#     ")",
#     ")",
#     ")",
#     ",",  # Sequence operator
#     "element6",
#     ")",  # End of the entire group
# ]

# # (                                                              )
# #  (                                                   ),element6
# #   element1|(                                        )
# #             element2,(                             )
# #                       element3|(                  )
# #                                 element4,element5*


# root = Dtd("root")
# easy_tokens = [
#     "(",
#     "name",
#     "?",
#     ",",
#     "address",
#     ",",
#     "profession",
#     ")",
# ]
# single_token = ["(", "name", ")"]
# tokens = ["(", "name", ",", "profession", "*", ")"]
# person_tokens = ["(", "first_name", ",", "middle_name", "?", ",", "last_name", "?", ")"]
# definition_tokens = ["(", "#PCDATA", "|", "term", ")", "*"]
# # root.add_defined_element("easy", easy_tokens)
# # print(root.find_element("easy", ["address", "profession"]))
# root.define_element_defined("complex", complex_tokens)
# print(
#     root.validate_parsed_element_with_element_definitions(
#         "complex", ["element2", "element4", "element5", "element5", "element6"]
#     )
# )
# # root.add_defined_element("single", single_token)
# # print(root.find_element("single", ["dsa"]))
# # root.add_defined_element("definition", definition_tokens)
# # allowed_content = root.check_allowed_content("person")
# # if allowed_content == AllowedContent.DEFINED:

# attr_definition = []
# # attr_definition.extend(["source", "CDATA", "#REQUIRED"])
# # attr_definition.extend(["width", "CDATA", "#REQUIRED"])
# # attr_definition.extend(["height", "CDATA", "#REQUIRED"])
# # attr_definition.extend(["alt", "CDATA", "#IMPLIED"])
# attr_definition.extend(["year", "(", "1", "|", "2", "|", "3", "|", "4", "|", "5", ")", "#REQUIRED"])
# attr_biography = []
# attr_biography.append("version")
# attr_biography.append("CDATA")
# attr_biography.extend(['"', "1.0", '"'])

# root.define_attribute("biography", attr_biography)

# print()
