## Introduction:

StoryLoom is a Python library designed to extract and process content from Twine stories. It provides tools for parsing Twine story formats, extracting macros, and handling nested content structures. Here's a brief overview of the key components and features of StoryLoom.

---

## Indices:

1. [Format Definitions](#1-format-definitions)
2. [Functions](#2-functions)
3. [Node Definitions](#3-node-definitions)
4. [Configuration](#4-configuration)

---

## 1. Format Definitions (./core/assets/formats)

Format definitions are JSON files that describe the structure and syntax of different Twine story formats. These definitions include information about macros, links, metadata, and other syntax elements. StoryLoom uses these definitions to parse and translate Twine stories.

#### 1.1 Example Format Definition (Harlowe 3.2.2)

```json
{
    "name": "Harlowe",
    "version": "3.2.2",
    "syntaxtype": "harlowe",
    "variables": {
    "global_prefix": "$",
    "local_prefix": "_"
     },
    "macros": {
        "open": "(",
        "close": ")",
        "hook_open": "[",
        "hook_close": "]"
    },
    "links": {
        "open": "[[",
        "close": "]]"
    },
    "metadata": {
        "open": "::",
        "close": "\n"
    }
}
``` 

#### 1.2 Mandatory Fields in Format Definitions

Mandatory fields in format definitions are the following:

* `name`: The name of the Twine format.
* `version`: The version of the Twine format.
* `syntaxtype`: The syntax style used in the Twine format (*markup* or *linear* are supported).
* `variables`: The variable prefixes used in the Twine format.
* `links`: The syntax for links in the Twine format.

#### 1.3 Name, Version, Syntaxtype

Are suggested to use an unique name and version for your format definition. The parsed story structure save the format data for later analysis and decoding and need to find the exact same JSON format file its use for the parsing process

Syntaxtype change the function behaviors when work with macro:
* **MARKUP:** are the distinguish 'Sugarcube' macro style, where some macro hooks are enclosure bethween two macro signatures, the first can have conditions, the second have a closure tag before the macro tag, in a matter like html script.
* **LINEAR:** are the distinguish 'Harlowe' macro style, where macros and hooks are presentend in line, conditions can contains other macros.

#### 1.4 Variables

Variables can be global or local. It's needed to declare both prefix tag. In the FormatDefinition they are declared by a VariableDefinition object containing the global and local prefix.

#### 1.5 Links

Links are Twee format distinctive passage pointer declaration. They are enclosure between double square brackets. The link can be a simple passage name or passage name with display text separated by pipe character ('separator').
In the FormatDefinition they are declared by a LinkDefinition object containing the open and close tag and the separator character.

#### 1.6 Macros

Macros are the main content control structure in Twine stories. They can be used to define variables, create conditional content, and control the flow of the story. Macros can have hooks, which are sections of content that are conditionally displayed based on the macro's logic.
In the FormatDefinition they are declared by a MacroDefinition object containing:

- Open and Close tag (ex. '(' and ')');
- Hook Open and Close tag (ex. '[' and ']');
- Closure tag (ex. '/') for markup syntaxtype;
- Hooked macros dict (ex. 'if', 'else-if', 'else', 'for', 'while', 'switch', 'case', 'default')
- Plain macros dict (ex. 'set', 'print', 'display', 'goto')

**Very important** is the distinction between Hooked and Plain macros, because the extractor will use different logic to extract their content.
Hooked macros are those that have hook while Plain macros are those that do not have it.

**Very Very important** if the syntaxtype is LINEAR the control macros are splitted in two different list, *control_opener* for the opener and *control_continue* for the continue macro. The extractor use a different logic if it find a control macro opener, because the content extraction is different. The control macro continue is used to recursively extract the content of the full control macro so it can be matched with the markup syntaxtype macro node.

#### 1.7 Meta

Tags and metadata are used to provide additional information and coding control about the story or its content. They can be used to group passages, define story-wide settings, or provide other metadata that can be used by the story engine or by StoryLoom itself. In the FormatDefinition they are declared by a dictonary of list of strings. The key division and content are not used by the StoryLoom logic but can be handy for the user if he need to operate to a specific tag or metadata. Otherwise the metadata content pass every function without any change.

#### 1.8 Html

HTML tags are used to include raw HTML content in the story file. In the FormatDefinition they are declared by HtmlDefinition object. Open, Close and Close_tag are used to identify the html content, the Html_tag list don't have any use in the StoryLoom logic but can be handy for the user if he need to operate to a specific html tag. Otherwise the html content pass every function without any change.

#### 1.9 Special Passages

Special passages are passage's names that are used for special and unique purpose. In the FormatDefinition they are declared by a list of strings. The special passages content pass every function without any change, but the user can use them to identify a special passage and operate on it.

#### 1.10 Operators, Literals, Formatting (WIP: and other fields):

There's a lot of other syntax elements that can be defined in the FormatDefinition, such as operators, literals, formatting, and other syntax elements. These elements are used to define the structure and behavior of the Twine story content. In the FormatDefinition they are declared by a dictonary of list of strings. The key division and content are not used by the StoryLoom logic but can be handy for the user if he need to operate to a specific operator or literal. Otherwise the content pass every function without any change.

**WIP:** The implementation of these additional syntax elements is still in progress, and their usage may change in future versions of StoryLoom.

---

## 2. Functions (./core/src)

StoryLoom provides a set of functions to facilitate the extraction and processing of Twine story content. Function selection is provided through REPL input, allowing users to choose the desired operation interactively.

#### 2.1 Parser

Parsers are called implicitly when a story is loaded. The parser extracts the story's content and metadata, creating an Abstract Syntax Tree (AST) representation of the story based on the specified Twine format JSON definition.

#### 2.2 Extractor

Extractors are called implicitly by the parser. The extractor processes the story's content passed to it by the parser, extracting macros and html full content and nested content structures. 

The extractor uses stack logic to handle nested content, ensuring that all macros and their associated content are correctly identified and extracted returning a dictionary with the macro data that can be used by the node builder to create the AST node.

#### 2.3 Render

Renderers are selected by the user through REPL input. The renderer takes the AST representation of the story and generates a new story file in the form of a string.

#### 2.4 Transformer (!WIP!)

Transformers are implicitly called by the renderer. The transformer processes the AST representation of the story, modifying the structure and the content of the story from 'markup' to 'linear' or vice versa, based on the specified Twine format JSON definition. The transformer ensures that the story's content is correctly transformed while preserving the original meaning and structure.

#### 2.5 Text Extractor (!WIP!)

Text extractors are selected by the user through REPL input. The text extractor takes the AST representation of the story and extracts all the text content from the story, returning it as a string. The extracted text can be sent to a translation service, and the translated text can be re-inserted into the AST using the same markers.

Non-text content, such as macros, links, and metadata, is passed with the node id enclosed between tags, allowing the text extractor to identify and preserve the original structure of the story while extracting the text content.

Tags are defined by default as `%%TX_{node_id}/%%`, they can be changed inside the `config.py` file.

#### 2.6 Replacer (!WIP!)

Replacers are selected by the user through REPL input. The replacer takes the AST representation of the story and can replace some value of the nodes with new values, returning a new AST representation of the story. The replacer can be used to modify variables name, specific macro, tags, metadata, and other syntax elements. The replacer ensures that the story's content is correctly modified while preserving the original meaning and structure.

#### 2.7 Decoder (!WIP!)

Decoders return the AST representation of the story in a JSON format. The decoder can be used to analyze the structure and content of the story, providing a detailed view of the story's components and their relationships.

#### 2.8 Encoder (!WIP!)

Encoders take the AST representation of the story in a JSON format and provides a new AST representation of the story. The encoder can be used to create a new story from a JSON representation, allowing for easy manipulation and modification of the story's structure and content.

---

## 3. Node Definitions (./core/ast/nodes)

#### 3.1 Node

Node is the base class for all AST nodes. It contains the **id** common attributes and the `next_id` counter method to generate unique ids for each node. The id is used to identify the node in the AST and to create the markers for text extraction and replacement.

#### 3.2 TextNode

Text node for content that is plain text.

#### 3.3 VariableNode

Variable node for content that is a variable. Contains a scope field to identify if the variable is global or local and a value field to identify the variable name.

#### 3.4 LinkNode

Link node for content that is a link. Contains a target field to identify the passage name and a display field to identify the display text.

#### 3.5 MacroNode

Macro node for content that is a macro. Contains a macro_type field to identify the macro type, a children field to identify the nested content as a list of node and a hook field to identify the hook content as a hook node class.

#### 3.6 HookNode

Hook node for content that is a hook. Contains a hooked_macro_id field to identify the macro id which hook are refered and a children field to identify the nested content as a list of node.

#### 3.7 MetaNode

Meta node for content that is a metadata. Contains a meta_type field to identify the metadata type and a raw field to identify the nested content as a list of node.

#### 3.8 HTMLNode

HTML node for content that is a html. Contains a tag field to identify the html type and a raw field to identify the nested content as a list of node.

#### 3.9 LiteralNode, FormattingNode, OperatorNode

Nodes for content that is a literal, formatting or operator. Contains a value field to identify the literal, formatting or operator value.

#### 3.10 Passage

Special node for the whole passage content. Contains a name field to identify the passage name and a children field to identify the nested content as a list of node. It's also provide a tags and metadata field to identify the passage tags and metadata as a list of strings.

#### 3.11 Story

Special class for the whole story content. The Story object are the capstone of the AST representation of the story. It contains a name field to identify the story name, a format field to store the story format definition and a passages field to identify the nested content as a list of passage node.

The Story object is passed from the parser to the other functions.

---

## 4. Configuration (./core/config)

#### 4.1 Configuration File

The configuration file is a Python file that contains various settings and parameters used by StoryLoom. It allows users to customize the behavior of the library, including specifying the paths to format definitions, setting default values for certain operations, and defining custom tags for text extraction and replacement.

#### 4.2 Maximum Story Size (MAX_STORY_SIZE)

The maximum story size setting defines the maximum byte size of a story that can be processed by StoryLoom. This setting helps prevent memory issues when working with large stories. That can be surpassed by the buffering functionality which will be implemented in the future.

#### 4.3 Format Definitions Path (FORMAT_DIR)

The format definitions path setting specifies the directory where the JSON format definition files are located. StoryLoom uses this path to locate and load the appropriate format definitions for parsing and processing Twine stories.

#### 4.4 Text Extraction Tags (TEXT_EXCAPE_KEY)

The text extraction tags setting defines the markers used to identify and extract text content from the AST representation of the story. These tags are used by the text extractor to preserve the original structure of the story while extracting the text content. The default tags are `%%`, but they can be customized in the configuration file.

#### 4.5 Suggested Output Path (SUGGESTED_OUTPUT_DIR)

The suggested output path setting specifies the default directory where processed stories and other output files will be saved. This setting helps organize the output files generated by StoryLoom, making it easier for users to locate and manage their processed stories.
In the REPL input the user define the file name, if its already exist StoryLoom will append a number to the file name to avoid overwriting existing files.