from __future__ import annotations

from itertools import accumulate
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from buffer_controller import Token

from buffer_controller import BufferController
from shared import verify_content_or_attribute_value
from shared import verify_element_or_attribute_name


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


class ValidatorAttribute:
    def __init__(
        self,
        name_token: Token,
        parent_tag: ValidatorTag | None = None,
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


class ValidatorCData:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.verify_start()
        self.verify_end()
        self.verify_and_get_content()

    def __repr__(self):
        if self.content is None:
            return "Empty Cdata"
        return f"Cdata: {self.content.chars}"

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


class ValidatorComment:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.verify_start()
        self.verify_end()
        self.verify_and_get_content()

    def __repr__(self):
        if self.content is None:
            return "Empty Comment"
        return f"Comment: {self.content.chars}"

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
        self.content = self.tokens[self.current]


class ValidatorDoctype:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.rootname: Token | None = None
        self.extern_system: None | Token = None
        self.extern_public: None | Token = None
        self.intern_declarations_closed = True
        self.closed = False
        self.doctype_tree: list[
            ValidatorDtdElement
            | ValidatorDtdAttlist
            | ValidatorDtdEntity
            | ValidatorDtdNotation
            | ValidatorDtdIncludeIgnore
            | ValidatorComment
            | ValidatorInstructions
        ] = []
        self.verify_start()
        self.verify_end()
        self.verify_and_get_root()
        self.optional_verify_and_get_extern_dtd()
        self.optional_verify_and_get_intern_dtd()
        self.check_trailing()

    def is_ending(self, text: ValidatorParsedText) -> bool:
        if text.content is None:
            return False
        first_stop = text.content.search_preceded_by_whitespace("]")
        if first_stop < 0:
            return False
        second_stop = text.content.search_preceded_by_whitespace(">", first_stop)
        if second_stop < 0:
            return False
        text.content.remove_length_from_left(second_stop)
        return True

    def is_element_added_to_tree(
        self,
        element: Any,
    ) -> bool:
        if self.closed:
            return False
        if len(self.doctype_tree) > 0 and isinstance(self.doctype_tree[-1], ValidatorDtdIncludeIgnore):
            if self.doctype_tree[-1].is_element_added_to_tree(element):
                return True
        if isinstance(
            element,
            (
                ValidatorDtdElement,
                ValidatorDtdAttlist,
                ValidatorDtdEntity,
                ValidatorDtdNotation,
                ValidatorDtdIncludeIgnore,
                ValidatorComment,
                ValidatorInstructions,
            ),
        ):
            self.doctype_tree.append(element)
            return True
        if isinstance(element, ValidatorParsedText) and self.is_ending(element):
            self.closed = True
            return True
        if self.error_collector is not None:
            self.error_collector.add_token_start(self.tokens[0], "Doctype tree was not properly closed.")
            if isinstance(element, ValidatorCData):
                self.error_collector.add_token_start(element.tokens[0], "Cdata cannot be added to Doctype tree.")
            if isinstance(element, ValidatorAttribute):
                self.error_collector.add_token_start(element.name, "Tag attribute cannot be added to Doctype tree.")
            if isinstance(element, ValidatorTag):
                self.error_collector.add_token_start(element.tokens[0], "Tag cannot be added to Doctype tree.")
            if isinstance(element, ValidatorParsedText):
                self.error_collector.add_token_start(element.tokens[0], "Parsed text cannot be added to Doctype tree.")
            if isinstance(element, ValidatorXmlDeclaration):
                self.error_collector.add_token_start(
                    element.tokens[0], "Xml declaration cannot be added to Doctype tree."
                )
        return False

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!DOCTYPE"):
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[0], "Doctype is missing starting sequence.")
        self.current += 1
        return

    def verify_end(self) -> None:
        if self.tokens[self.end].match(">"):
            self.closed = True
            self.end -= 1
            return

    def verify_and_get_root(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(
                    self.tokens[0], "Doctype is missing root element and closing sequence."
                )
            return
        self.rootname = self.tokens[self.current]
        verify_element_or_attribute_name(self.rootname, self.error_collector)
        self.current += 1

    def optional_verify_and_get_extern_dtd(self) -> None:
        if self.current > self.end:
            return
        if self.tokens[self.current].match("SYSTEM"):
            self.current += 1
            self.extern_system = self.verify_and_get_quotes_value("System identifier")
        elif self.tokens[self.current].match("PUBLIC"):
            self.current += 1
            self.extern_public = self.verify_and_get_quotes_value("Public identifier")
            self.extern_system = self.verify_and_get_quotes_value("System identifier")

    def verify_and_get_quotes_value(self, value_name: str) -> None | Token:
        quotes_value: None | Token = None
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[self.current], f"{value_name} value is missing.")
            return
        # The left quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], f"{value_name} value is missing left quote."
                )
        # The quotes value
        if self.current > self.end or self.tokens[self.current].is_quotes():
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], f"{value_name} value is missing.")
            return
        else:
            quotes_value = self.tokens[self.current]
            self.current += 1
        # The right quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], f"{value_name} value is missing right quote."
                )
        return quotes_value

    def optional_verify_and_get_intern_dtd(self) -> None:
        if self.current > self.end:
            return
        if self.tokens[self.current].match("["):
            self.current += 1
            self.intern_declarations_closed = False
        else:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "Invalid start of internal definitions."
                )
            return

        if self.current > self.end:
            return
        if self.tokens[self.current].match("]"):
            self.current += 1
            self.intern_declarations_closed = True
        else:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Invalid end of internal definitions.")
            return

    def check_trailing(self) -> None:
        if self.current <= self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[0], "Invalid trailing sequence found.")


