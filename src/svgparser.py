"""SvgParser Module."""

from __future__ import annotations

from shared import EMPTY_SPACES
from shared import QUOTES
from xmltoken import XMLToken
from xmltokenizer import get_tokens


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


class BufferController:
    def __init__(
        self,
        buffer: str,
        filename: str | None = None,
        buffer_type: str | None = None,
    ) -> None:
        self.slot_in_use: int = 0
        self.buffers: list[BufferUnit] = []
        if filename is None:
            filename = "In-memory Buffer"
        if buffer_type is None:
            buffer_type = "xml"
        self.buffers.append(BufferUnit(buffer, filename, self.slot_in_use, buffer_type))

    def add_xml_buffer(self, buffer: str, filename: str) -> None:
        parent = self.slot_in_use
        buffer_slot = len(self.buffers)
        buffer_unit = BufferUnit(buffer, filename, buffer_slot, "xml", parent)
        self.buffers.append(buffer_unit)
        self.slot_in_use = buffer_slot

    def add_entity_buffer(self, entity_token: XMLToken, filename: str) -> None:
        buffer_slot = len(self.buffers)
        parent = self.slot_in_use
        buffer = entity_token.content
        in_buffer_pointer_start = entity_token.pointer
        in_buffer_pointer_end = len(buffer)
        buffer_unit = BufferUnit(
            buffer,
            filename,
            buffer_slot,
            "entity",
            parent,
            in_buffer_pointer_start,
            in_buffer_pointer_end,
        )
        self.buffers.append(buffer_unit)
        self.slot_in_use = buffer_slot

    def tokens_current(self) -> XMLToken | None:
        if self.buffers[self.slot_in_use].tokens_pointer_current >= len(self.buffers[self.slot_in_use].tokens):
            return None
        return self.buffers[self.slot_in_use].tokens[self.buffers[self.slot_in_use].tokens_pointer_current]

    def tokens_next(self) -> XMLToken | None:
        pointer = self.buffers[self.slot_in_use].tokens_pointer_current + 1
        # unwind parent buffer
        while pointer >= len(self.buffers[self.slot_in_use].tokens):
            parent = self.buffers[self.slot_in_use].parent
            if parent is not None:
                self.slot_in_use = parent
                pointer = self.buffers[self.slot_in_use].tokens_pointer_current + 1
            else:
                self.slot_in_use = 0
                pointer = self.buffers[self.slot_in_use].tokens_pointer_current + 1
                break
        self.buffers[self.slot_in_use].tokens_pointer_current = pointer
        return self.tokens_current()

    def get_line_from_pointer_and_buffer_slot(self, pointer: int, buffer_slot: int) -> tuple[int, int, str]:
        return self.buffers[buffer_slot].get_line_from_pointer(pointer)


