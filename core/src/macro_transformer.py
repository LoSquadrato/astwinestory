 
from itertools import count

from core.ast.node import MacroNode
from core.formats.format_definition import FormatDefinition
from core.ast import Story, Passage, Node, TextNode, VariableNode, LinkNode, OperatorNode, MetaNode, LiteralNode, FormattingNode, HookNode

class TransformerError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "TransformerError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)

class Transformer:
    def __init__(self, fmt_original: str, fmt_output: str, next_node_id: int):
        self.source = fmt_original
        self.output = fmt_output
        self._counter = count(next_node_id)
        
    def _next_id(self) -> int:
        return next(self._counter)

    def transform_node_list(self, nodes: list[Node]) -> list[Node]:
        if nodes is None:
            raise TransformerError("Nodes list must be provided for transformation.")
        transformed_nodes = []
        counter = 0
        while counter < len(nodes):
            node = nodes[counter]
            if isinstance(node, MacroNode):
                trasformed_macro, counter_shift = self.transform_macro(nodes[counter:])
                transformed_nodes.extend(trasformed_macro)
                counter += counter_shift
            else:
                transformed_nodes.append(node)
                counter += 1
        return transformed_nodes
        
    def transform_macro(self, nodes: list[Node]) -> list[Node]:
        if nodes is None or len(nodes) == 0:
            raise TransformerError("Macro node must be provided for transformation.")
        if self.source== "linear" and self.output== "markup":
            return self._from_linear_to_markup(nodes)
        elif self.source== "markup" and self.output== "linear":
            return self._from_markup_to_linear(nodes)
        else:
            raise TransformerError("Unsupported transformation between the given syntax types.")
    
    def _from_linear_to_markup(self, nodes: list[Node]) -> list[Node]:
        macro = nodes[0]
        hook = nodes[1] if len(nodes) > 1 else None
        if hook is None or not isinstance(hook, HookNode):
            raise TransformerError("Node type HookNode must be provided for linear to markup transformation.")
        macro_container = [macro, hook]
        macro_container.append(
            MacroNode (                
                node_id = self._next_id(),
                name = self.output.macro.close_tag + macro.name,
                children = []
            )
        )
        return macro_container, 2
    
    def _from_markup_to_linear(self, nodes: list[Node]) -> list[Node]:
        macro = nodes[0]
        hook = nodes[1]
        closing_macro = nodes[2] if len(nodes) > 2 else None
        if hook is None or not isinstance(hook, HookNode) or closing_macro is None or not isinstance(closing_macro, MacroNode):
            raise TransformerError("Invalid macro structure for markup to linear transformation.")
        macro_container = [macro, hook]
        return macro_container, 3
        