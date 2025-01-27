from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer_controller import Token

from buffer_controller import BufferController


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


class ErrorCollector:
    def __init__(self) -> None:
        # dict[buffer_slot, list[in_buffer_pointer, message]]
        self.buffer_slot: dict[int, list[tuple[int, str]]] = {}

    # def add_pointer(self, buffer_slot: int, pointer: int, message: str) -> None:
    #     if buffer_slot not in self.buffer_slot:
    #         self.buffer_slot[buffer_slot] = []
    #     self.buffer_slot[buffer_slot].append((pointer, message))

    def add_token_start(self, token: Token, message: str) -> None:
        if token.buffer_slot not in self.buffer_slot:
            self.buffer_slot[token.buffer_slot] = []
        self.buffer_slot[token.buffer_slot].append((token.resolve_pointer(0), message))

    def add_token_end(self, token: Token, message: str) -> None:
        if token.buffer_slot not in self.buffer_slot:
            self.buffer_slot[token.buffer_slot] = []
        self.buffer_slot[token.buffer_slot].append((token.resolve_pointer(len(token.chars) - 1), message))

    def add_token_pointer(self, token: Token, in_token_pointer: int, message: str) -> None:
        if token.buffer_slot not in self.buffer_slot:
            self.buffer_slot[token.buffer_slot] = []
        self.buffer_slot[token.buffer_slot].append((token.resolve_pointer(in_token_pointer), message))

    # def sort_errors(self) -> None:
    #     self.buffer_slot = dict(sorted(self.buffer_slot.items()))
    #     for i in self.buffer_slot:
    #         self.buffer_slot[i].sort(key=lambda error: error[0])


class ElementTag:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.name: None | Token = None
        self.closed = False
        self.children: list[ElementTag | ElementComment | ElementInstructions | ElementText] = []
        self.attributes: list[ElementAttribute] = []
        self.current = 0
        self.end = len(self.tokens) - 1
        self.verify_start()
        self.verify_end()
        self.parse_tagname()
        self.parse_attributes()

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<"):
            self.current += 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_start(self.tokens[0], "Element is missing left angle bracket.")

    def verify_end(self) -> None:
        if self.current == self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[-1], "Element is missing right angle bracket.")
            return
        if self.tokens[self.end].match(">"):
            self.end -= 1
            return
        if self.tokens[self.end].match("/>"):
            self.closed = True
            self.end -= 1
            return
        if self.tokens[self.end].endswith(">"):
            self.end -= 1
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[-1], "Element has wrong ending sequence.")
            return
        if self.error_collector is not None:
            self.error_collector.add_token_end(self.tokens[self.end], "Element is missing right angle bracket.")

    def parse_tagname(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[0], "Tag name is missing.")
            return
        self.name = self.tokens[self.current]
        verify_element_or_attribute_name(self.name, self.error_collector)
        self.current += 1

    def parse_attribute_value(self) -> None | Token:
        attribute_value: Token | None = None
        if not self.tokens[self.current].is_quotes():
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "The attribute value must be enclosed in quotes."
                )
        else:
            self.current += 1
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "The attribute value is missing.")
            return
        if self.tokens[self.current].is_quotes():
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "The attribute value is missing.")
            return
        attribute_value = self.tokens[self.current]
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "The attribute value must be enclosed in quotes."
                )
            return attribute_value
        self.current += 1
        if not self.tokens[self.current].is_quotes():
            if self.error_collector is not None:
                self.error_collector.add_token_end(attribute_value, "The attribute value must be enclosed in quotes.")
        return attribute_value

    def parse_attributes(self) -> None:
        attribute: None | ElementAttribute = None
        while self.current < self.end:
            if self.tokens[self.current].match("="):
                if attribute is None:
                    if self.error_collector is not None:
                        self.error_collector.add_token_start(
                            self.tokens[self.current], "Missing attribute name to attach the value."
                        )
                    self.current += 1
                    continue
                self.current += 1
                attribute_value = self.parse_attribute_value()
                if attribute_value is not None:
                    verify_content_or_attribute_value(attribute_value, self.error_collector)
                    attribute.value = attribute_value
                self.current += 1
                continue
            attribute = ElementAttribute(self.tokens[self.current], self)
            self.attributes.append(attribute)
            self.current += 1


