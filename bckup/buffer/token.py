from __future__ import annotations

from .shared import EMPTY_SPACES
from .shared import QUOTES
from .fragment import Fragment


class Token:
    def __init__(self, fragment: Fragment) -> None:
        self.chars = fragment.chars
        self.buffer_slot = fragment.buffer_slot
        self.buffer_pointer = fragment.buffer_pointer
        self.is_cdata = True
        self.fragments: list[Fragment] = []
        self.fragments.append(fragment)

    def __hash__(self):
        return hash(self.chars)

    def __eq__(self, other: str | Token):
        if isinstance(other, Token):
            return self.chars == other.chars
        if isinstance(other, str):
            return self.chars == other
        return False

    def __repr__(self):
        return f"({self.chars!r})"

    def startswith(self, search_string: str) -> bool:
        if self.chars.startswith(search_string):
            return True
        return False

    def endswith(self, search_string: str) -> bool:
        if self.chars.endswith(search_string):
            return True
        return False

    def resolve_pointer(self, in_token_pointer: int) -> int:
        index = 0
        while in_token_pointer > len(self.fragments[index].chars):
            in_token_pointer -= len(self.fragments[index].chars)
            index += 1
            if index >= len(self.fragments):
                raise ValueError("Invalid in token pointer.")
        return self.fragments[index].buffer_pointer + in_token_pointer

    def end_pointer(self) -> int:
        return self.fragments[-1].end_pointer()

    def match(self, string_to_match: str) -> bool:
        if self.chars == string_to_match:
            return True
        return False

    def is_empty_spaces(self) -> bool:
        if self.chars in EMPTY_SPACES:
            return True
        return False

    def is_quotes(self) -> bool:
        if self.chars in QUOTES:
            return True
        return False

    def add_fragment(self, token: Fragment) -> None:
        last_fragment = self.fragments[-1]
        if last_fragment.buffer_slot == token.buffer_slot and last_fragment.end_pointer() + 1 == token.buffer_pointer:
            last_fragment.chars += token.chars
        else:
            self.fragments.append(token)
        self.chars += token.chars

    def add_token(self, token: Token) -> None:
        last_fragment = self.fragments[-1]
        if (
            last_fragment.buffer_slot == token.fragments[0].buffer_slot
            and last_fragment.end_pointer() + 1 == token.fragments[0].buffer_pointer
        ):
            self.add_fragment(token.fragments[0])
            if len(token.fragments) > 1:
                self.fragments.extend(token.fragments[1:])
        else:
            self.fragments.extend(token.fragments)
        token.fragments = []

    def remove_length_from_left(self, length) -> None:
        if length <= 0:
            raise ValueError("Length to remove must be larger than 0.")
        if length > len(self.chars):
            length = len(self.chars)
        fragments: list[Fragment] = []
        i = 0
        while length > 0:
            if length >= len(self.fragments[i].chars):
                length -= len(self.fragments[i].chars)
                i += 1
                continue
            new_fragment = Fragment(
                self.fragments[i].chars[length:],
                self.fragments[i].buffer_pointer,
                self.fragments[i].buffer_slot,
            )
            fragments.append(new_fragment)
            length = 0
            i += 1
        while i < len(self.fragments):
            fragments.append(self.fragments[i])
            i += 1
        i = 0
        self.chars = ""
        while i < len(fragments):
            self.chars += fragments[i].chars
            i += 1
        self.fragments = fragments
        if len(fragments) > 0:
            self.buffer_slot = fragments[0].buffer_slot
            self.buffer_pointer = fragments[0].buffer_pointer

    # def extract(self, length: int) -> Token:
    #     if length <= 0:
    #         raise ValueError("Length to extract must be larger than 0.")
    #     if length > len(self.chars):
    #         length = len(self.chars)
    #     length_to_remove = length
    #     fragments: list[Fragment] = []
    #     i = 0
    #     while length > 0 and i < len(self.fragments):
    #         if length >= len(self.fragments[i].chars):
    #             new_fragment = Fragment(
    #                 self.fragments[i].chars,
    #                 self.fragments[i].buffer_pointer,
    #                 self.fragments[i].buffer_slot,
    #             )
    #             fragments.append(new_fragment)
    #             length -= len(new_fragment.chars)
    #             i += 1
    #         else:
    #             new_fragment = Fragment(
    #                 self.fragments[i].chars[:length],
    #                 self.fragments[i].buffer_pointer,
    #                 self.fragments[i].buffer_slot,
    #             )
    #             fragments.append(new_fragment)
    #             length -= len(new_fragment.chars)
    #     i = 1
    #     new_token = Token(fragments[0])
    #     while i < len(fragments):
    #         new_token.add_fragment(fragments[i])
    #     self.remove_length_from_left(length_to_remove)
    #     return new_token

    def search_preceded_by_whitespace(self, substring: str, start: int = 0) -> int:
        while start < len(self.chars):
            if self.chars[start].isspace():
                start += 1
                continue
            else:
                break
        if start + len(substring) > len(self.chars):
            return -1
        if self.chars[start : start + len(substring)] == substring:
            return start + len(substring)
        return -1

    def is_namestartchar(self, char: str) -> bool:
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

    def is_namechar(self, char: str) -> bool:
        if len(char) != 1:
            return False
        if self.is_namestartchar(char):
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

    def is_xmlname(self) -> bool:
        error_pointers: list[int] = []
        if not self.is_namestartchar(self.chars[0]):
            error_pointers.append(0)
        i = 1
        while i < len(self.chars):
            if not self.is_namechar(self.chars[i]):
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def is_nmtoken(self) -> bool:
        error_pointers: list[int] = []
        i = 0
        while i < len(self.chars):
            if not self.is_namechar(self.chars[i]):
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def is_attvalue(self) -> bool:
        # both qoutes are already included in buffer separation
        error_pointers: list[int] = []
        i = 0
        while i < len(self.chars):
            if self.chars[i] == "<" or self.chars[i] == "&":
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def is_entityvalue(self) -> bool:
        # both qoutes are already included in buffer separation
        error_pointers: list[int] = []
        i = 0
        while i < len(self.chars):
            if self.chars[i] == "%" or self.chars[i] == "&":
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def is_pubidchar(self, char: str) -> bool:
        if len(char) != 1:
            return False
        if char in {" ", "\r", "\n"}:  # 0x20 | 0x0D | 0x0A
            return True
        if char.isalnum():  # [a-zA-Z0-9]
            return True
        if char in {"-()+,./:=?;!*#@$_%"}:
            return True
        return False

    def check_pubid_literal(self) -> bool:
        error_pointers: list[int] = []
        i = 0
        while i < len(self.chars):
            if not self.is_pubidchar(self.chars[i]):
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def replace_char_references(self, text: str) -> str:
        """Convert XML character references (&#NNN; and &#xNNN;) to Unicode characters."""
        result = []
        i = 0
        length = len(text)

        while i < length:
            if text[i : i + 2] == "&#":  # Start of a character reference
                end = i + 2
                is_hex = text[end] == "x" if end < length else False  # Check if it's hexadecimal

                if is_hex:
                    end += 1  # Move past 'x'

                # Extract numeric part
                num_start = end
                while end < length and text[end].isalnum():
                    end += 1

                if end < length and text[end] == ";":  # Ensure proper termination
                    num_str = text[num_start:end]
                    try:
                        char_code = int(num_str, 16 if is_hex else 10)  # Convert to Unicode
                        result.append(chr(char_code))  # Append Unicode character
                        i = end  # Move past `;`
                    except ValueError:
                        result.append(text[i])  # Append as-is if invalid reference
                else:
                    result.append(text[i])  # Append as-is if improperly formatted
            else:
                result.append(text[i])  # Append normal characters

            i += 1  # Move to next character

        return "".join(result)

    def normalize_spaces(self, text: str) -> str:
        return " ".join(text.split())

    def set_non_cdata(self) -> None:
        self.is_cdata = False

    def get_normalized_value(self) -> str:
        replaced_char_references = self.replace_char_references(self.chars)
        if self.is_cdata:
            return replaced_char_references
        return self.normalize_spaces(replaced_char_references)