class ValidatorDtdElement:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.element: None | Token = None
        self.definition_tokens: None | list[Token] = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_element()
        self.verify_and_get_definition_tokens()

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!ELEMENT"):
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[0], "Element tag is missing starting sequence.")
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[self.end], "Element tag is missing right angle bracket.")
            return
        self.end -= 1

    def verify_and_get_element(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[0], "Element tag is missing element name.")
            return
        self.element = self.tokens[self.current]
        verify_element_or_attribute_name(self.element, self.error_collector)
        self.current += 1

    def verify_and_get_definition_tokens(self) -> None:
        self.definition_tokens = self.tokens[self.current : self.end + 1]


class ValidatorDtdAttlist:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.element: None | Token = None
        self.attribute: None | Token = None
        self.definition_tokens: None | list[Token] = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_element()
        self.verify_and_get_attribute()
        self.verify_and_get_definition_tokens()

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!ATTLIST"):
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[0], "Attlist tag is missing starting sequence.")
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[self.end], "Attlist tag is missing right angle bracket.")
            return
        self.end -= 1

    def verify_and_get_element(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[0], "Attlist tag is missing element name.")
            return
        self.element = self.tokens[self.current]
        verify_element_or_attribute_name(self.element, self.error_collector)
        self.current += 1

    def verify_and_get_attribute(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[0], "Attlist tag is missing attribute name.")
            return
        self.attribute = self.tokens[self.current]
        verify_element_or_attribute_name(self.attribute, self.error_collector)
        self.current += 1

    def verify_and_get_definition_tokens(self) -> None:
        self.definition_tokens = self.tokens[self.current : self.end + 1]


