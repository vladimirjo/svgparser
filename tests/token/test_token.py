from buffer.token import Token
from buffer.fragment import Fragment
import pytest

# Randomized Test Cases
@pytest.mark.parametrize("input_text, expected_output", [
    # ✅ Basic tests
    ("&#60;", "<"),  # Less than
    ("&#62;", ">"),  # Greater than
    ("&#38;", "&"),  # Ampersand
    ("&#39;", "'"),  # Single quote
    ("&#34;", '"'),  # Double quote
    ("&#x3C;", "<"),  # Hexadecimal Less than
    ("&#x3E;", ">"),  # Hexadecimal Greater than
    ("&#x26;", "&"),  # Hexadecimal Ampersand

    # ✅ Edge cases
    ("", ""),  # Empty input
    ("No references here.", "No references here."),  # No replacements
    ("&#999999999;", "&#999999999;"),  # Out-of-range character reference

    # ✅ Mixed references and text
    ("A&#60;B&#62;C", "A<B>C"),  # Mixed with letters
    ("Price: &#36;100", "Price: $100"),  # Dollar symbol
    ("Smiley: &#128578;", "Smiley: 🙂"),  # Unicode emoji
    ("Hex Smiley: &#x1F60A;", "Hex Smiley: 😊"),  # Hexadecimal emoji

    # ✅ Invalid & malformed references
    ("&#;", "&#;"),  # Just the `&#` (invalid)
    ("&#x;", "&#x;"),  # Just `&#x` without a number
    ("&#123", "&#123"),  # Missing semicolon
    ("&#x1F60A", "&#x1F60A"),  # Missing semicolon (hex)
    ("&#xZZZZ;", "&#xZZZZ;"),  # Invalid hexadecimal number
    ("Text &# 123 ; More", "Text &# 123 ; More"),  # Spaces in reference

    # ✅ Real-world cases
    ("<p>Hello&#44; World!</p>", "<p>Hello, World!</p>"),  # HTML snippet
    ("Unicode: &#x1F4A9;", "Unicode: 💩"),  # Unicode poop emoji
])

def test__token_replace_char_references(input_text, expected_output):
    token = Token(Fragment(input_text, 0,0))
    assert token.replace_char_references() == expected_output