class BufferUnit:
    def __init__(
        self,
        buffer: str,
        filename: str,
        buffer_slot: int,
        buffer_type: str,
        parent: int | None = None,
        in_buffer_pointer_start: int | None = None,
        in_buffer_pointer_end: int | None = None,
    ) -> None:
        self.buffer = normalize_newlines(buffer)
        self.filename = filename
        self.buffer_slot = buffer_slot
        self.buffer_type = buffer_type  # xml | entity
        self.parent = parent
        if in_buffer_pointer_start is None:
            in_buffer_pointer_start = 0
        if in_buffer_pointer_end is None:
            in_buffer_pointer_end = in_buffer_pointer_start + len(buffer)
        self.tokens_pointer_current: int = 0
        self.lines: None | list[tuple[int, str]] = None
        self.tokens: list[XMLToken] = get_tokens(
            self.buffer,
            self.buffer_slot,
            in_buffer_pointer_start,
            in_buffer_pointer_end,
        )

    def is_end(self) -> bool:
        if self.tokens_pointer_current >= len(self.tokens):
            return True
        return False

    def create_lines(self) -> None:
        self.lines = []
        i = 0
        line_start = 0
        while not self.is_end():
            if self.buffer[i : i + 2] == "\r\n":
                i += 2
                self.lines.append((line_start, self.buffer[line_start:i]))
                line_start = i
                continue
            if self.buffer[i] == "\r":
                i += 1
                self.lines.append((line_start, self.buffer[line_start:i]))
                line_start = i
                continue
            if self.buffer[i] == "\n":
                i += 1
                self.lines.append((line_start, self.buffer[line_start:i]))
                line_start = i
                continue
            i += 1
        if line_start < i:
            self.lines.append((line_start, self.buffer[line_start:i]))

    def get_line_from_pointer(self, pointer: int) -> tuple[int, int, str]:
        # the line number, index of a character in the line, the whole line of text
        if self.lines is None:
            self.create_lines()
        if self.lines is None:
            raise ValueError()

        low, high = 0, len(self.lines) - 1
        while low <= high:
            mid = (low + high) // 2  # Calculate mid-point

            if mid == high and pointer >= self.lines[mid][0] and pointer < len(self.buffer):
                return (mid, pointer - self.lines[mid][0], self.lines[mid][1])
            elif pointer >= self.lines[mid][0] and pointer < self.lines[mid + 1][0]:
                return (mid, pointer - self.lines[mid][0], self.lines[mid][1])
            elif pointer < self.lines[mid][0]:
                high = mid - 1  # Search in the left half
            else:
                low = mid + 1  # Search in the right half
        raise ValueError()


class ErrorCollector:
    def __init__(self) -> None:
        # [0] - buffer_slot
        # [1] - pointer_in_buffer
        # [2] - message
        self.buffer_slot: dict[int, list[tuple[int, str]]] = {}

    def add_pointer(self, buffer_slot: int, pointer: int, message: str) -> None:
        if buffer_slot not in self.buffer_slot:
            self.buffer_slot[buffer_slot] = []
        self.buffer_slot[buffer_slot].append((pointer, message))

    def add_token(self, token: XMLToken, message: str) -> None:
        if token.buffer_slot not in self.buffer_slot:
            self.buffer_slot[token.buffer_slot] = []
        self.buffer_slot[token.buffer_slot].append((token.pointer, message))

    def sort_errors(self) -> None:
        self.buffer_slot = dict(sorted(self.buffer_slot.items()))
        for i in self.buffer_slot:
            self.buffer_slot[i].sort(key=lambda error: error[0])


class XMLTag:
    def __init__(self, start: XMLToken, parent: XMLTag | None = None) -> None:
        self.start = start
        self.parent = parent
        self.children: list[XMLTag | XMLComment | XMLInstructions | XMLText | XMLDeclaration] = []
        self.name: None | XMLToken = None
        self.attributes: list[XMLAttribute] = []
        self.closed = False
        self.end: XMLToken | None = None

    def last_pointer_and_slot(self) -> tuple[int, int]:
        if self.end is not None:
            return (self.end.buffer_slot, self.end.end_pointer())
        if len(self.attributes) > 0:
            last_attribute = self.attributes[-1]
            if last_attribute.value.pointer > last_attribute.name.pointer:
                return (last_attribute.value.buffer_slot, last_attribute.value.end_pointer())
            else:
                return (last_attribute.name.buffer_slot, last_attribute.name.end_pointer())
        if self.name is not None:
            return (self.name.buffer_slot, self.name.end_pointer())
        return (self.start.buffer_slot, self.start.end_pointer())

    def __repr__(self):
        if self.name is None:
            return "Tag"
        if self.name.content is None:
            return "Tag"
        return f"Tag: {self.name.content}"

    def close_tag(self, tag_name: str) -> bool:
        if self.name is None:
            raise ValueError("Tag name is undefiend.")
        start_tag_name = self.name.content.strip()
        if start_tag_name == tag_name:
            self.closed = True
            return True
        return False


