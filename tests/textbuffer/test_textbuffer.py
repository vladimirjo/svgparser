import pytest
from xmlvalidator import TextBuffer


@pytest.mark.parametrize(
    "input_str, expected_valid, expected_invalid, expected_discouraged",
    [
        # 1. Basic Valid Input
        ("abc", "abc", [], []),
        ("Hello World!", "Hello World!", [], []),
        ("\tThis is XML", "\tThis is XML", [], []),
        ("\nNewline Test\n", "\nNewline Test\n", [], []),

        # 2. Whitespace Normalization (CRLF → LF, CR → LF)
        ("\r\n", "\n", [], []),
        ("\r", "\n", [], []),
        ("Line1\r\nLine2", "Line1\nLine2", [], []),

        # 3. Handling Invalid Characters
        ("\x00\x01abc\x02", "abc", [(0, 0x00), (1, 0x01), (5, 0x02)], []),
        ("Valid\x1FInvalid", "ValidInvalid", [(5, 0x1F)], []),

        # 4. Handling Discouraged Characters
        ("\x7FTest\x84", "\x7FTest\x84", [], [(0, 0x7F), (5, 0x84)]),
        ("\uFDD0Discouraged\uFDEF", "\uFDD0Discouraged\uFDEF", [], [(0, 0xFDD0), (12, 0xFDEF)]),

        # 5. Mixed Valid, Invalid, and Discouraged Characters
        ("Test\x7FValid\x1FDiscouraged\uFDD0End", "Test\x7FValidDiscouraged\uFDD0End",
         [(10, 0x1F)], [(4, 0x7F), (22, 0xFDD0)]),

        # 6. Edge Cases
        ("", "", [], []),  # Empty input
        ("\x7F\x84\x86", "\x7F\x84\x86", [], [(0, 0x7F), (1, 0x84), (2, 0x86)]),  # Only discouraged
        ("\x00\x01\x02", "", [(0, 0x00), (1, 0x01), (2, 0x02)], []),  # Only invalid characters
    ],
)
def test_buffer(input_str, expected_valid, expected_invalid, expected_discouraged):
    buffer = TextBuffer(input_str)
    assert buffer.valid_chars == expected_valid
    assert buffer.invalid_and_skipped_chars == expected_invalid
    assert buffer.valid_but_discouraged_chars == expected_discouraged
