from __future__ import annotations

from enum import Enum
from enum import auto
from enum import unique

from xmlvalidator import QUOTES


@unique
class Modifier(Enum):
    ONLY_ONE_TIME = auto()
    ZERO_OR_ONE_TIMES = auto()
    ONE_OR_MORE_TIMES = auto()
    ZERO_OR_MORE_TIMES = auto()


@unique
class Order(Enum):
    SINGLE_ELEMENT = auto()
    SEQUENCE = auto()
    CHOICE = auto()


@unique
class AllowedContent(Enum):
    EMPTY = auto()
    ANY = auto()
    DEFINED = auto()


@unique
class AttributeDefaults(Enum):
    IMPLIED = auto()
    REQUIRED = auto()
    FIXED = auto()
    LITERAL = auto()


@unique
class AttributeType(Enum):
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


class DTD:
    def __init__(self, root_element: str) -> None:
        self.root_element = root_element
        self.elements: dict[str, AllowedContent] = {}
        self.definitions: dict[str, list[str]] = {}
        self.attr_ids: set = set()
        self.attributes: dict[str, AttributeDeclaration] = {}

    def add_empty_element(self, element_name: str) -> None:
        self.elements[element_name] = AllowedContent.EMPTY

    def add_any_element(self, element_name: str) -> None:
        self.elements[element_name] = AllowedContent.ANY

    def add_defined_element(self, element_name: str, tokens: list[str]) -> None:
        self.elements[element_name] = AllowedContent.DEFINED
        self.definitions[element_name] = tokens

    def add_attribute_definition(self, element_name: str, tokens: list[str]) -> None:
        if element_name in self.attributes:
            attr_decl = self.attributes[element_name]
            attr_decl.add_declaration(tokens)
        attr_decl = AttributeDeclaration(self, tokens)
        self.attributes[element_name] = attr_decl

    def compare_declared_element(self, declared_element: str, child_elements: list[str]) -> bool:
        if declared_element not in self.definitions:
            raise ValueError()
        declared_element_tree = ElementDefinition(self.definitions[declared_element])
        search_result = False
        for child_element in child_elements:
            if declared_element_tree.order == Order.SINGLE_ELEMENT or declared_element_tree.order == Order.SEQUENCE:
                if declared_element_tree.find_element(child_element):
                    search_result = True
                    continue
                search_result = False
                break
            if declared_element_tree.order == Order.CHOICE:
                search_result = search_result or declared_element_tree.find_element(child_element)
        # check to see if the search was complete
        if search_result and declared_element_tree.is_search_criteria_met():
            return True
        return False

    def compare_declared_attributes(self, element: str, attrs: list[tuple[str, str]]) -> None:
        if element not in self.attributes:
            raise ValueError("Element does not have defined attributes.")
        self.attributes[element].compare(attrs)


