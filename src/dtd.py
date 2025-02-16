from __future__ import annotations

from typing import TYPE_CHECKING


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


# @unique
# class ElementDefinitionsModifier(Enum):
#     ONLY_ONE_TIME = auto()
#     ZERO_OR_ONE_TIMES = auto()
#     ONE_OR_MORE_TIMES = auto()
#     ZERO_OR_MORE_TIMES = auto()


@unique
class ElementDefinitionsOrder(Enum):
    SINGLE_ELEMENT = auto()
    SEQUENCE = auto()
    CHOICE = auto()


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
        self.__representation = self.get_representation(tokens)
        self.tokens = tokens
        self.parent = parent
        self.is_definition_valid: bool = True
        self.modifier: int = self.get_modifier()
        self.strip_paranthesis()
        if not self.is_definition_valid:
            return
        self.order: ElementDefinitionsOrder = ElementDefinitionsOrder.SINGLE_ELEMENT
        self.child_definitions: list[ElementDefinitionsDefined] = []
        self.target: Token | None = None
        self.parse_tokens()

    def get_representation(self, tokens: list[Token]) -> str:
        text = ""
        for index, token in enumerate(tokens):
            if index == len(tokens) - 1:
                text += token.chars
            else:
                text += token.chars + " "
        return text

    def __repr__(self) -> str:
        return self.__representation

    def get_modifier(self) -> int:
        # 0: ONLY_ONE
        # 1: ZERO_OR_ONE
        # 2: ONE_OR_MORE
        # 3: ZERO_OR_MORE
        if self.tokens[-1] == ("+"):
            self.tokens.pop(-1)
            return 1
        if self.tokens[-1] == ("?"):
            self.tokens.pop(-1)
            return 2
        if self.tokens[-1] == ("*"):
            self.tokens.pop(-1)
            return 3
        return 0

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


class ModifierDefinition:
    def __init__(self, modifier: int) -> None:
        self.modifier = modifier

    def __repr__(self) -> str:
        # 0: ONLY_ONE
        # 1: ZERO_OR_ONE
        # 2: ONE_OR_MORE
        # 3: ZERO_OR_MORE
        match self.modifier:
            case 0:
                return "ONLY_ONE"
            case 1:
                return "ZERO_OR_ONE"
            case 2:
                return "ONE_OR_MORE"
            case 3:
                return "ZERO_OR_MORE"
            case _:
                return "UNKNOWN"

    def is_optional(self, count: int) -> bool:
        match self.modifier:
            case 0:
                return False
            case 1:
                if count < 1:
                    return True
                return False
            case 2:
                if count >= 1:
                    return True
                return False
            case 3:
                return True
            case _:
                raise ValueError("Unknown value for Modifier.")

    def is_finished(self, count: int) -> bool:
        match self.modifier:
            case 0:
                if count == 1:
                    return True
                return False
            case 1:
                if count == 0 or count == 1:
                    return True
                return False
            case 2:
                if count >= 1:
                    return True
                return False
            case 3:
                if count >= 0:
                    return True
                return False
            case _:
                raise ValueError("Unknown value for Modifier.")


