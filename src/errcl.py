from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from xmltokens import XmlChars


class CritErr(Enum):
    # Well-formedness
    # Mismatched tags, unclosed elements, invalid attribute syntax
    MIXED_PARENTHESIS = "Mixed content must be enclosed in parentheses."
    MIXED_PCDATA = "Mixed content must always begin with #PCDATA."
    MIXED_PCDATA_END_STAR = "Mixed content definition must end with * when defining both #PCDATA and tags."
    MIXED_SEQ_PIPE = "Mixed content definition contains 2 or more | sequential characters."
    MIXED_PIPE_SEPARATION = "Mixed content definition must separate elements with | character."
    MIXED_SINGLE_PCDATA_TAG = "Mixed content definition must contain only one #PCDATA and tag definitions."
    MIXED_DUPLICATE_TAGS = "Mixed content definition contains duplicate tag definitions."
    ELEMENT_MISSING_START_SEQUENCE = "Element is missing start sequence."
    ELEMENT_MISSING_END_SEQUENCE = "Element is missing end sequence."
    ELEMENT_WRONG_START_SEQUENCE = "Element has a wrong start sequence."
    ELEMENT_WRONG_END_SEQUENCE = "Element has a wrong end sequence."
    ELEMENT_EMPTY = "Empty element."
    ELEMENT_INVALID = "Invalid element structure."
    ELEMENT_NAME_MISSING = "Element name is missing."
    ELEMENT_VALUE_MISSING = "Element value is missing."
    ELEMENT_VALUE_NOT_IN_QUOTES = "Element values must be enclosed in quotes."
    ELEMENT_VALUE_MISSING_NAME = "Missing element name to attach the value."
    DOCTYPE_NOT_CLOSED = "Doctype tree was not properly closed."
    DOCTYPE_CDATA_IN_TREE = "Cdata cannot be added to Doctype tree."
    DOCTYPE_TAG_IN_TREE = "Tag cannot be added to Doctype tree."
    DOCTYPE_PARSED_TEXT_IN_TREE = "Parsed text cannot be added to Doctype tree."
    DOCTYPE_DOCTYPE_IN_TREE = "Doctype cannot be added to Doctype tree."
    DOCTYPE_XML_DECLARATION_IN_TREE = "XML declaration cannot be added to Doctype tree."
    DOCTYPE_MISSING_START_SEQUENCE = "Doctype is missing starting sequence."
    DOCTYPE_MISSING_ROOT_CLOSING = "Doctype is missing root element and closing sequence."
    DOCTYPE_IDENTIFIER_MISSING_VALUE = "{{identifier}} value is missing."
    DOCTYPE_IDENTIFIER_MISSING_LEFT_QUOTE = "{{identifier}} value is missing left quote."
    DOCTYPE_IDENTIFIER_MISSING_RIGHT_QUOTE = "{{identifier}} value is missing right quote."
    DOCTYPE_INVALID_INTERNAL_DEF_START = "Invalid start of internal definitions."
    DOCTYPE_INVALID_INTERNAL_DEF_END = "Invalid end of internal definitions."
    INVALID_TRAILING_SEQUENCE = "Invalid trailing sequence found."
    DTD_ELEMENT_MISSING_START_SEQUENCE = "Dtd ELEMENT is missing starting sequence."
    DTD_ELEMENT_MISSING_RIGHT_BRACKET = "Dtd ELEMENT is missing right angle bracket."
    DTD_ELEMENT_MISSING_NAME = "Dtd ELEMENT is missing element name for validation."
    DTD_ATTLIST_MISSING_START_SEQUENCE = "Dtd ATTLIST tag is missing starting sequence."
    DTD_ATTLIST_MISSING_RIGHT_BRACKET = "Dtd ATTLIST tag is missing right angle bracket."
    DTD_ATTLIST_MISSING_ELEMENT_NAME = "Dtd ATTLIST tag is missing element name for validation."
    DTD_ATTLIST_MISSING_ATTRIBUTE_NAME = "Dtd ATTLIST tag is missing attribute name for validation."
    DTD_ENTITY_MISSING_START_SEQUENCE = "Dtd ENTITY tag is missing starting sequence."
    DTD_ENTITY_MISSING_RIGHT_BRACKET = "Dtd ENTITY tag is missing right angle bracket."
    DTD_ENTITY_MISSING_ELEMENT_NAME = "Dtd ENTITY tag is missing entity name."
    DTD_NOTATION_MISSING_START_SEQUENCE = "Dtd NOTATION tag is missing starting sequence."
    DTD_NOTATION_MISSING_RIGHT_BRACKET = "Dtd NOTATION tag is missing right angle bracket."
    DTD_NOTATION_MISSING_NOTATION_NAME = "Dtd NOTATION tag is missing notation name."
    DTD_NOTATION_MISSING_NOTATION_VALUE = "Dtd NOTATION tag is missing notation value."
    DTD_NOTATION_MISSING_NOTATION_VALUE_LEFT_QUOTE = "Dtd NOTATION tag is missing notation value's left quote."
    DTD_NOTATION_MISSING_NOTATION_VALUE_RIGHT_QUOTE = "Dtd NOTATION tag is missing notation value's right quote."
    INCLUDEIGNORE_NOT_CLOSED = "Dtd conditional block was not properly closed."
    INCLUDEIGNORE_CDATA_IN_TREE = "Cdata cannot be added to Dtd conditional block ."
    INCLUDEIGNORE_TAG_IN_TREE = "Tag cannot be added to Dtd conditional block ."
    INCLUDEIGNORE_PARSED_TEXT_IN_TREE = "Parsed text cannot be added to Dtd conditional block ."
    INCLUDEIGNORE_DOCTYPE_IN_TREE = "Doctype cannot be added to Dtd conditional block ."
    INCLUDEIGNORE_XML_DECLARATION_IN_TREE = "XML declaration cannot be added to Dtd conditional block ."
    INCLUDEIGNORE_MISSING_START_SEQUENCE = "Dtd conditional block is missing starting sequence."
    INCLUDEIGNORE_MISSING_CONDITION = "Dtd conditional block is missing condition."
    INCLUDEIGNORE_CONDITION_NOT_RECOGNIZED = "Dtd conditional sequence is not recognized."
    INCLUDEIGNORE_CONDITION_START_MISSING = (
        "Left square bracket is missing for the start of definitions in dtd conditional section."
    )
    INCLUDEIGNORE_CONDITION_START_NOT_RECOGNIZED = "Start of definitions in conditional section is not recognized."
    TAG_DOCTYPE_IN_TREE = "DOCTYPE must be outside TAG element and added before root TAG element."
    TAG_DTD_ELEMENT_IN_TREE = "ELEMENT must be inside DOCTYPE element."
    TAG_DTD_ATTLIST_IN_TREE = "ATTLIST must be inside DOCTYPE element."
    TAG_DTD_ENTITY_IN_TREE = "ENTITY must be inside DOCTYPE element."
    TAG_DTD_NOTATION_IN_TREE = "NOTATION must be inside DOCTYPE element."
    TAG_DTD_INCLUDEIGNORE_IN_TREE = "Dtd conditional must be inside DOCTYPE element."
    TAG_XML_DECLARATION_IN_TREE = "XML declaration cannot be added to TAG element."
    XMLDECL_NOT_FIRST_LINE = "XML declaration must be the on the first line."
    XMLDECL_OVER_THREE_ATTRS = "Only three atributtes are allowed: version, encoding and standalone."
    XMLDECL_FIRST_ATTR_WRONG = "The first attribute in declaration must be the value attribute."
    XMLDECL_FIRST_ATTR_MISSING_VALUE = "The first attribute is missing its value."
    XMLDECL_FIRST_ATTR_NOT_VALID_VALUE = "Only the version 1.0 is supported."
    XMLDECL_SECOND_ATTR_WRONG = "The second attribute in declaration must be the encoding attribute."
    XMLDECL_SECOND_ATTR_MISSING_VALUE = "The second attribute is missing its value."
    XMLDECL_SECOND_ATTR_NOT_VALID_VALUE = "Only the UTF-8 and UTF-16 encodings are supported."
    XMLDECL_THIRD_ATTR_WRONG = "The third attribute in declaration must be the standalone attribute."
    XMLDECL_THIRD_ATTR_MISSING_VALUE = "The third attribute is missing its value."
    XMLDECL_THIRD_ATTR_NOT_VALID_VALUE = "Only the yes and no values are allowed for the standalone attribute."
    ENDTAG_INVALID = "End tag invalid."
    ENDTAG_INCOMPLETE = "End tag is incomplete."
    ENDTAG_MISSING_NAME = "End tag is missing tag name."
    ENDTAG_MISSING_END_SEQUENCE = "End tag is missing closing sequence."
    ENDTAG_INVALID_END_SEQUENCE = "End tag has invalid closing sequence."
    ENDTAG_NOT_MATCH = "End tag not matching any start tag."
    STARTTAG_NOT_MATCH = "The tag is missing its closing tag."
    ONLY_ONE_ROOT = "Only one root tag is allowed."
    CDATA_NOT_INSIDE_TAG = "Cdata sections can be only inside a tag element."
    PARSEDTEXT_NOT_INSIDE_TAG = "Parsed text can be only inside a tag element."
    DOCTYPE_LOCATION = "Doctype must come after either xml declaration,comments or instructions."
    DTD_ELEMENTS_LOCATION = "Dtd elements must be inside Doctype section."
    DTD_ALREADY_DEFINED = "Dtd is already defined."
    XMLNAME_ERROR = (
        "XML Name value must begin with a letter or an underscore(_) followed by any number of letters, "
        "digits, periods(.), hyphens(-), underscores or colons (:)."
    )
    NMTOKEN_ERROR = (
        "Nmtoken value can be any combination of letters, digits, periods(.), hyphens(-), underscores or colons (:)."
    )
    ATTIBUTE_VALUE_ERROR = "Attribute value cannot contain left angle bracket (<) or ampersand (&)."
    ENTITY_VALUE_ERROR = "Entity value cannot contain percent sign (%) or ampersand (&)."
    PUBID_LITERAL_ERROR = (
        "Public Literal can be any combination of space (0x20), carriage return (0x0D), line feed (0x0A), "
        "alphanumeric characters (a-zA-Z0-9) and punctuation characters (-'\"()+,./:=?;!*#@$_%)."
    )
    ATTLIST_ENUM_SEQ_PIPE = "Attribute enumeration contains 2 or more | sequential characters."
    ATTLIST_ENUM_PIPE_SEPARATION = "Attribute enumeration must separate elements with | character."
    ATTLIST_ENUM_DUPLICATE_TAGS = "Attribute enumeration contains duplicate attribute name definitions."
    ATTLIST_DEFAULT_NOT_RECOGNIZED = "Attribute default value is not recognized."
    ATTLIST_TYPE_NOT_RECOGNIZED = "Attribute type is not recognized"