class ElementDefinition:
    def __init__(self, tokens: list[str], parent: None | ElementDefinition = None) -> None:
        self.tokens = tokens
        self.parent = parent
        self.active = True
        self.used = 0
        self.proceed_with_the_same_search_string = False
        self.modifier: Modifier = self.get_modifier()
        self.order: Order = Order.SINGLE_ELEMENT
        self.num_of_match: int = 0
        self.children: list[ElementDefinition] = []
        self.target: str | None = None
        self.strip_paranthesis()
        self.parse_tokens()

    def get_index(self, index: int) -> None | ElementDefinition:
        if index < 0 or index > len(self.children):
            return None
        return self.children[index]

    def check_modifier_when_found(self) -> bool:
        match self.modifier:
            case Modifier.ONLY_ONE_TIME:
                self.active = False
                if self.used > 1:
                    return False
                return True
            case Modifier.ONE_OR_MORE_TIMES:
                self.active = True
                return True
            case Modifier.ZERO_OR_MORE_TIMES:
                self.active = True
                return True
            case Modifier.ZERO_OR_ONE_TIMES:
                if self.used > 1:
                    self.active = False
                    return False
                self.active = True
                return True
            case _:
                raise ValueError()

    def check_modifier_when_not_found(self) -> bool:
        self.active = False
        match self.modifier:
            case Modifier.ONLY_ONE_TIME:
                pass
            case Modifier.ONE_OR_MORE_TIMES:
                if self.used >= 1:
                    self.proceed_with_the_same_search_string = True
            case Modifier.ZERO_OR_MORE_TIMES:
                if self.used >= 0:
                    self.proceed_with_the_same_search_string = True
            case Modifier.ZERO_OR_ONE_TIMES:
                if self.used == 0 or self.used == 1:
                    self.proceed_with_the_same_search_string = True
            case _:
                raise ValueError()
        return False

    def are_children_deactivated(self) -> bool:
        result = True
        for child in self.children:
            if child.active:
                result = False
                break
        return result

    def is_modifier_met_after_search(self) -> bool:
        match self.modifier:
            case Modifier.ONLY_ONE_TIME:
                if self.used == 1:
                    return True
                return False
            case Modifier.ONE_OR_MORE_TIMES:
                if self.used == 0:
                    return False
                return True
            case Modifier.ZERO_OR_MORE_TIMES:
                return True
            case Modifier.ZERO_OR_ONE_TIMES:
                if self.used == 0 or self.used == 1:
                    return True
                return False
            case _:
                raise ValueError()

    def is_search_criteria_met(self) -> bool:
        if len(self.children) == 0:
            return self.is_modifier_met_after_search()
        # SEQUENCE OR CHOICE
        i = 0
        result = False
        while i < len(self.children):
            if self.order == Order.SINGLE_ELEMENT or self.order == Order.SEQUENCE:
                if not self.children[i].is_search_criteria_met():
                    result = False
                    break
                result = True
                i += 1
                continue
            if self.order == Order.CHOICE:
                if self.children[i].is_search_criteria_met():
                    result = result or True
                else:
                    result = result or False
                i += 1
                continue
        return result

    def find_element(self, search_string: str) -> bool:
        # FOUND TARGET
        if len(self.children) == 0:
            if self.target == search_string:
                self.used += 1
                return self.check_modifier_when_found()
            else:
                return self.check_modifier_when_not_found()
        # SEQUENCE OR CHOICE
        i = 0
        choice_result = False
        while i < len(self.children):
            if not self.children[i].active:
                i += 1
                continue
            if self.order == Order.SINGLE_ELEMENT or self.order == Order.SEQUENCE:
                if self.children[i].find_element(search_string):
                    if self.are_children_deactivated():
                        self.active = False
                    return True
                else:
                    if self.children[i].proceed_with_the_same_search_string:
                        self.proceed_with_the_same_search_string = True
                        continue
                    self.active = False
                    return False
            if self.order == Order.CHOICE:
                if self.children[i].find_element(search_string):
                    i += 1
                    choice_result = choice_result or True
                else:
                    if self.children[i].proceed_with_the_same_search_string:
                        self.proceed_with_the_same_search_string = True
                    choice_result = choice_result or False
        if self.are_children_deactivated():
            self.active = False
        return choice_result

    def get_modifier(self) -> Modifier:
        modifier: Modifier = Modifier.ONLY_ONE_TIME
        if self.tokens[-1] == ("?"):
            modifier = Modifier.ZERO_OR_ONE_TIMES
            self.tokens.pop(-1)
        elif self.tokens[-1] == ("+"):
            modifier = Modifier.ONE_OR_MORE_TIMES
            self.tokens.pop(-1)
        elif self.tokens[-1] == ("*"):
            modifier = Modifier.ZERO_OR_MORE_TIMES
            self.tokens.pop(-1)
        return modifier

    def strip_paranthesis(self) -> None:
        if self.tokens[0] == ("(") and self.tokens[-1] == (")"):
            self.tokens.pop(0)
            self.tokens.pop(-1)

    def parse_tokens(self) -> None:
        if len(self.tokens) == 1:
            self.target = self.tokens[0]
            return
        accumulator: list[str] = []
        i = 0
        nested_elements = 0
        while i < len(self.tokens):
            if self.tokens[i] == "," and nested_elements == 0:
                if self.order == Order.SINGLE_ELEMENT:
                    self.order = Order.SEQUENCE
                if self.order == Order.CHOICE:
                    raise ValueError()
                if len(accumulator) > 0:
                    sub_element = ElementDefinition(accumulator, self)
                    self.children.append(sub_element)
                    accumulator = []
                i += 1
                continue
            if self.tokens[i] == "|" and nested_elements == 0:
                if self.order == Order.SINGLE_ELEMENT:
                    self.order = Order.CHOICE
                if self.order == Order.SEQUENCE:
                    raise ValueError()
                if len(accumulator) > 0:
                    sub_element = ElementDefinition(accumulator, self)
                    self.children.append(sub_element)
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
            sub_element = ElementDefinition(accumulator, self)
            self.children.append(sub_element)


