from dtd import ElementDefinitionsDefined, DefinitionTreeValidator
from xmlvalidator import ValidatorDocument, ValidatorTag

def create_def_tree(definition: str) -> DefinitionTreeValidator:
    dtd_element = "<!ELEMENT element " + definition + "><element></element>"
    doc= ValidatorDocument()
    doc.read_buffer(dtd_element)
    doc.build_validation_tree()
    if not isinstance(doc.children[1], ValidatorTag):
        raise ValueError()
    element = doc.children[1]
    if element.name is None:
        raise ValueError()
    if doc.dtd is None:
        raise ValueError()
    element_definition = doc.dtd.element_definitions[element.name]
    if not isinstance(element_definition, ElementDefinitionsDefined):
        raise ValueError()
    return DefinitionTreeValidator(element_definition)
