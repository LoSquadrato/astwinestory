# StoryLoom — Editor for Interactive Stories

StoryLoom is a tool for parsing, translating, and converting interactive stories in Twine (`.twee`) format.
The idea is to provide a CLI for serializing stories into a JSON intermediate format, which can then be translated or processed and re-exported into `.twee` files.

---

## Getting Started

### Requirements
> Python 3.11 or higher

### Installation

```shell
git clone https://github.com/LoSquadrato/StoryLoom.git
cd StoryLoom
pip install -r requirements.txt
```
### Usage

Have a `.twee` file ready and the [format JSON file](##JSON-Library) of the story format inside the `core/assets/formats` folder, then run the following command:

```shell
python3 main.py story.twee
```
REPL Input:
* Select Output Format from the JSON file provided inside the `core/assets/formats` folder
* Select Function from a list menu
* Select Output File Name (or use the one suggested by the program)

## WARNING:
> StoryLoom is still in development and not yet stable. Make a backup of your work before using it. 

> Change only story that's are your own, or that you have permission to modify. Every copyrighted work is protected by law, and StoryLoom is not responsible for any illegal use of the software.  

---

## AST Structure

### Overview

The AST is organized into three hierarchical levels:

* `Story` — global container with metadata
* `Passage` — single passage
* `Node` — atomic content unit

Narrative hierarchy between passages is not structurally represented in the AST — it is implicit in `LinkNode`, because `.twee` files do not guarantee sequential ordering.

For translation purposes, this is not a problem: `TextNode` instances are extracted in parsing order.

---

### Story Class

Global story container. Metadata comes from the `StoryData` block in the `.twee` file.

```python
@dataclass
class Story:
    title:          str
    format:         FormatDefinition
    format_version: str
    passages:       list[Passage]
```

---

### Node Hierarchy

All nodes inherit from `Node`, which only defines `node_id`.
The ID is a globally progressive integer, unique across the entire story, that can retrieve the node in the AST for translation purposes.

```python
@dataclass
class Node:
    node_id: int
```

---

### Passage Class

Represents a single passage in the `.twee` file.
.   

```python
@dataclass
class Passage(Node):
    name:        str
    tags:        str
    metadata:    str
    children:    list[Node]
```

---

### TextNode

User-visible narrative text.

```python
@dataclass
class TextNode(Node):
    value: str
```

---

### VariableNode

Game variable.
`scope` distinguishes global vs local variables.

```python
@dataclass
class VariableNode(Node):
    name:  str
    scope: str   # 'global' | 'local'
```

---

### LinkNode

Navigation link to another passage. Display text is optional; if omitted, the target passage name is used as display text.

```python
@dataclass
class LinkNode(Node):
    display: str
    target:  str
```

---

### MacroNode

Game macro (`if`, `link`, `set`, `print`, etc.).
May contain child nodes, including nested `MacroNode`.

```python
@dataclass
class MacroNode(Node):
    macro_type: str
    children: list[Node]
    hook: HookNode  
```
---

### HookNode

Hook node for macro content. Used to attach a macro to a specific passage or content block.

```python
@dataclass
class HookNode(Node):
    hooked_macro_id: int
    children: list[Node] = field(default_factory=list)
```

---

### LiteralNode

Hardcoded string or numeric value inside a macro.
Never translated.

```python
@dataclass
class LiteralNode(Node):
    value: str
```

---

### OperatorNode

Syntactic operator inside a macro.

```python
@dataclass
class OperatorNode(Node):
    operator: str
```

---

### FormattingNode
Formatting node for MarkDown style formatting key (bold, italic, underline, etc.).
    
```python
@dataclass
class FormattingNode(Node):
    value: str
```

---

### MetaNode

Fallback node for content that must pass through untouched
(CSS, JavaScript, tag, metadata).

```python
@dataclass
class MetaNode(Node):
    kind: str
    raw: str | list[Node]
```

---

### HTMLNode
HTML node for content that must pass through untouched.

```python
@dataclass
class HTMLNode(Node):
    tag: str
    body: str = ""
```

---

### Full-Story Translation Key Logic

Each `TextNode` is wrapped with markers:

```
%%TX_8%% Good morning, %%/TX_8%%
%%TX_13%% Still sleeping. %%/TX_13%%
```

The extracted text can be sent to a translation service, and the translated text can be re-inserted into the AST using the same markers.

---

## JSON Library

The core of StoryLoom is a JSON library that contains all the semantics and information of Twine formats (Name, Version, Syntax Style) and the macros, links, meta delimiters, and other syntax elements.

In the `core/assets/formats` folder you can put JSON files representing Twine formats, and StoryLoom will be able to parse and translate them.

Every Twine format is represented as a `FormatDefinition` object, which is serialized into JSON for round-trip translation and re-export.

If two libraries matching most of the fields can be converted into each other, StoryLoom can translate between them.

---

## Future Work

* Finalize the AST structure and the parsing logic.
* Implement the conversion between different Twine formats.
* Implement the translation logic, including the extraction of text nodes and re-insertion of translated text.
* Implement a buffering system for reading and writing large stories, to avoid memory issues.
* Implement a GUI for easy story management.

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes. Make sure to follow the coding style and include tests for any new features or bug fixes.

---

### License

**License**: GPL v3 (GNU General Public License v3)
