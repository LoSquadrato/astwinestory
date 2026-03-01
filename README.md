Below is the English translation in a technical GitHub-style format, preserving structure, terminology, and intent.

---

# StoryLoom — Design Document

> v0.1 — March 2026

---

## Table of Contents

1. [Introduction and Objective](#1-introduction-and-objective)
2. [Version Roadmap](#2-version-roadmap)
3. [General Pipeline](#3-general-pipeline)
4. [File System](#4-file-system)
5. [AST Structure](#5-ast-structure)
6. [AI Translation System](#6-ai-translation-system)
7. [JSON Serialization](#7-json-serialization)
8. [Validator](#8-validator)
9. [CLI REPL](#9-cli-repl)
10. [Design Decisions Summary](#10-design-decisions-summary)
11. [Next Steps — Milestone v0.1](#11-next-steps--milestone-v01)

---

## 1. Introduction and Objective

StoryLoom is a tool for parsing, validating, translating, and converting interactive stories in Twine (`.twee`) format. The project is structured into progressive milestones, starting from a functional CLI and evolving into a complete UI with integrated AI translation.

This document consolidates the design decisions made during the planning phase, with particular emphasis on the AST (Abstract Syntax Tree) structure, which represents the core of the system.

---

## 2. Version Roadmap

| Version | Milestone                       | Description                                                                                                       |
| ------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| v0.1    | REPL + Base Structure           | Interactive CLI, FileLoader, Validator, Passage Parser, full AST structure, JSON serialization, `.twee` re-export |
| v0.2    | Harlowe Parser                  | Full parser for Harlowe syntax                                                                                    |
| v0.3    | SugarCube Parser                | Full parser for SugarCube syntax                                                                                  |
| v0.4    | Format Conversion               | Testing and implementation of Harlowe ↔ SugarCube conversion                                                      |
| v0.5    | AI Translator — Single Passages | AI API integration for per-passage translation                                                                    |
| v0.6    | AI Translator — Full Story      | Single body with `%%TX_n%%` keys, reinsertion via `node_id`                                                       |
| v0.7    | UI                              | Graphical interface                                                                                               |
| v0.8+   | Additional Formats & Features   | Additional parsers, translatable variable handling, advanced conditional branching                                |

---

## 3. General Pipeline

```
.twee file
↓
FileLoader
↓
Raw Text
↓
Validator
(StoryData: ifid, format, format_version, start — verifies start passage exists)
↓
Passage Parser
↓
Passage Objects
↓
Content Parser (Mini-AST)
↓
Story AST
↓
JSON Serialization
↓
CLI Action / render_nodes()
↓
Output File
```

The Validator runs immediately after loading the raw file, before full parsing.
Its sole purpose is to ensure the file contains the minimum required data to produce a valid output.

No checks are performed for broken links or other internal structural issues — an author may want to process an incomplete story, and debugging story logic is not the responsibility of StoryLoom.

---

## 4. File System

```
storyloom/
│
├── main.py                      # CLI entry point
├── repl.py                      # Interactive REPL
│
├── core/
│   ├── __init__.py
│   ├── validator.py             # StoryData validation
│   │
│   ├── ast/
│   │   ├── __init__.py
│   │   ├── story.py             # Story class
│   │   ├── passage.py           # Passage class
│   │   └── nodes.py             # Node + all subclasses
│   │
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── file_loader.py       # FileLoader (format-agnostic)
│   │   ├── passage_parser.py    # Passage separation (format-agnostic)
│   │   └── format/
│   │       ├── harlowe/
│   │       │   └── harlowe_parser.py
│   │       └── sugarcube/
│   │           └── sugarcube_parser.py
│   │
│   ├── serializer/
│   │   ├── __init__.py
│   │   └── json_serializer.py
│   │
│   └── renderer/
│       ├── __init__.py
│       ├── renderer.py          # render_nodes(text_transform)
│       └── format/
│           ├── harlowe/
│           │   └── harlowe_renderer.py
│           └── sugarcube/
│               └── sugarcube_renderer.py
│
├── tests/
│   ├── test_validator.py
│   ├── ast/
│   │   ├── test_story.py
│   │   ├── test_passage.py
│   │   └── test_nodes.py
│   ├── parser/
│   │   ├── test_file_loader.py
│   │   ├── test_passage_parser.py
│   │   └── format/
│   │       ├── test_harlowe_parser.py
│   │       └── test_sugarcube_parser.py
│   ├── serializer/
│   │   └── test_json_serializer.py
│   └── renderer/
│       ├── test_renderer.py
│       └── format/
│           ├── test_harlowe_renderer.py
│           └── test_sugarcube_renderer.py
│
├── examples/
│   ├── harlowe_sample.twee
│   └── sugarcube_sample.twee
│
├── docs/
│   └── StoryLoom_DesignDoc.md
│
├── requirements.txt
└── README.md
```

`core/` separates application logic from the entry point.
The validator lives at the root of `core/` because it is transversal to the entire system.
Parser and renderer are symmetrical and divided by format, allowing new syntaxes to be added without modifying existing code.

Tests mirror the `core/` structure for immediate navigability.

---

## 5. AST Structure

### 5.1 Overview

The AST is organized into three hierarchical levels:

* `Story` — global container with metadata
* `Passage` — single passage
* `Node` — atomic content unit

Narrative hierarchy between passages is not structurally represented in the AST — it is implicit in `LinkNode`, because `.twee` files do not guarantee sequential ordering.

For translation purposes, this is not a problem: `TextNode` instances are extracted in parsing order.

---

### 5.2 Story Class

Global story container. Metadata comes from the `StoryData` block in the `.twee` file.

```python
@dataclass
class Story:
    ifid:            str
    format:          str
    format_version:  str
    start_passage:   str
    passages:        dict[int, Passage]

    def get_passage_by_name(self, name: str) -> Passage: ...
```

---

### 5.3 Passage Class

Represents a single passage in the `.twee` file.
Conditionality belongs to content (`MacroNode`), not the passage itself.

```python
@dataclass
class Passage:
    passage_id:  int
    name:        str
    tags:        list[str]
    children:    list[Node]
```

---

### 5.4 Node Hierarchy

All nodes inherit from `Node`, which only defines `node_id`.
The ID is a globally progressive integer, unique across the entire story.

```python
@dataclass
class Node:
    node_id: int
```

---

### TextNode

User-visible narrative text.
**The only node type subject to AI translation.**

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
    scope: str   # 'global' | 'local' | 'unknown'
```

---

### LinkNode

Navigation link to another passage.

```python
@dataclass
class LinkNode(Node):
    display: str
    target:  str
```

---

### MacroNode

Game macro (`if`, `else`, `set`, `print`, etc.).
May contain child nodes, including nested `MacroNode`.

`macro_type` determines translation behavior:

* `print` → string children become `TextNode` (translatable)
* all other macros → string children become `LiteralNode` (non-translatable)

```python
@dataclass
class MacroNode(Node):
    macro_type: str
    children:   list[Node]
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

### MediaNode

Multimedia asset (image, audio, video).
Pass-through node.

```python
@dataclass
class MediaNode(Node):
    media_type: str
    source:     str
```

---

### MetaNode

Fallback node for content that must pass through untouched
(CSS, JavaScript, unrecognized markup).

```python
@dataclass
class MetaNode(Node):
    raw: str
```

---

## 6. AI Translation System

### 6.1 General Principle

Translation operates exclusively on `TextNode`.
All other node types remain unchanged.

Narrative order is irrelevant; terminological consistency is achieved by sending the entire story in a single request body.

---

### 6.2 `render_nodes` Hook

```python
def render_nodes(nodes: list[Node], text_transform=None) -> str:
    result = []
    for node in nodes:
        if isinstance(node, TextNode) and text_transform:
            result.append(text_transform(node.value))
        elif isinstance(node, MacroNode):
            result.append(render_nodes(node.children, text_transform))
        else:
            result.append(render_node(node))
    return ''.join(result)
```

* Re-export: `render_nodes(nodes)`
* Translation: `render_nodes(nodes, text_transform=translate)`

---

### 6.3 Full-Story Translation Key System (v0.6)

Each `TextNode` is wrapped with markers:

```
%%TX_8%% Good morning, %%/TX_8%%
%%TX_13%% Still sleeping. %%/TX_13%%
```

The AI translates the body while preserving markers.
A post-processor extracts translated text by `node_id` and reinserts it into the AST via recursive traversal.

---

## 7. JSON Serialization

### 7.1 v0.1 Schema

Versioned for forward compatibility.

Round-trip guarantee:

```
story.to_dict() → JSON → Story.from_dict(data)
```

Must return a semantically identical story.

---

## 8. Validator

Runs after `FileLoader`, before full parsing.

Checks only:

* `StoryData` block exists
* Contains `ifid`, `format`, `format-version`, `start`
* `start` passage exists

Nothing else.

---

## 9. CLI REPL

Interactive flow:

```
python3 main.py story.twee

Loaded 12 passages.
No structural errors found.

Options:
  1) Translate (WIP)
  2) Export JSON
  3) Re-export Twee
  4) Exit
```

Operational rules:

* No crashes on invalid input
* Clear error messages
* Output generated in source file directory
* Original file is never overwritten

---

## 10. Design Decisions Summary

| Component        | Choice                         | Rationale                                  |
| ---------------- | ------------------------------ | ------------------------------------------ |
| Passage parsing  | Controlled regex               | Sufficient for `.twee` separation          |
| Content          | Mini-AST Node hierarchy        | Selective translation + faithful re-export |
| Validator        | StoryData metadata only        | Story debugging is out of scope            |
| Passage order    | Irrelevant                     | `.twee` does not guarantee narrative order |
| Node IDs         | Global progressive integer     | Simple, sufficient uniqueness              |
| Translation hook | `render_nodes(text_transform)` | Same algorithm for export and translation  |
| Translation keys | `%%TX_n%%`                     | Marked format, unlikely in natural text    |
| Target formats   | Harlowe & SugarCube            | Different syntax, equivalent AST semantics |
| Core             | Typed Python objects           | Type checking, autocompletion              |
| Intermediate     | Versioned JSON                 | Forward compatibility + round-trip         |
| CLI              | Interactive REPL               | Simple UX for early stage                  |
| AI               | Placeholder → v0.5             | Structure ready, implementation deferred   |

---

## 11. Next Steps — Milestone v0.1

Implementation order:

1. FileLoader
2. Validator
3. Passage Parser
4. Content Parser (Mini-AST)
5. JSON Serialization (full round-trip)
6. `render_nodes()`
7. `.twee` Re-export
8. CLI REPL

At the end of v0.1, StoryLoom will be:

* A structural parser for Twine stories
* A metadata validator
* An intermediate JSON generator
* A reliable `.twee` re-exporter

A solid foundation for all subsequent milestones.

---

### License

**License**: GPL v3 (GNU General Public License v3)
