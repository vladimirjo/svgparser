from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector

    from .defelem import DefElemDefined

from errorcollector import ValidErr

from .defelem import DefElemModifierEnum
from .defelem import DefElemOrderEnum


class ValElemModifier:
    def __init__(self, modifier: DefElemModifierEnum) -> None:
        self.modifier = modifier

    def __repr__(self) -> str:
        match self.modifier:
            case DefElemModifierEnum.ONLY_ONE:
                return "ONLY_ONE"
            case DefElemModifierEnum.ZERO_OR_ONE:
                return "ZERO_OR_ONE"
            case DefElemModifierEnum.ONE_OR_MORE:
                return "ONE_OR_MORE"
            case DefElemModifierEnum.ZERO_OR_MORE:
                return "ZERO_OR_MORE"
            case _:
                return "UNKNOWN"

    def is_optional(self, count: int) -> bool:
        match self.modifier:
            case DefElemModifierEnum.ONLY_ONE:
                return False
            case DefElemModifierEnum.ZERO_OR_ONE:
                if count < 1:
                    return True
                return False
            case DefElemModifierEnum.ONE_OR_MORE:
                if count >= 1:
                    return True
                return False
            case DefElemModifierEnum.ZERO_OR_MORE:
                return True
            case _:
                raise ValueError("Unknown value for Modifier.")

    def is_count_met(self, count: int) -> bool:
        match self.modifier:
            case DefElemModifierEnum.ONLY_ONE:
                if count == 1:
                    return True
                return False
            case DefElemModifierEnum.ZERO_OR_ONE:
                if count == 0 or count == 1:
                    return True
                return False
            case DefElemModifierEnum.ONE_OR_MORE:
                if count >= 1:
                    return True
                return False
            case DefElemModifierEnum.ZERO_OR_MORE:
                if count >= 0:
                    return True
                return False
            case _:
                raise ValueError("Unknown value for Modifier.")


class ValElemChoice:
    def __init__(
        self,
        representation: str,
        modifier: ValElemModifier,
        parent: None | ValElemSequence | ValElemChoice = None,
    ) -> None:
        self.__representation = representation
        self.parent = parent
        self.modifier = modifier
        self.count = 0
        self.chosen_branch: None | ValElemSequence | ValElemChoice | ValElemTarget = None
        self.branches: list[ValElemSequence | ValElemChoice | ValElemTarget] = []

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
        while isinstance(branch, ValElemChoice | ValElemSequence) and branch.chosen_branch is not None:
            branch = branch.chosen_branch
        return branch.modifier.is_optional(branch.count)

    def is_count_met(self) -> bool:
        return self.modifier.is_count_met(self.count)

    def get_available_branches(self) -> list[ValElemSequence | ValElemChoice | ValElemTarget]:
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
        available_targets: list[ValElemTarget],
    ) -> list[ValElemTarget]:
        available_branches = self.get_available_branches()
        for branch in available_branches:
            if isinstance(branch, ValElemTarget):
                available_targets.append(branch)
            else:
                branch.get_available_targets(available_targets)
        return available_targets

    def resolve_branch(self) -> None:
        self.count += 1
        self.chosen_branch = None
        for branch in self.branches:
            branch.count = 0

    def set_chosen_branch(self, child_branch: ValElemSequence | ValElemChoice | ValElemTarget) -> None:
        if not child_branch.modifier.is_optional(child_branch.count) and child_branch.is_count_met():
            self.count += 1
            self.chosen_branch = None
            for branch in self.branches:
                branch.count = 0
        else:
            self.chosen_branch = child_branch
        if self.parent is not None:
            self.parent.set_chosen_branch(self)

    def resolve_optional_branch(self, child_branch: ValElemSequence | ValElemChoice | ValElemTarget) -> None:
        if child_branch.is_optional() and self.is_count_met():
            self.resolve_branch()
        if self.parent is not None:
            self.parent.resolve_optional_branch(self)


