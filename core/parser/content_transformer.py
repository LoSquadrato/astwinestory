from core.ast.node import FormattingNode, LinkNode, LiteralNode, MacroNode, MetaNode, OperatorNode, TextNode, VariableNode
from core.formats.format_definition import FormatDefinition
from core.ast import Story, Passage, Node


class TransformerError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "TransformerError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)

class Transformer:
    def __init__(self, story: Story, fmt_output: FormatDefinition):
        self.story = story
        self.fmt_output = fmt_output
        self.fmt_original = story.format
        
    def transform_story(self) -> Story:
        if self.story is None or self.fmt_output is None:
            raise TransformerError("Story and output format must be provided for transformation.")
        passages = []
        for passage in self.story.passages:
            passages.append(self.transform_passage(passage))
        return Story(
            title=self.story.title,
            format=self.fmt_output,
            passages=passages
        )
        
    def transform_passage(self, passage: Passage) -> Passage:
        if passage is None:
            raise TransformerError("Passage must be provided for transformation.")
        nodes = []
        for node in passage.children:
            nodes.append(self.transform_node(node))
        return Passage(
            node_id=passage.node_id,
            name=passage.name,
            tags=passage.tags,
            metadata=passage.metadata,
            children=nodes,
        )

    def transform_node(self, node: Node) -> Node:
        if node is None:
            raise TransformerError("Node must be provided for transformation.")
        match node:
            case TextNode():
                return node
            case VariableNode():
                return node
            case MacroNode():
                return MacroNode(node_id=node.node_id, macro_type=node.macro_type, children=[self.transform_node(child) for child in node.children])
            case LinkNode():
                return LinkNode(node_id=node.node_id, display=node.display, children=[self.transform_node(child) for child in node.children])
            case OperatorNode():
                idx, key = self.get_token_index_and_category(node.operator, self.fmt_original.operators)
                new_operator = self.fmt_output.operators[key][idx]
                return OperatorNode(node_id=node.node_id, operator=new_operator)
            case MetaNode():
                return MetaNode(node_id=node.node_id, kind=node.kind, raw=node.raw)
            case LiteralNode():
                idx, key = self.get_token_index_and_category(node.value, self.fmt_original.literals)
                new_value = self.fmt_output.literals[key][idx]
                return LiteralNode(node_id=node.node_id, value=new_value)
            case FormattingNode():
                idx, key = self.get_token_index_and_category(node.value, self.fmt_original.formatting)
                new_value = self.fmt_output.formatting[key][idx]
                return FormattingNode(node_id=node.node_id, value=new_value)
            case _:
                raise TransformerError(f"Unknown node type: {type(node)}")
            
    def get_token_index_and_category(self, token: str, category: dict[str, list[str]]) -> str:
        if token is None:
            raise TransformerError("Token must be provided for transformation.")
        for cat, token_list in category.items():
            if token in token_list:
                return token_list.index(token), cat
        raise TransformerError(f"Token '{token}' does not belong to any category.")