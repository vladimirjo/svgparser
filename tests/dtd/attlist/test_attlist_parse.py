from xmlstruct.attlist import Attlist
from buffer import BufferController
from errorcollector import ErrorCollector

def test__attrlist_parse() -> None:
    buffer = BufferController()
    text = """<!ATTLIST person
        id          ID       #REQUIRED
        nationality CDATA    #IMPLIED
        status      (single | married | divorced) "single"
        employed    (yes | no) #FIXED "yes"
        ageGroup    NMTOKEN  #IMPLIED
        alias       IDREF    #IMPLIED
        references  IDREFS   #IMPLIED
        >"""
    buffer.add_buffer_unit(text, "")
    tokens = buffer.get_buffer_tokens()
    assert tokens is not None
    attlist = Attlist(tokens, ErrorCollector())
    print()