class ValElemSequence:
    def __init__(
        self,
        representation: str,
        modifier: ValElemModifier,
        parent: None | ValElemSequence | ValElemChoice = None,
    ) -> None:
        self.__representation = representation
        self.parent = parent
        self.modifier = modifier
        self.count = 0
        self.chosen_branch: None | ValElemSequence | ValElemChoice | ValElemTarget = None
        self.branches: list[ValElemSequence | ValElemChoice | ValElemTarget] = []

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
        while isinstance(branch, ValElemChoice | ValElemSequence) and branch.chosen_branch is not None:
            branch = branch.chosen_branch
        return branch.modifier.is_optional(branch.count)

    def is_count_met(self) -> bool:
        return self.modifier.is_count_met(self.count)

    def get_available_branches(self) -> list[ValElemSequence | ValElemChoice | ValElemTarget]:
        available_branches: list[ValElemSequence | ValElemChoice | ValElemTarget] = []
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
        available_targets: list[ValElemTarget],
    ) -> list[ValElemTarget]:
        available_branches = self.get_available_branches()
        for branch in available_branches:
            if isinstance(branch, ValElemTarget):
                available_targets.append(branch)
            else:
                branch.get_available_targets(available_targets)
        return available_targets

    def is_there_next_branch(self, child_branch: ValElemSequence | ValElemChoice | ValElemTarget) -> bool:
        index = self.branches.index(child_branch)
        if index + 1 < len(self.branches):
            return True
        return False

    def set_next_branch(self, child_branch: ValElemSequence | ValElemChoice | ValElemTarget) -> None:
        index = self.branches.index(child_branch)
        self.chosen_branch = self.branches[index + 1]

    def resolve_branch(self) -> None:
        self.chosen_branch = None
        self.count += 1
        for branch in self.branches:
            branch.count = 0

    def set_chosen_branch(self, child_branch: ValElemSequence | ValElemChoice | ValElemTarget) -> None:
        if not child_branch.modifier.is_optional(child_branch.count) and child_branch.is_count_met():
            if self.is_there_next_branch(child_branch):
                self.set_next_branch(child_branch)
            else:
                self.resolve_branch()
        else:
            self.chosen_branch = child_branch
        if self.parent is not None:
            self.parent.set_chosen_branch(self)

    def resolve_optional_branch(self, child_branch: ValElemSequence | ValElemChoice | ValElemTarget) -> None:
        if child_branch.is_optional() and child_branch.is_count_met():
            if self.is_there_next_branch(child_branch):
                self.set_next_branch(child_branch)
            else:
                self.resolve_branch()
        else:
            self.chosen_branch = None
        if self.parent is not None:
            self.parent.resolve_optional_branch(self)


class ValElemTarget:
    def __init__(
        self,
        representation: str,
        modifier: ValElemModifier,
        name: Token,
        parent: None | ValElemSequence | ValElemChoice = None,
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


class ValElemTree:
    def __init__(self, edd: DefElemDefined, error_collector: ErrorCollector) -> None:
        self.__edd = edd
        self.__representation = str(f"{edd!r}")
        self.err = error_collector
        self.root: None | ValElemChoice | ValElemSequence | ValElemTarget = None
        self.build_definition_tree(edd)

    def __repr__(self) -> str:
        return self.__representation

    def build_definition_tree(self, edd: DefElemDefined, parent: None | ValElemChoice | ValElemSequence = None) -> None:
        if edd.order == DefElemOrderEnum.SINGLE_ELEMENT and edd.target is not None:
            if parent is None:
                target = ValElemTarget(f"{edd!r}", ValElemModifier(edd.modifier), edd.target)
                self.root = target
            else:
                target = ValElemTarget(f"{edd!r}", ValElemModifier(edd.modifier), edd.target, parent)
                parent.branches.append(target)
            return

        elif edd.order == DefElemOrderEnum.CHOICE:
            if parent is None:
                choice = ValElemChoice(f"{edd!r}", ValElemModifier(edd.modifier))
                self.root = choice
            else:
                choice = ValElemChoice(f"{edd!r}", ValElemModifier(edd.modifier), parent)
                parent.branches.append(choice)
            for child_def in edd.child_definitions:
                self.build_definition_tree(child_def, choice)
            return

        elif edd.order == DefElemOrderEnum.SEQUENCE:
            if parent is None:
                sequence = ValElemSequence(f"{edd!r}", ValElemModifier(edd.modifier))
                self.root = sequence
            else:
                sequence = ValElemSequence(f"{edd!r}", ValElemModifier(edd.modifier), parent)
                parent.branches.append(sequence)
            for child_def in edd.child_definitions:
                self.build_definition_tree(child_def, sequence)

    def get_available_targets(
        self,
    ) -> list[ValElemTarget]:
        available_targets: list[ValElemTarget] = []
        if isinstance(self.root, ValElemTarget):
            target = self.root
            if not target.is_optional() and target.is_count_met():
                return available_targets
            available_targets.append(target)
            return available_targets
        elif isinstance(self.root, ValElemChoice | ValElemSequence):
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
        cached_available_targets: list[ValElemTarget],
    ) -> bool:
        optional_targets: list[ValElemTarget] = []
        target: ValElemTarget | None = None

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

    def is_non_deterministic_content_model(self, targets: list[ValElemTarget]) -> bool:
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
