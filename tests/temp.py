from xml.etree import ElementTree as ET

def test():
    # Define the XML string
    xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE example [
  <!ENTITY nestedample "&#x26;amp;">
  <!ENTITY ample "&nestedample;">
  <!ENTITY light "&lt;">
  <!ENTITY gt "&gt;">
]>
<example>
    <text attr="This is an example of &ample; &light; and &gt; inside an attribute"/>
    <description attr="The character reference &ample; represents an ampersand"/>
</example>'''

    # Parse the XML data
    root = ET.fromstring(xml_data)
    text_element = root.find('text')
    print()

    # # Access the 'text' element and its 'attr' attribute
    # attr_value = text_element.get('attr')

    # # Print the value of the 'attr' attribute
    # print("Attribute value:", attr_value)

test()
