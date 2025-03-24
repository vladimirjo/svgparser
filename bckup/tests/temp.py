from xml.etree import ElementTree as ET

def test():
    # Define the XML string
    xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE example [
  <!ENTITY   % pub    "Editions Gallimard" >
  <!ENTITY   rights "%pub;All rights reserved" >
  <!ENTITY   book   "La Peste: Albert Camus, &#xA9; 1947 . &rights;" >
]>
<example>
    <text attr="This is an example of &book; inside an attribute"/>
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
