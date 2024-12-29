from __future__ import annotations

from shared import EMPTY_SPACES
from shared import QUOTES


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


class BufferUnit:
    def __init__(
        self,
        buffer: str,
        filename: str,
        buffer_slot: int,
    ) -> None:
        self.buffer = buffer
        self.filename = filename
        self.buffer_slot = buffer_slot


class BufferView:
    def __init__(self, buffer_unit: BufferUnit, buffer_type: str = "xml") -> None:
        self.buffer_unit = buffer_unit
        self.buffer_type = buffer_type
        self.in_buffer_pointer_start = 0
        self.in_buffer_pointer_end = self.in_buffer_pointer_start + len(self.buffer_unit.buffer)
        self.in_buffer_pointer_current = 0


class Fragment:
    def __init__(self, chars: str, buffer_pointer: int, buffer_slot: int) -> None:
        self.chars = chars
        self.buffer_pointer = buffer_pointer
        self.buffer_slot = buffer_slot

    def end_pointer(self) -> int:
        return self.buffer_pointer + len(self.chars) - 1


class Token:
    def __init__(self, fragment: Fragment) -> None:
        self.chars = fragment.chars
        self.buffer_slot = fragment.buffer_slot
        self.buffer_pointer = fragment.buffer_pointer
        self.fragments: list[Fragment] = []
        self.fragments.append(fragment)

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


class TokenAccumulator:
    def __init__(self) -> None:
        self.tokens: list[Token] = []

    def add_token(self, token: Token) -> None:
        self.tokens.append(token)

    def get_token(self) -> None | Token:
        if len(self.tokens) == 0:
            return None
        accumulator_token = self.tokens[0]
        i = 1
        while i < len(self.tokens):
            accumulator_token.add_token(self.tokens[i])
            i += 1
        return accumulator_token


