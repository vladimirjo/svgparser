from __future__ import annotations

from typing import TYPE_CHECKING
from enum import Enum, auto, unique


if TYPE_CHECKING:
    from buffer_controller import Token

from buffer_controller import BufferController
from dtd import Dtd
from errorcollector import CritErr
from errorcollector import ErrorCollector

# from shared import verify_content_or_attribute_value
from shared import check_nmtoken, check_xmlname


class ValidatorAttribute:
    def __init__(
        self,
        name_token: Token,
        parent: None | ValidatorTag | ValidatorXmlDeclaration,
        error_collector: ErrorCollector,
    ) -> None:
        self.name = name_token
        self.parent = parent
        self.err = error_collector
        check_xmlname(self.name, self.err)
        self.value: None | Token = None

    def add_value(self, value_token: Token) -> None:
        self.value = value_token

    def __repr__(self):
        return f"Attribute: {self.name.chars}"


class ValidatorCData:
    def __init__(
        self,
        element_tokens: list[Token],
        error_collector: ErrorCollector,
    ) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: None | ValidatorDocument | ValidatorTag = None
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
        self.err.add(self.tokens[0], CritErr.ELEMENT_MISSING_START_SEQUENCE)

    def verify_end(self) -> None:
        if self.current == self.end:
            self.err.add(self.tokens[-1], CritErr.ELEMENT_MISSING_END_SEQUENCE)
        if self.tokens[self.end].match("]]>"):
            self.end -= 1
            return
        if self.err is not None:
            self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE)

    def verify_and_get_content(self) -> None:
        if self.current > self.end:
            if self.err is not None:
                self.err.add(self.tokens[self.current], CritErr.ELEMENT_EMPTY)
            return
        if len(self.tokens[self.current : self.end]) > 1:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_INVALID)
            return
        self.content = self.tokens[self.current]
        self.current += 1


class ValidatorComment:
    def __init__(
        self,
        element_tokens: list[Token],
        error_collector: ErrorCollector,
    ) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: None | ValidatorDocument | ValidatorDoctype | ValidatorDtdIncludeIgnore | ValidatorTag = None
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
        self.err.add(self.tokens[0], CritErr.ELEMENT_MISSING_START_SEQUENCE)

    def verify_end(self) -> None:
        if self.current == self.end:
            self.err.add(self.tokens[-1], CritErr.ELEMENT_MISSING_END_SEQUENCE)
            return
        if self.tokens[self.end].match("-->"):
            self.end -= 1
            return
        self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE)

    def verify_and_get_content(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_EMPTY)
            return
        if len(self.tokens[self.current : self.end]) > 1:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_INVALID)
            return
        self.content = self.tokens[self.current]


class ValidatorDoctype:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: None | ValidatorDocument | ValidatorTag = None
        self.rootname: Token | None = None
        self.extern_system: None | Token = None
        self.extern_public: None | Token = None
        self.intern_declarations_closed = True
        self.closed = False
        self.children: list[
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

    def __repr__(self):
        if self.rootname is None:
            return "Doctype"
        return f"Doctype: {self.rootname.chars}"

    def get_active_includeignore(self) -> None | ValidatorDtdIncludeIgnore:
        if len(self.children) == 0:
            return None
        active_includeignore: None | ValidatorDtdIncludeIgnore = None
        if isinstance(self.children[-1], ValidatorDtdIncludeIgnore) and not self.children[-1].closed:
            active_includeignore = self.children[-1]
        else:
            return active_includeignore
        while len(active_includeignore.children) > 0:
            if (
                isinstance(active_includeignore.children[-1], ValidatorDtdIncludeIgnore)
                and not active_includeignore.children[-1].closed
            ):
                active_includeignore = active_includeignore.children[-1]
            else:
                break
        return active_includeignore

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

    def is_element_added_to_doctype(
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
    ) -> bool:
        if self.closed:
            return False
        if len(self.children) > 0 and isinstance(self.children[-1], ValidatorDtdIncludeIgnore):
            if self.children[-1].is_element_added_to_includeignore(element):
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
            element.parent = self
            self.children.append(element)
            return True
        if isinstance(element, ValidatorParsedText) and self.is_ending(element):
            self.closed = True
            return True
        self.err.add(self.tokens[0], CritErr.DOCTYPE_NOT_CLOSED)
        if isinstance(element, ValidatorCData):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_CDATA_IN_TREE)
        if isinstance(element, ValidatorTag):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_TAG_IN_TREE)
        if isinstance(element, ValidatorParsedText):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_PARSED_TEXT_IN_TREE)
        if isinstance(element, ValidatorDoctype):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_DOCTYPE_IN_TREE)
        if isinstance(element, ValidatorXmlDeclaration):
            self.err.add(element.tokens[0], CritErr.DOCTYPE_XML_DECLARATION_IN_TREE)
        return False

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!DOCTYPE"):
            self.err.add(self.tokens[0], CritErr.DOCTYPE_MISSING_START_SEQUENCE)
        self.current += 1
        return

    def verify_end(self) -> None:
        if self.tokens[self.end].match(">"):
            self.closed = True
            self.end -= 1
            return

    def verify_and_get_root(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[0], CritErr.DOCTYPE_MISSING_ROOT_CLOSING)
            return
        self.rootname = self.tokens[self.current]
        check_xmlname(self.rootname, self.err)
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

    def verify_and_get_quotes_value(self, identifier: str) -> None | Token:
        quotes_value: None | Token = None
        if self.current > self.end:
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_VALUE,
                -1,
                {identifier: identifier},
            )
            return
        # The left quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_LEFT_QUOTE,
                0,
                {identifier: identifier},
            )
        # The quotes value
        if self.current > self.end or self.tokens[self.current].is_quotes():
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_VALUE,
                0,
                {identifier: identifier},
            )
            return
        else:
            quotes_value = self.tokens[self.current]
            self.current += 1
        # The right quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_RIGHT_QUOTE,
                0,
                {identifier: identifier},
            )
        return quotes_value

    def optional_verify_and_get_intern_dtd(self) -> None:
        if self.current > self.end:
            return
        if self.tokens[self.current].match("["):
            self.current += 1
            self.intern_declarations_closed = False
        else:
            self.err.add(self.tokens[self.current], CritErr.DOCTYPE_INVALID_INTERNAL_DEF_START)
            return

        if self.current > self.end:
            return
        if self.tokens[self.current].match("]"):
            self.current += 1
            self.intern_declarations_closed = True
        else:
            self.err.add(self.tokens[self.current], CritErr.DOCTYPE_INVALID_INTERNAL_DEF_END)
            return

    def check_trailing(self) -> None:
        if self.current <= self.end:
            self.err.add(self.tokens[0], CritErr.INVALID_TRAILING_SEQUENCE)


