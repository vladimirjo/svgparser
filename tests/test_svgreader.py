from svgparser import SvgReader, XMLToken

def test__svgreader():
    svg_reader = SvgReader("<svg attr=\"<>value\" >")
    tag = svg_reader.extract_start_tag()
    assert tag.contents() == "svg attr=\"<>value\" "
