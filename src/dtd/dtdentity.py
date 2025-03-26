from __future__ import annotations

from typing import TYPE_CHECKING
from typing import NamedTuple

from xmlstruct import entity


if TYPE_CHECKING:
    from errcl import ErrorCollector

from errcl import CritErr
from xmltokens import XmlChar
from xmltokens import XmlCharRef
from xmltokens import XmlChars
from xmltokens import XmlProccesor


# id=1 reserved for main file
# id=2 reserved for external subset file
# id>2 all other entities

class GeneralEntity(NamedTuple):
    name: str
    entity_id: int
    is_predefined: bool
    system_id: str | None
    public_id: str | None
    ndata: str | None
    replacement_text: XmlChars | None


class ParameterEntity(NamedTuple):
    name: str
    entity_id: int
    is_predifined: bool
    system_id: str | None
    public_id: str | None
    replacement_text: XmlChars


class DtdEntity:
    def __init__(self, err: ErrorCollector) -> None:
        self.err = err
        self.gents: dict[str, GeneralEntity] = {}
        self.pents: dict[str, ParameterEntity] = {}
        self.idcnt = 2
        for predef_gent in [
            ("lt", "&#38;#60;"),
            ("gt", "&#62;"),
            ("amp", "&#38;#38;"),
            ("apos", "&#39;"),
            ("quot", "&#34;")
         ]:
            self.register_gent(predef_gent[0], predef_gent[1], True)

    def get_next_id(self) -> int:
        self.idcnt += 1
        return self.idcnt

    def register_gent(
        self,
        name: str | XmlChars,
        replacement_text: str | XmlChars,
        is_predefined: bool,
        system_id: str | None = None,
        public_id: str | None = None,
        ndata: str | None = None
        ) -> None:
        if isinstance(name, str):
            name = XmlChars(*[XmlChar(char, -1, -1, -1) for char in name])
        if name.strchars in self.gents:
            self.err.add(name, CritErr.ENTITY_ALREADY_REGISTERED)
            return
        if isinstance(replacement_text, str):
            replacement_text = XmlChars(*[XmlChar(char, -1, -1, -1) for char in replacement_text])
        else:
            replacement_text = replacement_text.copy_with_new_entity_id(-1)
        calling_stack = [-1]
        proc = XmlProccesor(replacement_text)
        while not proc.is_end():
            if proc.read() == "&":
                # parse charref
                chrref = proc.get_chrref()
                if chrref is not None:
                    chrref_value = self.get_chrref_value(chrref)
                    if chrref_value is not None:
                        proc.ins_repl_text(len(chrref.xmlchars), chrref_value)
                        proc.move(len(chrref.xmlchars))
                        continue
                # bypass without parsing gent
                sub_gent_ref = proc.get_gent_ref()
                if sub_gent_ref is not None:
                    if sub_gent_ref.strchars in self.gents:
                        proc.move(len(sub_gent_ref))
                    else:
                        # generate error gent not recognized
                        proc.move()
                    continue
                else:
                    # generate error invalid usage of ampersand
                    pass
            if proc.read() == "%":
                # parse pent
                sub_pent_ref = proc.get_pent_ref()
                if sub_pent_ref is not None:
                    new_entity_id = proc.xmlchars.get_entity_id()
                    resolved_pent = self.deref_pent(sub_pent_ref, calling_stack)
                    if resolved_pent is None:
                        proc.move()
                        continue
                    resolved_pent_new_id = resolved_pent.copy_with_new_entity_id(new_entity_id)
                    proc.ins_repl_text(len(sub_pent_ref), resolved_pent_new_id)
                    proc.move(len(sub_pent_ref))
                    continue
                else:
                    # error invalid usage of procent sign
                    proc.move()
                    continue
            proc.move()
        entity_id = self.get_next_id()
        proc.xmlchars.add_entity_id(entity_id)
        self.gents[name.strchars] = GeneralEntity(name.strchars, entity_id, is_predefined, system_id, public_id, ndata, proc.xmlchars,)



    # def get_gent_name(self, gent_ref: XmlChars) -> XmlChars | None:
    #     if gent_ref.strchars[0] != "&":
    #         return None
    #     if gent_ref.strchars[-1] != ";":
    #         return None
    #     return XmlChars(*gent_ref.xmlchars[1:-1])

    # def get_pent_name(self, pent_ref: XmlChars) -> XmlChars | None:
    #     if pent_ref.strchars[0] != "%":
    #         return None
    #     if pent_ref.strchars[-1] != ";":
    #         return None
    #     return XmlChars(*pent_ref.xmlchars[1:-1])

    def get_chrref_value(self, chrref: XmlChars) -> XmlChars | None:
        if chrref.strchars[0:2] != "&#":
            return None
        if chrref.strchars[-1] != ";":
            return None
        if chrref.xmlchars[2] == "x":
            chrref_hexdec = XmlChars(*chrref.xmlchars[3:-1])
            is_hex = True
        else:
            chrref_hexdec = XmlChars(*chrref.xmlchars[2:-1])
            is_hex = False
        try:
            char_code = int(chrref_hexdec.strchars, 16 if is_hex else 10)
            xmlchars = XmlChars(XmlCharRef(chr(char_code), *chrref.xmlchars))
            return xmlchars
        except ValueError:
            return None

    def create_xmlchar_for_predef(self, repl_text: str, gent_ref: XmlChars) -> XmlChars:
        buffer_slot = gent_ref.xmlchars[0].get_buffer_slot()
        buffer_pos = gent_ref.xmlchars[0].get_buffer_pos()
        entity_id = 0
        xmlchars_arr: list[XmlChar] = [XmlChar(char, buffer_slot, buffer_pos, entity_id) for char in repl_text]
        return XmlChars(*xmlchars_arr)

    # def get_gent_repl(self, gent_ref: XmlChars) -> GeneralEntity | None:
    #     gent_name = gent_ref.strchars[1:-1]
    #     if gent_name in self.gents_predef:
    #         repl_text = self.gents_predef[gent_name]
    #         return GeneralEntity(0, None, None, None, self.create_xmlchar_for_predef(repl_text, gent_ref))
    #     if gent_name in self.gents:
    #         return self.gents[gent_name]
    #     return None

    def deref_gent(self, gent_ref: XmlChars, calling_stack: list[int] | None = None) -> XmlChars | None:
        gent_repl = self.get_gent_repl(gent_ref)
        if gent_repl is None:
            # generate not found gent name in predifined entities
            return None
        # # check for recursion
        if calling_stack is None:
            calling_stack = []
        if calling_stack.count(gent_repl.entity_id) > 0:
            # generate entity recursion error
            raise ValueError("Entity Recursion")
        else:
            calling_stack.append(gent_repl.entity_id)
        # no parsing of external entity
        if gent_repl.system_id is not None:
            return gent_repl.replacement_text
        # check for ndata entity
        if gent_repl.replacement_text is None:
            raise ValueError("Ndata not allowed.")
        # parsing of internal entity
        proc = XmlProccesor(gent_repl.replacement_text)
        while not proc.is_end():
            # parse charref
            chrref = proc.get_chrref()
            if chrref is not None:
                chrref_value = self.get_chrref_value(chrref)
                if chrref_value is not None:
                    proc.ins_repl_text(len(chrref.xmlchars), chrref_value)
                    proc.move(len(chrref.xmlchars))
                    continue
            # parse gent
            sub_gent_ref = proc.get_gent_ref()
            if sub_gent_ref is None:
                # generate error
                pass
            else:
                new_entity_id = proc.xmlchars.get_entity_id()
                resolved_gent = self.deref_gent(sub_gent_ref, calling_stack)
                if resolved_gent is None:
                    # generate error
                    proc.move()
                    continue
                resolved_gent_new_id = resolved_gent.copy_with_new_entity_id(new_entity_id)
                proc.ins_repl_text(len(sub_gent_ref), resolved_gent_new_id)
                proc.move(len(sub_gent_ref))
                continue
            proc.move()
        return proc.xmlchars

    def get_pent_repl(self, pent_ref: XmlChars) -> ParameterEntity | None:
        pent_name = pent_ref.strchars[1:-1]
        if pent_name in self.pents_predef:
            repl_text = self.pents_predef[pent_name]
            return ParameterEntity(0, None, None, self.create_xmlchar_for_predef(repl_text, pent_ref))
        if pent_name in self.pents:
            return self.pents[pent_name]
        return None

    def check_gent_recursion(self, gent_repl_text: str | XmlChars, calling_stack: list[int] | None) -> None:
        if isinstance(gent_repl_text, str):
            xmlchars_arr: list[XmlChar] = [XmlChar(char, -1, -1, -1) for char in gent_repl_text]
            gent_repl_text = XmlChars(*xmlchars_arr)
        if calling_stack is None:
            calling_stack = []
        proc = XmlProccesor(gent_repl_text)
        while not proc.is_end():



    def deref_pent(self, pent_ref: XmlChars, calling_stack: list[int] | None = None) -> XmlChars | None:
        pent_repl = self.get_pent_repl(pent_ref)
        if pent_repl is None:
            # generate not found gent name in predifined entities
            return None
        # check for recursion
        if calling_stack is None:
            calling_stack = []
        if calling_stack.count(pent_repl.entity_id) > 0:
            # generate entity recursion error
            raise ValueError("Entity Recursion")
        else:
            calling_stack.append(pent_repl.entity_id)
        # no parsing of external entity
        if pent_repl.system_id is not None:
            return pent_repl.replacement_text
        # parsing of internal entity
        proc = XmlProccesor(pent_repl.replacement_text)
        while not proc.is_end():
            # parse charref
            chrref = proc.get_chrref()
            if chrref is not None:
                chrref_value = self.get_chrref_value(chrref)
                if chrref_value is not None:
                    proc.ins_repl_text(len(chrref.xmlchars), chrref_value)
                    proc.move(len(chrref.xmlchars))
                    continue
            # bypass without parsing gent
            sub_gent_ref = proc.get_gent_ref()
            if sub_gent_ref is not None:
                gent_name = self.get_gent_repl(sub_gent_ref)
                if gent_name is None:
                    # not valid parameter entity reference
                    return None
                proc.move(len(sub_gent_ref))
                continue
            # parse pent
            sub_pent_ref = proc.get_pent_ref()
            if sub_pent_ref is not None:
                new_entity_id = proc.xmlchars.get_entity_id()
                resolved_pent = self.deref_pent(sub_pent_ref, calling_stack)
                if resolved_pent is None:
                    proc.move()
                    continue
                resolved_pent_new_id = resolved_pent.copy_with_new_entity_id(new_entity_id)
                proc.ins_repl_text(len(sub_pent_ref), resolved_pent_new_id)
                proc.move(len(sub_pent_ref))
                continue
            proc.move()
        return proc.xmlchars

    def deref_pent_with_spaces(self, pent_ref: XmlChars) -> XmlChars | None:
        resolved_pent = self.deref_pent(pent_ref)
        if resolved_pent is None:
            return None
        first_space = XmlCharRef(" ", resolved_pent.xmlchars[0])
        last_space = XmlCharRef(" ", resolved_pent.xmlchars[-1])
        return XmlChars(first_space, resolved_pent, last_space)
