# TODO: I'd like to decouple the builder from the parser but maybe it's not necessary, 
# since the builder is only used by the parser and not by other components.

class Builder:
    def __init__(self):
        self._counter = count(1)
        self._patterns = RegexBuilder(format_def)
        

    def _next_id(self) -> int:
        return next(self._counter)
    
    def _build_node(self, **kwargs) -> Node:
        kind = kwargs.get("kind")
        match = kwargs.get("match")
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
                raise ParsingError(["Macro nodes should be built using MacroParser, not _build_node."])
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
                    value=match.group("literal")
                )
            case "formatting":
                return FormattingNode(
                    node_id=self._next_id(),
                    value=match.group("formatting")
                )
            case _:
                raise ParsingError([f"Unknown node type: {kind}"])