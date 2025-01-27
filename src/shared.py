from __future__ import annotations


from typing import TYPE_CHECKING

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


def verify_element_or_attribute_name(element_name: Token, error_collector: None | ErrorCollector = None) -> None:
    if len(element_name.chars) >= 1:
        first_char = element_name.chars[0]
        if not first_char.isalpha() and not first_char == "_":
            if error_collector is not None:
                error_collector.add_token_start(
                    element_name, "Element names must begin with a letter or an underscore(_)."
                )
    num_of_colons = 0
    if len(element_name.chars) >= 2:
        for index, char in enumerate(element_name.chars[1:]):
            if not char.isalnum() and char not in {"-", "_", ":", "."}:
                if error_collector is not None:
                    error_collector.add_token_pointer(
                        element_name,
                        index,
                        "The initial character of the name of an element can be followed by any number of letters, "
                        "digits, periods(.), hyphens(-), underscores or colons (:).",
                    )
            if char == ":":
                num_of_colons += 1
        if num_of_colons > 1:
            if error_collector is not None:
                error_collector.add_token_start(
                    element_name,
                    "Multiple colons are not allowed in element names. "
                    "The colon character is reserved for namespaces in XML.",
                )


def get_base_entity_increment(entity_reference: str) -> int:
    for key in BASE_ENTITY_REFERENCES.keys():
        if entity_reference[: len(key)] == key:
            return len(key)
    return 1


def verify_content_or_attribute_value(
    element_value: Token,
    error_collector: None | ErrorCollector = None,
) -> None:
    i = 0
    while i < len(element_value.chars):
        if element_value.chars[i] == '"':
            if error_collector is not None:
                error_collector.add_token_pointer(
                    element_value,
                    i,
                    'The " character must be escaped with &quot; sequence.',
                )
            i += 1
            continue
        if element_value.chars[i] == "'":
            if error_collector is not None:
                error_collector.add_token_pointer(
                    element_value,
                    i,
                    "The ' character must be escaped with &apos; sequence.",
                )
            i += 1
            continue
        if element_value.chars[i] == "<":
            if error_collector is not None:
                error_collector.add_token_pointer(
                    element_value,
                    i,
                    "The < character must be escaped with &lt; sequence.",
                )
            i += 1
            continue
        if element_value.chars[i] == ">":
            if error_collector is not None:
                error_collector.add_token_pointer(
                    element_value,
                    i,
                    "The > character must be escaped with &gt; sequence.",
                )
            i += 1
            continue
        if element_value.chars[i] == "&":
            increment = get_base_entity_increment(element_value.chars[i:])
            if increment == 1 and error_collector is not None:
                error_collector.add_token_pointer(
                    element_value,
                    i,
                    "The & character must be escaped with &amp; sequence.",
                )
            i += increment
            continue
        i += 1