class ElementAttribute:
    def __init__(
        self,
        name_token: Token,
        parent_tag: ElementTag | None = None,
        error_collector: ErrorCollector | None = None,
    ) -> None:
        self.name = name_token
        self.parent_tag = parent_tag
        self.error_collector = error_collector
        verify_element_or_attribute_name(self.name, self.error_collector)
        self.value: None | Token = None

    def add_value(self, value_token: Token) -> None:
        self.value = value_token

    def __repr__(self):
        return f"Attribute: {self.name.chars}"


class ElementCData:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.verify_start()
        self.verify_end()
        self.verify_and_get_content()

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<![CDATA["):
            self.current += 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_start(self.tokens[0], "CData element is missing left angle bracket.")

    def verify_end(self) -> None:
        if self.current == self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[-1], "CData element is missing right angle bracket.")
            return
        if self.tokens[self.end].match("]]>"):
            self.end -= 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_end(self.tokens[self.end], "CData element is missing right angle bracket.")

    def verify_and_get_content(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Empty CData element.")
            return
        if len(self.tokens[self.current : self.end]) > 1:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Invalid CData element.")
            return
        self.current += 1
        self.content = self.tokens[self.current]


class ElementClosingTag:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.name: None | Token = None
        self.error_collector = error_collector
        self.current = 0
        self.end = len(element_tokens) - 1
        self.verify_start()
        self.verify_end()
        self.verify_and_get_name()

    def verify_start(self) -> None:
        if self.tokens[self.current].match("</"):
            self.current += 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_start(self.tokens[0], "Closing tag is missing left angle bracket.")

    def verify_end(self) -> None:
        if self.current == self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[-1], "Closing tag is missing right angle bracket.")
            return
        if self.tokens[self.end].match(">"):
            self.end -= 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_end(self.tokens[self.end], "Closing tag is missing right angle bracket.")

    def verify_and_get_name(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Empty closing tag.")
            return
        if len(self.tokens[self.current : self.end]) > 0:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Invalid closing tag.")
            return
        self.name = self.tokens[self.current]
        verify_element_or_attribute_name(self.name, self.error_collector)


class ElementComment:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.verify_start()
        self.verify_end()
        self.verify_and_get_content()

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<!--"):
            self.current += 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_start(self.tokens[0], "Comment element is missing left angle bracket.")

    def verify_end(self) -> None:
        if self.current == self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[-1], "Comment element is missing closing bracket.")
            return
        if self.tokens[self.end].match("-->"):
            self.end -= 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_end(self.tokens[self.end], "Comment element is missing closing bracket.")

    def verify_and_get_content(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Empty Comment element.")
            return
        if len(self.tokens[self.current : self.end]) > 1:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Invalid Comment element.")
            return
        self.current += 1
        self.content = self.tokens[self.current]


class ElementInstructions:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.verify_start()
        self.verify_end()
        self.verify_and_get_content()

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<?"):
            self.current += 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_start(self.tokens[0], "Instructions element is missing left angle bracket.")

    def verify_end(self) -> None:
        if self.current == self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(
                    self.tokens[-1], "Instructions element is missing right angle bracket."
                )
            return
        if self.tokens[self.end].match("?>"):
            self.end -= 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_end(
                self.tokens[self.end], "Instructions element is missing closing bracket."
            )

    def verify_and_get_content(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Empty Instructions element.")
            return
        if len(self.tokens[self.current : self.end]) > 1:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Invalid Instructions element.")
            return
        self.current += 1
        self.content = self.tokens[self.current]


class ElementText:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.content: None | Token = None
        self.verify_and_get_content()

    def verify_and_get_content(self) -> None:
        if len(self.tokens) > 1:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[0], "Invalid Comment element.")
            return
        self.content = self.tokens[0]
        verify_content_or_attribute_value(self.content, self.error_collector)


class ElementXmlDeclaration:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.attributes: list[ElementAttribute] = []
        self.verify_start()
        self.verify_end()
        self.parse_attributes()
        self.verify_xml_declaration()

    def verify_xml_declaration(self) -> None:
        if not (self.tokens[0].buffer_slot == 0 and self.tokens[0].buffer_pointer == 0):
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[0], "XML declaration must be the on the first line.")
        if len(self.attributes) >= 1:
            self.verify_attribute_version(self.attributes[0])
        if len(self.attributes) >= 2:
            self.verify_attribute_encoding(self.attributes[1])
        if len(self.attributes) >= 3:
            self.verify_attribute_standalone(self.attributes[2])
        if len(self.attributes) > 3:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.attributes[3].name,
                    "Only three atributtes are allowed: version, encoding and standalone.",
                )

    def verify_attribute_version(self, attribute: ElementAttribute) -> None:
        if not attribute.name.match("version"):
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    attribute.name,
                    "The first attribute in declaration must be the value attribute.",
                )
        if attribute.value is None:
            if self.error_collector is not None:
                self.error_collector.add_token_end(
                    attribute.name,
                    "The first attribute is missing its value.",
                )
            return
        if not attribute.value.match("1.0"):
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    attribute.value,
                    "Only the version 1.0 is supported.",
                )
            return

    def verify_attribute_encoding(self, attribute: ElementAttribute) -> None:
        if not attribute.name.match("encoding"):
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    attribute.name,
                    "The second attribute in declaration must be the encoding attribute.",
                )
        if attribute.value is None:
            if self.error_collector is not None:
                self.error_collector.add_token_end(
                    attribute.name,
                    "The second attribute is missing its value.",
                )
            return
        if attribute.value.chars not in {"UTF-8", "UTF-16"}:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    attribute.value,
                    "Only the UTF-8 and UTF-16 encodings are supported.",
                )
            return

    def verify_attribute_standalone(self, attribute: ElementAttribute) -> None:
        if not attribute.name.match("standalone"):
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    attribute.name,
                    "The third attribute in declaration must be the standalone attribute.",
                )
        if attribute.value is None:
            if self.error_collector is not None:
                self.error_collector.add_token_end(
                    attribute.name,
                    "The third attribute is missing its value.",
                )
            return
        if attribute.value.chars not in {"yes", "no"}:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    attribute.value,
                    "Only the yes and no values are allowed for the standalone attribute.",
                )
            return

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<?xml"):
            self.current += 1
            return
        if self.error_collector is not None:
            self.error_collector.add_token_start(self.tokens[0], "Xml declaration has wrong opening sequence.")

    def verify_end(self) -> None:
        if self.current == self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[-1], "Xml declaration is missing ending sequence.")
            return
        if self.tokens[self.end].match("?>"):
            self.end -= 1
            return
        if self.tokens[self.end].endswith(">"):
            self.end -= 1
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[-1], "Xml declaration has wrong ending sequence.")
            return
        if self.error_collector is not None:
            self.error_collector.add_token_end(self.tokens[self.end], "Xml declaration is missing ending sequence.")

    def parse_attribute_value(self) -> None | Token:
        attribute_value: Token | None = None
        if not self.tokens[self.current].is_quotes():
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "The attribute value must be enclosed in quotes."
                )
        else:
            self.current += 1
        if self.current == self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "The attribute value is missing.")
            return
        if self.tokens[self.current].is_quotes():
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "The attribute value is missing.")
            return
        attribute_value = self.tokens[self.current]
        if self.current == self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "The attribute value must be enclosed in quotes."
                )
            return attribute_value
        self.current += 1
        if not self.tokens[self.current].is_quotes():
            if self.error_collector is not None:
                self.error_collector.add_token_end(attribute_value, "The attribute value must be enclosed in quotes.")
        return attribute_value

    def parse_attributes(self) -> None:
        attribute: None | ElementAttribute = None
        while self.current < self.end:
            if self.tokens[self.current].match("="):
                if attribute is None:
                    if self.error_collector is not None:
                        self.error_collector.add_token_start(
                            self.tokens[self.current], "Missing attribute name to attach the value."
                        )
                    self.current += 1
                    continue
                self.current += 1
                attribute_value = self.parse_attribute_value()
                if attribute_value is not None:
                    verify_content_or_attribute_value(attribute_value, self.error_collector)
                    attribute.value = attribute_value
                self.current += 1
                continue
            attribute = ElementAttribute(self.tokens[self.current])
            self.attributes.append(attribute)
            self.current += 1


