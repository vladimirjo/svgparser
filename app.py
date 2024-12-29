from svgparser import BufferController
from svgparser import XMLBuilder
from svgparser import XMLParser


svg = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<!-- This is the root element of the XML document -->
<root xmlns="http://example.com/default" xmlns:ns="http://example.com/ns">

    <!-- XML declaration, comments, and processing instructions -->
    <?xml-stylesheet type="text/xsl" href="style.xsl"?>
    <!-- Comment about data below -->

    <metadata>
        <author>John Doe</author>
        <date>2024-10-20</date>
        <version>1.0</version>
    </metadata>

    <!-- Standard elements with attributes -->
    <section id="1" type="intro">
        <title Introduction to XML</title>
        <paragraph>This document &provides an overview of XML structure and elements.</paragraph>
    </section>

    <!-- CDATA Section -->
    <example>
        <code><![CDATA[
            <div>Some HTML code example here</div>
        ]]></code>
    </example>

    <!-- Namespaced elements -->
    <ns:data>
        <ns:item id="a1&lt;" value="Example A">Namespaced item A</ns:item>
        <ns:item id="b2" value="Example B">Namespaced item B</ns:item>
    </ns:data>

    <!-- Nested structure with mixed content -->
    <content>
        <header>This is a header</header>
        Some text outside tags.
        <paragraph>First paragraph inside content.</paragraph>
        <footer>End of content</footer>
    </content>

    <!-- An empty element -->
    <emptyElement />

</root>
<root1></root1>"""


svg1 = """<!-- Comment1 --"""
svg2 = """< root></root>"""
svg2 = """Blah blas"""

dtd_example = """<?xml version="1.0"?>
<!DOCTYPE person [
    <!ELEMENT first_name (#PCDATA)>
    <!ELEMENT last_name ( #PCDATA )>
    <!ELEMENT profession (#PCDATA)>
    <!ELEMENT name (first_name|last_name)>
    <!ELEMENT person (name, profession*)>
    <!ATTLIST image source CDATA #REQUIRED
                    width CDATA #REQUIRED
                    height CDATA #REQUIRED
                    alt CDATA #IMPLIED
    >
]>
<person>
    <name>
        <first_name>Alan</first_name>
    </name>
    <image source="source_value" width="width_value" height="heigth_value"/>
    <profession>computer scientist</profession>
    <profession>mathematician</profession>
    <profession>cryptographer</profession>
</person>"""


builder = XMLBuilder()
tree = builder.get_tree_from_buffer(dtd_example)
print()

# xml = XMLBuilder()
# buffer_controller = BufferController(svg1, "In-memory buffer svg1")
# xml.buffer_controller = buffer_controller
# xml.buffer_controller.add_buffer(svg2, "In-memory buffer svg2")
# xml.buffer_controller.slot_in_use = 1
# xml.buffer_controller.buffers[0].pointer = 2
# xmlparser = XMLParser(buffer_controller, xml.error)
# xml.tree = xmlparser.get_tree()

# xml.print_error_messages()
# print()