class ValidatorDtdElement:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: None | ValidatorDoctype | ValidatorDtdIncludeIgnore | ValidatorDocument | ValidatorTag = None
        self.element: None | Token = None
        self.definition_tokens: None | list[Token] = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_element()
        self.verify_and_get_definition_tokens()

    def __repr__(self):
        if self.element is None:
            return "DtdElement"
        return f"DtdElement: {self.element.chars}"

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!ELEMENT"):
            self.err.add(self.tokens[0], CritErr.DTD_ELEMENT_MISSING_START_SEQUENCE)
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            self.err.add(self.tokens[self.end], CritErr.DTD_ELEMENT_MISSING_RIGHT_BRACKET)
            return
        self.end -= 1

    def verify_and_get_element(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[0], CritErr.DTD_ELEMENT_MISSING_NAME, -1)
            return
        self.element = self.tokens[self.current]
        check_xmlname(self.element, self.err)
        self.current += 1

    def verify_and_get_definition_tokens(self) -> None:
        self.definition_tokens = self.tokens[self.current : self.end + 1]


class AttrType(Enum):
    CDATA = auto()
    NMTOKEN = auto()
    NMTOKENS = auto()
    ENUM = auto()
    ENTITY = auto()
    ENTITIES = auto()
    ID = auto()
    IDREF = auto()
    IDREFS = auto()
    NOTATION = auto()


class AttrDefault(Enum):
    REQUIRED = auto()
    IMPLIED = auto()
    OPTIONAL = auto()
    FIXED = auto()


class DtdAttributeDefinition:
    def __init__(
        self,
        attr_name: Token,
        attr_type: AttrType,
        attr_enum: list[Token] | None,
        attr_default: AttrDefault,
        attr_literal: Token | None,
    ) -> None:
        self.attr_name = attr_name
        self.attr_type = attr_type
        self.attr_enum = attr_enum
        self.attr_default = attr_default
        self.attr_literal = attr_literal


class ValidatorDtdAttlist:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: None | ValidatorDoctype | ValidatorDtdIncludeIgnore | ValidatorDocument | ValidatorTag = None
        self.element: None | Token = None
        self.attr_defs: list[DtdAttributeDefinition] = []
        self.verify_start()
        self.verify_end()
        self.verify_and_get_element()
        if not self.valid:
            return

    def __repr__(self):
        if self.element is None:
            return "!ATTLIST"
        return f"!ATTLIST: {self.element.chars}"

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!ATTLIST"):
            self.err.add(self.tokens[0], CritErr.ELEMENT_MISSING_START_SEQUENCE)
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)
            return
        self.end -= 1

    def verify_and_get_element(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[0], CritErr.ELEMENT_NAME_MISSING, -1)
            self.valid = False
            return
        self.element = self.tokens[self.current]
        check_xmlname(self.element, self.err)
        self.current += 1

    def get_attribute_name(self) -> Token | None:
        if self.current > self.end:
            return None
        name_pos = self.current
        self.current += 1
        check_xmlname(self.tokens[name_pos], self.err)
        return self.tokens[name_pos]

    def get_attr_type(self) -> AttrType | None:
        if self.current > self.end:
            return None
        if self.tokens[self.current] == "CDATA":
            self.current += 1
            return AttrType.CDATA
        if self.tokens[self.current] == "NMTOKEN":
            self.current += 1
            return AttrType.NMTOKEN
        if self.tokens[self.current] == "NMTOKENS":
            self.current += 1
            return AttrType.NMTOKENS
        if self.tokens[self.current] == "ENTITY":
            self.current += 1
            return AttrType.ENTITY
        if self.tokens[self.current] == "ENTITIES":
            self.current += 1
            return AttrType.ENTITIES
        if self.tokens[self.current] == "ID":
            self.current += 1
            return AttrType.ID
        if self.tokens[self.current] == "IDREF":
            self.current += 1
            return AttrType.IDREF
        if self.tokens[self.current] == "IDREFS":
            self.current += 1
            return AttrType.IDREFS
        if self.tokens[self.current] == "NOTATION":
            self.current += 1
            return AttrType.NOTATION
        if self.tokens[self.current] == "(":
            self.current += 1
            return AttrType.ENUM
        self.err.add(self.tokens[self.current], CritErr.ATTLIST_TYPE_NOT_RECOGNIZED)
        return None

    def get_attr_enum(self) -> list[Token] | None:
        enum_tokens: list[Token] = []
        is_last_token_pipe = False
        while self.current <= self.end or self.tokens[self.current] != ")":
            if self.tokens[self.current] == "|" and is_last_token_pipe:
                self.err.add(self.tokens[self.current], CritErr.ATTLIST_ENUM_SEQ_PIPE)
                self.current += 1
                continue
            if self.tokens[self.current] != "|" and not is_last_token_pipe:
                self.err.add(self.tokens[self.current], CritErr.ATTLIST_ENUM_PIPE_SEPARATION)
                self.current += 1
                continue
            if self.tokens[self.current] == "|" and not is_last_token_pipe:
                self.current += 1
                is_last_token_pipe = True
                continue
            if self.tokens[self.current] != "|" and is_last_token_pipe:
                check_nmtoken(self.tokens[self.current], self.err)
                enum_tokens.append(self.tokens[self.current])
                self.current += 1
                is_last_token_pipe = False
                continue
        if self.current == ")":
            self.current += 1
        for enum_token in enum_tokens:
            if enum_tokens.count(enum_token) > 1:
                self.err.add(enum_token, CritErr.ATTLIST_ENUM_DUPLICATE_TAGS)
        if len(enum_tokens) < 1:
            return None
        return enum_tokens

    def get_attr_default(self) -> AttrDefault | None:
        if self.current > self.end:
            return None
        if self.tokens[self.current] == "#REQUIRED":
            self.current += 1
            return AttrDefault.REQUIRED
        if self.tokens[self.current] == "#IMPLIED":
            self.current += 1
            return AttrDefault.IMPLIED
        if self.tokens[self.current] == "#FIXED":
            self.current += 1
            return AttrDefault.FIXED
        if self.tokens[self.current].is_quotes():
            return AttrDefault.OPTIONAL
        self.err.add(self.tokens[self.current], CritErr.ATTLIST_DEFAULT_NOT_RECOGNIZED)
        return None

    def get_attr_literal(self) -> Token | None:
        if self.current > self.end:
            return None
        quotes_in_use = self.tokens[self.current]
        self.current += 1
        if self.current > self.end:
            return None
        attr_default = self.tokens[self.current]
        self.current += 1
        if self.current > self.end:
            return attr_default
        if quotes_in_use == attr_default:
            self.current += 1
        return attr_default

    def get_definitions(self) -> None:
        while self.current <= self.end:
            attr_name = self.get_attribute_name()
            if attr_name is None:
                return
            attr_type = self.get_attr_type()
            if attr_type is None:
                return
            attr_enum: list[Token] | None = None
            if attr_type == AttrType.ENUM:
                attr_enum = self.get_attr_enum()
            attr_default = self.get_attr_default()
            if attr_default is None:
                return
            attr_literal: Token | None = None
            if attr_default == AttrDefault.OPTIONAL or attr_default == AttrDefault.FIXED:
                attr_literal = self.get_attr_literal()
            self.attr_defs.append(DtdAttributeDefinition(attr_name, attr_type, attr_enum, attr_default, attr_literal))


