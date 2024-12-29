from svgparser import skip_empty_places
from bufferreader import BufferReader
from svgparser import EMPTY_SPACES
from svgparser import extract_attribute_value_pairs
from svgparser import extract_namespace_prefix_with_tag
from svgparser import parse_start_tag

def test__skip_empty_places():
    buffer = BufferReader("start \n  end")
    buffer.set_pointer(0,5)
    skip_empty_places(buffer)
    assert buffer.line == 1
    assert buffer.char == 2
    assert buffer.read(0,2) is True
    assert buffer.stream == "end"

def test__extract_attrbute_value_pairs():
    buffer=BufferReader("name=\"value\"")
    attribute, value = extract_attribute_value_pairs(buffer)
    assert attribute == "name"
    assert value == "value"

def test__extract_namespace_prefix_with_tag():
    buffer = BufferReader("tag ")
    namespace_prefix, tag = extract_namespace_prefix_with_tag(buffer)
    assert namespace_prefix is None
    assert tag == "tag"
    buffer = BufferReader("namespace:tag ")
    namespace_prefix, tag = extract_namespace_prefix_with_tag(buffer)
    assert namespace_prefix == "namespace"
    assert tag == "tag"
    assert buffer.char == 12

def test__parse_start_tag():
    buffer = BufferReader("""<body>""")
    namespace_prefix, tag, attributes, self_enclosed = parse_start_tag(buffer)
    pass