class BufferController:
    def __init__(self) -> None:
        self.buffer_units: list[BufferUnit] = []
        self.buffer_views: list[BufferView] = []
        self.buffer_view_in_use: int = 0
        self.entity_stack: list[str] = []
        self.accumulator: TokenAccumulator = TokenAccumulator()
        self.tokens: list[Token] = []

    def add_buffer_unit(self, buffer: str, filename: str) -> None:
        buffer = normalize_newlines(buffer)
        buffer_slot = len(self.buffer_units)
        buffer_unit = BufferUnit(buffer, filename, buffer_slot)
        self.buffer_units.append(buffer_unit)
        buffer_view = BufferView(buffer_unit)
        self.buffer_views.append(buffer_view)

    def add_entity_to_buffer_views(self, entity_name: str, entity_sequence: Token):
        skip_places = len("&" + entity_name + ";")
        buffer_unit = self.buffer_units[entity_sequence.buffer_slot]
        entity_buffer_view = BufferView(buffer_unit)
        entity_buffer_view.in_buffer_pointer_end = len(entity_sequence.chars)

        first_buffer_view = self.buffer_views[self.buffer_view_in_use]
        first_buffer_view_end = self.buffer_views[self.buffer_view_in_use].in_buffer_pointer_current
        first_buffer_view.in_buffer_pointer_current -= 1

        second_buffer_view_start = (
            self.buffer_views[self.buffer_view_in_use].in_buffer_pointer_current + 1 + skip_places
        )
        second_buffer_view_end = self.buffer_views[self.buffer_view_in_use].in_buffer_pointer_end
        first_buffer_view.in_buffer_pointer_end = first_buffer_view_end

        second_buffer_view = BufferView(first_buffer_view.buffer_unit)
        second_buffer_view.in_buffer_pointer_start = second_buffer_view_start
        second_buffer_view.in_buffer_pointer_current = second_buffer_view_start
        second_buffer_view.in_buffer_pointer_end = second_buffer_view_end

        self.buffer_views.append(entity_buffer_view)
        self.buffer_views.append(second_buffer_view)
        self.buffer_view_in_use += 1
        self.entity_stack.append(entity_name)

    def get_read_offset(self, read_offset: int = 0) -> tuple[int, int]:
        if read_offset < 0:
            raise ValueError("Offset cannot be less than zero.")
        if read_offset == 0:
            return (self.buffer_view_in_use, self.buffer_views[self.buffer_view_in_use].in_buffer_pointer_current)

        buffer_index = self.buffer_view_in_use
        active_buffer = self.buffer_views[buffer_index]
        in_buffer_pointer = active_buffer.in_buffer_pointer_current

        while in_buffer_pointer + read_offset >= active_buffer.in_buffer_pointer_end:
            if buffer_index + 1 < len(self.buffer_views):
                read_offset -= active_buffer.in_buffer_pointer_end - in_buffer_pointer
                buffer_index += 1
                active_buffer = self.buffer_views[buffer_index]
                in_buffer_pointer = active_buffer.in_buffer_pointer_current
            else:
                break
        return (buffer_index, in_buffer_pointer + read_offset)

    def read(self, read_offset: int = 0, length: int = 1) -> Token | None:
        if length < 1:
            return None

        result = self.get_read_offset(read_offset)
        buffer_index, in_buffer_pointer = result

        active_buffer = self.buffer_views[buffer_index]
        if in_buffer_pointer >= len(active_buffer.buffer_unit.buffer):
            return None
        chars = active_buffer.buffer_unit.buffer[in_buffer_pointer]
        buffer_slot = active_buffer.buffer_unit.buffer_slot
        char_token = Fragment(chars, in_buffer_pointer, buffer_slot)
        sequence = Token(char_token)

        if length == 1:
            return sequence

        if in_buffer_pointer + length <= active_buffer.in_buffer_pointer_end:
            char_token.chars += active_buffer.buffer_unit.buffer[in_buffer_pointer + 1 : in_buffer_pointer + length]
            sequence.chars += active_buffer.buffer_unit.buffer[in_buffer_pointer + 1 : in_buffer_pointer + length]
            return sequence

        while in_buffer_pointer + length > active_buffer.in_buffer_pointer_end:
            char_token.chars += active_buffer.buffer_unit.buffer[
                in_buffer_pointer + 1 : active_buffer.in_buffer_pointer_end
            ]
            sequence.chars += active_buffer.buffer_unit.buffer[
                in_buffer_pointer + 1 : active_buffer.in_buffer_pointer_end
            ]
            length -= active_buffer.in_buffer_pointer_end - in_buffer_pointer
            if buffer_index + 1 < len(self.buffer_views):
                buffer_index += 1
                active_buffer = self.buffer_views[buffer_index]
                chars = active_buffer.buffer_unit.buffer[active_buffer.in_buffer_pointer_current]
                in_buffer_pointer = active_buffer.in_buffer_pointer_current
                buffer_slot = active_buffer.buffer_unit.buffer_slot
                char_token = Fragment(chars, in_buffer_pointer, buffer_slot)
                sequence.add_fragment(char_token)
            else:
                return None
        char_token.chars += active_buffer.buffer_unit.buffer[
            active_buffer.in_buffer_pointer_current + 1 : active_buffer.in_buffer_pointer_current + length
        ]
        sequence.chars += active_buffer.buffer_unit.buffer[
            active_buffer.in_buffer_pointer_current + 1 : active_buffer.in_buffer_pointer_current + length
        ]
        return sequence

    def move(self, move_offset: int = 1) -> None:
        if move_offset < 1:
            return None
        result = self.get_read_offset(move_offset)
        buffer_index, in_buffer_pointer = result
        self.buffer_view_in_use = buffer_index
        self.buffer_views[buffer_index].in_buffer_pointer_current = in_buffer_pointer

    def skip_forward(self) -> None:
        self.add_accumulator_to_tokens()
        current = self.read()
        while current is not None and current.chars in EMPTY_SPACES:
            self.move()
            current = self.read()

    def search(self, string_to_search: str) -> bool:
        token = self.read(length=len(string_to_search))
        if token is None:
            return False
        if token.chars == string_to_search:
            return True
        else:
            return False

    def search_in_tokens(self, tokens_string: str) -> bool:
        current = self.read()
        if current is None:
            return False
        if current.chars in tokens_string:
            return True
        return False

    def search_followed_by_empty_spaces(self, string_to_search: str) -> bool:
        sequence = self.read(len(string_to_search) + 1)
        if sequence is None:
            return False
        if sequence.chars[: len(string_to_search) + 1] != string_to_search:
            return False
        if sequence.chars[:-1] not in EMPTY_SPACES:
            return False
        return True

    def add_tagname(self) -> Token | None:
        self.add_accumulator_to_tokens()
        current = self.read()
        while current is not None and current.is_empty_spaces() and not current.match(">") and not current.match("<"):
            self.add_token_to_accumulator(current)
            current = self.read()
        while (
            current is not None and not current.is_empty_spaces() and not current.match(">") and not current.match("<")
        ):
            self.add_token_to_accumulator(current)
            current = self.read()
        self.add_accumulator_to_tokens()

    def clear_session(self) -> None:
        self.tokens = []
        self.accumulator = TokenAccumulator()

    def add_string(self, search_string: str) -> None:
        self.add_accumulator_to_tokens()
        if not self.search(search_string):
            return
        search_token = self.read(read_offset=0, length=len(search_string))
        if search_token is None:
            return
        self.tokens.append(search_token)
        self.move(move_offset=len(search_string))

    def add_accumulator_to_tokens(self) -> None:
        accumulator = self.accumulator.get_token()
        if accumulator is not None:
            self.tokens.append(accumulator)
            self.accumulator = TokenAccumulator()

    def add_token_to_accumulator(self, token: Token) -> None:
        self.accumulator.add_token(token)
        self.move(len(token.chars))

    def add_token(self, token: Token) -> None:
        self.tokens.append(token)
        self.move(len(token.chars))

    def is_xml_declaration(self) -> bool:
        read_from_buffer = self.read(read_offset=0, length=6)
        if read_from_buffer is None:
            return False
        if read_from_buffer.chars[:5] != "<?xml":
            return False
        if read_from_buffer.chars[5] not in EMPTY_SPACES:
            return False
        return True

    def tokenize_comment(self) -> None:
        if not self.search("<!--"):
            return
        self.add_string("<!--")
        current = self.read()
        while current is not None:
            if self.search("-->"):
                self.add_string("-->")
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_cdata(self) -> None:
        if not self.search("<![CDATA["):
            return
        self.add_string("<![CDATA[")
        current = self.read()
        while current is not None:
            if self.search("]]>"):
                self.add_string("]]>")
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_instructions(self) -> None:
        if not self.search("<?"):
            return
        self.add_string("<?")
        current = self.read()
        while current is not None:
            if self.search("?>"):
                self.add_string("?>")
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_dtd(self) -> None:
        nested_levels = 1
        quotes_in_use = ""
        tag_name_finished = False
        if not self.search("<!"):
            return
        self.add_string("<!")
        current = self.read()
        while current is not None:
            # inside quotes
            if quotes_in_use != "":
                if quotes_in_use == current.chars:
                    quotes_in_use = ""
                    self.add_token(current)
                    current = self.read()
                else:
                    self.add_token_to_accumulator(current)
                continue
            if current.chars in QUOTES:
                quotes_in_use = current.chars
                self.add_token_to_accumulator(current)
                current = self.read()
                continue
            # exit dtd
            if self.search("<") and not self.search("<!"):
                self.add_accumulator_to_tokens()
                return
            if not tag_name_finished:
                self.add_tagname()
                tag_name_finished = True
                continue
            # nesting further
            if self.search("<!"):
                self.add_string("<!")
                quotes_in_use = ""
                nested_levels += 1
                continue
            # skip empty spaces
            if current.chars in EMPTY_SPACES:
                self.skip_forward()
                current = self.read()
                continue
            # go up one level
            if self.search(">"):
                self.add_string(">")
                nested_levels -= 1
                if nested_levels == 0:
                    # exit dtd
                    return
                continue
            if self.search_in_tokens("|()[],?*+"):
                self.add_token_to_accumulator(current)
                continue
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_closing_tag(self) -> None:
        if not self.search("</"):
            return
        self.add_string("</")
        current = self.read()
        while current is not None:
            if self.search("<"):
                self.add_accumulator_to_tokens()
                return
            if self.search(">"):
                self.add_string(">")
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_tag(self, xml_declaration: bool) -> None:
        tag_name_finished = False
        quotes_in_use = ""
        if not self.search("<"):
            return
        self.add_string("<")
        current = self.read()
        while current is not None:
            if self.search("<"):
                self.add_accumulator_to_tokens()
                return
            if not xml_declaration and not tag_name_finished:
                self.add_tagname()
                tag_name_finished = True
                current = self.read()
                continue
            if quotes_in_use != "":
                if current.match(quotes_in_use):
                    self.add_string(quotes_in_use)
                    quotes_in_use = ""
                    current = self.read()
                else:
                    self.add_token_to_accumulator(current)
                    current = self.read()
                continue
            if current.is_quotes():
                quotes_in_use = current.chars
                self.add_string(quotes_in_use)
                current = self.read()
                continue
            if current.is_empty_spaces():
                self.skip_forward()
                current = self.read()
                continue
            if current.match("="):
                self.add_string("=")
                current = self.read()
                continue
            if not xml_declaration and self.search("/>"):
                self.add_string("/>")
                return
            if xml_declaration and self.search("?>"):
                self.add_string("?>")
                return
            if self.search(">"):
                self.add_string(">")
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_text(self) -> None:
        current = self.read()
        while current is not None:
            if self.search("<"):
                self.add_accumulator_to_tokens()
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def get_element_tokens(self) -> None | list[Token]:
        self.clear_session()
        if self.read() is None:
            return None
        if self.is_xml_declaration():
            self.tokenize_tag(xml_declaration=True)
            return self.tokens
        if self.search("<!--"):
            self.tokenize_comment()
            return self.tokens
        if self.search("<![CDATA["):
            self.tokenize_cdata()
            return self.tokens
        if self.search("<?"):
            self.tokenize_instructions()
            return self.tokens
        if self.search("<!"):
            self.tokenize_dtd()
            return self.tokens
        if self.search("</"):
            self.tokenize_closing_tag()
            return self.tokens
        if self.search("<"):
            self.tokenize_tag(xml_declaration=False)
            return self.tokens
        self.tokenize_text()
        return self.tokens


svg = """barbara<root>&foo;<example/></root>"""
tag_example = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>"""

complete_example = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<!-- This is the root element of the XML document -->"""

buffer_controller = BufferController()
buffer_controller.add_buffer_unit(complete_example, "In-memory buffer")
tokens = buffer_controller.get_element_tokens()
while tokens is not None:
    tokens = buffer_controller.get_element_tokens()
print()


# buffer_controller.add_buffer_unit(svg, "In-memory buffer")
# seq = buffer_controller.read(read_offset=5, length=3)
# if seq is not None:
#     print(seq.chars)
# char_token = Fragment("barbara", 0, 0)
# entity_sequnce = Token(char_token)
# buffer_controller.move(13)
# # buffer_controller.buffer_views[0].in_buffer_pointer_current = 13
# buffer_controller.add_entity_to_buffer_views("foo", entity_sequnce)
# sequence1 = buffer_controller.read(read_offset=0, length=7)
# if sequence1 is not None:
#     print(sequence1.chars)
# buffer_controller.move(7)
# sequence2 = buffer_controller.read(read_offset=0, length=10)
# if sequence2 is not None:
#     print(sequence2.chars)
# print()