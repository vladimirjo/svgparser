from xmltokens import XmlChar, XmlChars, XmlProccesor, XmlCharRef

def test__xmlcharref():
    xmlchar_a = XmlChar("a", 0, 0, 1)
    xmlchar_b = XmlChar("b", 0, 0, 1)
    xmlchar_c = XmlChar("c", 0, 0, 1)
    xmlcharref = XmlCharRef("f", xmlchar_a, xmlchar_b, xmlchar_c)
    assert xmlcharref.strchars == "f"
    assert len(xmlcharref.xmlchars) == 3
    assert xmlcharref.xmlchars[0].strchars == "a"
    assert xmlcharref.xmlchars[1].strchars == "b"
    assert xmlcharref.xmlchars[2].strchars == "c"

def test__xmlchars_copy():
    xmlchar_a = XmlChar("a", 0, 0, 1)
    xmlchar_b = XmlChar("b", 0, 0, 1)
    xmlchar_c = XmlChar("c", 0, 0, 1)
    xmlchar_d = XmlChar("d", 0, 0, 1)
    xmlchar_e = XmlChar("e", 0, 0, 1)
    xmlchar_f = XmlChar("f", 0, 0, 1)
    xmlchar_g = XmlChar("g", 0, 0, 1)
    xmlchar_h = XmlChar("h", 0, 0, 1)
    xmlchar_i = XmlChar("i", 0, 0, 1)
    xmlcharref_x = XmlCharRef("x", xmlchar_a, xmlchar_b, xmlchar_c)
    xmlcharref_y = XmlCharRef("y", xmlchar_d, xmlchar_e, xmlchar_f)
    xmlcharref_z = XmlCharRef("z", xmlchar_g, xmlcharref_x, xmlcharref_y)
    xmlchars = XmlChars(xmlchar_a, xmlchar_b, xmlcharref_z)
    new_xmlchars = xmlchars.copy()
    assert id(new_xmlchars) != id(xmlchars)
    assert id(new_xmlchars.xmlchars[0]) != id(xmlchars.xmlchars[0])
    assert id(new_xmlchars.xmlchars[1]) != id(xmlchars.xmlchars[1])
    assert id(new_xmlchars.xmlchars[2]) != id(xmlchars.xmlchars[2])
    assert isinstance(new_xmlchars.xmlchars[2], XmlCharRef)
    assert isinstance(xmlchars.xmlchars[2],XmlCharRef)
    assert id(new_xmlchars.xmlchars[2].xmlchars[0]) != id(xmlchars.xmlchars[2].xmlchars[0])
    assert id(new_xmlchars.xmlchars[2].xmlchars[1]) != id(xmlchars.xmlchars[2].xmlchars[1])
    assert id(new_xmlchars.xmlchars[2].xmlchars[2]) != id(xmlchars.xmlchars[2].xmlchars[2])