class AttributeValue:
    def __init__(
        self,
        dtd: DTD,
        attr_type: AttributeType,
        default: AttributeDefaults,
        enum_values: None | list[str],
        fixed_value: None | str,
        literal_value: None | str,
    ) -> None:
        self.dtd = dtd
        self.attr_type = attr_type
        self.default = default
        self.enum_values = enum_values
        self.fixed_value = fixed_value
        self.literal = literal_value

    def is_nmtoken(self, value: str) -> bool:
        for char in value:
            if not char.isalnum() and char not in {"-", "_", ":", "."}:
                return False
        return True

    def is_xml_name(self, value: str) -> bool:
        if len(value) >= 1:
            first_char = value[0]
            if not first_char.isalpha() and not first_char == "_":
                return False
        if len(value) >= 2:
            for char in value[1:]:
                if not char.isalnum() and char not in {"-", "_", ":", "."}:
                    return False
        return True

    def is_nmtokens(self, value: str) -> bool:
        tokens = value.split()
        for token in tokens:
            if not self.is_nmtoken(token):
                return False
        return True

    def is_enum_value(self, value: str) -> bool:
        if self.enum_values is None:
            raise ValueError("Enum values must be present.")
        if value not in self.enum_values:
            return False
        return True

    def is_id(self, value: str) -> bool:
        if not self.is_xml_name(value):
            print("Not xml name.")
            return False
        if value in self.dtd.attr_ids:
            print("Value exists already.")
            return False
        self.dtd.attr_ids.add(value)
        return True

    def is_id_ref(self, value: str) -> bool:
        if not self.is_xml_name(value):
            print("Not xml name.")
            return False
        if value not in self.dtd.attr_ids:
            return False
        return True

    def is_id_refs(self, value: str) -> bool:
        tokens = value.split()
        for token in tokens:
            if not self.is_id_ref(token):
                return False
        return True

    def check_value(self, attr_value: str) -> bool:
        match self.attr_type:
            case AttributeType.CDATA:
                return True
            case AttributeType.NMTOKEN:
                return self.is_nmtoken(attr_value)
            case AttributeType.NMTOKENS:
                return self.is_nmtokens(attr_value)
            case AttributeType.ENUMERATION:
                return self.is_enum_value(attr_value)
            case AttributeType.ID:
                return self.is_id(attr_value)
            case AttributeType.IDREF:
                return self.is_id_ref(attr_value)
            case AttributeType.IDREFS:
                return self.is_id_refs(attr_value)


class AttributeDeclaration:
    def __init__(self, dtd: DTD, tokens: list[str]) -> None:
        self.dtd = dtd
        self.tokens: list[list[str]] = []
        self.tokens.append(tokens)
        self.pointer = 0
        self.attributes: dict[str, AttributeValue] = {}
        self.parse_tokens()

    def next(self) -> None:
        self.pointer += 1

    def current(self) -> str:
        return self.tokens[-1][self.pointer]

    def has_next_value(self) -> bool:
        if self.pointer < len(self.tokens[-1]):
            return True
        return False

    def compare(self, attrs: list[tuple[str, str]]) -> bool:
        attr_defs = self.get_all_attr_definitions()
        for attr in attrs:
            attr_name = attr[0]
            attr_value = attr[1]
            if attr_name not in self.attributes:
                print("Attribute not defined.")
            self.attributes[attr_name].check_value(attr_value)

    def add_declaration(self, tokens: list[str]) -> None:
        self.tokens.append(tokens)
        self.pointer = 0
        self.parse_tokens()

    def get_all_attr_definitions(self) -> dict[str, int]:
        attr_defs: dict[str, int] = {}
        for attr in self.attributes:
            attr_defs[attr] = 0
        return attr_defs

    def get_attr_type(self) -> AttributeType:
        match self.current():
            case "CDATA":
                return AttributeType.CDATA
            case "NMTOKEN":
                return AttributeType.NMTOKEN
            case "NMTOKENS":
                return AttributeType.NMTOKENS
            case "(":
                return AttributeType.ENUMERATION
            case "ENTITY":
                return AttributeType.ENTITY
            case "ENTITIES":
                return AttributeType.ENTITIES
            case "ID":
                return AttributeType.ID
            case "IDREF":
                return AttributeType.IDREF
            case "IDREFS":
                return AttributeType.IDREFS
            case "NOTATION":
                return AttributeType.NOTATION
            case _:
                raise ValueError("Unrecognized attribute type.")

    def parse_enumeration(self) -> list[str]:
        if self.current() != "(":
            raise ValueError("Enum values must be enclosed in parentheses.")
        self.next()
        enum_value: str = ""
        values: list[str] = []
        is_enum_closed = False
        while self.has_next_value():
            if self.current() == ")":
                is_enum_closed = True
                break
            if self.current() == "|":
                if enum_value == "":
                    raise ValueError("Enumeration must first begin with a value.")
                values.append(enum_value)
                enum_value = ""
                self.next()
                continue
            self.verify_nmtoken(self.current())
            if enum_value != "":
                raise ValueError("All enum values must be comma separated.")
            enum_value = self.current()
            self.next()
            continue
        if not is_enum_closed:
            raise ValueError("Enum values must be enclosed in")
        if enum_value != "":
            values.append(enum_value)
        return values

    def get_attr_defaults(self) -> AttributeDefaults:
        if self.current() == "#IMPLIED":
            return AttributeDefaults.IMPLIED
        if self.current() == "#REQUIRED":
            return AttributeDefaults.REQUIRED
        if self.current() == "#FIXED":
            return AttributeDefaults.FIXED
        if self.current() in QUOTES:
            return AttributeDefaults.LITERAL
        raise ValueError("Unrecognized attribute default.")

    def get_literal_or_fixed_value(self) -> str:
        if self.current() not in QUOTES:
            raise ValueError("Value must be enclosed in quotes.")
        quote_in_use = self.current()
        self.next()
        if not self.has_next_value():
            raise ValueError("Value not found.")
        return_value = self.current()
        self.next()
        if not self.has_next_value():
            raise ValueError("Value must be enclosed in quotes.")
        if self.current() != quote_in_use:
            raise ValueError("Ending quote must match the start quote.")
        return return_value

    def verify_nmtoken(self, value: str) -> None:
        for char in value:
            if not char.isalnum() and char not in {"-", "_", ":", "."}:
                raise ValueError(f"Character {char} is not allowed as NMTOKEN value.")

    def parse_tokens(self) -> None:
        while self.has_next_value():
            attr_name = self.current()
            self.next()
            attr_type = self.get_attr_type()
            enum_values: None | list[str] = None
            if attr_type == AttributeType.ENUMERATION:
                enum_values = self.parse_enumeration()
            self.next()
            if not self.has_next_value():
                break
            defaults = self.get_attr_defaults()
            fixed_value: None | str = None
            if not self.has_next_value():
                break
            if defaults == AttributeDefaults.FIXED:
                self.next()
                if not self.has_next_value():
                    break
                fixed_value = self.get_literal_or_fixed_value()
            literal_value: None | str = None
            if not self.has_next_value():
                break
            if defaults == AttributeDefaults.LITERAL:
                literal_value = self.get_literal_or_fixed_value()
            attr_value = AttributeValue(self.dtd, attr_type, defaults, enum_values, fixed_value, literal_value)
            self.attributes[attr_name] = attr_value
            self.next()
            continue