class XMLDeclaration:
    def __init__(self, start: XMLToken, parent: XMLTag | None = None) -> None:
        self.start = start
        self.parent = parent
        self.attributes: list[XMLAttribute] = []
        self.end: XMLToken | None = None

    def last_pointer_and_slot(self) -> tuple[int, int]:
        if self.end is not None:
            return (self.end.buffer_slot, self.end.end_pointer())
        if len(self.attributes) > 0:
            last_attribute = self.attributes[-1]
            if last_attribute.value.pointer > last_attribute.name.pointer:
                return (last_attribute.value.buffer_slot, last_attribute.value.end_pointer())
            else:
                return (last_attribute.name.buffer_slot, last_attribute.name.end_pointer())
        return (self.start.buffer_slot, self.start.end_pointer())

    def __repr__(self):
        return "XML Declaration"


class XMLAttribute:
    def __init__(self, name_token: XMLToken, parent: XMLTag | None = None) -> None:
        self.name: XMLToken = name_token
        self.value = XMLToken("True", name_token.pointer, name_token.buffer_slot)
        self.parent = parent

    def __repr__(self):
        if self.name is None:
            return "Attribute"
        return f"Attribute: {self.name.content}"


class XMLComment:
    def __init__(self, start: XMLToken, parent: XMLTag | None = None) -> None:
        self.start = start
        self.parent = parent
        self.content: XMLToken | None = None
        self.end: XMLToken | None = None

    def last_pointer_and_slot(self) -> tuple[int, int]:
        if self.end is not None:
            return (self.end.buffer_slot, self.end.end_pointer())
        if self.content is not None:
            return (self.content.buffer_slot, self.content.end_pointer())
        return (self.start.buffer_slot, self.start.end_pointer())

    def __repr__(self):
        return "Comment"


class XMLInstructions:
    def __init__(self, start: XMLToken, parent: XMLTag | None = None) -> None:
        self.start = start
        self.parent = parent
        self.content: XMLToken | None = None
        self.end: XMLToken | None = None

    def slot_and_last_pointer(self) -> tuple[int, int]:
        if self.end is not None:
            return (self.end.buffer_slot, self.end.end_pointer())
        if self.content is not None:
            return (self.content.buffer_slot, self.content.end_pointer())
        return (self.start.buffer_slot, self.start.end_pointer())

    def __repr__(self):
        return "Instructions"


class XMLText:
    def __init__(self, start: XMLToken, parent: XMLTag | None = None) -> None:
        self.start = start
        self.parent = parent
        self.content: XMLToken | None = None
        self.content_size: int = 0
        self.end: XMLToken | None = None

    def last_pointer_and_slot(self) -> tuple[int, int]:
        if self.end is not None:
            return (self.end.buffer_slot, self.end.end_pointer())
        if self.content is not None:
            return (self.content.buffer_slot, self.content.pointer + self.content_size)
        return (self.start.buffer_slot, self.start.end_pointer())

    def append_token_text(self, token: XMLToken, content_size: int) -> None:
        if self.content is None:
            self.content = token
            self.content_size = content_size
        else:
            self.content.add_token(token)
            self.content_size += content_size

    def is_empty_space(self) -> bool:
        if self.content is None:
            return False
        for char in self.content.content:
            if char not in EMPTY_SPACES:
                return False
        return True

    def __repr__(self):
        return "Text"