class XmlParser:
    def __init__(self) -> None:
        self.buffer_controller = BufferController()
        self.base_entities: dict[str, str] = {}
        self.error_collector = ErrorCollector()
        self.dtd: None = None
        self.inside_dtd: bool = False
        self.inside_element_tree: bool = False
        self.element_list: list = []
        self.element_tree: list = []

    def read_buffer(self, buffer: str) -> None:
        self.buffer_controller.add_buffer_unit(buffer, "In-memory bufer")

    def read_file(self, filename: str) -> None:
        pass

    def element_text_is_empty(self, element_tokens: list[Token]) -> bool:
        if len(element_tokens) > 1:
            return False
        element_text = element_tokens[0]
        if element_text.chars.isspace():
            return True
        return False

    def build_element_list(self) -> None:
        element_tokens = self.buffer_controller.get_token_list()
        while element_tokens is not None:
            match element_tokens[0].chars:
                case "<?xml":
                    xml_declaration = ElementXmlDeclaration(element_tokens, self.error_collector)
                    self.element_list.append(xml_declaration)
                case "<?":
                    xml_instructions = ElementInstructions(element_tokens, self.error_collector)
                    self.element_list.append(xml_instructions)
                case "<!--":
                    xml_comment = ElementComment(element_tokens, self.error_collector)
                    self.element_list.append(xml_comment)
                case "<![CDATA[":
                    xml_cdata = ElementCData(element_tokens, self.error_collector)
                    self.element_list.append(xml_cdata)
                case "<!":
                    xml_dtd = ElementDtd(element_tokens, self.error_collector)
                    self.element_list.append(xml_dtd)
                case "</":
                    xml_closing_tag = ElementClosingTag(element_tokens, self.error_collector)
                    self.element_list.append(xml_closing_tag)
                case "<":
                    xml_tag = ElementTag(element_tokens, self.error_collector)
                    self.element_list.append(xml_tag)
                case _:
                    if not self.element_text_is_empty(element_tokens):
                        xml_text = ElementText(element_tokens, self.error_collector)
                        self.element_list.append(xml_text)
            element_tokens = self.buffer_controller.get_token_list()