class ValidatorDtdEntity:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: None | ValidatorDoctype | ValidatorDtdIncludeIgnore | ValidatorDocument | ValidatorTag = None
        self.name: None | Token = None
        self.intern_value: None | Token = None
        self.extern_system: None | Token = None
        self.extern_public: None | Token = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_name()
        self.verify_and_get_entity_type()

    def __repr__(self):
        if self.name is None:
            return "DtdEntity"
        return f"DtdEntity: {self.name.chars}"

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!ENTITY"):
            self.err.add(self.tokens[self.current], CritErr.DTD_ENTITY_MISSING_START_SEQUENCE)
        else:
            self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            self.err.add(self.tokens[self.end], CritErr.DTD_ENTITY_MISSING_RIGHT_BRACKET, -1)
        else:
            self.end -= 1

    def verify_and_get_name(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.DTD_ENTITY_MISSING_ELEMENT_NAME, -1)
        else:
            self.name = self.tokens[self.current]
            check_xmlname(self.name, self.err)
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

    def verify_and_get_quotes_value(self, identifier: str) -> None | Token:
        quotes_value: None | Token = None
        if self.current > self.end:
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_VALUE,
                -1,
                {identifier: identifier},
            )
            return
        # The left quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_LEFT_QUOTE,
                0,
                {identifier: identifier},
            )
        # The quotes value
        if self.current > self.end or self.tokens[self.current].is_quotes():
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_VALUE,
                0,
                {identifier: identifier},
            )
            return
        else:
            quotes_value = self.tokens[self.current]
            self.current += 1
        # The right quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(
                self.tokens[self.current],
                CritErr.DOCTYPE_IDENTIFIER_MISSING_RIGHT_QUOTE,
                0,
                {identifier: identifier},
            )
        return quotes_value


class ValidatorDtdNotation:
    def __init__(self, tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: None | ValidatorDoctype | ValidatorDtdIncludeIgnore | ValidatorDocument | ValidatorTag = None
        self.notation: None | Token = None
        self.value: None | Token = None
        self.verify_start()
        self.verify_end()
        self.verify_and_get_notation()
        self.verify_and_get_value()
        self.check_trailing()

    def __repr__(self):
        if self.notation is None:
            return "DtdNotation"
        if self.value is None:
            return f"DtdNotation: {self.notation.chars}"
        return f"DtdNotation: {self.notation.chars} {self.value.chars}"

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!NOTATION"):
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_START_SEQUENCE)
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match(">"):
            self.err.add(self.tokens[self.end], CritErr.DTD_NOTATION_MISSING_RIGHT_BRACKET, -1)
            return
        self.end -= 1

    def verify_and_get_notation(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_NAME, -1)
        else:
            self.element = self.tokens[self.current]
            check_xmlname(self.element, self.err)
            self.current += 1

    def verify_and_get_value(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_VALUE, -1)
            return
        # The left quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_VALUE_LEFT_QUOTE)
        # The notation value
        if self.current > self.end or self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_VALUE)
            return
        else:
            self.substitute_text = self.tokens[self.current]
            self.current += 1
        # The right quote
        if self.tokens[self.current].is_quotes():
            self.current += 1
        else:
            self.err.add(self.tokens[self.current], CritErr.DTD_NOTATION_MISSING_NOTATION_VALUE_RIGHT_QUOTE)

    def check_trailing(self) -> None:
        if self.current <= self.end:
            self.err.add(self.tokens[0], CritErr.INVALID_TRAILING_SEQUENCE, -1)


