# Twee Parser – Clean Architecture Design

## 🎯 Obiettivo

Parser robusto per file `.twee` con:

* Parsing strutturato
* Validazione separata
* Dominio pulito
* Rendering sicuro
* Round-trip validation

---

# 📐 Architettura

```
File .twee
    ↓
Lexer
    ↓
Parser
    ↓
StoryData (dict)
    ↓
Validator
    ↓
Domain Model (Story)
    ↓
Renderer
    ↓
Nuovo .twee
    ↓
Re-parse + Re-validate (round-trip)
```

Separazione netta tra:

* Parsing
* Validazione
* Dominio
* Rendering

---

# 🧱 1. Domain Model (Puro)

```python
from dataclasses import dataclass, field
from enum import Enum

class StoryFormat(str, Enum):
    SUGARCUBE = "SugarCube"
    HARLOWE = "Harlowe"
    SNOWMAN = "Snowman"


@dataclass
class Passage:
    title: str
    content: str


@dataclass
class Story:
    title: str
    ifid: str
    format: StoryFormat
    format_version: str
    start_passage: str
    passages: dict[str, Passage] = field(default_factory=dict)
```

❗ Nessuna logica dentro. Solo dati.

---

# 🛡 2. Validation Layer

## Validation Result

```python
from dataclasses import dataclass

@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.errors
```

---

## Validator

```python
import uuid

SUPPORTED_FORMAT_VERSIONS = {
    "SugarCube": {"2.37.3"},
    "Harlowe": {"3.3.9"},
}


class StoryValidator:

    @staticmethod
    def validate_structure(data: dict) -> list[str]:
        errors = []

        if not data.get("ifid"):
            errors.append("Missing IFID")

        if not data.get("start"):
            errors.append("Missing start node")

        if not data.get("format"):
            errors.append("Missing format")

        return errors

    @staticmethod
    def validate_semantics(data: dict) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        # IFID UUID check
        if "ifid" in data:
            try:
                uuid.UUID(data["ifid"])
            except Exception:
                errors.append("Invalid IFID (must be valid UUID)")

        # Format enum check
        try:
            StoryFormat(data["format"])
        except Exception:
            errors.append(f"Unsupported format '{data.get('format')}'")

        # Format-version check
        fmt = data.get("format")
        version = data.get("format-version")

        if fmt in SUPPORTED_FORMAT_VERSIONS:
            if version not in SUPPORTED_FORMAT_VERSIONS[fmt]:
                warnings.append(
                    f"Format-version '{version}' not officially supported for '{fmt}'"
                )

        return errors, warnings

    @classmethod
    def validate(cls, data: dict) -> ValidationResult:
        errors = []
        warnings = []

        errors += cls.validate_structure(data)

        sem_errors, sem_warnings = cls.validate_semantics(data)
        errors += sem_errors
        warnings += sem_warnings

        return ValidationResult(errors, warnings)
```
---

# 🎨 4. Renderer

```python
class StoryRenderer:

    @staticmethod
    def render(story: Story) -> str:
        # genera il nuovo file .twee
        ...
```

---

# 🔁 5. Round-Trip Validation

Dopo il render:

```python
rendered = StoryRenderer.render(story)

parsed_again = parse_twee(rendered)

validation = StoryValidator.validate(parsed_again)

if not validation.is_valid:
    raise Exception("Round-trip validation failed")
```

Questo garantisce:

* Output consistente
* Nessuna corruzione strutturale
* Sicurezza contro regressioni future

---

# 🧠 Validazione a Livelli

Puoi aggiungere:

* `validate_references()` → start_passage esiste nei passages
* `validate_links()` → tutti i link puntano a nodi validi
* `validate_tags()`
* `validate_story_graph()` → grafo raggiungibile

---

# 🏆 Principi Architetturali Applicati

✔ Single Responsibility
✔ Separazione Dominio / Validazione
✔ No side effects nel Model
✔ Validazione riutilizzabile
✔ Round-trip safety
✔ Estendibile per future versioni Twee

---

# 🚀 Struttura Progetto Consigliata

```
twee_parser/
│
├── lexer.py
├── parser.py
├── models.py
├── validator.py
├── factory.py
├── renderer.py
└── exceptions.py
```

---

# 🧩 Evoluzione Futura

* Modalità strict vs lax
* Logging strutturato invece di print
* Report JSON delle validation
* Plugin per nuovi formati Twine
* Test automatici di round-trip

---

**Risultato:** parser solido, estendibile e professional-grade.