xml = """ <?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<!-- This is the root element of the XML document -->
<root xmlns="http://example.com/default" xmlns:ns="http://example.com/ns">

    <!-- XML declaration, comments, and processing instructions -->
    <?xml-stylesheet type="text/xsl" href="style.xsl"?>
    <!-- Comment about data below -->

    <metadata>
        <author>John Doe</author>
        <date>2024-10-20</date>
        <version>1.0</version>
    </metadata>

    <!-- Standard elements with attributes -->
    <section id="1" type="intro">
        <title>Introduction to XML</title>
        <paragraph>This document provides an overview of XML structure and elements.</paragraph>
    </section>

    <!-- CDATA Section -->
    <example>
        <code><![CDATA[
            <div>Some HTML code example here</div>
        ]]></code>
    </example>

    <!-- Namespaced elements -->
    <ns:data>
        <ns:item id="a1&lt;" value="Example A">Namespaced item A</ns:item>
        <ns:item id="b2" value="Example B">Namespaced item B</ns:item>
    </ns:data>

    <!-- Nested structure with mixed content -->
    <content>
        <header>This is a header</header>
        Some text outside tags.
        <paragraph>First paragraph inside content.</paragraph>
        <footer>End of content</footer>
    </content>

    <!-- An empty element -->
    <emptyElement />

</root>
<root1></root1>"""

basic_tag = """<ns:item id="a1&lt;" value="Example A">"""

dtd = """<!DOCTYPE person [
    <!ELEMENT first_name (#PCDATA)>
    <!ELEMENT last_name (#PCDATA)>
    <!ELEMENT profession (#PCDATA)>
    <!ELEMENT name (first_name, last_name)>
    <!ELEMENT person (name, profession*)>
]>"""

xmlparser = XmlParser()
xmlparser.read_buffer(basic_tag)
xmlparser.build_element_list()
print()
