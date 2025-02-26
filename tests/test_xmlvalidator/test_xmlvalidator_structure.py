from xmlvalidator import XmlValidator

xml = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="style.xsl"?>
<!DOCTYPE catalog [
    <!-- Root element containing books -->
    <!ELEMENT catalog (book*)>

    <!-- Define book element structure -->
    <!ELEMENT book (title, author, year, price, description, metadata?)>
    <!ELEMENT title (#PCDATA)>
    <!ELEMENT author (#PCDATA)>
    <!ELEMENT year (#PCDATA)>
    <!ELEMENT price (#PCDATA)>
    <!ELEMENT description (#PCDATA | CDATA)*>
    <!ELEMENT metadata (data*)>
    <!ELEMENT data (#PCDATA)>

    <!-- Attributes for book -->
    <!ATTLIST book id ID #REQUIRED>
    <!ATTLIST book genre CDATA #IMPLIED>

    <!-- Entity definitions -->
    <!ENTITY publisher "OpenAI Publishing">
    <!ENTITY trademark "&#8482;">  <!-- ™ symbol -->

    <!-- External entity (file or URL reference) -->
    <!ENTITY externalData SYSTEM "http://example.com/data.xml">

    <!-- Parameter entity -->
    <!ENTITY % bookDetails "title, author, year, price">

    <!-- Notation (used for non-XML data processing) -->
    <!NOTATION pdfFormat SYSTEM "application/pdf">

    <!-- Conditional sections -->
    <![ INCLUDE [
        <!ELEMENT includedElement (#PCDATA)>
    ]]>

    <![IGNORE[
        <!ELEMENT ignoredElement (#PCDATA)>
    ]]>
]>

<catalog>
    <!-- Comment inside XML -->
    <!-- This is a book collection -->

    <book id="b1" genre="fiction">
        <title>The Great XML Guide</title>
        <author>John Doe</author>
        <year>2024</year>
        <price>29.99</price>

        <!-- CDATA section to include special characters -->
        <description><![CDATA[
            This book covers <XML> & <DTD> structures in depth.
        ]]></description>

        <!-- Using a predefined entity -->
        <publisher>&publisher;</publisher>

        <!-- Metadata with processing instruction inside -->
        <metadata>
            <data>First Edition</data>
            <?processing-instruction name="cache-control" value="no-cache"?>
        </metadata>
    </book>
</catalog>"""

def test__xml_structure():
    doc = XmlValidator()
    doc.read_buffer(xml)
    doc.build_validation_tree()
    print()