class ValidatorDtdEntity:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.name: None | Token = None
        self.intern_value: None | Token = None
        self.extern_system: None | Token = None
        self.extern_public: None | Token = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_name()
        self.verify_and_get_entity_type()

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!ENTITY"):
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Invalid Entity starting sequence.")
        else:
            self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[self.end], "Entity is missing right angle bracket.")
        else:
            self.end -= 1

    def verify_and_get_name(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[self.current], "Entity is missing a name.")
        else:
            self.name = self.tokens[self.current]
            verify_element_or_attribute_name(self.name, self.error_collector)
            self.current += 1

    def verify_and_get_entity_type(self) -> None:
        if self.current > self.end:
            self.intern_value = self.verify_and_get_quotes_value("Entity substition")
            return
        if self.tokens[self.current].match("SYSTEM"):
            self.current += 1
            self.extern_system = self.verify_and_get_quotes_value("System identifier")
        elif self.tokens[self.current].match("PUBLIC"):
            self.current += 1
            self.extern_public = self.verify_and_get_quotes_value("Public identifier")
            self.extern_system = self.verify_and_get_quotes_value("System identifier")
        else:
            self.intern_value = self.verify_and_get_quotes_value("Entity substition")

    def verify_and_get_quotes_value(self, value_name: str) -> None | Token:
        quotes_value: None | Token = None
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[self.current], f"{value_name} value is missing.")
            return
        # The left quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], f"{value_name} value is missing left quote."
                )
        # The quotes value
        if self.current > self.end or self.tokens[self.current].is_quotes():
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], f"{value_name} value is missing.")
            return
        else:
            quotes_value = self.tokens[self.current]
            self.current += 1
        # The right quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], f"{value_name} value is missing right quote."
                )
        return quotes_value


class ValidatorDtdNotation:
    def __init__(self, tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = tokens
        self.error_collector = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.notation: None | Token = None
        self.value: None | Token = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_notation()
        self.verify_and_get_value()
        self.check_trailing()

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!NOTATION"):
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "Notation tag is missing starting sequence."
                )
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            if self.error_collector is not None:
                self.error_collector.add_token_end(
                    self.tokens[self.end], "Notation tag is missing right angle bracket."
                )
            return
        self.end -= 1

    def verify_and_get_notation(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[self.current], "Notation tag is missing notation name.")
        else:
            self.element = self.tokens[self.current]
            verify_element_or_attribute_name(self.element, self.error_collector)
            self.current += 1

    def verify_and_get_value(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[self.current], "Notation tag is missing value.")
            return
        # The left quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Notation value is missing left quote.")
        # The notation value
        if self.current > self.end or self.tokens[self.current].is_quotes():
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Notation value is missing.")
            return
        else:
            self.substitute_text = self.tokens[self.current]
            self.current += 1
        # The right quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "Notation value is missing right quote."
                )

    def check_trailing(self) -> None:
        if self.current <= self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[0], "Invalid trailing sequence found.")


