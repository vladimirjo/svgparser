from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer_controller import Token
    from errorcollector import ErrorCollector
    from xmlvalidator import ValidatorAttribute
    from xmlvalidator import ValidatorCData
    from xmlvalidator import ValidatorParsedText
    from xmlvalidator import ValidatorTag

from enum import Enum
from enum import auto
from enum import unique

from errorcollector import ValidErr
from errorcollector import CritErr


@unique
class ElementDefinitionsModifier(Enum):
    ONLY_ONE = auto()
    ZERO_OR_ONE = auto()
    ONE_OR_MORE = auto()
    ZERO_OR_MORE = auto()


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


class PCDATAElement:
    def __init__(self, content: Token) -> None:
        self.content = content

    def get_token(self) -> Token:
        return self.content


class TagElement:
    def __init__(self, name: Token) -> None:
        self.name: Token = name
        self.child_elements: list[TagElement | PCDATAElement] = []
        self.attrs: list[AttrElement] = []

    def get_token(self) -> Token:
        return self.name


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
        self.modifier: ElementDefinitionsModifier = self.get_modifier()
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

    def get_modifier(self) -> ElementDefinitionsModifier:
        if self.tokens[-1] == ("+"):
            self.tokens.pop(-1)
            return ElementDefinitionsModifier.ZERO_OR_ONE
        if self.tokens[-1] == ("?"):
            self.tokens.pop(-1)
            return ElementDefinitionsModifier.ONE_OR_MORE
        if self.tokens[-1] == ("*"):
            self.tokens.pop(-1)
            return ElementDefinitionsModifier.ZERO_OR_MORE
        return ElementDefinitionsModifier.ONLY_ONE

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


