from __future__ import annotations

from typing import NamedTuple

from xmltokens import XmlCharRef
from xmltokens import XmlChars
from xmltokens import XmlProccesor


class GeneralEntityReplacement(NamedTuple):
    # id=0 predefined entities
    # id=1 reserved for main file
    # id=2 reserved for external subset file
    # id>2 all other entities
    entity_id: int
    system_id: XmlChars | None
    public_id: XmlChars | None
    ndata: XmlChars | None
    replacement_text: XmlChars | None


class ParameterEntityReplacement(NamedTuple):
    # id=0 predefined entities
    # id=1 reserved for main file
    # id=2 reserved for external subset file
    # id>2 all other entities
    entity_id: int
    system_id: XmlChars | None
    public_id: XmlChars | None
    replacement_text: XmlChars


class DtdEntity:
    def __init__(self) -> None:
        self.predefs: dict[str, str] = {"lt": "<", "gt": ">", "amp": "&", "apos": "'", "quot": '"'}
        self.gents: dict[str, GeneralEntityReplacement] = {}
        self.pents: dict[str, ParameterEntityReplacement] = {}
        self.idcnt = 2

    def get_next_id(self) -> int:
        self.idcnt += 1
        return self.idcnt

    def get_gent_name(self, gent_ref: XmlChars) -> XmlChars | None:
        if gent_ref.strchars[0] != "&":
            return None
        if gent_ref.strchars[-1] != ";":
            return None
        return XmlChars(*gent_ref.xmlchars[1:-1])

    def get_pent_name(self, pent_ref: XmlChars) -> XmlChars | None:
        if pent_ref.strchars[0] != "%":
            return None
        if pent_ref.strchars[-1] != ";":
            return None
        return XmlChars(*pent_ref.xmlchars[1:-1])

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

    def deref_gent(self, gent_ref: XmlChars, calling_stack: list[int] | None = None) -> XmlChars | None:
        gent_name = self.get_gent_name(gent_ref)
        if gent_name is None:
            # not valid general entity reference
            return None
        if gent_name.strchars not in self.gents:
            # generate not found gent name in predifined entities
            return None
        # check for recursion
        if calling_stack is None:
            calling_stack = []
        if calling_stack.count(self.gents[gent_name.strchars].entity_id) > 0:
            # generate entity recursion error
            raise ValueError("Entity Recursion")
        else:
            calling_stack.append(self.gents[gent_name.strchars].entity_id)
        # no parsing of external entity
        if self.gents[gent_name.strchars].system_id is not None:
            return self.gents[gent_name.strchars].replacement_text
        # check for ndata entity
        repl_text = self.gents[gent_name.strchars].replacement_text
        if repl_text is None:
            raise ValueError("Ndata not allowed.")
        # parsing of internal entity
        proc = XmlProccesor(repl_text)
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
            if sub_gent_ref is not None:
                new_entity_id = proc.xmlchars[proc.pointer].xmlchars[0].entity_id
                resolved_gent = self.deref_gent(sub_gent_ref)
                if resolved_gent is None:
                    proc.move()
                    continue
                resolved_gent_new_id = resolved_gent.copy_with_new_entity_id(new_entity_id)
                proc.ins_repl_text(len(sub_gent_ref), resolved_gent_new_id)
                proc.move(len(sub_gent_ref))
                continue
            proc.move()
        return proc.xmlchars

    def deref_pent(self, pent_ref: XmlChars, calling_stack: list[int] | None = None) -> XmlChars | None:
        pent_name = self.get_pent_name(pent_ref)
        if pent_name is None:
            # not valid parameter entity reference
            return None
        if pent_name.strchars not in self.pents:
            # generate not found pent name in predifined parameter entities
            return None
        # check for recursion
        if calling_stack is None:
            calling_stack = []
        if calling_stack.count(self.pents[pent_name.strchars].entity_id) > 0:
            # generate entity recursion error
            raise ValueError("Entity Recursion")
        else:
            calling_stack.append(self.pents[pent_name.strchars].entity_id)
        # no parsing of external entity
        if self.pents[pent_name.strchars].system_id is not None:
            return self.pents[pent_name.strchars].replacement_text
        # parsing of internal entity
        proc = XmlProccesor(self.pents[pent_name.strchars].replacement_text)
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
                gent_name = self.get_gent_name(sub_gent_ref)
                if gent_name is None:
                    # not valid parameter entity reference
                    return None
                if gent_name.strchars not in self.gents:
                    # generate not found pent name in predifined parameter entities
                    return None
                proc.move(len(sub_gent_ref))
                continue
            # parse pent
            sub_pent_ref = proc.get_pent_ref()
            if sub_pent_ref is not None:
                new_entity_id = proc.xmlchars[proc.pointer].xmlchars[0].entity_id
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