class ValidatorDtdIncludeIgnore:
    def __init__(self, tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = tokens
        self.error_collector = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.include: bool = False
        self.closed: bool = False
        self.parent: None | ValidatorDtdIncludeIgnore = None
        self.current_includeignore: None | ValidatorDtdIncludeIgnore = None
        self.includeignore_tree: list[
            ValidatorDtdElement
            | ValidatorDtdAttlist
            | ValidatorDtdEntity
            | ValidatorDtdNotation
            | ValidatorDtdIncludeIgnore
            | ValidatorComment
            | ValidatorInstructions
        ] = []
        self.verify_start()
        self.verify_end()
        self.verify_conditional()
        self.verify_begin_section()
        self.check_trailing()

    def is_ending(self, text: ValidatorParsedText) -> bool:
        if text.content is None:
            return False
        length_to_remove = text.content.search_preceded_by_whitespace("]]>")
        if length_to_remove < 0:
            return False
        text.content.remove_length_from_left(length_to_remove)
        return True

    def is_element_added_to_tree(self, element: Any) -> bool:
        if self.closed:
            return False
        if self.current_includeignore is not None:
            if isinstance(element, ValidatorDtdIncludeIgnore):
                self.current_includeignore.includeignore_tree.append(element)
                element.parent = self.current_includeignore
                self.current_includeignore = element
            elif isinstance(
                element,
                (
                    ValidatorDtdElement,
                    ValidatorDtdAttlist,
                    ValidatorDtdEntity,
                    ValidatorDtdNotation,
                    ValidatorDtdIncludeIgnore,
                    ValidatorComment,
                    ValidatorInstructions,
                ),
            ):
                self.current_includeignore.includeignore_tree.append(element)
                return True
            elif isinstance(element, ValidatorParsedText) and self.is_ending(element):
                self.current_includeignore.closed = True
                self.current_includeignore = self.current_includeignore.parent
                return True
            else:
                if self.error_collector is not None:
                    self.error_collector.add_token_start(self.tokens[0], "Dtd conditional was not properly closed.")
                    if isinstance(element, ValidatorCData):
                        self.error_collector.add_token_start(
                            element.tokens[0], "Cdata cannot be added to Doctype tree."
                        )
                    if isinstance(element, ValidatorAttribute):
                        self.error_collector.add_token_start(element.name, "Attribute cannot be added to Doctype tree.")
                    if isinstance(element, ValidatorTag):
                        self.error_collector.add_token_start(element.tokens[0], "Tag cannot be added to Doctype tree.")
                    if isinstance(element, ValidatorParsedText):
                        self.error_collector.add_token_start(
                            element.tokens[0], "Parsed text cannot be added to Doctype tree."
                        )
                    if isinstance(element, ValidatorXmlDeclaration):
                        self.error_collector.add_token_start(
                            element.tokens[0], "Xml declaration cannot be added to Doctype tree."
                        )
                return False
        if isinstance(element, ValidatorDtdIncludeIgnore):
            self.includeignore_tree.append(element)
            element.parent = self.current_includeignore
            self.current_includeignore = element
            return True
        if isinstance(
            element,
            (
                ValidatorDtdElement,
                ValidatorDtdAttlist,
                ValidatorDtdEntity,
                ValidatorDtdNotation,
                ValidatorDtdIncludeIgnore,
                ValidatorComment,
                ValidatorInstructions,
            ),
        ):
            self.includeignore_tree.append(element)
            return True
        if isinstance(element, ValidatorParsedText) and self.is_ending(element):
            self.closed = True
            return True
        if self.error_collector is not None:
            self.error_collector.add_token_start(self.tokens[0], "Doctype tree was not properly closed.")
            if isinstance(element, ValidatorCData):
                self.error_collector.add_token_start(element.tokens[0], "Cdata cannot be added to Doctype tree.")
            if isinstance(element, ValidatorAttribute):
                self.error_collector.add_token_start(element.name, "Tag attribute cannot be added to Doctype tree.")
            if isinstance(element, ValidatorTag):
                self.error_collector.add_token_start(element.tokens[0], "Tag cannot be added to Doctype tree.")
            if isinstance(element, ValidatorParsedText):
                self.error_collector.add_token_start(element.tokens[0], "Parsed text cannot be added to Doctype tree.")
            if isinstance(element, ValidatorXmlDeclaration):
                self.error_collector.add_token_start(
                    element.tokens[0], "Xml declaration cannot be added to Doctype tree."
                )
        return False

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!["):
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "Conditional section is missing starting sequence."
                )
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match("]]>"):
            return
        self.closed = True
        self.end -= 1

    def verify_conditional(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[self.current], "Condition is missing.")
        if self.tokens[self.current].match("INCLUDE"):
            self.include = True
            self.current += 1
        elif self.tokens[self.current].match("IGNORE"):
            self.current += 1
        else:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "Conditional section is not recognized."
                )

    def verify_begin_section(self) -> None:
        if self.current > self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "Start of definitions in conditional section is missing."
                )
        if not self.tokens[self.current].match("["):
            if self.error_collector is not None:
                self.error_collector.add_token_start(
                    self.tokens[self.current], "Start of definitions in conditional section is not recognized."
                )
        self.current += 1

    def check_trailing(self) -> None:
        if self.current <= self.end:
            if self.error_collector is not None:
                self.error_collector.add_token_end(self.tokens[0], "Invalid trailing sequence found.")