class ValidatorDtdIncludeIgnore:
    def __init__(self, tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.include: bool = False
        self.closed: bool = False
        self.parent: None | ValidatorDoctype | ValidatorDtdIncludeIgnore | ValidatorDocument | ValidatorTag = None
        self.children: list[
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

    def __repr__(self):
        if self.include:
            return "DtdConditional: Include"
        return "DtdConditional: Ignore"

    # def get_active_includeignore(self) -> None | ValidatorDtdIncludeIgnore:
    #     if len(self.children) == 0:
    #         return None
    #     active_includeignore: None | ValidatorDtdIncludeIgnore = None
    #     if isinstance(self.children[-1], ValidatorDtdIncludeIgnore) and not self.children[-1].closed:
    #         active_includeignore = self.children[-1]
    #     else:
    #         return active_includeignore
    #     while len(active_includeignore.children) > 0:
    #         if (
    #             isinstance(active_includeignore.children[-1], ValidatorDtdIncludeIgnore)
    #             and not active_includeignore.children[-1].closed
    #         ):
    #             active_includeignore = active_includeignore.children[-1]
    #         else:
    #             break
    #     return active_includeignore

    def is_ending(self, text: ValidatorParsedText) -> bool:
        if text.content is None:
            return False
        length_to_remove = text.content.search_preceded_by_whitespace("]]>")
        if length_to_remove < 0:
            return False
        text.content.remove_length_from_left(length_to_remove)
        return True

    def is_element_added_to_includeignore(
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
    ) -> bool:
        if self.closed:
            return False
        if len(self.children) > 0 and isinstance(self.children[-1], ValidatorDtdIncludeIgnore):
            if self.children[-1].is_element_added_to_includeignore(element):
                return True
        # if self.current_includeignore is not None:
        #     if isinstance(element, ValidatorDtdIncludeIgnore):
        #         self.current_includeignore.children.append(element)
        #         element.parent = self.current_includeignore
        #         self.current_includeignore = element
        #     elif isinstance(
        #         element,
        #         (
        #             ValidatorDtdElement,
        #             ValidatorDtdAttlist,
        #             ValidatorDtdEntity,
        #             ValidatorDtdNotation,
        #             ValidatorDtdIncludeIgnore,
        #             ValidatorComment,
        #             ValidatorInstructions,
        #         ),
        #     ):
        #         self.current_includeignore.children.append(element)
        #         return True
        #     elif isinstance(element, ValidatorParsedText) and self.is_ending(element):
        #         self.current_includeignore.closed = True
        #         self.current_includeignore = self.current_includeignore.parent
        #         return True
        #     else:
        #         if self.error_collector is not None:
        #             self.error_collector.add_token_start(self.tokens[0], "Dtd conditional was not properly closed.")
        #             if isinstance(element, ValidatorCData):
        #                 self.error_collector.add_token_start(
        #                     element.tokens[0], "Cdata cannot be added to Doctype tree."
        #                 )
        #             if isinstance(element, ValidatorAttribute):
        #                 self.error_collector.add_token_start(element.name, "Attribute cannot be added to Doctype tree.")
        #             if isinstance(element, ValidatorTag):
        #                 self.error_collector.add_token_start(element.tokens[0], "Tag cannot be added to Doctype tree.")
        #             if isinstance(element, ValidatorParsedText):
        #                 self.error_collector.add_token_start(
        #                     element.tokens[0], "Parsed text cannot be added to Doctype tree."
        #                 )
        #             if isinstance(element, ValidatorXmlDeclaration):
        #                 self.error_collector.add_token_start(
        #                     element.tokens[0], "Xml declaration cannot be added to Doctype tree."
        #                 )
        #         return False
        # if isinstance(element, ValidatorDtdIncludeIgnore):
        #     element.parent = self
        #     self.children.append(element)
        #     return True
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
            element.parent = self
            self.children.append(element)
            return True
        if isinstance(element, ValidatorParsedText) and self.is_ending(element):
            self.closed = True
            return True
        self.err.add(self.tokens[0], CritErr.INCLUDEIGNORE_NOT_CLOSED)
        if isinstance(element, ValidatorCData):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_CDATA_IN_TREE)
        if isinstance(element, ValidatorTag):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_TAG_IN_TREE)
        if isinstance(element, ValidatorParsedText):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_PARSED_TEXT_IN_TREE)
        if isinstance(element, ValidatorDoctype):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_DOCTYPE_IN_TREE)
        if isinstance(element, ValidatorXmlDeclaration):
            self.err.add(element.tokens[0], CritErr.INCLUDEIGNORE_XML_DECLARATION_IN_TREE)
        return False

    def verify_start(self) -> None:
        if not self.tokens[self.current].match("<!["):
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_MISSING_START_SEQUENCE)
            return
        self.current += 1

    def verify_end(self) -> None:
        if not self.tokens[self.end].match("]]>"):
            return
        self.closed = True
        self.end -= 1

    def verify_conditional(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_MISSING_CONDITION)
        if self.tokens[self.current].match("INCLUDE"):
            self.include = True
            self.current += 1
        elif self.tokens[self.current].match("IGNORE"):
            self.current += 1
        else:
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_CONDITION_NOT_RECOGNIZED)

    def verify_begin_section(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_CONDITION_START_MISSING)
        if not self.tokens[self.current].match("["):
            self.err.add(self.tokens[self.current], CritErr.INCLUDEIGNORE_CONDITION_START_NOT_RECOGNIZED)
        self.current += 1

    def check_trailing(self) -> None:
        if self.current <= self.end:
            self.err.add(self.tokens[0], CritErr.INVALID_TRAILING_SEQUENCE, -1)


