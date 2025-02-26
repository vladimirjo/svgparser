from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token
    from errorcollector import ErrorCollector

    from .dtdcore import DtdCData
    from .dtdcore import DtdTag

from enum import Enum
from enum import auto

from errorcollector import CritErr
from errorcollector import ValidErr


class DefElemModifierEnum(Enum):
    ONLY_ONE = auto()
    ZERO_OR_ONE = auto()
    ONE_OR_MORE = auto()
    ZERO_OR_MORE = auto()


class DefElemOrderEnum(Enum):
    SINGLE_ELEMENT = auto()
    SEQUENCE = auto()
    CHOICE = auto()


class DefElemAny:
    def validate(self) -> bool:
        return True


class DefElemEmpty:
    def validate(self) -> bool:
        return True


class DefElemDefined:
    def __init__(self, tokens: list[Token], parent: None | DefElemDefined = None) -> None:
        self.__representation = self.get_representation(tokens)
        self.tokens = tokens
        self.parent = parent
        self.is_definition_valid: bool = True
        self.modifier: DefElemModifierEnum = self.get_modifier()
        self.strip_paranthesis()
        if not self.is_definition_valid:
            return
        self.order: DefElemOrderEnum = DefElemOrderEnum.SINGLE_ELEMENT
        self.child_definitions: list[DefElemDefined] = []
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

    def get_modifier(self) -> DefElemModifierEnum:
        if self.tokens[-1] == ("+"):
            self.tokens.pop(-1)
            return DefElemModifierEnum.ZERO_OR_ONE
        if self.tokens[-1] == ("?"):
            self.tokens.pop(-1)
            return DefElemModifierEnum.ONE_OR_MORE
        if self.tokens[-1] == ("*"):
            self.tokens.pop(-1)
            return DefElemModifierEnum.ZERO_OR_MORE
        return DefElemModifierEnum.ONLY_ONE

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
                if self.order == DefElemOrderEnum.SINGLE_ELEMENT:
                    self.order = DefElemOrderEnum.SEQUENCE
                if self.order == DefElemOrderEnum.CHOICE:
                    ##################################################
                    # what about collecting errors while parsing definitions?
                    ##################################################
                    self.mark_definition_as_invalid()
                    return
                if len(accumulator) > 0:
                    child_definition = DefElemDefined(tokens=accumulator, parent=self)
                    self.child_definitions.append(child_definition)
                    accumulator = []
                i += 1
                continue
            if self.tokens[i] == "|" and nested_elements == 0:
                if self.order == DefElemOrderEnum.SINGLE_ELEMENT:
                    self.order = DefElemOrderEnum.CHOICE
                if self.order == DefElemOrderEnum.SEQUENCE:
                    self.mark_definition_as_invalid()
                    return
                if len(accumulator) > 0:
                    child_definition = DefElemDefined(accumulator, self)
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
            child_definition = DefElemDefined(accumulator, self)
            self.child_definitions.append(child_definition)


class DefElemMixed:
    def __init__(self, tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.__representation = self.get_representation(tokens)
        self.err = error_collector
        self.tokens = tokens
        self.is_definition_valid: bool = True
        self.modifier: DefElemModifierEnum = self.get_modifier()
        self.strip_paranthesis()
        if not self.is_definition_valid:
            return
        self.valid_tags: set[Token] = set()
        self.parse_elements()

    def __repr__(self) -> str:
        return self.__representation

    def get_modifier(self) -> DefElemModifierEnum:
        if self.tokens[-1] == ("*"):
            self.tokens.pop(-1)
            return DefElemModifierEnum.ZERO_OR_MORE
        # check for other not valid tokens at the end of the sequence
        return DefElemModifierEnum.ONLY_ONE

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
        if self.tokens[0] == "#PCDATA" and len(self.tokens) > 1 and self.modifier != DefElemModifierEnum.ZERO_OR_MORE:
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

    def validate_elements(self, elements: list[DtdTag | DtdCData]) -> None:
        from .dtdcore import DtdCData

        for element in elements:
            if isinstance(element, DtdCData):
                continue
            if element.name in self.valid_tags:
                continue
            self.err.add(element.name, ValidErr.MIXED_UNDEFINED_TAG)
        return
