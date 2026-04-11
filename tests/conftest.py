from pathlib import Path
import sys

import pydantic


# Ensure tests can import the project package via absolute imports (from core...)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _assert_pydantic_v2() -> None:
	version = getattr(pydantic, "__version__", "0")
	try:
		major = int(version.split(".", 1)[0])
	except (TypeError, ValueError):
		major = 0

	if major < 2:
		path = getattr(pydantic, "__file__", "<unknown>")
		raise RuntimeError(
			"StoryLoom tests require pydantic>=2.0 (model_validator API). "
			f"Detected pydantic {version} from {path}. "
			"Use the project environment/interpreter and reinstall requirements."
		)


_assert_pydantic_v2()