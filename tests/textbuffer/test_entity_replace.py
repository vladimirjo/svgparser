from xmlvalidator import NodeTreeBuilder
from xmlvalidator import Dtd
from xmltokens import XmlChar
from xmltokens import XmlChars
from xmltokens import XmlCharRef
from xmltokens import XmlTokenProccesor

def get_processor(text: str) -> XmlTokenProccesor:
    xmlchars_arr = []
    for i, char in enumerate(text):
        xmlchar = XmlChar(char, 0, i)
        xmlchars_arr.append(xmlchar)
    return XmlTokenProccesor(XmlChars(*xmlchars_arr))



def test__entity_replace() -> None:
    dtd = Dtd()
    dtd.gents["alice"] = "brave"
    # ("David", "Smart"),
    # ("Ethan", "Swift"),
    # ("Grace", "Kind"),
    # ("Mason", "Tough"),
    # ("Julia", "Happy"),
    # ("Sarah", "Calm"),
    # ("Oscar", "Witty"),
    # ("Lucas", "Loyal"),
    # ("Chloe", "Sweet"),
    # ("Jack", "Bold"),
    # ("Henry", "Quick"),
    # ("Sophie", "Clever"),
    # ("Bella", "Cheer"),
    # ("Noah", "Neat"),
    # ("Emma", "Neat"),
    # ("Zoe", "Cute"),
    # ("Kevin", "Noble"),
    # ("Jason", "Strong"),
    # ("Ryan", "Cool"),
    # self.gents["alice"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["david"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["ethan"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["grace"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["mason"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["julia"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["sarah"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["alice"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["alice"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["alice"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["alice"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["alice"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    # self.gents["alice"] = XmlToken(*[XmlChar(char, 0, 0) for char in "brave"])
    processor = get_processor("")
    nodetree = NodeTreeBuilder()
