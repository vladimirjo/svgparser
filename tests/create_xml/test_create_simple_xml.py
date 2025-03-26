from xmlvalidator import XmlValidator

def test__simple_xml() -> None:
    xmlvalidator = XmlValidator()
    # x41 = A
    xmlvalidator.add_buffer("""<tag a="1" b="2" c="3"></tag >""")
    xmlvalidator.build()
    print()