class ValidatorInstructions:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.verify_start()
        self.verify_end()
        self.verify_and_get_content()

    def __repr__(self):
        if self.content is None:
            return "Empty Instructions"
        return f"Instructions: {self.content.chars}"

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
        self.content = self.tokens[self.current]


class ValidatorTag:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.name: None | Token = None
        self.closed = False
        self.parent: None | ValidatorTag = None
        self.children: list[
            ValidatorTag
            | ValidatorCData
            | ValidatorComment
            | ValidatorDoctype
            | ValidatorDtdElement
            | ValidatorDtdAttlist
            | ValidatorDtdEntity
            | ValidatorDtdNotation
            | ValidatorDtdIncludeIgnore
            | ValidatorInstructions
            | ValidatorParsedText
            | ValidatorXmlDeclaration
        ] = []
        self.attributes: list[ValidatorAttribute] = []
        self.current = 0
        self.end = len(self.tokens) - 1
        self.verify_start()
        self.verify_end()
        self.parse_tagname()
        self.parse_attributes()

    def __repr__(self):
        if self.name is None:
            return "Empty Tag"
        return f"Tag: {self.name.chars}"

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

    def close_tag(self, closing_tagname: str) -> bool:
        if self.name is None:
            return False
        if self.name.chars.strip() == closing_tagname.strip():
            self.closed = True
            return True
        return False

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
        attribute: None | ValidatorAttribute = None
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
            attribute = ValidatorAttribute(self.tokens[self.current], self)
            self.attributes.append(attribute)
            self.current += 1


class ValidatorParsedText:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.content: None | Token = None
        self.add_to_tree: bool = True
        self.get_content()

    def is_empty(self) -> bool:
        if self.content is None:
            return True
        if len(self.content.chars) == 0:
            return True
        if self.content.chars.isspace():
            return True
        return False

    def get_content(self) -> None:
        if len(self.tokens) > 1:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[0], "Invalid Text element.")
            return
        self.content = self.tokens[0]

    def verify_content(self) -> None:
        if self.content is None:
            if self.error_collector is not None:
                self.error_collector.add_token_start(self.tokens[0], "Invalid Text element.")
            return
        verify_content_or_attribute_value(self.content, self.error_collector)

    def __repr__(self):
        if self.content is None:
            return "Empty Text"
        return f"Text: {self.content.chars}"


class ValidatorXmlDeclaration:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.attributes: list[ValidatorAttribute] = []
        self.verify_start()
        self.verify_end()
        self.parse_attributes()
        self.verify_xml_declaration()

    def __repr__(self):
        return "XmlDeclaration"

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

    def verify_attribute_version(self, attribute: ValidatorAttribute) -> None:
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

    def verify_attribute_encoding(self, attribute: ValidatorAttribute) -> None:
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

    def verify_attribute_standalone(self, attribute: ValidatorAttribute) -> None:
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
        attribute: None | ValidatorAttribute = None
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
            attribute = ValidatorAttribute(self.tokens[self.current])
            self.attributes.append(attribute)
            self.current += 1