class ValidErr(Enum):
    # DTD Conformance
    # Order violations, missing elements, attribute constraint violations
    MIXED_UNDEFINED_TAG = "Tag is not defined in mixed content definition."
    NON_DETERMINISTIC_DUPLICATES = (
        "Detected non-deterministic content model, duplicate references were found in definition."
    )
    UNDEFINED_ELEMENT = "Element not defined."
    INCOMPLETE_DEFINITION = "Not all requirements in definition are met."
    ELEMENT_ALREADY_DEFINED = "Element is defined already."
    ELEMENT_NO_DEFINITION = "Element does not have any definitions."
    NO_PARSED_TEXT_IN_CONTENT = "Parsed text data is not allowed in element content definition."


class ErrorToken:
    def __init__(
        self,
        xmlchars: XmlChars,
        err: CritErr | ValidErr,
        intoken_pointer: int,
        options: dict[str, str] | None,
    ) -> None:
        self.xmlchars = xmlchars
        self.err = err
        if intoken_pointer < -1:
            raise ValueError("Values lesser than -1 are not allowed.")
        if intoken_pointer == -1:
            self.intoken_pointer = len(xmlchars.strchars) - 1
        else:
            self.intoken_pointer = intoken_pointer
        self.options = options


class ErrorCollector:
    def __init__(self) -> None:
        self.tokens: list[ErrorToken] = []
        # self.buffer_slot: dict[int, list[tuple[int, str]]] = {}

    def add(
        self,
        xmlchars: XmlChars,
        error: CritErr | ValidErr,
        intoken_pointer: int = 0,
        options: dict[str, str] | None = None,
    ) -> None:
        if intoken_pointer < -1:
            raise ValueError("Values lesser than -1 are not allowed.")
        if intoken_pointer == -1:
            self.tokens.append(ErrorToken(xmlchars, error, len(xmlchars.strchars) - 1, options))
        else:
            self.tokens.append(ErrorToken(xmlchars, error, intoken_pointer, options))
