from dtd.dtdcore import Dtd
from dtd.dtdentity import GeneralEntityReplacement, ParameterEntityReplacement
from xmltokens.xmlchar import XmlChar
from xmltokens.xmlchars import XmlChars
import pytest

def test__resolve_pent():
    dtd = Dtd()
    xmlchars_abc = XmlChars(XmlChar("a", 0,0,1), XmlChar("b", 0,0,1), XmlChar("c", 0,0,1),XmlChar("%", 0,0,1),XmlChar("y", 0,0,1),XmlChar(";", 0,0,1), XmlChar("x", 0,0,1), XmlChar("y", 0,0,1), XmlChar("z", 0,0,1))
    xmlchars_def = XmlChars(XmlChar("d", 0,0,2), XmlChar("e", 0,0,2), XmlChar("f", 0,0,2),XmlChar("%", 0,0,2),XmlChar("z", 0,0,2),XmlChar(";", 0,0,2))
    xmlchars_ghi = XmlChars(XmlChar("g", 0,0,3), XmlChar("h", 0,0,3), XmlChar("i", 0,0,3),XmlChar("&", 0,0,0),XmlChar("X", 0,0,0),XmlChar(";", 0,0,0))
    xmlchars_jkl = XmlChars(XmlChar("j", 0,0,3), XmlChar("k", 0,0,3), XmlChar("l", 0,0,3))
    pent_abc = ParameterEntityReplacement(1,None, None, xmlchars_abc)
    pent_def = ParameterEntityReplacement(2,None, None, xmlchars_def)
    pent_ghi = ParameterEntityReplacement(3,None, None, xmlchars_ghi)
    gent_jkl = GeneralEntityReplacement(3,None, None, None, xmlchars_jkl)
    dtd.entity.pents["x"] = pent_abc
    dtd.entity.pents["y"] = pent_def
    dtd.entity.pents["z"] = pent_ghi
    dtd.entity.gents["X"] = gent_jkl

    xmlchars_x = XmlChars(XmlChar("%", 0,0,0),XmlChar("x", 0,0,0),XmlChar(";", 0,0,0))
    result = dtd.entity.deref_pent(xmlchars_x)
    assert result is not None
    assert result.strchars =="abcdefghi&X;xyz"

def test__raise_entity_recursion_error():
    dtd = Dtd()
    xmlchars_abc = XmlChars(XmlChar("a", 0,0,1), XmlChar("b", 0,0,1), XmlChar("c", 0,0,1),XmlChar("%", 0,0,1),XmlChar("y", 0,0,1),XmlChar(";", 0,0,1), XmlChar("x", 0,0,1), XmlChar("y", 0,0,1), XmlChar("z", 0,0,1))
    xmlchars_def = XmlChars(XmlChar("d", 0,0,2), XmlChar("e", 0,0,2), XmlChar("f", 0,0,2),XmlChar("%", 0,0,2),XmlChar("z", 0,0,2),XmlChar(";", 0,0,2))
    xmlchars_ghi = XmlChars(XmlChar("g", 0,0,3), XmlChar("h", 0,0,3), XmlChar("i", 0,0,3),XmlChar("%", 0,0,0),XmlChar("y", 0,0,0),XmlChar(";", 0,0,0))
    pent_abc = ParameterEntityReplacement(1, None, None, xmlchars_abc)
    pent_def = ParameterEntityReplacement(2, None, None, xmlchars_def)
    pent_ghi = ParameterEntityReplacement(3, None, None, xmlchars_ghi)
    dtd.entity.pents["x"] = pent_abc
    dtd.entity.pents["y"] = pent_def
    dtd.entity.pents["z"] = pent_ghi

    xmlchars_x = XmlChars(XmlChar("%", 0,0,0),XmlChar("x", 0,0,0),XmlChar(";", 0,0,0))
    with pytest.raises(ValueError) as err:
        dtd.entity.deref_pent(xmlchars_x)
    assert "Entity Recursion" in str(err.value)

def test__deref_pent_with_spaces():
    dtd = Dtd()
    xmlchars_abc = XmlChars(XmlChar("a", 0,0,1), XmlChar("b", 0,0,1), XmlChar("c", 0,0,1))
    pent_abc = ParameterEntityReplacement(1, None, None, xmlchars_abc)
    dtd.entity.pents["x"] = pent_abc
    xmlchars_x = XmlChars(XmlChar("%", 0,0,0),XmlChar("x", 0,0,0),XmlChar(";", 0,0,0))
    result = dtd.entity.deref_pent_with_spaces(xmlchars_x)
    assert result is not None
    assert result.strchars == " abc "
