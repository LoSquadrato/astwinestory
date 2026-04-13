from core.ast.node import FormattingNode, LinkNode, LiteralNode, MacroNode, MetaNode, OperatorNode, TextNode, VariableNode
from core.formats.format_definition import FormatDefinition
from core.ast import Story, Passage, Node
from core.parser.macro_transformer import Transformer

class ConverterError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "ConverterError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)

class Converter:
    def __init__(self, story: Story, fmt_output: FormatDefinition):
        self.story = story
        self.fmt_output = fmt_output
        self.fmt_original = story.format
        self.transformer = Transformer(self.fmt_original, self.fmt_output)
        
    def convert_story(self) -> Story:
        if self.story is None or self.fmt_output is None:
            raise ConverterError("Story and output format must be provided for conversion.")
        passages = []
        for passage in self.story.passages:
            passages.append(self.convert_passage(passage))
        return Story(
            title=self.story.title,
            format=self.fmt_output,
            passages=passages
        )
        
    def convert_passage(self, passage: Passage) -> Passage:
        if passage is None:
            raise ConverterError("Passage must be provided for conversion.")
        try:
            nodes = self.convert_children(passage.children)
        except ConverterError as e:
            raise ConverterError(f"Error converting passage '{passage.name}': {e}")
        return Passage(
            node_id=passage.node_id,
            name=passage.name,
            tags=passage.tags,
            metadata=passage.metadata,
            children=nodes,
        )

    def convert_children(self, nodes: list[Node]) -> list[Node]:
        if nodes is None:
            raise ConverterError("Nodes list must be provided for conversion.")
        if self.story.fmt.syntax_type != self.fmt_output.syntax_type:
            nodes = self.transformer.transform_node_list(nodes)
        converted_nodes = []
        for node in nodes:
            converted_nodes.append(self._convert_node(node))
        if converted_nodes is None:
            raise ConverterError("Conversion resulted in None, expected list of nodes.")
        return converted_nodes
        
    def _convert_node(self, node: Node) -> Node:
        match node:
            case TextNode():
                return node
            case VariableNode():
                return node
            case MacroNode():
                idx, key = self.get_token_index_and_category(node.operator, self.fmt_original.macros.inner)
                new_macro_type = self.fmt_output.macros.inner[key][idx]
                return MacroNode(
                    node_id=node.node_id, 
                    macro_type=new_macro_type, 
                    children=self.convert_children(node.children)
                    )
            case LinkNode():
                return LinkNode(
                    node_id=node.node_id, 
                    display=node.display, 
                    children=self.convert_children(node.children)
                    )
            case OperatorNode():
                idx, key = self.get_token_index_and_category(node.operator, self.fmt_original.operators)
                new_operator = self.fmt_output.operators[key][idx]
                return OperatorNode(node_id=node.node_id, operator=new_operator)
            case MetaNode():
                idx, key = self.get_token_index_and_category(node.kind, self.fmt_original.meta)
                new_kind = self.fmt_output.meta[key][idx]
                return MetaNode(node_id=node.node_id, kind=new_kind, raw=node.raw)
            case LiteralNode():
                idx, key = self.get_token_index_and_category(node.value, self.fmt_original.literals)
                new_value = self.fmt_output.literals[key][idx]
                return LiteralNode(node_id=node.node_id, value=new_value)
            case FormattingNode():
                idx, key = self.get_token_index_and_category(node.value, self.fmt_original.formatting)
                new_value = self.fmt_output.formatting[key][idx]
                return FormattingNode(node_id=node.node_id, value=new_value)
            case _:
                raise ConverterError(f"Unknown node type: {type(node)}")
            
    def get_token_index_and_category(self, token: str, category: dict[str, list[str]]) -> str:
        if token is None:
            raise ConverterError("Token must be provided for conversion.")
        for cat, token_list in category.items():
            if token in token_list:
                return token_list.index(token), cat
        raise ConverterError(f"Token '{token}' does not belong to any category.")
    
   
        
    
    