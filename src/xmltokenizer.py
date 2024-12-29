from __future__ import annotations

from shared import EMPTY_SPACES
from shared import QUOTES
from xmltoken import XMLToken as XMLToken


def get_tokens(
    buffer: str, buffer_slot: int, in_buffer_pointer_start: int, in_buffer_pointer_end: int
) -> list[XMLToken]:
    tokenizer = XMLTokenizer(buffer, buffer_slot, in_buffer_pointer_start, in_buffer_pointer_end)
    return tokenizer.get_tokens()


class XMLTokenizer:
    def __init__(
        self,
        buffer: str,
        buffer_slot: int,
        in_buffer_pointer_start: int,
        in_buffer_pointer_end: int,
    ) -> None:
        self.buffer = buffer
        self.buffer_slot = buffer_slot
        self.in_buffer_pointer_start = in_buffer_pointer_start
        self.in_buffer_pointer_end = in_buffer_pointer_end
        self.in_buffer_pointer_current = in_buffer_pointer_start
        self.char_current: str | None = self.buffer[self.in_buffer_pointer_current]
        self.tokens: list[XMLToken] = []
        self.accumulator: XMLToken | None = None
        self.in_buffer_switch: int = 0
        self.create_tokens()

    def create_tokens(self) -> None:
        while self.char_current is not None:
            match self.in_buffer_switch:
                case 0:  # inside text
                    self.tokenize_text()
                case 1:  # inside comment
                    self.tokenize_comment()
                case 2:  # inside cdata
                    self.tokenize_cdata()
                case 3:  # inside instructions
                    self.tokenize_instructions()
                case 4:  # inside dtd
                    self.tokenize_dtd()
                case 5:  # inside closing tag
                    self.tokenize_closing_tag()
                case 6:  # inside tag
                    self.tokenize_tag(xml_declaration=False)
                case 7:  # inside xml declaration
                    self.tokenize_tag(xml_declaration=True)
                case _:
                    raise ValueError("Content not recognized.")
        self.save_old_token()

    def tokenize_text(self) -> None:
        while self.char_current is not None:
            if self.is_xml_declaration():
                self.in_buffer_switch = 7  # inside xml declaration
                self.save_old_token()
                self.create_token_and_move("<?xml")
                return
            if self.buffer_search("<!--"):
                self.in_buffer_switch = 1  # inside comments
                self.save_old_token()
                self.create_token_and_move("<!--")
                return
            if self.buffer_search("<![CDATA["):
                self.in_buffer_switch = 2  # inside cdata
                self.save_old_token()
                self.create_token_and_move("<![CDATA[")
                return
            if self.buffer_search("<?"):
                self.in_buffer_switch = 3  # inside instructions
                self.save_old_token()
                self.create_token_and_move("<?")
                return
            if self.buffer_search("<!"):
                self.in_buffer_switch = 4  # inside dtd
                self.save_old_token()
                self.create_token_and_move("<!")
                return
            if self.buffer_search("</"):
                self.in_buffer_switch = 5  # inside closing tag
                self.save_old_token()
                self.create_token_and_move("</")
                return
            if self.buffer_search("<"):
                self.in_buffer_switch = 6  # inside tag
                self.save_old_token()
                self.create_token_and_move("<")
                return
            self.add_current_and_move()

    def tokenize_comment(self) -> None:
        while self.char_current is not None:
            if self.buffer_search("-->"):
                self.in_buffer_switch = 0
                self.save_old_token()
                self.create_token_and_move("-->")
                return
            self.add_current_and_move()

    def tokenize_cdata(self) -> None:
        while self.char_current is not None:
            if self.buffer_search("]]>"):
                self.in_buffer_switch = 0
                self.save_old_token()
                self.create_token_and_move("]]>")
                return
            self.add_current_and_move()

    def tokenize_instructions(self) -> None:
        while self.char_current is not None:
            if self.buffer_search("?>"):
                self.in_buffer_switch = 0
                self.save_old_token()
                self.create_token_and_move("?>")
                return
            self.add_current_and_move()

    def tokenize_dtd(self) -> None:
        nested_levels = 1
        quotes_in_use = ""
        tag_name = ""
        while self.char_current is not None:
            # exit dtd
            if self.buffer_search("<") and not self.buffer_search("<!"):
                self.in_buffer_switch = 0
                self.save_old_token()
                return
            if tag_name == "":
                self.save_old_token()
                tag_name = self.buffer_get_tag_name_and_move()
                self.create_token_and_move(tag_name)
                continue
            # nesting further
            if self.buffer_search("<!"):
                self.save_old_token()
                self.create_token_and_move("<!")
                quotes_in_use = ""
                nested_levels += 1
                continue
            # inside quotes
            if quotes_in_use != "":
                if quotes_in_use == self.char_current:
                    quotes_in_use = ""
                    self.save_old_token()
                    self.create_token_and_move(self.char_current)
                else:
                    self.add_current_and_move()
                continue
            if self.char_current in QUOTES:
                quotes_in_use = self.char_current
                self.save_old_token()
                self.create_token_and_move(self.char_current)
                continue
            # skip empty spaces
            if self.char_current in EMPTY_SPACES:
                self.save_old_token()
                self.buffer_skip_forward()
                continue
            # go up one level
            if self.buffer_search(">"):
                self.save_old_token()
                self.create_token_and_move(">")
                nested_levels -= 1
                if nested_levels == 0:
                    # exit dtd
                    self.in_buffer_switch = 0
                    return
                continue
            if self.buffer_search_in_tokens("|()[],?*+"):
                self.save_old_token()
                self.create_token_and_move(self.char_current)
                continue
            self.add_current_and_move()

    def buffer_search_in_tokens(self, tokens_string: str) -> bool:
        current = self.buffer_read(self.in_buffer_pointer_current)
        if current is None:
            return False
        if current in tokens_string:
            return True
        return False

    def tokenize_closing_tag(self) -> None:
        while self.char_current is not None:
            if self.char_current == ">":
                self.in_buffer_switch = 0
                self.save_old_token()
                self.create_token_and_move(">")
                return
            elif self.buffer_search("<"):
                self.in_buffer_switch = 0
                self.save_old_token()
                return
            self.add_current_and_move()

    def tokenize_tag(self, xml_declaration: bool) -> None:
        tag_name = ""
        quotes_in_use = ""
        while self.char_current is not None:
            if self.buffer_search("<"):
                self.in_buffer_switch = 0
                self.save_old_token()
                return
            if not xml_declaration and tag_name == "":
                self.save_old_token()
                tag_name = self.buffer_get_tag_name_and_move()
                self.create_token_and_move(tag_name)
                continue
            if quotes_in_use != "":
                if quotes_in_use == self.char_current:
                    quotes_in_use = ""
                    self.save_old_token()
                    self.create_token_and_move(self.char_current)
                else:
                    self.add_current_and_move()
                continue
            if self.char_current in QUOTES:
                quotes_in_use = self.char_current
                self.save_old_token()
                self.create_token_and_move(self.char_current)
                continue
            if self.char_current in EMPTY_SPACES:
                self.save_old_token()
                self.buffer_skip_forward()
                continue
            if self.char_current == "=":
                self.save_old_token()
                self.create_token_and_move("=")
                continue
            if not xml_declaration and self.buffer_search("/>"):
                self.in_buffer_switch = 0
                self.save_old_token()
                self.create_token_and_move("/>")
                return
            if xml_declaration and self.buffer_search("?>"):
                self.in_buffer_switch = 0
                self.save_old_token()
                self.create_token_and_move("?>")
                return
            if self.buffer_search(">"):
                self.in_buffer_switch = 0
                self.save_old_token()
                self.create_token_and_move(">")
                return
            self.add_current_and_move()

    def get_tokens(self) -> list[XMLToken]:
        return self.tokens

    def buffer_read(self, pointer: int, length: int = 1) -> str | None:
        if pointer + length > self.in_buffer_pointer_end:
            return None
        if length == 1:
            return self.buffer[pointer]
        return self.buffer[pointer : pointer + length]

    def buffer_move(self, offset: int = 1) -> None:
        self.in_buffer_pointer_current += offset

    def buffer_skip_forward(self) -> None:
        while (
            self.buffer_read(self.in_buffer_pointer_current) in EMPTY_SPACES
            and self.buffer_read(self.in_buffer_pointer_current) is not None
        ):
            self.buffer_move()
        self.char_current = self.buffer_read(self.in_buffer_pointer_current)

    def buffer_search(self, string_to_search: str) -> bool:
        read_buffer = self.buffer_read(self.in_buffer_pointer_current, len(string_to_search))
        if read_buffer is None:
            return False
        if read_buffer == string_to_search:
            return True
        return False

    def buffer_search_followed_by_empty_spaces(self, string_to_search: str) -> bool:
        read_buffer = self.buffer_read(self.in_buffer_pointer_current, len(string_to_search) + 1)
        if read_buffer is None:
            return False
        if read_buffer[: len(string_to_search) + 1] != string_to_search:
            return False
        if read_buffer[:-1] not in EMPTY_SPACES:
            return False
        return True

    def buffer_get_tag_name_and_move(self) -> str:
        tag_name = ""
        pointer = self.in_buffer_pointer_current
        value = self.buffer_read(pointer)
        while value is not None and value in EMPTY_SPACES:
            tag_name += value
            pointer += 1
            value = self.buffer_read(pointer)
        while value is not None and value not in EMPTY_SPACES and value != ">":
            tag_name += value
            pointer += 1
            value = self.buffer_read(pointer)
        return tag_name

    def save_old_token(self) -> None:
        if self.accumulator is not None:
            self.tokens.append(self.accumulator)
            self.accumulator = None

    def add_chars_to_token(self, buffer_current: str) -> None:
        if self.accumulator is None:
            self.accumulator = XMLToken(buffer_current, self.in_buffer_pointer_current, self.buffer_slot)
        else:
            self.accumulator.add_value(buffer_current)

    def create_and_add_token(self, value: str) -> None:
        self.tokens.append(XMLToken(value, self.in_buffer_pointer_current, self.buffer_slot))

    def create_token_and_move(self, value: str) -> None:
        self.create_and_add_token(value)
        self.buffer_move(len(value))
        self.char_current = self.buffer_read(self.in_buffer_pointer_current)

    def add_current_and_move(self) -> None:
        if self.char_current is None:
            raise ValueError()
        self.add_chars_to_token(self.char_current)
        self.buffer_move(len(self.char_current))
        self.char_current = self.buffer_read(self.in_buffer_pointer_current)

    def is_xml_declaration(self) -> bool:
        read_from_buffer = self.buffer_read(self.in_buffer_pointer_current, 6)
        if read_from_buffer is None:
            return False
        if read_from_buffer[:5] != "<?xml":
            return False
        if read_from_buffer[5] not in EMPTY_SPACES:
            return False
        return True