class ValidatorInstructions:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.content: None | Token = None
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: None | ValidatorDocument | ValidatorDtdIncludeIgnore | ValidatorDoctype | ValidatorTag = None
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
        self.err.add(self.tokens[0], CritErr.ELEMENT_MISSING_START_SEQUENCE)

    def verify_end(self) -> None:
        if self.current == self.end:
            self.err.add(self.tokens[-1], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)
            return
        if self.tokens[self.end].match("?>"):
            self.end -= 1
            return
        self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE)

    def verify_and_get_content(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_EMPTY)
            return
        if len(self.tokens[self.current : self.end]) > 1:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_INVALID)
            return
        self.content = self.tokens[self.current]


class ValidatorTag:
    def __init__(
        self,
        element_tokens: list[Token],
        error_collector: ErrorCollector,
    ) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.name: None | Token = None
        self.closed = False
        self.parent: None | ValidatorDocument | ValidatorTag = None
        self.children: list[
            ValidatorTag
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

    def is_element_added_to_tag(
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
    ) -> bool:
        if self.closed:
            return False
        if len(self.children) > 0 and isinstance(self.children[-1], ValidatorDoctype):
            if self.children[-1].is_element_added_to_doctype(element):
                return True
        if len(self.children) > 0 and isinstance(self.children[-1], ValidatorDtdIncludeIgnore):
            if self.children[-1].is_element_added_to_includeignore(element):
                return True
        if len(self.children) > 0 and isinstance(self.children[-1], ValidatorTag):
            if self.children[-1].is_element_added_to_tag(element):
                return True
        if isinstance(
            element,
            (
                ValidatorCData,
                ValidatorComment,
                ValidatorInstructions,
                ValidatorTag,
            ),
        ):
            element.parent = self
            self.children.append(element)
            return True
        if isinstance(element, ValidatorParsedText):
            element.parent = self
            self.children.append(element)
            element.add_to_tree = False
            return True

        if isinstance(element, ValidatorDoctype):
            self.err.add(element.tokens[0], CritErr.TAG_DOCTYPE_IN_TREE)
        if isinstance(element, ValidatorDtdAttlist):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_ATTLIST_IN_TREE)
        if isinstance(element, ValidatorDtdElement):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_ELEMENT_IN_TREE)
        if isinstance(element, ValidatorDtdEntity):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_ENTITY_IN_TREE)
        if isinstance(element, ValidatorDtdNotation):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_NOTATION_IN_TREE)
        if isinstance(element, ValidatorDtdIncludeIgnore):
            self.err.add(element.tokens[0], CritErr.TAG_DTD_INCLUDEIGNORE_IN_TREE)
        if isinstance(element, ValidatorXmlDeclaration):
            self.err.add(element.tokens[0], CritErr.TAG_XML_DECLARATION_IN_TREE)
        element.parent = self
        self.children.append(element)
        return False

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<"):
            self.current += 1
            return
        self.err.add(self.tokens[0], CritErr.ELEMENT_MISSING_START_SEQUENCE)

    def verify_end(self) -> None:
        if self.current == self.end:
            self.err.add(self.tokens[-1], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)
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
            self.err.add(self.tokens[-1], CritErr.ELEMENT_WRONG_END_SEQUENCE, -1)
            return
        self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)

    def close_tag(self, closing_tagname: str) -> bool:
        if self.name is None:
            return False
        if self.name.chars.strip() == closing_tagname.strip():
            self.closed = True
            return True
        return False

    def parse_tagname(self) -> None:
        if self.current > self.end:
            self.err.add(self.tokens[0], CritErr.ELEMENT_NAME_MISSING)
            return
        self.name = self.tokens[self.current]
        check_xmlname(self.name, self.err)
        self.current += 1

    def parse_attribute_value(self) -> None | Token:
        attribute_value: Token | None = None
        if not self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_NOT_IN_QUOTES)
        else:
            self.current += 1
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING)
            return
        if self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING)
            return
        attribute_value = self.tokens[self.current]
        if self.current > self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_NOT_IN_QUOTES)
            return attribute_value
        self.current += 1
        if not self.tokens[self.current].is_quotes():
            self.err.add(attribute_value, CritErr.ELEMENT_VALUE_NOT_IN_QUOTES, -1)
        return attribute_value

    def parse_attributes(self) -> None:
        attribute: None | ValidatorAttribute = None
        while self.current < self.end:
            if self.tokens[self.current].match("="):
                if attribute is None:
                    self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING_NAME)
                    self.current += 1
                    continue
                self.current += 1
                attribute_value = self.parse_attribute_value()
                if attribute_value is not None:
                    # verify_content_or_attribute_value(attribute_value, self.err)
                    attribute.value = attribute_value
                self.current += 1
                continue
            attribute = ValidatorAttribute(self.tokens[self.current], self, self.err)
            self.attributes.append(attribute)
            self.current += 1


class ValidatorParsedText:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.parent: None | ValidatorDocument | ValidatorTag = None
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
            self.err.add(self.tokens[0], CritErr.ELEMENT_INVALID)
            return
        self.content = self.tokens[0]

    def verify_content(self) -> None:
        if self.content is None:
            self.err.add(self.tokens[0], CritErr.ELEMENT_INVALID)
            return
        # verify_content_or_attribute_value(self.content, self.err)

    def __repr__(self):
        if self.content is None:
            return "Empty Text"
        return f"Text: {self.content.chars.strip()}"


