import re

from core.formats import FormatDefinition
from cli.src.regex_builder import RegexBuilder

class ExtractorError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "ExtractorError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        
        
class Extractor():
    def __init__(self, fmt: FormatDefinition, patterns: RegexBuilder):
        self._fmt = fmt
        self._patterns = patterns
        
    def _get_macro(self, text: str) -> re.Match | None:
        match = self._patterns.build_pattern(["macro"]).match(text)
        return match if match else None
    
    def _get_macro_first_match(self, text: str) -> re.Match | None:
        match = self._patterns.build_macro_content_pattern().search(text)
        return match if match else None
    
#############################################################################
# Method for markup syntax type
#############################################################################
    
    def get_macro_params_markup(self, text: str) -> dict:
        match = self._get_macro(text)
        if not match:
            raise ExtractorError([f"Failed to extract macro from text: {text}"])
        macro_type = match.group("macro_type")
        if macro_type is None:
            raise ExtractorError([f"Regex match missing group: {match}"])
        children = match.group("macro_inner")
        if self._fmt.have_hook(macro_type):
            hook_content, closer = self._extract_full_markup_macro_content(macro_type, text[match.end():])
            return {
                "offset": match.end() + len(hook_content) + len(closer),
                "kind": "macro", 
                "macro_type": macro_type, 
                "children": children,
                "hook": hook_content
                }
        else:
            return {
                "offset": match.end(),
                "kind": "macro", 
                "macro_type": macro_type, 
                "children": children,
                }
            
    def _extract_full_markup_macro_content(self, opener_type: str, text: str) -> tuple[str, str] | None:
            stack = 1
            for match in self._patterns.build_macro_content_pattern().finditer(text):
                macro_type = match.group("macro_type")
                if macro_type is None:
                    raise ExtractorError([f"Regex match missing group: {match}"])
                if macro_type == self._fmt.macros.close_tag + opener_type:
                    stack -= 1
                if macro_type == opener_type:
                    stack += 1
                if stack == 0:
                    return text[:match.start()], match.group(0) 
            raise ExtractorError([f"Unmatched macro opener: {opener_type}"])  # No matching closing tag found
    
#############################################################################
# Method for linear syntax type
#############################################################################
    
    def get_macro_params_linear(self, text: str) -> dict:
        params = self._get_macro_and_children_params(text)
        pivot = params["pivot"]
        macro_type = params["macro_type"]
        children = params["children"]
        hook = self._get_hook(text[pivot:], macro_type)
        return {
                "offset": pivot + (len(hook) if hook else 0),  # +1 for the hook opener parenthesis
                "kind": "macro", 
                "macro_type": macro_type, 
                "children": children[:-1],  # Exclude the closing tag from children
                "hook": self._strip_hook_parenthesis(hook) if hook else "" 
                }
        
    def _get_macro_and_children_params(self, text: str) -> dict:
        match = self._get_macro_first_match(text)
        if not match:
            raise ExtractorError([f"Failed to extract linear macro from text: {text}"])          
        macro_type = (match.group("opener")).strip(self._fmt.macros.open)
        if macro_type is None:
            raise ExtractorError([f"Regex match missing group: {match}"])
        pivot = match.end()
        children = self._extract_linear_content_stack(
            text[pivot:], self._patterns.build_macro_content_pattern(), 1)
        pivot += len(children)
        return {"macro_type": macro_type, "children": children, "pivot": pivot}
           
    def _get_hook(self, text: str, macro_type: str) -> re.Match | None:
        if self._fmt.is_control_macro_opener(macro_type):
            return self._extract_linear_control_content(text)
        elif self._fmt.have_hook(macro_type):
            return self._extract_linear_content_stack(text, self._patterns.build_hook_content_pattern(), 0)
        else:
            return ""
        
    def _strip_hook_parenthesis(self, hook: str) -> str:
        if hook.startswith(self._fmt.macros.hook_open) and hook.endswith(self._fmt.macros.hook_close):
            return hook[1:-1]  # Remove the opening and closing parenthesis
        else:
            raise ExtractorError([f"Hook does not have proper parenthesis: {hook}"])
     
    def _extract_linear_content_stack(self, text: str, pattern: re.Pattern, stack: int) -> str:
        match_list = list(pattern.finditer(text))
        if not match_list:
            raise ExtractorError([f"Failed to extract linear content from text: {text}"])
        for match in match_list:
            if match.groupdict().get("opener"):
                stack += 1
            elif match.groupdict().get("closer"):
                stack -= 1
            if stack == 0:
                return text[:match.end()]
        raise ExtractorError([f"Unmatched linear opener"])
        
    
    def _extract_linear_control_content(self, text: str) -> str:
        hook = self._extract_linear_content_stack(text, self._patterns.build_hook_content_pattern(), 0)
        remaining = text[len(hook):]
        next_match = self._get_macro(remaining)
        if next_match is None or not self._fmt.is_control_macro_continue(next_match.group("macro_type")):
            return hook
        else:
            params = self._get_macro_and_children_params(remaining)
        return (
            hook
            + remaining[:params["pivot"]]
            + self._extract_linear_control_content(remaining[params["pivot"]:])
        )

    
#############################################################################
# Method for html content extraction
#############################################################################     
    
    def get_html_params(self, text: str) -> dict:
        match = self._get_html_tag(text)
        if not match:
            raise ExtractorError([f"Failed to extract html macro from text: {text}"])
        html_tag = match.group("html_tag")
        if html_tag is None:
            raise ExtractorError([f"Regex match missing group: {match}"])
        html_content = self._extract_full_html_content(html_tag, text[match.end():])
        return {
            "offset": len(match.group(0)) + len(html_content),
            "kind": "html", 
            "tag": html_tag, 
            "body": match.group(0) + html_content
            }
    
    def _get_html_tag(self, text: str) -> re.Match | None:
        match = self._patterns.build_pattern(["html"]).match(text)
        return match if match else None
    
    def _extract_full_html_content(self, opener_tag: str, text: str) -> str:
        stack = 1
        for match in self._patterns.build_html_content_pattern().finditer(text):
            html_tag = match.group("html_tag")
            if html_tag is None:
                raise ExtractorError([f"Regex match missing group: {match}"])
            if html_tag == self._fmt.html.close_tag + opener_tag:
                stack -= 1
            if html_tag == opener_tag:
                stack += 1
            if stack == 0:
                return text[:match.end()]  # Return the content between opener and closer
        raise ExtractorError([f"Unmatched html tag opener: {opener_tag}"])  # No matching closing tag found
    
    
########################################################################################
# Methods for extracting hook, named hook, hidden hook, unclosed hook from linear syntax
#########################################################################################