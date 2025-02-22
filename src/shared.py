from __future__ import annotations

from typing import TYPE_CHECKING

from errorcollector import CritErr


if TYPE_CHECKING:
    from buffer_controller import Token
    from xmlvalidator import ErrorCollector


EMPTY_SPACES = {" ", "\n", "\t"}
QUOTES = {'"', "'"}
BASE_ENTITY_REFERENCES = {
    "&quot;": '"',
    "&apos;": "'",
    "&lt;": "<",
    "&gt;": ">",
    "&amp;": "&",
}


def is_namestartchar(char: str) -> bool:
    if len(char) != 1:
        return False
    codechar = ord(char)
    if codechar == ord(":"):
        return True
    if ord("A") <= codechar <= ord("Z"):
        return True
    if codechar == ord("_"):
        return True
    if ord("a") <= codechar <= ord("z"):
        return True
    if (
        0xC0 <= codechar <= 0xD6
        or 0xD8 <= codechar <= 0xF6
        or 0xF8 <= codechar <= 0x2FF
        or 0x370 <= codechar <= 0x37D
        or 0x37F <= codechar <= 0x1FFF
        or 0x200C <= codechar <= 0x200D
        or 0x2070 <= codechar <= 0x218F
        or 0x2C00 <= codechar <= 0x2FEF
        or 0x3001 <= codechar <= 0xD7FF
        or 0xF900 <= codechar <= 0xFDCF
        or 0xFDF0 <= codechar <= 0xFFFD
        or 0x10000 <= codechar <= 0xEFFFF
    ):
        return True
    return False


def is_namechar(char: str) -> bool:
    if len(char) != 1:
        return False
    if is_namestartchar(char):
        return True
    codechar = ord(char)
    if codechar == ord("-"):
        return True
    if codechar == ord("."):
        return True
    if ord("0") <= codechar <= ord("9"):
        return True
    if codechar == 0xB7 or 0x0300 <= codechar <= 0x036F or 0x203F <= codechar <= 0x2040:
        return True
    return False


def check_xmlname(token: Token, err: ErrorCollector) -> None:
    if not is_namestartchar(token.chars[0]):
        err.add(token, CritErr.XMLNAME_FIRST_CHAR_ERROR, 0)
    error_pointers: list[int] = []
    i = 1
    while i < len(token.chars):
        if not is_namechar(token.chars[i]):
            error_pointers.append(i)
        i += 1
    for error_pointer in error_pointers:
        err.add(token, CritErr.XMLNAME_OTHER_CHARS_ERROR, error_pointer)


def check_nmtoken(token: Token, err: ErrorCollector) -> None:
    error_pointers: list[int] = []
    i = 0
    while i < len(token.chars):
        if not is_namechar(token.chars[i]):
            error_pointers.append(i)
        i += 1
    for error_pointer in error_pointers:
        err.add(token, CritErr.NMTOKEN_ERROR, error_pointer)


def check_attvalue(token: Token, err: ErrorCollector) -> None:
    # both qoutes are already included in buffer separation
    error_pointers: list[int] = []
    i = 0
    while i < len(token.chars):
        if token.chars[i] == "<" or token.chars[i] == "&":
            error_pointers.append(i)
        i += 1
    for error_pointer in error_pointers:
        err.add(token, CritErr.ATTIBUTE_VALUE_ERROR, error_pointer)


def check_entityvalue(token: Token, err: ErrorCollector) -> None:
    # both qoutes are already included in buffer separation
    error_pointers: list[int] = []
    i = 0
    while i < len(token.chars):
        if token.chars[i] == "%" or token.chars[i] == "&":
            error_pointers.append(i)
        i += 1
    for error_pointer in error_pointers:
        err.add(token, CritErr.ENTITY_VALUE_ERROR, error_pointer)


def is_pubidchar(char: str) -> bool:
    if len(char) != 1:
        return False
    if char in {" ", "\r", "\n"}:  # 0x20 | 0x0D | 0x0A
        return True
    if char.isalnum():  # [a-zA-Z0-9]
        return True
    if char in {"-()+,./:=?;!*#@$_%"}:
        return True
    return False


def check_pubid_literal(token: Token, err: ErrorCollector) -> None:
    error_pointers: list[int] = []
    i = 0
    while i < len(token.chars):
        if not is_pubidchar(token.chars[i]):
            error_pointers.append(i)
        i += 1
    for error_pointer in error_pointers:
        err.add(token, CritErr.PUBID_LITERAL_ERROR, error_pointer)


# def verify_element_or_attribute_name(element_name: Token, err: ErrorCollector) -> None:
#     if len(element_name.chars) >= 1:
#         first_char = element_name.chars[0]
#         if not first_char.isalpha() and not first_char == "_":
#             if err is not None:
#                 err.add_token_start(element_name, "Element names must begin with a letter or an underscore(_).")
#     num_of_colons = 0
#     if len(element_name.chars) >= 2:
#         for index, char in enumerate(element_name.chars[1:]):
#             if not char.isalnum() and char not in {"-", "_", ":", "."}:
#                 if err is not None:
#                     err.add_token_pointer(
#                         element_name,
#                         index,
#                         "The initial character of the name of an element can be followed by any number of letters, "
#                         "digits, periods(.), hyphens(-), underscores or colons (:).",
#                     )
#             if char == ":":
#                 num_of_colons += 1
#         if num_of_colons > 1:
#             if err is not None:
#                 err.add_token_start(
#                     element_name,
#                     "Multiple colons are not allowed in element names. "
#                     "The colon character is reserved for namespaces in XML.",
#                 )


def get_base_entity_increment(entity_reference: str) -> int:
    for key in BASE_ENTITY_REFERENCES.keys():
        if entity_reference[: len(key)] == key:
            return len(key)
    return 1


# def verify_content_or_attribute_value(
#     element_value: Token,
#     error_collector: None | ErrorCollector = None,
# ) -> None:
#     i = 0
#     while i < len(element_value.chars):
#         if element_value.chars[i] == '"':
#             if error_collector is not None:
#                 error_collector.add_token_pointer(
#                     element_value,
#                     i,
#                     'The " character must be escaped with &quot; sequence.',
#                 )
#             i += 1
#             continue
#         if element_value.chars[i] == "'":
#             if error_collector is not None:
#                 error_collector.add_token_pointer(
#                     element_value,
#                     i,
#                     "The ' character must be escaped with &apos; sequence.",
#                 )
#             i += 1
#             continue
#         if element_value.chars[i] == "<":
#             if error_collector is not None:
#                 error_collector.add_token_pointer(
#                     element_value,
#                     i,
#                     "The < character must be escaped with &lt; sequence.",
#                 )
#             i += 1
#             continue
#         if element_value.chars[i] == ">":
#             if error_collector is not None:
#                 error_collector.add_token_pointer(
#                     element_value,
#                     i,
#                     "The > character must be escaped with &gt; sequence.",
#                 )
#             i += 1
#             continue
#         if element_value.chars[i] == "&":
#             increment = get_base_entity_increment(element_value.chars[i:])
#             if increment == 1 and error_collector is not None:
#                 error_collector.add_token_pointer(
#                     element_value,
#                     i,
#                     "The & character must be escaped with &amp; sequence.",
#                 )
#             i += increment
#             continue
#         i += 1