class ValidatorXmlDeclaration:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector) -> None:
        self.tokens = element_tokens
        self.err = error_collector
        self.current = 0
        self.end = len(self.tokens) - 1
        self.parent: None | ValidatorDocument | ValidatorTag = None
        self.attributes: list[ValidatorAttribute] = []
        self.verify_start()
        self.verify_end()
        self.parse_attributes()
        self.verify_xml_declaration()

    def __repr__(self):
        return "XmlDeclaration"

    def verify_xml_declaration(self) -> None:
        if not (self.tokens[0].buffer_slot == 0 and self.tokens[0].buffer_pointer == 0):
            self.err.add(self.tokens[0], CritErr.XMLDECL_NOT_FIRST_LINE)
        if len(self.attributes) >= 1:
            self.verify_attribute_version(self.attributes[0])
        if len(self.attributes) >= 2:
            self.verify_attribute_encoding(self.attributes[1])
        if len(self.attributes) >= 3:
            self.verify_attribute_standalone(self.attributes[2])
        if len(self.attributes) > 3:
            self.err.add(self.attributes[3].name, CritErr.XMLDECL_OVER_THREE_ATTRS)

    def verify_attribute_version(self, attribute: ValidatorAttribute) -> None:
        if not attribute.name.match("version"):
            self.err.add(attribute.name, CritErr.XMLDECL_FIRST_ATTR_WRONG)
            return
        if attribute.value is None:
            self.err.add(attribute.name, CritErr.XMLDECL_FIRST_ATTR_MISSING_VALUE, -1)
            return
        if not attribute.value.match("1.0"):
            self.err.add(attribute.value, CritErr.XMLDECL_FIRST_ATTR_NOT_VALID_VALUE)
            return

    def verify_attribute_encoding(self, attribute: ValidatorAttribute) -> None:
        if not attribute.name.match("encoding"):
            self.err.add(attribute.name, CritErr.XMLDECL_SECOND_ATTR_WRONG)
            return
        if attribute.value is None:
            self.err.add(attribute.name, CritErr.XMLDECL_SECOND_ATTR_MISSING_VALUE, -1)
            return
        if attribute.value.chars not in {"UTF-8", "UTF-16"}:
            self.err.add(attribute.value, CritErr.XMLDECL_SECOND_ATTR_NOT_VALID_VALUE)
            return

    def verify_attribute_standalone(self, attribute: ValidatorAttribute) -> None:
        if not attribute.name.match("standalone"):
            self.err.add(attribute.name, CritErr.XMLDECL_THIRD_ATTR_WRONG)
            return
        if attribute.value is None:
            self.err.add(attribute.name, CritErr.XMLDECL_THIRD_ATTR_MISSING_VALUE, -1)
            return
        if attribute.value.chars not in {"yes", "no"}:
            self.err.add(attribute.value, CritErr.XMLDECL_THIRD_ATTR_NOT_VALID_VALUE)
            return

    def verify_start(self) -> None:
        if self.tokens[self.current].match("<?xml"):
            self.current += 1
            return
        self.err.add(self.tokens[0], CritErr.ELEMENT_WRONG_START_SEQUENCE)

    def verify_end(self) -> None:
        if self.current == self.end:
            self.err.add(self.tokens[-1], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)
            return
        if self.tokens[self.end].match("?>"):
            self.end -= 1
            return
        if self.tokens[self.end].endswith(">"):
            self.end -= 1
            self.err.add(self.tokens[-1], CritErr.ELEMENT_WRONG_END_SEQUENCE, -1)
            return
        self.err.add(self.tokens[self.end], CritErr.ELEMENT_MISSING_END_SEQUENCE, -1)

    def parse_attribute_value(self) -> None | Token:
        attribute_value: Token | None = None
        if not self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_NOT_IN_QUOTES)
        else:
            self.current += 1
        if self.current == self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING)
            return
        if self.tokens[self.current].is_quotes():
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING)
            return
        attribute_value = self.tokens[self.current]
        if self.current == self.end:
            self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_NOT_IN_QUOTES)
            return attribute_value
        self.current += 1
        if not self.tokens[self.current].is_quotes():
            self.err.add(attribute_value, CritErr.ELEMENT_VALUE_NOT_IN_QUOTES, -1)
        return attribute_value

    def parse_attributes(self) -> None:
        attribute: None | ValidatorAttribute = None
        while self.current < self.end:
            if self.tokens[self.current].match("="):
                if attribute is None:
                    self.err.add(self.tokens[self.current], CritErr.ELEMENT_VALUE_MISSING_NAME)
                    self.current += 1
                    continue
                self.current += 1
                attribute_value = self.parse_attribute_value()
                if attribute_value is not None:
                    # verify_content_or_attribute_value(attribute_value, self.err)
                    attribute.value = attribute_value
                self.current += 1
                continue
            attribute = ValidatorAttribute(self.tokens[self.current], self, self.err)
            self.attributes.append(attribute)
            self.current += 1