class ChoiceDefinition:
    def __init__(
        self,
        representation: str,
        modifier: ModifierDefinition,
        parent: None | SequenceDefinition | ChoiceDefinition = None,
    ) -> None:
        self.__representation = representation
        self.parent = parent
        self.modifier = modifier
        self.count = 0
        self.chosen_branch: None | SequenceDefinition | ChoiceDefinition | TargetDefinition = None
        self.branches: list[SequenceDefinition | ChoiceDefinition | TargetDefinition] = []

    def __repr__(self) -> str:
        return self.__representation

    def get_last_unresolved_branch(self) -> None | SequenceDefinition | ChoiceDefinition | TargetDefinition:
        if self.chosen_branch is None:
            return None
        traverse_node = self.chosen_branch
        result_node: None | SequenceDefinition | ChoiceDefinition | TargetDefinition = None
        while traverse_node is not None:
            if isinstance(traverse_node, TargetDefinition):
                result_node = traverse_node
                break
            if isinstance(traverse_node, SequenceDefinition):
                result_node = traverse_node
                traverse_node = traverse_node.chosen_branch
            if isinstance(traverse_node, ChoiceDefinition):
                result_node = traverse_node
                traverse_node = traverse_node.chosen_branch
        return result_node

    def is_optional(self) -> bool:
        count = self.count
        if self.chosen_branch is not None:
            count += 1
        return self.modifier.is_optional(count)

    def is_chosen_path_optional(self) -> bool:
        if self.chosen_branch is None:
            return False
        branch = self.chosen_branch
        while isinstance(branch, ChoiceDefinition | SequenceDefinition) and branch.chosen_branch is not None:
            branch = branch.chosen_branch
        return branch.is_optional()

    def is_finished(self) -> bool:
        if self.chosen_branch is not None:
            return False
        return self.modifier.is_finished(self.count)

    def get_priority_sequence(self) -> list[int]:
        chosen_branch_index = 0
        if self.chosen_branch is not None:
            chosen_branch_index = self.branches.index(self.chosen_branch)
        priority_sequence = []
        if chosen_branch_index != 0:
            priority_sequence.append(chosen_branch_index)
        i = 0
        while i < len(self.branches):
            if i not in priority_sequence:
                priority_sequence.append(i)
            i += 1
        return priority_sequence

    def get_available_targets(
        self,
        available_targets: list[TargetDefinition] | None = None,
    ) -> list[TargetDefinition]:
        if available_targets is None:
            available_targets = []

        if not self.is_optional() and self.is_finished():
            return available_targets

        # rearrange priority for branches
        priority_sequence = self.get_priority_sequence()

        i = 0
        while i < len(priority_sequence):
            branch = self.branches[priority_sequence[i]]
            if isinstance(branch, TargetDefinition):
                available_targets.append(branch)
            else:
                branch.get_available_targets(available_targets)
            if self.is_chosen_path_optional() and self.is_optional():
                i += 1
                continue
            if self.chosen_branch is None:
                i += 1
                continue
            break
        return available_targets

    def resolve_branch(self) -> None:
        self.count += 1
        self.chosen_branch = None
        for branch in self.branches:
            branch.count = 0

    def set_chosen_branch(self, child_branch: SequenceDefinition | ChoiceDefinition | TargetDefinition) -> None:
        if not child_branch.is_optional() and child_branch.is_finished():
            self.count += 1
            self.chosen_branch = None
            for branch in self.branches:
                branch.count = 0
        else:
            self.chosen_branch = child_branch
        if self.parent is not None:
            self.parent.set_chosen_branch(self)

    def resolve_optional_branch(self, child_branch: SequenceDefinition | ChoiceDefinition | TargetDefinition) -> None:
        if child_branch.is_optional() and self.is_finished():
            self.resolve_branch()
        if self.parent is not None:
            self.parent.resolve_optional_branch(self)


