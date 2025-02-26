from __future__ import annotations

from .buffacc import TokenAccumulator
from .buffunit import BufferUnit
from .buffview import BufferView
from .fragment import Fragment
from .shared import EMPTY_SPACES
from .shared import QUOTES
from .token import Token


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


class BufferController:
    def __init__(self) -> None:
        self.buffer_units: list[BufferUnit] = []
        self.buffer_views: list[BufferView] = []
        self.buffer_view_in_use: int = 0
        self.accumulator: TokenAccumulator = TokenAccumulator()
        self.entity_stack: list = []
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

    def tokenize_end_tag(self) -> None:
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

    def tokenize_start_tag(self, xml_declaration: bool) -> None:
        if xml_declaration:
            self.add_string("<?xml")
        else:
            self.add_string("<")
            self.add_tagname()
        current = self.read()
        while current is not None:
            if self.search("<"):
                self.add_accumulator_to_tokens()
                return
            if current.is_quotes():
                self.tokenize_attribute_quotes()
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
        self.add_accumulator_to_tokens()

    def tokenize_attribute_quotes(self) -> None:
        current = self.read()
        if current is None:
            return
        if not current.is_quotes():
            return
        quotes_in_use = current.chars
        self.add_string(quotes_in_use)
        current = self.read()
        while current is not None:
            if current.match("<"):
                self.add_accumulator_to_tokens()
                return
            if current.match(quotes_in_use):
                self.add_string(quotes_in_use)
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_dtd_quotes(self) -> None:
        current = self.read()
        if current is None:
            return
        if not current.is_quotes():
            return
        quotes_in_use = current.chars
        self.add_string(quotes_in_use)
        current = self.read()
        while current is not None:
            if current.match(quotes_in_use):
                self.add_string(quotes_in_use)
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_doctype(self) -> None:
        if not self.search("<!DOCTYPE"):
            return
        self.add_string("<!DOCTYPE")
        current = self.read()
        while current is not None:
            if self.search("<"):
                self.add_accumulator_to_tokens()
                return
            if current.is_quotes():
                self.tokenize_dtd_quotes()
                current = self.read()
                continue
            if current.is_empty_spaces():
                self.skip_forward()
                current = self.read()
                continue
            if self.search(">"):
                self.add_string(">")
                return
            if self.search("["):
                self.add_string("[")
                return
            if self.search("]"):
                self.add_string("]")
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_element_or_attlist(self) -> None:
        if self.search("<!ELEMENT"):
            self.add_string("<!ELEMENT")
        elif self.search("<!ATTLIST"):
            self.add_string("<!ATTLIST")
        else:
            return
        current = self.read()
        while current is not None:
            if self.search("<"):
                self.add_accumulator_to_tokens()
                return
            if current.is_quotes():
                self.tokenize_dtd_quotes()
                current = self.read()
                continue
            if current.is_empty_spaces():
                self.skip_forward()
                current = self.read()
                continue
            if self.search(">"):
                self.add_string(">")
                return
            if self.search_in_tokens("|(),?*+"):
                self.add_accumulator_to_tokens()
                self.add_token_to_accumulator(current)
                self.add_accumulator_to_tokens()
                current = self.read()
                continue
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_entity_or_notation(self) -> None:
        if self.search("<!ENTITY"):
            self.add_string("<!ENTITY")
        elif self.search("<!NOTATION"):
            self.add_string("<!NOTATION")
        else:
            return
        current = self.read()
        while current is not None:
            if self.search("<"):
                self.add_accumulator_to_tokens()
                return
            if current.is_quotes():
                self.tokenize_dtd_quotes()
                current = self.read()
                continue
            if current.is_empty_spaces():
                self.skip_forward()
                current = self.read()
                continue
            if self.search(">"):
                self.add_string(">")
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def tokenize_conditional(self) -> None:
        if not self.search("<!["):
            return
        self.add_string("<![")
        current = self.read()
        while current is not None:
            if self.search("<"):
                self.add_accumulator_to_tokens()
                return
            if current.is_empty_spaces():
                self.skip_forward()
                current = self.read()
                continue
            if self.search("["):
                self.add_string("[")
                return
            if self.search("]]>"):
                self.add_string("]]>")
                return
            self.add_token_to_accumulator(current)
            current = self.read()

    def get_buffer_tokens(self) -> None | list[Token]:
        self.clear_session()
        if self.read() is None:
            return None
        if self.search("<![CDATA["):
            self.tokenize_cdata()
            return self.tokens
        # start DTD
        if self.search("<!DOCTYPE"):
            self.tokenize_doctype()
            return self.tokens
        if self.search("<!ELEMENT") or self.search("<!ATTLIST"):
            self.tokenize_element_or_attlist()
            return self.tokens
        if self.search("<!ENTITY") or self.search("<!NOTATION"):
            self.tokenize_entity_or_notation()
            return self.tokens
        if self.search("<!["):
            self.tokenize_conditional()
            return self.tokens
        # end DTD
        if self.search("<!--"):
            self.tokenize_comment()
            return self.tokens
        if self.is_xml_declaration():
            self.tokenize_start_tag(xml_declaration=True)
            return self.tokens
        if self.search("<?"):
            self.tokenize_instructions()
            return self.tokens
        if self.search("</"):
            self.tokenize_end_tag()
            return self.tokens
        if self.search("<"):
            self.tokenize_start_tag(xml_declaration=False)
            return self.tokens
        self.tokenize_text()
        return self.tokens
