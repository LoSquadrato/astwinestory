# TODO: I'd like to decouple the builder from the parser but maybe it's not necessary, 
# since the builder is only used by the parser and not by other components.

from itertools import count

from core.ast import (
    Node,
    Passage,
    Story,
    TextNode,
    VariableNode,
    LinkNode,
    OperatorNode,
    MetaNode,
    LiteralNode,
    FormattingNode,
    MacroNode,
    HTMLNode
)

class BuilderError(Exception):
    pass

class Builder:
    def __init__(self):
        self._counter = count(1)
        

    def _next_id(self) -> int:
        return next(self._counter)
    
    def _build_node(self, params: dict) -> Node:
        kind = params["kind"]
        match = params["match"]
        match kind:
            case "link":
                display = match.group("link_display") if match.group("link_display") is not None else ""
                target  = match.group("link_target") or match.group("link_inner")
                return LinkNode(
                    node_id=self._next_id(),
                    display=display,
                    children=self.parse_content(target, 
                        self._patterns.build_node_content_pattern())
                    )
            case "variable":
                prefix = match.group("var_prefix")
                name = match.group("var_name")
                scope = "global_prefix" if prefix == self.format_def.variables.global_prefix else "local_prefix"
                return VariableNode(
                    node_id=self._next_id(),
                    name=name,
                    scope=scope
                )
            case "macro":
                macro_type = params["macro_type"]
                children = params["children"]
                hook = params["hook"] if "hook" in params else None
                return MacroNode(
                    node_id=self._next_id(),
                    macro_type=macro_type,
                    children=self.parse_content(children, self._patterns.build_node_content_pattern()) if children else [],
                    hook=self.parse_content(hook, self._patterns.build_node_content_pattern()) if hook else None
                )
            case "html":
                tag = params["tag"]
                body = params["body"]
                return HTMLNode(
                    node_id=self._next_id(),
                    tag=tag,
                    body=body
                )
            case "operator":
                return OperatorNode(
                    node_id=self._next_id(),
                    operator=match.group(0)
                )
            case "meta":
                return MetaNode(
                    node_id=self._next_id(),
                    kind=match.group("meta_prefix"),
                    raw=match.group("meta_content")
                )
            case "literal":
                return LiteralNode(
                    node_id=self._next_id(),
                    value=match.group(0)
                )
            case "formatting":
                return FormattingNode(
                    node_id=self._next_id(),
                    value=match.group(0)
                )
            case _:
                raise BuilderError(f"Unknown node type: {kind}")