class SequenceDefinition:
    def __init__(
        self,
        representation: str,
        modifier: ModifierDefinition,
        parent: None | SequenceDefinition | ChoiceDefinition = None,
    ) -> None:
        self.__representation = representation
        self.parent = parent
        self.modifier = modifier
        self.count = 0
        self.chosen_branch: None | SequenceDefinition | ChoiceDefinition | TargetDefinition = None
        self.branches: list[SequenceDefinition | ChoiceDefinition | TargetDefinition] = []

    def __repr__(self) -> str:
        return self.__representation

    def get_last_unresolved_branch(self) -> None | SequenceDefinition | ChoiceDefinition | TargetDefinition:
        if self.chosen_branch is None:
            return None
        traverse_node = self.chosen_branch
        result_node: None | SequenceDefinition | ChoiceDefinition | TargetDefinition = None
        while traverse_node is not None:
            if isinstance(traverse_node, TargetDefinition):
                result_node = traverse_node
                break
            if isinstance(traverse_node, SequenceDefinition):
                result_node = traverse_node
                traverse_node = traverse_node.chosen_branch
            if isinstance(traverse_node, ChoiceDefinition):
                result_node = traverse_node
                traverse_node = traverse_node.chosen_branch
        return result_node

    def is_optional(self) -> bool:
        if self.chosen_branch is not None and not self.chosen_branch.is_optional():
            return False
        return self.modifier.is_optional(self.count)

    def is_chosen_path_optional(self) -> bool:
        if self.chosen_branch is None:
            return False
        branch = self.chosen_branch
        while isinstance(branch, ChoiceDefinition | SequenceDefinition) and branch.chosen_branch is not None:
            branch = branch.chosen_branch
        return branch.is_optional()

    def is_finished(self) -> bool:
        if self.chosen_branch is not None:
            return False
        return self.modifier.is_finished(self.count)

    def get_priority_sequence(self) -> list[int]:
        # if self.chosen_branch is not None:
        #     i = self.branches.index(self.chosen_branch)

        i = 0
        chosen_branch_index = 0
        if self.chosen_branch is not None:
            i = self.branches.index(self.chosen_branch)
            chosen_branch_index = i

        priority_sequence = []
        while i < len(self.branches):
            priority_sequence.append(i)
            i += 1
        if self.is_optional():
            i = 0
            while i < chosen_branch_index:
                priority_sequence.append(i)
                i += 1
        return priority_sequence

    def get_available_targets(
        self,
        available_targets: list[TargetDefinition] | None = None,
    ) -> list[TargetDefinition]:
        if available_targets is None:
            available_targets = []

        if not self.is_optional() and self.is_finished():
            return available_targets

        # rearrange priority for branches
        priority_sequence = self.get_priority_sequence()

        i = 0
        while i < len(priority_sequence):
            branch = self.branches[priority_sequence[i]]
            if isinstance(branch, TargetDefinition):
                available_targets.append(branch)
            else:
                branch.get_available_targets(available_targets)
            if isinstance(branch, ChoiceDefinition | SequenceDefinition) and branch.is_chosen_path_optional():
                i += 1
                continue
            if branch.is_optional():
                i += 1
                continue
            else:
                break
        return available_targets

    def is_there_next_branch(self, child_branch: SequenceDefinition | ChoiceDefinition | TargetDefinition) -> bool:
        index = self.branches.index(child_branch)
        if index + 1 < len(self.branches):
            return True
        return False

    def set_next_branch(self, child_branch: SequenceDefinition | ChoiceDefinition | TargetDefinition) -> None:
        index = self.branches.index(child_branch)
        self.chosen_branch = self.branches[index + 1]

    def resolve_branch(self) -> None:
        self.chosen_branch = None
        self.count += 1
        for branch in self.branches:
            branch.count = 0

    def set_chosen_branch(self, child_branch: SequenceDefinition | ChoiceDefinition | TargetDefinition) -> None:
        if not child_branch.is_optional() and child_branch.is_finished():
            if self.is_there_next_branch(child_branch):
                self.set_next_branch(child_branch)
            else:
                self.resolve_branch()
        else:
            self.chosen_branch = child_branch
        if self.parent is not None:
            self.parent.set_chosen_branch(self)

    def resolve_optional_branch(self, child_branch: SequenceDefinition | ChoiceDefinition | TargetDefinition) -> None:
        if child_branch.is_optional() and child_branch.is_finished():
            # if child_branch.is_optional() or child_branch.is_finished():
            if self.is_there_next_branch(child_branch):
                self.set_next_branch(child_branch)
            else:
                self.resolve_branch()
        else:
            self.chosen_branch = None
        if self.parent is not None:
            self.parent.resolve_optional_branch(self)


class TargetDefinition:
    def __init__(
        self,
        representation: str,
        modifier: ModifierDefinition,
        name: Token,
        parent: None | SequenceDefinition | ChoiceDefinition = None,
    ) -> None:
        self.__representation = representation
        self.parent = parent
        self.modifier = modifier
        self.count = 0
        self.name = name

    def __repr__(self) -> str:
        return self.__representation

    def is_optional(self) -> bool:
        return self.modifier.is_optional(self.count)

    def is_finished(self) -> bool:
        return self.modifier.is_finished(self.count)

    def resolve_optional_target(self) -> None:
        if self.parent is None:
            return
        self.parent.resolve_optional_branch(self)

    def register_match(self) -> None:
        self.count += 1
        if self.parent is None:
            return
        self.parent.set_chosen_branch(self)


