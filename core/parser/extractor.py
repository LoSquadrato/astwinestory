import re

from core.formats.format_definition import FormatDefinition
from core.parser.regex_builder import RegexBuilder

class MarkupExtractorError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        message = "MarkupExtractorError:\n" + "\n".join(f"- {e}" for e in errors)
        super().__init__(message)
        
        
# TODO: DRY the logic so it can be used for html script in SugarCube.
# Extracts macros from a given text and returns a dict of macros.
class MarkupExtractor():
    def __init__(self, fmt: FormatDefinition, patterns: RegexBuilder):
        self._fmt = fmt
        self._patterns = patterns
    
    def get_macro_params(self, text: str) -> dict:
        match = self._get_macro(text)
        if not match:
            raise MarkupExtractorError([f"Failed to extract macro from text: {text}"])
        macro_type = match.group("macro_type")
        if macro_type is None:
            raise MarkupExtractorError([f"Regex match missing group: {match}"])
        children = match.group("macro_inner")
        if self._fmt.is_outer_macro(macro_type):
            hook_content, last_match = self._extract_full_macro_content(macro_type, text[match.end():])
            return {
                "offset": match.end() + len(hook_content) + len(last_match),
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
    
    
    def _extract_full_macro_content(self, opener_type: str, text: str) -> tuple[str, str] | None:
        stack = 1
        for match in self._patterns.build_macro_content_pattern().finditer(text):
            macro_type = match.group("macro_type")
            if macro_type is None:
                raise MarkupExtractorError([f"Regex match missing group: {match}"])
            if macro_type == self._fmt.macros.close_tag + opener_type:
                stack -= 1
            if macro_type == opener_type:
                stack += 1
            if stack == 0:
                return text[:match.start()], match.group(0)  # Return the content between opener and closer, and the match object for the closer
        raise MarkupExtractorError([f"Unmatched macro opener: {opener_type}"])  # No matching closing tag found
        
    
    def _get_macro(self, text: str) -> re.Match | None:
        match = self._patterns.build_macro_with_stack_pattern().match(text)
        return match if match else None
            
    
    def get_html_params(self, text: str) -> dict:
        match = self._get_html_tag(text)
        if not match:
            raise MarkupExtractorError([f"Failed to extract html macro from text: {text}"])
        html_tag = match.group("html_tag")
        if html_tag is None:
            raise MarkupExtractorError([f"Regex match missing group: {match}"])
        html_content = self._extract_full_html_content(html_tag, text[match.end():])
        return {
            "offset": len(match.group(0)) + len(html_content),
            "kind": "html", 
            "tag": html_tag, 
            "body": match.group(0) + html_content
            }
    
    def _get_html_tag(self, text: str) -> re.Match | None:
        match = self._patterns.build_html_pattern().match(text)
        return match if match else None
    
    def _extract_full_html_content(self, opener_tag: str, text: str) -> str:
        stack = 1
        for match in self._patterns.build_html_content_pattern().finditer(text):
            html_tag = match.group("html_tag")
            if html_tag is None:
                raise MarkupExtractorError([f"Regex match missing group: {match}"])
            if html_tag == self._fmt.html.close_tag + opener_tag:
                stack -= 1
            if html_tag == opener_tag:
                stack += 1
            if stack == 0:
                return text[:match.end()]  # Return the content between opener and closer
        raise MarkupExtractorError([f"Unmatched html tag opener: {opener_tag}"])  # No matching closing tag found