class XmlValidator:
    def __init__(self) -> None:
        self.buffer_controller = BufferController()
        self.error_collector = ErrorCollector()
        self.dtd: None = None
        self.current_node: ValidatorTag | None = None
        self.validation_tree: list[
            ValidatorTag
            | ValidatorCData
            | ValidatorComment
            | ValidatorDoctype
            | ValidatorDtdElement
            | ValidatorDtdAttlist
            | ValidatorDtdEntity
            | ValidatorDtdNotation
            | ValidatorDtdIncludeIgnore
            | ValidatorInstructions
            | ValidatorParsedText
            | ValidatorXmlDeclaration
        ] = []

    def read_buffer(self, buffer: str) -> None:
        self.buffer_controller.add_buffer_unit(buffer, "In-memory bufer")

    def read_file(self, filename: str) -> None:
        pass

    def parse_closing_tag(self, token_list: list[Token]) -> None:
        # name of a closing tag
        if not token_list[0].match("</"):
            self.error_collector.add_token_start(token_list[0], "Invalid closing tag.")
            return
        if len(token_list) == 1:
            self.error_collector.add_token_start(token_list[0], "Incomplete closing tag.")
            return
        if len(token_list) == 2:
            if token_list[1].match(">"):
                self.error_collector.add_token_start(token_list[1], "Closing tag is missing tag name.")
                return
            else:
                self.error_collector.add_token_end(token_list[1], "Closing tag is missing closing bracket.")
        if len(token_list) == 3 and not token_list[2].match(">"):
            self.error_collector.add_token_end(token_list[1], "Invalid closing sequence for the closing tag.")
        closing_tagname = token_list[1].chars
        # Check for blank spaces in beggining of a name
        current_node = self.current_node
        missing_close_tags: list[ValidatorTag] = []
        while current_node is not None:
            if current_node.close_tag(closing_tagname):
                self.current_node = current_node.parent
                if len(missing_close_tags) > 0:
                    for tag in missing_close_tags:
                        if tag.name is not None:
                            self.error_collector.add_token_start(tag.name, "The tag is missing its closing tag.")
                break
            else:
                missing_close_tags.append(current_node)
                current_node = current_node.parent
        if current_node is None:
            self.error_collector.add_token_start(token_list[1], "Closing tag not matching any other tag.")

    def check_closing_tags(self) -> None:
        current = self.current_node
        if current is not None:
            self.error_collector.add_token_start(current.tokens[0], "Missing close tag.")
            current = current.parent

    def add_element_to_validation_tree(
        self,
        element: ValidatorTag
        | ValidatorCData
        | ValidatorComment
        | ValidatorDoctype
        | ValidatorDtdElement
        | ValidatorDtdAttlist
        | ValidatorDtdNotation
        | ValidatorDtdEntity
        | ValidatorDtdIncludeIgnore
        | ValidatorInstructions
        | ValidatorParsedText
        | ValidatorXmlDeclaration,
    ) -> None:
        if self.current_node is None:
            if len(self.validation_tree) > 0 and isinstance(self.validation_tree[-1], ValidatorDoctype):
                if self.validation_tree[-1].is_element_added_to_tree(element):
                    return
            if len(self.validation_tree) > 0 and isinstance(self.validation_tree[-1], ValidatorDtdIncludeIgnore):
                if self.validation_tree[-1].is_element_added_to_tree(element):
                    return
            self.validation_tree.append(element)
            return
        ###############
        if len(self.current_node.children) > 0 and isinstance(self.current_node.children[-1], ValidatorDoctype):
            if self.current_node.children[-1].is_element_added_to_tree(element):
                return
        if len(self.current_node.children) > 0 and isinstance(
            self.current_node.children[-1], ValidatorDtdIncludeIgnore
        ):
            if self.current_node.children[-1].is_element_added_to_tree(element):
                return
        self.current_node.children.append(element)
        ################
        if isinstance(element, ValidatorParsedText):
            element.add_to_tree = True
        ################
        if isinstance(element, ValidatorTag):
            element.parent = self.current_node
            self.current_node = element
            if element.closed:
                self.current_node = self.current_node.parent

    def build_validation_tree(self) -> None:
        token_list = self.buffer_controller.get_token_list()
        while token_list is not None:
            match token_list[0].chars:
                case "<?xml":
                    element = ValidatorXmlDeclaration(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "<!DOCTYPE":
                    element = ValidatorDoctype(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "<!ELEMENT":
                    element = ValidatorDtdElement(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "<!ATTLIST":
                    element = ValidatorDtdAttlist(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "<!NOTATION":
                    element = ValidatorDtdNotation(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "<!ENTITY":
                    element = ValidatorDtdEntity(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "<![":
                    element = ValidatorDtdIncludeIgnore(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "<?":
                    element = ValidatorInstructions(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "<!--":
                    element = ValidatorComment(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "<![CDATA[":
                    element = ValidatorCData(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case "</":
                    self.parse_closing_tag(token_list)
                case "<":
                    element = ValidatorTag(token_list, self.error_collector)
                    self.add_element_to_validation_tree(element)
                case _:
                    if len(token_list) > 1:
                        raise ValueError("Text node cannot have more than 1 token.")
                    element = ValidatorParsedText(token_list, self.error_collector)
                    while not element.is_empty() and element.add_to_tree:
                        self.add_element_to_validation_tree(element)
            token_list = self.buffer_controller.get_token_list()
        self.check_closing_tags()

    def print_tree(self) -> None:
        pass


xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<!-- This is the root element of the XML document -->
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

nested_dtd = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE library [
    <!-- Declare Elements -->
    <!ELEMENT library (book+, journal*)>
    <!ELEMENT book (title, author+, publisher, price)>
    <!ELEMENT journal (title, editor, issue, price)>
    <!ELEMENT title (#PCDATA)>
    <!ELEMENT author (#PCDATA)>
    <!ELEMENT publisher (#PCDATA)>
    <!ELEMENT price (#PCDATA)>
    <!ELEMENT editor (#PCDATA)>
    <!ELEMENT issue (#PCDATA)>

    <!-- Declare Attributes -->
    <!ATTLIST book
        isbn CDATA #REQUIRED
        genre (fiction|nonfiction|fantasy|biography) #IMPLIED>
    <!ATTLIST journal
        issn CDATA #REQUIRED
        frequency (daily|weekly|monthly|yearly) #IMPLIED>

    <!-- Declare Entities -->
    <!ENTITY pub1 "Penguin Random House">
    <!ENTITY pub2 "HarperCollins">
    <!ENTITY priceUSD "&dollar;"> <!-- Character entity -->

    <!-- Declare Notations -->
    <!NOTATION gif SYSTEM "image/gif">
    <!NOTATION jpg SYSTEM "image/jpeg">

    <!-- Conditional Sections -->
    <![INCLUDE[
        <!ENTITY exampleBook "Advanced XML Techniques">
    ]]>
    <![IGNORE[
        <!ENTITY exampleBook "This will be ignored">
    ]]>

    <!-- Nested Conditional Sections -->
    <![INCLUDE[
        <![IGNORE[
            <!ENTITY nestedIgnored "This content is ignored due to nesting">
        ]]>
        <![INCLUDE[
            <!ENTITY nestedIncluded "Nested conditional section content included">
        ]]>
    ]]>

]>

<library>
    <book isbn="1234567890" genre="fiction">
        <title>XML Mastery</title>
        <author>John Doe</author>
        <author>Jane Smith</author>
        <publisher>&pub1;</publisher>
        <price>&priceUSD;19.99</price>
    </book>
    <journal issn="9876543210" frequency="monthly">
        <title>XML Journal</title>
        <editor>Emma Watson</editor>
        <issue>42</issue>
        <price>&priceUSD;5.99</price>
    </journal>
</library>"""

nested_dtd1 = """<!DOCTYPE library [
    <![INCLUDE[
        <![IGNORE[
            <!ENTITY nestedIgnored "This content is ignored due to nesting">
        ]]>
        <![INCLUDE[
            <!ENTITY nestedIncluded "Nested conditional section content included">
        ]]>
    ]]>

]>"""

basic_tag = """<ns:item id="a1&lt;" value="Example A">"""

dtd = """<!DOCTYPE person [
    <!ELEMENT first_name (#PCDATA)>
    <!ELEMENT last_name (#PCDATA)>
    <!ELEMENT profession (#PCDATA)>
    <!ELEMENT name (first_name, last_name)>
    <!ELEMENT person (name, profession*)>
]>"""

xmlvalidator = XmlValidator()
xmlvalidator.read_buffer(nested_dtd1)
xmlvalidator.build_validation_tree()
print()
