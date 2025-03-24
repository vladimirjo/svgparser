from __future__ import annotations

from typing import NamedTuple


class CharInfo(NamedTuple):
    position: int
    code: int


class TextBuffer:
    def __init__(self, chars: str, bufferslot: int) -> None:
        """Processes and classifies characters in XML text."""
        self.bufferslot = bufferslot
        # #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
        self.valid_chars: str
        # INVALID AND SKIPPED CHARACTERS
        # Control characters (except for tab #x9, newline #xA, and carriage return #xD) are not allowed.
        # Surrogate pairs (#xD800-#xDFFF) are not allowed.
        # Special Unicode characters (#xFFFE, #xFFFF) are explicitly excluded.
        self.invalid_and_skipped_chars: list[CharInfo] = []
        # VALID BUT DISCOURAGED CHARS
        # However, some characters, while technically legal, are discouraged by the specification. These include:
        # C1 Control Characters (#x7F-#x84, #x86-#x9F).
        # Noncharacters (#xFDD0-#xFDEF, and #x[1-10]FFFE-#x[1-10]FFFF).
        self.valid_but_discouraged_chars: list[CharInfo] = []
        self.read(chars)

    def is_discouraged(self, code: int) -> bool:
        """Checks if a character is valid but discouraged."""
        return (
            (0x7F <= code <= 0x84)
            or (0x86 <= code <= 0x9F)
            or (0xFDD0 <= code <= 0xFDEF)
            or (0x1FFFE <= code <= 0x10FFFF and code & 0xFFFF in {0xFFFE, 0xFFFF})
        )

    def is_valid(self, code: int) -> bool:
        """Checks if a character is a valid XML character."""
        return (
            code in {0x9, 0xA}
            or (0x20 <= code <= 0xD7FF)
            or (0xE000 <= code <= 0xFFFD)
            or (0x10000 <= code <= 0x10FFFF)
        )

    def read(self, chars: str) -> None:
        """Reads and processes the input characters."""
        valid_chars: list[str] = []
        invalid_and_skipped_chars: list[CharInfo] = []
        valid_but_discouraged_chars: list[CharInfo] = []
        i = 0

        while i < len(chars):
            char = chars[i]
            code = ord(char)

            # Normalize line breaks correctly
            if code == 0xD:  # '\r'
                if i + 1 < len(chars) and chars[i + 1] == "\n":
                    i += 1  # Skip the '\n' in "\r\n"
                valid_chars.append("\n")
            elif self.is_valid(code):
                if self.is_discouraged(code):
                    valid_but_discouraged_chars.append(CharInfo(i, code))
                valid_chars.append(char)
            else:
                invalid_and_skipped_chars.append(CharInfo(i, code))

            i += 1

        self.valid_chars = "".join(valid_chars)
        self.invalid_and_skipped_chars = invalid_and_skipped_chars
        self.valid_but_discouraged_chars = valid_but_discouraged_chars