class TreeDefinitionValidator:
    def __init__(self, edd: ElementDefinitionsDefined) -> None:
        self.__representation = str(f"{edd!r}")
        self.root: None | ChoiceDefinition | SequenceDefinition | TargetDefinition = None
        self.build_definition_tree(edd)

    def __repr__(self) -> str:
        return self.__representation

    def build_definition_tree(
        self, edd: ElementDefinitionsDefined, parent: None | ChoiceDefinition | SequenceDefinition = None
    ) -> None:
        if edd.order == ElementDefinitionsOrder.SINGLE_ELEMENT and edd.target is not None:
            if parent is None:
                target = TargetDefinition(f"{edd!r}", ModifierDefinition(edd.modifier), edd.target)
                self.root = target
            else:
                target = TargetDefinition(f"{edd!r}", ModifierDefinition(edd.modifier), edd.target, parent)
                parent.branches.append(target)
            return

        elif edd.order == ElementDefinitionsOrder.CHOICE:
            if parent is None:
                choice = ChoiceDefinition(f"{edd!r}", ModifierDefinition(edd.modifier))
                self.root = choice
            else:
                choice = ChoiceDefinition(f"{edd!r}", ModifierDefinition(edd.modifier), parent)
                parent.branches.append(choice)
            for child_def in edd.child_definitions:
                self.build_definition_tree(child_def, choice)
            return

        elif edd.order == ElementDefinitionsOrder.SEQUENCE:
            if parent is None:
                sequence = SequenceDefinition(f"{edd!r}", ModifierDefinition(edd.modifier))
                self.root = sequence
            else:
                sequence = SequenceDefinition(f"{edd!r}", ModifierDefinition(edd.modifier), parent)
                parent.branches.append(sequence)
            for child_def in edd.child_definitions:
                self.build_definition_tree(child_def, sequence)

    def get_available_targets(
        self,
    ) -> list[TargetDefinition]:
        available_targets: list[TargetDefinition] = []
        if isinstance(self.root, TargetDefinition):
            if self.root.is_optional() or not self.root.is_finished():
                available_targets.append(self.root)
        elif isinstance(self.root, ChoiceDefinition | SequenceDefinition):
            available_targets = self.root.get_available_targets()
        return available_targets

    def match_element(
        self,
        element: Token | str,
        cached_available_targets: list[TargetDefinition],
    ) -> bool:
        optional_targets: list[TargetDefinition] = []
        target: TargetDefinition | None = None

        i = 0
        while i < len(cached_available_targets):
            if element == cached_available_targets[i].name:
                target = cached_available_targets[i]
            elif cached_available_targets[i].is_optional():
                optional_targets.append(cached_available_targets[i])
            i += 1
            continue

        if target is None:
            return False

        if len(optional_targets) > 0:
            for optional_target in optional_targets:
                optional_target.resolve_optional_target()

        target.register_match()
        return True


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

    # def is_validation_complete(self, eddvalidator: ElementDefinitionsDefinedValidator) -> bool:
    #     if eddvalidator.is_target():
    #         match eddvalidator.modifier:
    #             case ElementDefinitionsModifier.ONLY_ONE_TIME:
    #                 if eddvalidator.match_count == 1:
    #                     return True
    #                 return False
    #             case ElementDefinitionsModifier.ONE_OR_MORE_TIMES:
    #                 if eddvalidator.match_count >= 1:
    #                     return True
    #                 return False
    #             case ElementDefinitionsModifier.ZERO_OR_MORE_TIMES:
    #                 return True
    #             case ElementDefinitionsModifier.ZERO_OR_ONE_TIMES:
    #                 if eddvalidator.match_count == 0 or eddvalidator.match_count == 1:
    #                     return True
    #                 return False
    #     # SEQUENCE OR CHOICE
    #     i = 0
    #     result = False
    #     for transit_definition in eddvalidator.branches:
    #         if transit_definition.order == ElementDefinitionsOrder.SINGLE_ELEMENT:
    #             pass
    #             continue
    #         if transit_definition.order == ElementDefinitionsOrder.SEQUENCE:
    #             if not self.is_validation_complete(transit_definition):
    #                 result = False
    #                 break
    #             result = True
    #             i += 1
    #             continue
    #         if transit_definition.order == ElementDefinitionsOrder.CHOICE:
    #             if self.is_validation_complete(transit_definition):
    #                 result = result or True
    #             else:
    #                 result = result or False
    #             i += 1
    #             continue
    #     return result

    def is_non_deterministic_content_model(self, targets: list[TargetDefinition]) -> bool:
        result = set()
        for target in targets:
            if target.name in result:
                return True
        return False

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
            # tree = TreeDefinitionValidator(element_definition)
            # available_targets = edd_tree.get_available_targets()
            # if self.is_non_deterministic_content_model(available_targets):
            #     # generate error
            #     pass
            return False
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