class XMLParser:
    def __init__(self, buffer_controller: BufferController, error_collector: ErrorCollector) -> None:
        self.error_collector: ErrorCollector = error_collector
        self.buffer_controller = buffer_controller
        self.current_node: XMLTag | None = None
        self.tree: list[XMLTag | XMLComment | XMLInstructions | XMLText | XMLDeclaration] = []
        self.parse_tokens()

    def get_tree(self) -> list[XMLTag | XMLComment | XMLInstructions | XMLText | XMLDeclaration]:
        return self.tree

    def check_closing_tags(self) -> None:
        current = self.current_node
        if current is not None:
            self.error_collector.add_token(current.start, "Missing close tag.")
            current = current.parent

    def parse_tokens(self) -> None:
        current = self.buffer_controller.tokens_current()
        while current is not None:
            if current.match("<!--"):
                self.parse_comment(current)
                current = self.buffer_controller.tokens_current()
                continue
            if current.match("<![CDATA["):
                self.parse_cdata(current)
                current = self.buffer_controller.tokens_current()
                continue
            if current.match("<?"):
                self.parse_instructions(current)
                current = self.buffer_controller.tokens_current()
                continue
            if current.match("</"):
                self.parse_end_tag(current)
                current = self.buffer_controller.tokens_current()
                continue
            if current.match("<!"):
                self.parse_dtd(current)
                current = self.buffer_controller.tokens_current()
                continue
            if current.match("<?xml"):
                self.parse_xml_declaration(current)
                current = self.buffer_controller.tokens_current()
                continue
            if current.match("<"):
                self.parse_start_tag(current)
                current = self.buffer_controller.tokens_current()
                continue
            self.parse_text(current)
            current = self.buffer_controller.tokens_current()
            continue
        self.check_closing_tags()

    def parse_dtd(self, start: XMLToken) -> None:
        dtd_type = self.buffer_controller.tokens_next()
        if dtd_type is None:
            self.error_collector.add_pointer(start.buffer_slot, start.end_pointer(), "DTD declaration is incomplete.")
            return
        if dtd_type.begins_with_empty_space():
            self.error_collector.add_token(dtd_type, "DTD cannot begin with empty space.")
        if dtd_type.ends_with("DOCTYPE"):
            dtd_doctype = self.buffer_controller.tokens_next()
            if dtd_doctype is None:
                self.error_collector.add_pointer(
                    dtd_type.buffer_slot, dtd_type.end_pointer(), "DOCTYPE tag is incomplete."
                )
                return
            self.parse_dtd_doctype(dtd_doctype)
            return
        if dtd_type.ends_with("ELEMENT"):
            dtd_element = self.buffer_controller.tokens_next()
            if dtd_element is None:
                self.error_collector.add_pointer(
                    dtd_type.buffer_slot, dtd_type.end_pointer(), "ELEMENT tag is incomplete."
                )
                return
            self.parse_dtd_element(dtd_element)
            return
        if dtd_type.ends_with("ATTLIST"):
            dtd_attlist = self.buffer_controller.tokens_next()
            if dtd_attlist is None:
                self.error_collector.add_pointer(
                    dtd_type.buffer_slot, dtd_type.end_pointer(), "ATTLIST tag is incomplete."
                )
                return
            self.parse_dtd_attlist(dtd_attlist)
            return
        self.error_collector.add_token(dtd_type, "DTD tag invalid, skippi")
        self.skip_invalid_dtd(dtd_type)

    def skip_invalid_dtd(self, current: XMLToken | None) -> None:
        nested_levels = 1
        while current is not None:
            if current.begins_with("<") and not current.match("<!"):
                return
            if current.match("<!"):
                nested_levels += 1
                current = self.buffer_controller.tokens_next()
                continue
            if current.match(">"):
                nested_levels -= 1
                if nested_levels == 0:
                    # exit dtd
                    return
                current = self.buffer_controller.tokens_next()
                continue
            current = self.buffer_controller.tokens_next()

    def parse_dtd_doctype(self, start: XMLToken) -> None:
        pass

    def parse_dtd_element(self, start: XMLToken) -> None:
        pass

    def parse_dtd_attlist(self, start: XMLToken) -> None:
        pass

    def parse_comment(self, start: XMLToken) -> None:
        # creation of a token
        comment = XMLComment(start, self.current_node)
        # connect new token
        if self.current_node is None:
            self.tree.append(comment)
        else:
            self.current_node.children.append(comment)
        # content
        current = self.buffer_controller.tokens_next()
        if current is None:
            self.error_collector.add_pointer(*comment.last_pointer_and_slot(), "Missing closing sequence for comment.")
            return
        if current.match("-->"):
            comment.end = current
            return
        else:
            comment.content = current
        # closing sequence
        current = self.buffer_controller.tokens_next()
        if current is None:
            self.error_collector.add_pointer(*comment.last_pointer_and_slot(), "Missing closing sequence for comment.")
            return
        comment.end = current

    def get_text_node(self, start_token: XMLToken) -> XMLText:
        text_node = XMLText(start_token)
        if self.current_node is None:
            if len(self.tree) > 0 and isinstance(self.tree[-1], XMLText):
                return self.tree[-1]
            else:
                self.tree.append(text_node)
                return text_node
        else:
            if len(self.current_node.children) > 0 and isinstance(self.current_node.children[-1], XMLText):
                return self.current_node.children[-1]
            else:
                self.current_node.children.append(text_node)
                text_node.parent = self.current_node
                return text_node

    def parse_cdata(self, start: XMLToken) -> None:
        # cdata content
        cdata_content = self.buffer_controller.tokens_next()
        if cdata_content is None:
            self.error_collector.add_token(start, "Missing closing sequence for CData.")
            return
        text_node = self.get_text_node(cdata_content)
        # closing sequence
        end = self.buffer_controller.tokens_next()
        if end is None:
            self.error_collector.add_pointer(
                cdata_content.buffer_slot,
                cdata_content.end_pointer(),
                "Missing closing sequence for CData.",
            )
            return
        if not end.match("]]>"):
            self.error_collector.add_pointer(end.buffer_slot, end.pointer, "Invalid closing tag for CData.")
        text_node.append_token_text(cdata_content, end.end_pointer() - start.pointer)

    def parse_instructions(self, start: XMLToken) -> None:
        # creation of a token
        instructions = XMLInstructions(start, self.current_node)
        # connect to node
        if self.current_node is None:
            self.tree.append(instructions)
        else:
            self.current_node.children.append(instructions)
        # instructions content
        current = self.buffer_controller.tokens_next()
        if current is None:
            self.error_collector.add_token(instructions.start, "Missing closing sequence for instructions tag.")
            return
        if current.match("?>"):
            instructions.end = current
            return
        instructions.content = current
        # closing sequence
        end = self.buffer_controller.tokens_next()
        if end is None:
            self.error_collector.add_pointer(
                *instructions.slot_and_last_pointer(),
                "Missing closing tag for Instructions tag.",
            )
            return
        if not end.match("?>"):
            self.error_collector.add_token(end, "Invalid closing sequence for instructions tag.")
        instructions.end = end

    def parse_end_tag(self, start: XMLToken) -> None:
        # name of a closing tag
        closing_tag_name = self.buffer_controller.tokens_next()
        if closing_tag_name is None:
            self.error_collector.add_token(start, "Closing tag is missing a name and closing bracket.")
            return
        # Check for blank spaces in beggining of a name
        closing_tag_striped = closing_tag_name.content.strip()
        current_node = self.current_node
        missing_close_tags: list[XMLTag] = []
        while current_node is not None:
            if current_node.close_tag(closing_tag_striped):
                self.current_node = current_node.parent
                if len(missing_close_tags) > 0:
                    for tag in missing_close_tags:
                        self.error_collector.add_token(tag.start, "The tag is missing its closing tag.")
                break
            else:
                missing_close_tags.append(current_node)
                current_node = current_node.parent
        if current_node is None:
            self.error_collector.add_token(closing_tag_name, "Closing tag not matching any other tag.")
            self.buffer_controller.tokens_next()
            return
        last_pointer = closing_tag_name.pointer + len(closing_tag_name.content)
        # closing tag
        closing_tag = self.buffer_controller.tokens_next()
        if closing_tag is None:
            self.error_collector.add_pointer(
                closing_tag_name.buffer_slot, last_pointer, "Closing tag is missing angle bracket."
            )
            return
        if not closing_tag.match(">"):
            self.error_collector.add_token(closing_tag, "Closing tag is missing angle bracket.")

    def __verify_xml_declaration(self, xml_declaration: XMLDeclaration) -> None:
        if xml_declaration.start.pointer > 0:
            self.error_collector.add_token(xml_declaration.start, "XML declaration must be the on the first line.")
        if len(xml_declaration.attributes) >= 1:
            self.__verify_attribute_version(xml_declaration.attributes[0])
        if len(xml_declaration.attributes) >= 2:
            self.__verify_attribute_encoding(xml_declaration.attributes[1])
        if len(xml_declaration.attributes) >= 3:
            self.__verify_attribute_standalone(xml_declaration.attributes[2])
        if len(xml_declaration.attributes) > 3:
            self.error_collector.add_token(
                xml_declaration.attributes[3].name,
                "Only three atributtes are allowed: version, encoding and standalone.",
            )

    def __verify_attribute_version(self, attribute: XMLAttribute) -> None:
        if attribute.name.content != "version":
            self.error_collector.add_token(
                attribute.name,
                "The first attribute in declaration must be the value attribute.",
            )
            return
        if attribute.value.content != "1.0":
            self.error_collector.add_token(
                attribute.value,
                "Only the version 1.0 is supported.",
            )

    def __verify_attribute_encoding(self, attribute: XMLAttribute) -> None:
        if attribute.name.content != "encoding":
            self.error_collector.add_token(
                attribute.name,
                "The second attribute in declaration must be the encoding attribute.",
            )
            return
        if attribute.value.content not in {"UTF-8", "UTF-16"}:
            self.error_collector.add_token(
                attribute.value,
                "Only the UTF-8 and UTF-16 encodings are supported.",
            )

    def __verify_attribute_standalone(self, attribute: XMLAttribute) -> None:
        if attribute.name.content != "standalone":
            self.error_collector.add_token(
                attribute.name,
                "The third attribute in declaration must be the standalone attribute.",
            )
            return
        if attribute.value.content not in {"yes", "no"}:
            self.error_collector.add_token(
                attribute.value,
                "Only the yes and no values are allowed for the standalone attribute.",
            )

    def __verify_element_or_attribute_name(self, element_name: XMLToken) -> None:
        if len(element_name.content) >= 1:
            first_char = element_name.content[0]
            if not first_char.isalpha() and not first_char == "_":
                self.error_collector.add_token(
                    element_name, "Element names must begin with a letter or an underscore(_)."
                )
        num_of_colons = 0
        if len(element_name.content) >= 2:
            for char in element_name.content[1:]:
                if not char.isalnum() and char not in {"-", "_", ":", "."}:
                    self.error_collector.add_token(
                        element_name,
                        "The initial character of the name of an element can be followed by any number of letters, "
                        "digits, periods(.), hyphens(-), underscores or colons (:).",
                    )
                if char == ":":
                    num_of_colons += 1
            if num_of_colons > 1:
                self.error_collector.add_token(
                    element_name,
                    "Multiple colons are not allowed in element names. "
                    "The colon character is reserved for namespaces in XML.",
                )

    def __get_content_or_attribute_value(self, element_value: XMLToken) -> str:
        i = 0
        text = element_value.content
        interpreted_value = ""
        while i < len(text):
            if text[i] == '"':
                self.error_collector.add_pointer(
                    element_value.buffer_slot,
                    element_value.pointer + i,
                    'The " character must be escaped with &quot; sequence.',
                )
                interpreted_value += text[i]
                i += 1
                continue
            if text[i] == "'":
                self.error_collector.add_pointer(
                    element_value.buffer_slot,
                    element_value.pointer + i,
                    "The ' character must be escaped with &apos; sequence.",
                )
                interpreted_value += text[i]
                i += 1
                continue
            if text[i] == "<":
                self.error_collector.add_pointer(
                    element_value.buffer_slot,
                    element_value.pointer + i,
                    "The < character must be escaped with &lt; sequence.",
                )
                interpreted_value += text[i]
                i += 1
                continue
            if text[i] == ">":
                self.error_collector.add_pointer(
                    element_value.buffer_slot,
                    element_value.pointer + i,
                    "The > character must be escaped with &gt; sequence.",
                )
                interpreted_value += text[i]
                i += 1
                continue
            if text[i] == "&":
                increment, char_replacement = self.__get_entity_reference(text[i:])
                if char_replacement == "":
                    self.error_collector.add_pointer(
                        element_value.buffer_slot,
                        element_value.pointer + i,
                        "The & character must be escaped with &amp; sequence.",
                    )
                interpreted_value += char_replacement
                i += increment
                continue
            interpreted_value += text[i]
            i += 1
        return interpreted_value

    def __get_entity_reference(self, entity_reference: str) -> tuple[int, str]:
        if entity_reference[: len("&lt;")] == "&lt;":
            return (len("&lt;"), "<")
        if entity_reference[: len("&gt;")] == "&gt;":
            return (len("&gt;"), ">")
        if entity_reference[: len("&quot;")] == "&quot;":
            return (len("&quot;"), '"')
        if entity_reference[: len("&apos;")] == "&apos;":
            return (len("&apos;"), "'")
        if entity_reference[: len("&amp;")] == "&amp;":
            return (len("&amp;"), "&")
        return (1, "")

    def __verify_number_of_root_elements(self) -> None:
        number_of_root_elements = 0
        for node in self.tree:
            if isinstance(node, XMLTag) and node.name is not None and node.name.content != "?xml":
                number_of_root_elements += 1
                if number_of_root_elements > 1:
                    self.error_collector.add_token(node.start, "Only one root element is allowed.")

    def parse_xml_declaration(self, start: XMLToken) -> None:
        declaration = XMLDeclaration(start)
        if self.current_node is not None:
            self.error_collector.add_token(start, "XML Declaration cannot be nested.")
        elif len(self.tree) > 0:
            self.error_collector.add_token(start, "XML Declaration must be at top of document.")
        else:
            self.tree.append(declaration)
        # attributes
        current = self.buffer_controller.tokens_next()
        attrib: None | XMLAttribute = None
        while current is not None:
            if current.match("?>"):
                self.__verify_xml_declaration(declaration)
                declaration.end = current
                break
            if current.match(">"):
                self.error_collector.add_token(current, "Invalid closing angle bracket for declaration.")
                self.__verify_xml_declaration(declaration)
                declaration.end = current
                break
            if current.begins_with("<"):
                self.error_collector.add_token(current, "Missing closing angle bracket.")
                self.__verify_xml_declaration(declaration)
                break
            if current.match("="):
                if attrib is None:
                    self.error_collector.add_token(current, "Missing attribute name to attach the value.")
                    current = self.buffer_controller.tokens_next()
                    continue
                attrib_value = self.__parse_attribute_value(current)
                if attrib_value is not None:
                    attrib_value.content = self.__get_content_or_attribute_value(attrib_value)
                    attrib.value = attrib_value
                current = self.buffer_controller.tokens_current()
                continue
            attrib = XMLAttribute(current)
            self.__verify_element_or_attribute_name(attrib.name)
            declaration.attributes.append(attrib)
            current = self.buffer_controller.tokens_next()

    def parse_start_tag(self, start: XMLToken) -> None:
        tag = XMLTag(start)
        if self.current_node is None:
            self.tree.append(tag)
        else:
            self.current_node.children.append(tag)
        tag.parent = self.current_node
        self.current_node = tag
        name = self.buffer_controller.tokens_next()
        if name is None:
            self.error_collector.add_token(start, "Missing tag name and closing bracket.")
            return
        tag.name = name
        if tag.parent is None:
            self.__verify_number_of_root_elements()
        # attributes
        current = self.buffer_controller.tokens_next()
        attrib: None | XMLAttribute = None
        while current is not None:
            if current.match("/>"):
                tag.closed = True
                tag.end = current
                if self.current_node is not None:
                    self.current_node = self.current_node.parent
                break
            if current.match(">"):
                tag.end = current
                break
            if current.begins_with("<"):
                self.error_collector.add_token(current, "Missing closing angle bracket.")
                break
            if current.begins_with("?>"):
                self.error_collector.add_token(current, "Invalid closing angle bracket.")
                tag.end = current
                break
            if current.match("="):
                if attrib is None:
                    self.error_collector.add_token(current, "Missing attribute name to attach the value.")
                    current = self.buffer_controller.tokens_next()
                    continue
                attrib_value = self.__parse_attribute_value(current)
                if attrib_value is not None:
                    attrib_value.content = self.__get_content_or_attribute_value(attrib_value)
                    attrib.value = attrib_value
                current = self.buffer_controller.tokens_current()
                continue
            attrib = XMLAttribute(current)
            self.__verify_element_or_attribute_name(attrib.name)
            tag.attributes.append(attrib)
            attrib.parent = tag
            current = self.buffer_controller.tokens_next()

    def __parse_attribute_value(self, start: XMLToken) -> XMLToken | None:
        start_quotes = self.buffer_controller.tokens_next()
        if start_quotes is None:
            self.error_collector.add_token(start, "The attribute value is missing.")
            return
        if start_quotes.content not in QUOTES:
            self.error_collector.add_token(start, "The attribute value must be enclosed in quotes.")
            return
        attribute_value = self.buffer_controller.tokens_next()
        if attribute_value is None:
            self.error_collector.add_token(start_quotes, "The attribute value is missing.")
            return
        end_quotes = self.buffer_controller.tokens_next()
        if end_quotes is None:
            self.error_collector.add_token(attribute_value, "Ending quote is missing.")
            return attribute_value
        if end_quotes.content not in QUOTES:
            self.error_collector.add_token(attribute_value, "The attribute value must be enclose in quotes.")
            return attribute_value
        self.buffer_controller.tokens_next()
        return attribute_value

    def parse_text(self, start: XMLToken) -> None:
        # edge case when the text node can be at the beginning of an xml
        if start.ends_with(">"):
            self.buffer_controller.tokens_next()
            return
        text_content = self.buffer_controller.tokens_current()
        if text_content is None:
            return
        if text_content.begins_with("<"):
            return
        is_empty = True
        for char in text_content.content:
            if char not in EMPTY_SPACES:
                is_empty = False
                break
        if not is_empty:
            text_content.content = self.__get_content_or_attribute_value(text_content)
            text_node = self.get_text_node(start)
            text_node.append_token_text(text_content, len(text_content.content))
        end_tag = self.buffer_controller.tokens_next()
        if end_tag is None:
            self.error_collector.add_token(text_node.start, "Text is not allowed at the end of the file.")
            return
        if not end_tag.begins_with("<"):
            self.error_collector.add_token(text_node.start, "Invalid start of another tag.")
            return


