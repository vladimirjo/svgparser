from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from xmltokens import XmlChars


class CritErr(Enum):
    # Well-formedness
    # Mismatched tags, unclosed elements, invalid attribute syntax
    ENTITY_ALREADY_REGISTERED = "Entity is already registed and cannot be registed again."
    TAG_LOCATION_INVALID = "Tag is not allowed inside DOCTYPE or Dtd Conditional subset."
    TAG_NAME_INVALID = "Tag name is missing. The tag is invalid."
    TAG_ONLY_ONE_ROOT = "Only one root tag is allowed."
    NODE_START_END = "Node start and sequence are inside same entity."
    NODE_MISSING_END = "Node is missing closing bracket."
    ATTR_EXPECTED_NAME = "Expected attribute name."
    ATTR_EXPECTED_EQUAL = "Expected equal sign."
    ATTR_EXPECTED_VALUE = "Expected attribute value enclosed in quotes."
    ATTR_EXPECTED_SPACE = "Expected empty space after attribute value."
    END_TAG_INVALID_TRAILING = "Invalid trailing after the name of the end-tag."
    END_TAG_NESTED_IN_DTD = "End-tag is not allowed inside DOCTYPE or Dtd Conditional subset."
    TAG_NOT_CLOSED = "Tag is not closed."
    END_TAG_NOT_MATCH = "End tag not matching any start tag."
    PUBID_LITERAL_CHAR_NOT_ALLOWED = "Character not allowed inside Pubid Literal."


class ValidErr(Enum):
    # DTD Conformance
    # Order violations, missing elements, attribute constraint violations
    MIXED_UNDEFINED_TAG = "Tag is not defined in mixed content definition."
    NON_DETERMINISTIC_DUPLICATES = (
        "Detected non-deterministic content model, duplicate references were found in definition."
    )
    UNDEFINED_ELEMENT = "Element not defined."
    INCOMPLETE_DEFINITION = "Not all requirements in definition are met."
    ELEMENT_ALREADY_DEFINED = "Element is defined already."
    ELEMENT_NO_DEFINITION = "Element does not have any definitions."
    NO_PARSED_TEXT_IN_CONTENT = "Parsed text data is not allowed in element content definition."


class ErrorToken:
    def __init__(
        self,
        xmlchars: XmlChars,
        err: CritErr | ValidErr,
        intoken_pointer: int,
        options: dict[str, str] | None,
    ) -> None:
        self.xmlchars = xmlchars
        self.err = err
        if intoken_pointer < -1:
            raise ValueError("Values lesser than -1 are not allowed.")
        if intoken_pointer == -1:
            self.intoken_pointer = len(xmlchars.strchars) - 1
        else:
            self.intoken_pointer = intoken_pointer
        self.options = options


class ErrorCollector:
    def __init__(self) -> None:
        self.tokens: list[ErrorToken] = []
        # self.buffer_slot: dict[int, list[tuple[int, str]]] = {}

    def add(
        self,
        xmlchars: XmlChars,
        error: CritErr | ValidErr,
        intoken_pointer: int = 0,
        options: dict[str, str] | None = None,
    ) -> None:
        if intoken_pointer < -1:
            raise ValueError("Values lesser than -1 are not allowed.")
        if intoken_pointer == -1:
            self.tokens.append(ErrorToken(xmlchars, error, len(xmlchars.strchars) - 1, options))
        else:
            self.tokens.append(ErrorToken(xmlchars, error, intoken_pointer, options))
