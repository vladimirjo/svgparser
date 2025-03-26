xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<!-- This is the root element of the XML document -->
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
        <title>Introduction to XML</title>
        <paragraph>This document provides an overview of XML structure and elements.</paragraph>
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

nested_dtd = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE library [
    <!-- Declare Elements -->
    <!ELEMENT library (book+, journal*)>
    <!ELEMENT book (title, author+, publisher, price)>
    <!ELEMENT journal (title, editor, issue, price)>
    <!ELEMENT title (#PCDATA)>
    <!ELEMENT author (#PCDATA)>
    <!ELEMENT publisher (#PCDATA)>
    <!ELEMENT price (#PCDATA)>
    <!ELEMENT editor (#PCDATA)>
    <!ELEMENT issue (#PCDATA)>

    <!-- Declare Attributes -->
    <!ATTLIST book
        isbn CDATA #REQUIRED
        genre (fiction|nonfiction|fantasy|biography) #IMPLIED>
    <!ATTLIST journal
        issn CDATA #REQUIRED
        frequency (daily|weekly|monthly|yearly) #IMPLIED>

    <!-- Declare Entities -->
    <!ENTITY pub1 "Penguin Random House">
    <!ENTITY pub2 "HarperCollins">
    <!ENTITY priceUSD "&dollar;"> <!-- Character entity -->

    <!-- Declare Notations -->
    <!NOTATION gif SYSTEM "image/gif">
    <!NOTATION jpg SYSTEM "image/jpeg">

    <!-- Conditional Sections -->
    <![INCLUDE[
        <!ENTITY exampleBook "Advanced XML Techniques">
    ]]>
    <![IGNORE[
        <!ENTITY exampleBook "This will be ignored">
    ]]>

    <!-- Nested Conditional Sections -->
    <![INCLUDE[
        <![IGNORE[
            <!ENTITY nestedIgnored "This content is ignored due to nesting">
        ]]>
        <![INCLUDE[
            <!ENTITY nestedIncluded "Nested conditional section content included">
        ]]>
    ]]>

]>

<library>
    <book isbn="1234567890" genre="fiction">
        <title>XML Mastery</title>
        <author>John Doe</author>
        <author>Jane Smith</author>
        <publisher>&pub1;</publisher>
        <price>&priceUSD;19.99</price>
    </book>
    <journal issn="9876543210" frequency="monthly">
        <title>XML Journal</title>
        <editor>Emma Watson</editor>
        <issue>42</issue>
        <price>&priceUSD;5.99</price>
    </journal>
</library>"""

nested_dtd1 = """<!DOCTYPE library [
    <![INCLUDE[
        <![IGNORE[
            <!ENTITY nestedIgnored "This content is ignored due to nesting">
        ]]>
        <![INCLUDE[
            <!ENTITY nestedIncluded "Nested conditional section content included">
        ]]>
    ]]>

]>"""

basic_tag = """<ns:item id="a1&lt;" value="Example A">"""

dtd = """<!DOCTYPE person [
    <!ELEMENT first_name ((#PCDATA | title), (paragraph | image)*)>
    <!ELEMENT title (#PCDATA)>
    <!ELEMENT paragraph (#PCDATA)>
    <!ELEMENT image EMPTY>
    <!ATTLIST image src CDATA #REQUIRED>
]>
<person>
    <first_name>
        Dr. <!-- #PCDATA allowed here -->
        <title>John</title> <!-- Title allowed -->
        <paragraph>Brief introduction about John.</paragraph>
        <image src="john.png"/>
        <paragraph>More details about John's background.</paragraph>
    </first_name>
</person>"""

simple_dtd = """<!DOCTYPE person [
    <!ELEMENT person (name, age?, address)*>
]>
<person>
    <name>John Doe</name>
    <age>30</age>
    <address>123 Main St</address>
    <name>John Doe</name>

</person>"""

dtd1 = """<!DOCTYPE person [
    <!ELEMENT person (name,address)*>
]>
<person>
    <name>John Doe</name>
    <address>123 Main St</address>
    <name>John Doe</name>
    <address>123 Main St</address>
</person>"""

dtd_choice = """<!DOCTYPE person [
    <!ELEMENT person (a|b)*>
]>
<person>
    <b>John Doe</b>
    <a>John Doe</a>
    <c>John Doe</c>
    <b>John Doe</b>
    <a>John Doe</a>
</person>"""

dtd_sequence = """<!DOCTYPE test [
    <!ELEMENT test ((e1 | (e2 , (e3 | (e4 , e5*)))), e6)>
]>
<test>
    <e2></e2>
    <e4></e4>
    <e5></e5>
    <e5></e5>
    <e6></e6>
</test>"""

from lxml import etree

parser = etree.XMLParser(load_dtd=True, no_network=False)

tree = etree.parse("examples/dtd/example1.xml", parser=parser)
root = tree.getroot()
for child in root:
    child
    print(child)
print()