class XMLBuilder:
    def __init__(self) -> None:
        self.buffer_controller: None | BufferController = None
        self.error = ErrorCollector()
        self.tree: None | list[XMLTag | XMLComment | XMLInstructions | XMLText | XMLDeclaration] = None

    def get_tree_from_buffer(
        self,
        buffer: str,
    ) -> list[XMLTag | XMLComment | XMLInstructions | XMLText | XMLDeclaration]:
        buffer_controller = BufferController(buffer)
        self.buffer_controller = buffer_controller
        self.tree = XMLParser(buffer_controller, self.error).get_tree()
        if len(self.error.buffer_slot) > 0:
            print(self.print_error_messages())
        return self.tree

    def get_tree_from_file(self, filename: str) -> None:
        pass

    def print_error_messages(self) -> str:
        # lines = self.get_lines()
        self.error.sort_errors()
        if self.buffer_controller is None:
            raise ValueError()
        text_to_print = ""
        for slot in self.error.buffer_slot:
            text_to_print = f"Filename: {self.buffer_controller.buffers[slot].filename} has following errors:\n"
            for error in self.error.buffer_slot[slot]:
                line = self.buffer_controller.get_line_from_pointer_and_buffer_slot(error[0], slot)
                text_to_print += f"{error[1]}\n"
                text_to_print += f"Line number:{line[0]}\n"
                if line[2][-1] == "\n":
                    text_to_print += f"{line[2]}"
                else:
                    text_to_print += f"{line[2]}\n"
                num_of_spaces = " " * line[1]
                text_to_print += f"{num_of_spaces}^\n"
        return text_to_print