class ValidatorDocument:
    def __init__(self) -> None:
        self.buffer_controller = BufferController()
        self.err = ErrorCollector()
        self.dtd: None | Dtd = None
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

    def read_buffer(self, buffer: str) -> None:
        self.buffer_controller.add_buffer_unit(buffer, "In-memory bufer")

    def read_file(self, filename: str) -> None:
        pass

    def parse_end_tag(self, tokens: list[Token]) -> None:
        # name of a closing tag
        if not tokens[0].match("</"):
            self.err.add(tokens[0], CritErr.ENDTAG_INVALID)
            return
        if len(tokens) == 1:
            self.err.add(tokens[0], CritErr.ENDTAG_INCOMPLETE)
            return
        if len(tokens) == 2:
            if tokens[1].match(">"):
                self.err.add(tokens[1], CritErr.ENDTAG_MISSING_NAME)
                return
            else:
                self.err.add(tokens[1], CritErr.ENDTAG_MISSING_END_SEQUENCE, -1)
        if len(tokens) == 3 and not tokens[2].match(">"):
            self.err.add(tokens[1], CritErr.ENDTAG_INVALID_END_SEQUENCE, -1)
        endtag_name = tokens[1].chars
        # Check for blank spaces in beggining of a name
        active_tag = self.get_active_tag()
        if active_tag is None:
            self.err.add(tokens[1], CritErr.ENDTAG_NOT_MATCH, -1)
            return
        missing_close_tags: list[ValidatorTag] = []
        while isinstance(active_tag, ValidatorTag):
            if active_tag.close_tag(endtag_name):
                if len(missing_close_tags) > 0:
                    for tag in missing_close_tags:
                        if tag.name is not None:
                            self.err.add(tag.name, CritErr.STARTTAG_NOT_MATCH)
                break
            else:
                missing_close_tags.append(active_tag)
                active_tag = active_tag.parent
        if active_tag is None or isinstance(active_tag, ValidatorDocument):
            self.err.add(tokens[1], CritErr.ENDTAG_NOT_MATCH)

    def get_active_tag(self) -> None | ValidatorTag:
        if len(self.children) == 0:
            return None
        active_tag: None | ValidatorTag = None
        if isinstance(self.children[-1], ValidatorTag) and not self.children[-1].closed:
            active_tag = self.children[-1]
        else:
            return None
        while len(active_tag.children) > 0:
            if isinstance(active_tag.children[-1], ValidatorTag) and not active_tag.children[-1].closed:
                active_tag = active_tag.children[-1]
            else:
                break
        return active_tag

    def check_closing_tags(self) -> None:
        active_tag = self.get_active_tag()
        while isinstance(active_tag, ValidatorTag):
            self.err.add(active_tag.tokens[0], CritErr.STARTTAG_NOT_MATCH)
            active_tag = active_tag.parent

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
        if len(self.children) > 0 and isinstance(self.children[-1], ValidatorDoctype):
            if self.children[-1].is_element_added_to_doctype(element):
                return
        if len(self.children) > 0 and isinstance(self.children[-1], ValidatorDtdIncludeIgnore):
            if self.children[-1].is_element_added_to_includeignore(element):
                return
        if len(self.children) > 0 and isinstance(self.children[-1], ValidatorTag):
            if self.children[-1].is_element_added_to_tag(element):
                return
        if isinstance(element, ValidatorParsedText):
            element.add_to_tree = False
        element.parent = self
        self.children.append(element)

    def validate_tag_location(self, tag: ValidatorTag) -> None:
        if isinstance(tag.parent, ValidatorDocument):
            tag_index = tag.parent.children.index(tag)
            is_valid = True
            i = 0
            while i < tag_index:
                if isinstance(tag.parent.children[i], ValidatorTag):
                    is_valid = False
                    break
                i += 1
            if not is_valid:
                self.err.add(tag.tokens[0], CritErr.ONLY_ONE_ROOT)

    def validate_cdata_and_parsedtext_location(self, text: ValidatorCData | ValidatorParsedText) -> None:
        if not isinstance(text.parent, ValidatorDocument) and text.parent is not None:
            return
        if isinstance(text, ValidatorCData):
            self.err.add(text.tokens[0], CritErr.CDATA_NOT_INSIDE_TAG)
            return
        self.err.add(text.tokens[0], CritErr.PARSEDTEXT_NOT_INSIDE_TAG)

    def validate_xmldecl_location(self, xmldecl: ValidatorXmlDeclaration) -> None:
        if isinstance(xmldecl.parent, ValidatorDocument):
            i = xmldecl.parent.children.index(xmldecl)
            if i > 0:
                self.err.add(xmldecl.tokens[0], CritErr.XMLDECL_NOT_FIRST_LINE)
        return

    def validate_doctype_location(self, doctype: ValidatorDoctype) -> None:
        if isinstance(doctype.parent, ValidatorDocument):
            doctype_index = doctype.parent.children.index(doctype)
            is_valid = True
            i = 0
            while i < doctype_index:
                if isinstance(doctype.parent.children[i], ValidatorTag):
                    is_valid = False
                    break
                i += 1
            if not is_valid:
                self.err.add(doctype.tokens[0], CritErr.DOCTYPE_LOCATION)

    def validate_dtd_elements(
        self,
        dtd_element: ValidatorDtdAttlist
        | ValidatorDtdElement
        | ValidatorDtdEntity
        | ValidatorDtdNotation
        | ValidatorDtdIncludeIgnore,
    ) -> None:
        if isinstance(dtd_element.parent, ValidatorDocument):
            self.err.add(dtd_element.tokens[0], CritErr.DTD_ELEMENTS_LOCATION)
        return

    def add_doctype_to_dtd(self, doctype: ValidatorDoctype) -> None:
        if self.dtd is not None:
            self.err.add(doctype.tokens[0], CritErr.DTD_ALREADY_DEFINED)
        self.dtd = Dtd(self.err, doctype.rootname)

    def add_dtdelement_to_dtd(self, dtdelement: ValidatorDtdElement) -> None:
        if self.dtd is None:
            self.dtd = Dtd(self.err, None)
        if dtdelement.element is not None and dtdelement.definition_tokens is not None:
            self.dtd.define_element(dtdelement.element, dtdelement.definition_tokens)

    def validate_tag_in_dtd(self, tag: ValidatorTag) -> None:
        if self.dtd is None:
            return
        if tag.name is not None:
            parsed_element = tag.name
        parsed_child_elements: list[ValidatorTag | ValidatorCData | ValidatorParsedText] = []
        for child in tag.children:
            if isinstance(child, ValidatorTag):
                if child.name is not None:
                    parsed_child_elements.append(child)
                    continue
            if isinstance(child, ValidatorCData):
                parsed_child_elements.append(child)
                continue
            if isinstance(child, ValidatorParsedText):
                parsed_child_elements.append(child)
                continue
        self.dtd.validate_parsed_element_with_element_definitions(parsed_element, parsed_child_elements)

    def build_validation_tree(self) -> None:
        tokens = self.buffer_controller.get_buffer_tokens()
        while tokens is not None:
            match tokens[0].chars:
                case "<?xml":
                    xmldecl = ValidatorXmlDeclaration(tokens, self.err)
                    self.add_element_to_validation_tree(xmldecl)
                    self.validate_xmldecl_location(xmldecl)
                case "<![CDATA[":
                    cdata = ValidatorCData(tokens, self.err)
                    self.add_element_to_validation_tree(cdata)
                    self.validate_cdata_and_parsedtext_location(cdata)
                case "<!DOCTYPE":
                    doctype = ValidatorDoctype(tokens, self.err)
                    self.add_element_to_validation_tree(doctype)
                    self.add_doctype_to_dtd(doctype)
                    self.validate_doctype_location(doctype)
                case "<!ELEMENT":
                    dtd_element = ValidatorDtdElement(tokens, self.err)
                    self.add_element_to_validation_tree(dtd_element)
                    self.add_dtdelement_to_dtd(dtd_element)
                    self.validate_dtd_elements(dtd_element)
                case "<!ATTLIST":
                    dtd_attlist = ValidatorDtdAttlist(tokens, self.err)
                    self.add_element_to_validation_tree(dtd_attlist)
                    self.validate_dtd_elements(dtd_attlist)
                case "<!NOTATION":
                    dtd_notation = ValidatorDtdNotation(tokens, self.err)
                    self.add_element_to_validation_tree(dtd_notation)
                    self.validate_dtd_elements(dtd_notation)
                case "<!ENTITY":
                    dtd_entity = ValidatorDtdEntity(tokens, self.err)
                    self.add_element_to_validation_tree(dtd_entity)
                    self.validate_dtd_elements(dtd_entity)
                case "<![":
                    dtd_includeignore = ValidatorDtdIncludeIgnore(tokens, self.err)
                    self.add_element_to_validation_tree(dtd_includeignore)
                    self.validate_dtd_elements(dtd_includeignore)
                case "<?":
                    instructions = ValidatorInstructions(tokens, self.err)
                    self.add_element_to_validation_tree(instructions)
                case "<!--":
                    comment = ValidatorComment(tokens, self.err)
                    self.add_element_to_validation_tree(comment)
                case "</":
                    self.parse_end_tag(tokens)
                case "<":
                    tag = ValidatorTag(tokens, self.err)
                    self.add_element_to_validation_tree(tag)
                    self.validate_tag_location(tag)
                case _:
                    parsedtext = ValidatorParsedText(tokens, self.err)
                    while not parsedtext.is_empty() and parsedtext.add_to_tree:
                        self.add_element_to_validation_tree(parsedtext)
                    if not parsedtext.is_empty:
                        parsedtext.verify_content()
                        self.validate_cdata_and_parsedtext_location(parsedtext)
            tokens = self.buffer_controller.get_buffer_tokens()
        self.check_closing_tags()

    def print_tree(
        self,
        element: (
            None
            | ValidatorTag
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
            | ValidatorXmlDeclaration
        ) = None,
        indent: int = 0,
    ) -> None:
        if element is None:
            for child in self.children:
                print(f"{child.__repr__().strip()}")
                self.print_tree(child, indent + 1)
        if isinstance(element, ValidatorDoctype | ValidatorTag | ValidatorDtdIncludeIgnore):
            for child in element.children:
                num_indents = (indent * 2 - 1) * "-"
                print(f"|{num_indents}{child}")
                self.print_tree(child, indent + 1)


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
    <!ELEMENT first_name ((#PCDATA | title), (paragraph | image)*)>
    <!ELEMENT title (#PCDATA)>
    <!ELEMENT paragraph (#PCDATA)>
    <!ELEMENT image EMPTY>
    <!ATTLIST image src CDATA #REQUIRED>
]>
<person>
    <first_name>
        Dr. <!-- #PCDATA allowed here -->
        <title>John</title> <!-- Title allowed -->
        <paragraph>Brief introduction about John.</paragraph>
        <image src="john.png"/>
        <paragraph>More details about John's background.</paragraph>
    </first_name>
</person>"""

simple_dtd = """<!DOCTYPE person [
    <!ELEMENT person (name, age?, address)*>
]>
<person>
    <name>John Doe</name>
    <age>30</age>
    <address>123 Main St</address>
    <name>John Doe</name>

</person>"""

dtd1 = """<!DOCTYPE person [
    <!ELEMENT person (name,address)*>
]>
<person>
    <name>John Doe</name>
    <address>123 Main St</address>
    <name>John Doe</name>
    <address>123 Main St</address>
</person>"""

dtd_choice = """<!DOCTYPE person [
    <!ELEMENT person (a|b)*>
]>
<person>
    <b>John Doe</b>
    <a>John Doe</a>
    <c>John Doe</c>
    <b>John Doe</b>
    <a>John Doe</a>
</person>"""

dtd_sequence = """<!DOCTYPE test [
    <!ELEMENT test ((e1 | (e2 , (e3 | (e4 , e5*)))), e6)>
]>
<test>
    <e2></e2>
    <e4></e4>
    <e5></e5>
    <e5></e5>
    <e6></e6>
</test>"""

xmlvalidator = ValidatorDocument()
xmlvalidator.read_buffer(dtd_sequence)
xmlvalidator.build_validation_tree()
if isinstance(xmlvalidator.children[1], ValidatorTag) and isinstance(
    xmlvalidator.children[1].children[0], ValidatorTag
):
    tag = xmlvalidator.children[1]
print(xmlvalidator.validate_tag_in_dtd(tag))
# xmlvalidator.print_tree()
print()