class ElementDefinitionsMixed:
    def __init__(self, tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.__representation = self.get_representation(tokens)
        self.err = error_collector
        self.tokens = tokens
        self.is_definition_valid: bool = True
        self.modifier: ElementDefinitionsModifier = self.get_modifier()
        self.strip_paranthesis()
        if not self.is_definition_valid:
            return
        self.valid_tags: set[Token] = set()
        self.parse_elements()

    def __repr__(self) -> str:
        return self.__representation

    def get_modifier(self) -> ElementDefinitionsModifier:
        if self.tokens[-1] == ("*"):
            self.tokens.pop(-1)
            return ElementDefinitionsModifier.ZERO_OR_MORE
        # check for other not valid tokens at the end of the sequence
        return ElementDefinitionsModifier.ONLY_ONE

    def strip_paranthesis(self) -> None:
        if self.tokens[0] != ("(") or self.tokens[-1] != (")"):
            self.is_definition_valid = False
            self.err.add(self.tokens[0], CritErr.MIXED_PARENTHESIS)
            return
        else:
            self.tokens.pop(0)
            self.tokens.pop(-1)

    def get_representation(self, tokens: list[Token]) -> str:
        text = ""
        for index, token in enumerate(tokens):
            if index == len(tokens) - 1:
                text += token.chars
            else:
                text += token.chars + " "
        return text

    def parse_elements(self) -> None:
        if self.tokens[0].chars != "#PCDATA":
            self.err.add(self.tokens[0], CritErr.MIXED_PCDATA)
            self.is_definition_valid = False
            return
        ##########################################################
        # check if a tagname is a valid name to see if it needs to be deactivated
        ##########################################################
        if (
            self.tokens[0] == "#PCDATA"
            and len(self.tokens) > 1
            and self.modifier != ElementDefinitionsModifier.ZERO_OR_MORE
        ):
            self.err.add(self.tokens[0], CritErr.MIXED_PCDATA_END_STAR)
            self.is_definition_valid = False
            return

        i = 1
        last_token_is_element = True
        while i < len(self.tokens):
            element = self.tokens[i]
            if element == "|" and last_token_is_element:
                i += 1
                last_token_is_element = False
                continue
            if element == "|" and not last_token_is_element:
                self.err.add(element, CritErr.MIXED_SEQ_PIPE)
                self.is_definition_valid = False
                return
            if element != "|" and last_token_is_element:
                self.err.add(element, CritErr.MIXED_PIPE_SEPARATION)
                self.is_definition_valid = False
                return
            if element != "|" and not last_token_is_element:
                if element.chars == "#PCDATA":
                    self.err.add(element, CritErr.MIXED_SINGLE_PCDATA_TAG)
                    self.is_definition_valid = False
                    return
                if element in self.valid_tags:
                    self.err.add(element, CritErr.MIXED_DUPLICATE_TAGS)
                    self.is_definition_valid = False
                    return
                self.valid_tags.add(element)
                last_token_is_element = True
                i += 1

    def validate_elements(self, elements: list[TagElement | PCDATAElement]) -> None:
        for element in elements:
            if isinstance(element, PCDATAElement):
                continue
            if element.name in self.valid_tags:
                continue
            self.err.add(element.name, ValidErr.MIXED_UNDEFINED_TAG)
        return


class ModifierDefinition:
    def __init__(self, modifier: ElementDefinitionsModifier) -> None:
        self.modifier = modifier

    def __repr__(self) -> str:
        match self.modifier:
            case ElementDefinitionsModifier.ONLY_ONE:
                return "ONLY_ONE"
            case ElementDefinitionsModifier.ZERO_OR_ONE:
                return "ZERO_OR_ONE"
            case ElementDefinitionsModifier.ONE_OR_MORE:
                return "ONE_OR_MORE"
            case ElementDefinitionsModifier.ZERO_OR_MORE:
                return "ZERO_OR_MORE"
            case _:
                return "UNKNOWN"

    def is_optional(self, count: int) -> bool:
        match self.modifier:
            case ElementDefinitionsModifier.ONLY_ONE:
                return False
            case ElementDefinitionsModifier.ZERO_OR_ONE:
                if count < 1:
                    return True
                return False
            case ElementDefinitionsModifier.ONE_OR_MORE:
                if count >= 1:
                    return True
                return False
            case ElementDefinitionsModifier.ZERO_OR_MORE:
                return True
            case _:
                raise ValueError("Unknown value for Modifier.")

    def is_count_met(self, count: int) -> bool:
        match self.modifier:
            case ElementDefinitionsModifier.ONLY_ONE:
                if count == 1:
                    return True
                return False
            case ElementDefinitionsModifier.ZERO_OR_ONE:
                if count == 0 or count == 1:
                    return True
                return False
            case ElementDefinitionsModifier.ONE_OR_MORE:
                if count >= 1:
                    return True
                return False
            case ElementDefinitionsModifier.ZERO_OR_MORE:
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

    def is_optional(self) -> bool:
        if self.chosen_branch is not None:
            return self.is_chosen_branch_optional()
        else:
            return self.modifier.is_optional(self.count)

    def is_chosen_branch_optional(self) -> bool:
        if self.chosen_branch is None:
            return False
        branch = self.chosen_branch
        while isinstance(branch, ChoiceDefinition | SequenceDefinition) and branch.chosen_branch is not None:
            branch = branch.chosen_branch
        return branch.modifier.is_optional(branch.count)

    def is_count_met(self) -> bool:
        return self.modifier.is_count_met(self.count)

    def get_available_branches(self) -> list[SequenceDefinition | ChoiceDefinition | TargetDefinition]:
        available_branches = []

        if self.chosen_branch is not None:
            if not self.modifier.is_optional(self.count + 1) and self.modifier.is_count_met(self.count + 1):
                available_branches.append(self.chosen_branch)
                return available_branches
            if not self.chosen_branch.is_optional():
                available_branches.append(self.chosen_branch)
                return available_branches

        for branch in self.branches:
            if branch not in available_branches:
                available_branches.append(branch)
        return available_branches

    def get_available_targets(
        self,
        available_targets: list[TargetDefinition],
    ) -> list[TargetDefinition]:
        available_branches = self.get_available_branches()
        for branch in available_branches:
            if isinstance(branch, TargetDefinition):
                available_targets.append(branch)
            else:
                branch.get_available_targets(available_targets)
        return available_targets

    def resolve_branch(self) -> None:
        self.count += 1
        self.chosen_branch = None
        for branch in self.branches:
            branch.count = 0

    def set_chosen_branch(self, child_branch: SequenceDefinition | ChoiceDefinition | TargetDefinition) -> None:
        if not child_branch.modifier.is_optional(child_branch.count) and child_branch.is_count_met():
            self.count += 1
            self.chosen_branch = None
            for branch in self.branches:
                branch.count = 0
        else:
            self.chosen_branch = child_branch
        if self.parent is not None:
            self.parent.set_chosen_branch(self)

    def resolve_optional_branch(self, child_branch: SequenceDefinition | ChoiceDefinition | TargetDefinition) -> None:
        if child_branch.is_optional() and self.is_count_met():
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

    def is_optional(self) -> bool:
        if self.chosen_branch is not None:
            if self.is_chosen_branch_optional():
                i = self.branches.index(self.chosen_branch)
                while i < len(self.branches):
                    if not self.branches[i].is_optional():
                        # if not self.branches[i].modifier.is_optional(self.branches[i].count):
                        return False
                    i += 1
                return True
            else:
                return False
        else:
            return self.modifier.is_optional(self.count)

    def is_chosen_branch_optional(self) -> bool:
        if self.chosen_branch is None:
            return False
        branch = self.chosen_branch
        while isinstance(branch, ChoiceDefinition | SequenceDefinition) and branch.chosen_branch is not None:
            branch = branch.chosen_branch
        return branch.modifier.is_optional(branch.count)

    def is_count_met(self) -> bool:
        return self.modifier.is_count_met(self.count)

    def get_available_branches(self) -> list[SequenceDefinition | ChoiceDefinition | TargetDefinition]:
        available_branches: list[SequenceDefinition | ChoiceDefinition | TargetDefinition] = []
        chosen_branch_index = i = 0

        if self.chosen_branch is not None:
            chosen_branch_index = i = self.branches.index(self.chosen_branch)

        while i < len(self.branches):
            available_branches.append(self.branches[i])
            if self.branches[i].is_optional():
                i += 1
            else:
                return available_branches

        if self.modifier.is_optional(self.count):
            i = 0
            while i < chosen_branch_index:
                available_branches.append(self.branches[i])
                i += 1
        return available_branches

    def get_available_targets(
        self,
        available_targets: list[TargetDefinition],
    ) -> list[TargetDefinition]:
        available_branches = self.get_available_branches()
        for branch in available_branches:
            if isinstance(branch, TargetDefinition):
                available_targets.append(branch)
            else:
                branch.get_available_targets(available_targets)
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
        if not child_branch.modifier.is_optional(child_branch.count) and child_branch.is_count_met():
            if self.is_there_next_branch(child_branch):
                self.set_next_branch(child_branch)
            else:
                self.resolve_branch()
        else:
            self.chosen_branch = child_branch
        if self.parent is not None:
            self.parent.set_chosen_branch(self)

    def resolve_optional_branch(self, child_branch: SequenceDefinition | ChoiceDefinition | TargetDefinition) -> None:
        if child_branch.is_optional() and child_branch.is_count_met():
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

    def is_count_met(self) -> bool:
        return self.modifier.is_count_met(self.count)

    def resolve_optional_target(self) -> None:
        if self.parent is None:
            return
        self.parent.resolve_optional_branch(self)

    def register_match(self) -> None:
        self.count += 1
        if self.parent is None:
            return
        self.parent.set_chosen_branch(self)


class DefinitionTreeValidator:
    def __init__(self, edd: ElementDefinitionsDefined, error_collector: ErrorCollector) -> None:
        self.__edd = edd
        self.__representation = str(f"{edd!r}")
        self.err = error_collector
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
            target = self.root
            if not target.is_optional() and target.is_count_met():
                return available_targets
            available_targets.append(target)
            return available_targets
        elif isinstance(self.root, ChoiceDefinition | SequenceDefinition):
            branch = self.root
            if (
                branch.chosen_branch is None
                and not branch.modifier.is_optional(branch.count)
                and branch.modifier.is_count_met(branch.count)
            ):
                return available_targets
            branch.get_available_targets(available_targets)
            return available_targets
        else:
            return available_targets

    def match(
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

    def is_non_deterministic_content_model(self, targets: list[TargetDefinition]) -> bool:
        # Duplicate targets are not allowed
        return len(targets) != len(set(targets))

    def is_requirements_met(self) -> bool:
        available_targets = self.get_available_targets()

        for target in available_targets:
            if not target.is_optional():
                return False

        for target in available_targets:
            target.resolve_optional_target()

        if self.root is not None and self.root.is_count_met():
            return True
        return False

    def validate_elements(self, elements: list[Token]) -> None:
        for element in elements:
            available_targets = self.get_available_targets()
            if self.is_non_deterministic_content_model(available_targets):
                self.err.add(self.__edd.tokens[0], ValidErr.NON_DETERMINISTIC_DUPLICATES)
                return

            if not self.match(element, available_targets):
                self.err.add(element, ValidErr.UNDEFINED_ELEMENT)
                return

        if not self.is_requirements_met():
            self.err.add(self.__edd.tokens[0], ValidErr.INCOMPLETE_DEFINITION)


class Dtd:
    def __init__(
        self,
        error_collector: ErrorCollector,
        root: Token | None = None,
    ) -> None:
        self.err = error_collector
        self.root = root
        self.element_definitions: dict[
            Token, ElementDefinitionsDefined | ElementDefinitionsMixed | ElementDefinitionsAny | ElementDefinitionsEmpty
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
            self.err.add(element_name, ValidErr.ELEMENT_ALREADY_DEFINED)
            return
        if len(tokens) == 0:
            self.err.add(element_name, ValidErr.ELEMENT_NO_DEFINITION)
            return
        if len(tokens) == 1 and tokens[0] == "ANY":
            self.element_definitions[element_name] = ElementDefinitionsAny()
            return
        if len(tokens) == 1 and tokens[0] == "EMPTY":
            self.element_definitions[element_name] = ElementDefinitionsEmpty()
            return
        for token in tokens:
            if token == "#PCDATA":
                mixed_content = ElementDefinitionsMixed(tokens, self.err)
                if mixed_content.is_definition_valid:
                    self.element_definitions[element_name] = mixed_content
                return
        self.element_definitions[element_name] = ElementDefinitionsDefined(tokens)

    def validate_parsed_element_with_element_definitions(
        self, parsed_element: Token, parsed_child_elements: list[ValidatorTag | ValidatorCData | ValidatorParsedText]
    ) -> None:
        if parsed_element not in self.element_definitions:
            self.err.add(parsed_element, ValidErr.UNDEFINED_ELEMENT)
            return
        element_definition = self.element_definitions[parsed_element]
        #######################################################
        # convert child elements in mixed content elements
        mixed_content_elements: list[TagElement | PCDATAElement] = []
        for child_element in parsed_child_elements:
            if isinstance(child_element, ValidatorTag) and child_element.name is not None:
                mixed_content_elements.append(TagElement(child_element.name))
            if isinstance(child_element, ValidatorCData | ValidatorParsedText) and child_element.content is not None:
                if len(mixed_content_elements) > 0 and isinstance(mixed_content_elements[-1], PCDATAElement):
                    mixed_content_elements[-1].content.add_token(child_element.content)
                else:
                    mixed_content_elements.append(PCDATAElement(child_element.content))
        #######################################################
        if isinstance(element_definition, ElementDefinitionsAny):
            return
        if isinstance(element_definition, ElementDefinitionsEmpty):
            return
        if isinstance(element_definition, ElementDefinitionsMixed):
            element_definition.validate_elements(mixed_content_elements)
            return
        if isinstance(element_definition, ElementDefinitionsDefined):
            tree = DefinitionTreeValidator(element_definition, self.err)
            non_mixed_child_elements: list[Token] = []
            for child_element in mixed_content_elements:
                if isinstance(child_element, PCDATAElement):
                    self.err.add(child_element.content, ValidErr.NO_PARSED_TEXT_IN_CONTENT)
                    continue
                non_mixed_child_elements.append(child_element.name)
            tree.validate_elements(non_mixed_child_elements)
            return
        return

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