section_tokens = ["(", "(", "#PCDATA", "|", "title", ")", ",", "(", "paragraph", "|", "image", ")", "*", ")"]

complex_tokens = [
    "(",  # Start of the entire group
    "(",  # Start of choice: element1 or the nested sequence
    "element1",
    "|",  # Choice operator
    "(",  # Start of sequence: element2, ...
    "element2",
    ",",  # Sequence operator
    "(",  # Start of choice: element3 or the nested sequence
    "element3",
    "|",  # Choice operator
    "(",  # Start of nested sequence: element4, element5*
    "element4",
    ",",  # Sequence operator
    "element5",
    "*",  # Zero or more occurrences of element5
    ")",
    ")",
    ")",
    ")",
    ",",  # Sequence operator
    "element6",
    ")",  # End of the entire group
]

# (                                                              )
#  (                                                   ),element6
#   element1|(                                        )
#             element2,(                             )
#                       element3|(                  )
#                                 element4,element5*


root = DTD("root")
easy_tokens = [
    "(",
    "name",
    "?",
    ",",
    "address",
    ",",
    "profession",
    ")",
]
single_token = ["(", "name", ")"]
tokens = ["(", "name", ",", "profession", "*", ")"]
person_tokens = ["(", "first_name", ",", "middle_name", "?", ",", "last_name", "?", ")"]
definition_tokens = ["(", "#PCDATA", "|", "term", ")", "*"]
# root.add_defined_element("easy", easy_tokens)
# print(root.find_element("easy", ["address", "profession"]))
root.add_defined_element("complex", complex_tokens)
print(root.compare_declared_element("complex", ["element2", "element4", "element5", "element5", "element6"]))
# root.add_defined_element("single", single_token)
# print(root.find_element("single", ["dsa"]))
# root.add_defined_element("definition", definition_tokens)
# allowed_content = root.check_allowed_content("person")
# if allowed_content == AllowedContent.DEFINED:

attr_definition = []
# attr_definition.extend(["source", "CDATA", "#REQUIRED"])
# attr_definition.extend(["width", "CDATA", "#REQUIRED"])
# attr_definition.extend(["height", "CDATA", "#REQUIRED"])
# attr_definition.extend(["alt", "CDATA", "#IMPLIED"])
attr_definition.extend(["year", "(", "1", "|", "2", "|", "3", "|", "4", "|", "5", ")", "#REQUIRED"])
attr_biography = []
attr_biography.append("version")
attr_biography.append("CDATA")
attr_biography.extend(['"', "1.0", '"'])

root.add_attribute_definition("biography", attr_biography)

print()
