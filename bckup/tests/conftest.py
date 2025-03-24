# from dtd.dtdcore import DtdTag, DtdCData
# from dtd.defelem import DefElemDefined
# from dtd.valelem import ValElemTree
# from buffer.token import  Token
# from buffer.fragment import Fragment
# from errorcollector import ErrorCollector

# def tokenize_definition(definition: str) -> list[Token]:
#     tokens: list[Token] = []
#     accumulator: str = ""
#     for char in definition:
#         if char.isspace():
#             continue
#         if any(char == operator for operator in "|(),?*+"):
#             if accumulator != "":
#                 tokens.append(Token(Fragment(accumulator, 0,0)))
#                 accumulator = ""
#             tokens.append(Token(Fragment(char, 0,0)))
#             continue
#         accumulator += char
#     return tokens

# def tokenize_elements_to_validate(targets: list[str]) -> list[Token]:
#     tokenized_targets: list[Token] = []
#     for target in targets:
#         token = Token(Fragment(target, 0, 0))
#         tokenized_targets.append(token)
#     return tokenized_targets

# def create_pcdata_element(content: str) -> DtdCData:
#     cdata = DtdCData(Token(Fragment(content, 0, 0)))
#     return cdata

# def create_tag_element(name: str) -> DtdTag:
#     return DtdTag(Token(Fragment(name, 0, 0)))

# class MixedContentTest:
#     def __init__(self) -> None:
#         self.mixed_contents: list[DtdCData | DtdTag] = []

#     def add_pcdata(self, content: str) -> None:
#         self.mixed_contents.append(create_pcdata_element(content))

#     def add_element(self, name: str) -> None:
#         self.mixed_contents.append(create_tag_element(name))

# def create_element_definition(definition: str) -> ValElemTree:
#     tokens = tokenize_definition(definition)
#     edd = DefElemDefined(tokens)
#     def_tree = ValElemTree(edd, ErrorCollector())
#     return def_tree
