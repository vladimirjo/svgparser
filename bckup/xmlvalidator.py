from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer import Token

from buffer import BufferController
from dtd import DtdCore
from errorcollector import CritErr
from errorcollector import ErrorCollector
from xmlstruct import Attlist
from xmlstruct import CData
from xmlstruct import Comment
from xmlstruct import Doctype
from xmlstruct import Element
from xmlstruct import Entity
from xmlstruct import IncludeIgnore
from xmlstruct import Instructions
from xmlstruct import Notation
from xmlstruct import ParsedText
from xmlstruct import Tag
from xmlstruct import XmlDeclaration


class XmlValidator:
    def __init__(self) -> None:
        self.buffer_controller = BufferController()
        self.err = ErrorCollector()
        self.dtd: DtdCore | None = None
        self.children: list[
            Tag
            | CData
            | Comment
            | Doctype
            | Element
            | Attlist
            | Entity
            | Notation
            | IncludeIgnore
            | Instructions
            | ParsedText
            | XmlDeclaration
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
        missing_close_tags: list[Tag] = []
        while isinstance(active_tag, Tag):
            if active_tag.close_tag(endtag_name):
                if len(missing_close_tags) > 0:
                    for tag in missing_close_tags:
                        if tag.name is not None:
                            self.err.add(tag.name, CritErr.STARTTAG_NOT_MATCH)
                break
            else:
                missing_close_tags.append(active_tag)
                active_tag = active_tag.parent
        if active_tag is None or isinstance(active_tag, XmlValidator):
            self.err.add(tokens[1], CritErr.ENDTAG_NOT_MATCH)

    def get_active_tag(self) -> None | Tag:
        if len(self.children) == 0:
            return None
        active_tag: None | Tag = None
        if isinstance(self.children[-1], Tag) and not self.children[-1].closed:
            active_tag = self.children[-1]
        else:
            return None
        while len(active_tag.children) > 0:
            if isinstance(active_tag.children[-1], Tag) and not active_tag.children[-1].closed:
                active_tag = active_tag.children[-1]
            else:
                break
        return active_tag

    def check_closing_tags(self) -> None:
        active_tag = self.get_active_tag()
        while isinstance(active_tag, Tag):
            self.err.add(active_tag.tokens[0], CritErr.STARTTAG_NOT_MATCH)
            active_tag = active_tag.parent

    def add_node_to_validation_tree(
        self,
        element: Tag
        | CData
        | Comment
        | Doctype
        | Element
        | Attlist
        | Notation
        | Entity
        | IncludeIgnore
        | Instructions
        | ParsedText
        | XmlDeclaration,
    ) -> None:
        if len(self.children) > 0 and isinstance(self.children[-1], Doctype):
            if self.children[-1].is_element_added_to_doctype(element):
                return
        if len(self.children) > 0 and isinstance(self.children[-1], IncludeIgnore):
            if self.children[-1].is_element_added_to_includeignore(element):
                return
        if len(self.children) > 0 and isinstance(self.children[-1], Tag):
            if self.children[-1].is_element_added_to_tag(element):
                return
        if isinstance(element, ParsedText):
            element.add_to_tree = False
        element.parent = self
        self.children.append(element)

    def validate_tag_location(self, tag: Tag) -> None:
        if isinstance(tag.parent, XmlValidator):
            tag_index = tag.parent.children.index(tag)
            is_valid = True
            i = 0
            while i < tag_index:
                if isinstance(tag.parent.children[i], Tag):
                    is_valid = False
                    break
                i += 1
            if not is_valid:
                self.err.add(tag.tokens[0], CritErr.ONLY_ONE_ROOT)

    def validate_cdata_and_parsedtext_location(self, text: CData | ParsedText) -> None:
        if not isinstance(text.parent, XmlValidator) and text.parent is not None:
            return
        if isinstance(text, CData):
            self.err.add(text.tokens[0], CritErr.CDATA_NOT_INSIDE_TAG)
            return
        self.err.add(text.tokens[0], CritErr.PARSEDTEXT_NOT_INSIDE_TAG)

    def validate_xmldecl_location(self, xmldecl: XmlDeclaration) -> None:
        if isinstance(xmldecl.parent, XmlValidator):
            i = xmldecl.parent.children.index(xmldecl)
            if i > 0:
                self.err.add(xmldecl.tokens[0], CritErr.XMLDECL_NOT_FIRST_LINE)
        return

    def validate_doctype_location(self, doctype: Doctype) -> None:
        if isinstance(doctype.parent, XmlValidator):
            doctype_index = doctype.parent.children.index(doctype)
            is_valid = True
            i = 0
            while i < doctype_index:
                if isinstance(doctype.parent.children[i], Tag):
                    is_valid = False
                    break
                i += 1
            if not is_valid:
                self.err.add(doctype.tokens[0], CritErr.DOCTYPE_LOCATION)

    def validate_dtd_elements(
        self,
        dtd_element: Attlist | Element | Entity | Notation | IncludeIgnore,
    ) -> None:
        if isinstance(dtd_element.parent, XmlValidator):
            self.err.add(dtd_element.tokens[0], CritErr.DTD_ELEMENTS_LOCATION)
        return

    def add_doctype_to_dtd(self, doctype: Doctype) -> None:
        if self.dtd is None:
            self.dtd = DtdCore(self.err, doctype.rootname)
        else:
            self.err.add(doctype.tokens[0], CritErr.DTD_ALREADY_DEFINED)

    def add_element_to_dtd(self, element: Element) -> None:
        if self.dtd is None:
            # error dtd not defined with doctype
            self.dtd = DtdCore(self.err, None)
        if element.element is not None and element.definition_tokens is not None:
            self.dtd.define_element(element.element, element.definition_tokens)

    def add_attlist_to_dtd(self, attlist: Attlist) -> None:
        pass

    def validate_tag_in_dtd(self, tag: Tag) -> None:
        if self.dtd is None:
            return
        if tag.name is not None:
            parsed_element = tag.name
        parsed_child_elements: list[Tag | CData | ParsedText] = []
        for child in tag.children:
            if isinstance(child, Tag):
                if child.name is not None:
                    parsed_child_elements.append(child)
                    continue
            if isinstance(child, CData):
                parsed_child_elements.append(child)
                continue
            if isinstance(child, ParsedText):
                parsed_child_elements.append(child)
                continue
        self.dtd.validate_parsed_element_with_element_definitions(parsed_element, parsed_child_elements)

    def build_validation_tree(self) -> None:
        tokens = self.buffer_controller.get_buffer_tokens()
        while tokens is not None:
            match tokens[0].chars:
                case "<?xml":
                    xmldecl = XmlDeclaration(tokens, self.err)
                    self.add_node_to_validation_tree(xmldecl)
                    self.validate_xmldecl_location(xmldecl)
                case "<![CDATA[":
                    cdata = CData(tokens, self.err)
                    self.add_node_to_validation_tree(cdata)
                    self.validate_cdata_and_parsedtext_location(cdata)
                case "<!DOCTYPE":
                    doctype = Doctype(tokens, self.err)
                    self.add_node_to_validation_tree(doctype)
                    self.add_doctype_to_dtd(doctype)
                    self.validate_doctype_location(doctype)
                case "<!ELEMENT":
                    dtd_element = Element(tokens, self.err)
                    self.add_node_to_validation_tree(dtd_element)
                    self.add_element_to_dtd(dtd_element)
                    self.validate_dtd_elements(dtd_element)
                case "<!ATTLIST":
                    dtd_attlist = Attlist(tokens, self.err)
                    self.add_node_to_validation_tree(dtd_attlist)
                    self.validate_dtd_elements(dtd_attlist)
                case "<!NOTATION":
                    dtd_notation = Notation(tokens, self.err)
                    self.add_node_to_validation_tree(dtd_notation)
                    self.validate_dtd_elements(dtd_notation)
                case "<!ENTITY":
                    dtd_entity = Entity(tokens, self.err)
                    self.add_node_to_validation_tree(dtd_entity)
                    self.validate_dtd_elements(dtd_entity)
                case "<![":
                    dtd_includeignore = IncludeIgnore(tokens, self.err)
                    self.add_node_to_validation_tree(dtd_includeignore)
                    self.validate_dtd_elements(dtd_includeignore)
                case "<?":
                    instructions = Instructions(tokens, self.err)
                    self.add_node_to_validation_tree(instructions)
                case "<!--":
                    comment = Comment(tokens, self.err)
                    self.add_node_to_validation_tree(comment)
                case "</":
                    self.parse_end_tag(tokens)
                case "<":
                    tag = Tag(tokens, self.err)
                    self.add_node_to_validation_tree(tag)
                    self.validate_tag_location(tag)
                case _:
                    parsedtext = ParsedText(tokens, self.err)
                    while not parsedtext.is_empty() and parsedtext.add_to_tree:
                        self.add_node_to_validation_tree(parsedtext)
                    if not parsedtext.is_empty:
                        parsedtext.verify_content()
                        self.validate_cdata_and_parsedtext_location(parsedtext)
            tokens = self.buffer_controller.get_buffer_tokens()
        self.check_closing_tags()

    def print_tree(
        self,
        element: (
            Tag
            | CData
            | Comment
            | Doctype
            | Element
            | Attlist
            | Notation
            | Entity
            | IncludeIgnore
            | Instructions
            | ParsedText
            | XmlDeclaration
            | None
        ) = None,
        indent: int = 0,
    ) -> None:
        if element is None:
            for child in self.children:
                print(f"{child.__repr__().strip()}")
                self.print_tree(child, indent + 1)
        if isinstance(element, Doctype | Tag | IncludeIgnore):
            for child in element.children:
                num_indents = (indent * 2 - 1) * "-"
                print(f"|{num_indents}{child}")
                self.print_tree(child, indent + 1)
