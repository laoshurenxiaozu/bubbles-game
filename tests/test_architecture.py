import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArchitectureTest(unittest.TestCase):
    def test_ui_modules_do_not_import_scenes(self):
        violations = []
        for path in (ROOT / "ui").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.module and node.module.startswith("scenes"):
                    violations.append(f"{path.name}:{node.lineno}")

        self.assertEqual([], violations)

    def test_core_systems_do_not_depend_on_scenes_or_ui(self):
        violations = []
        for path in (ROOT / "core").glob("*.py"):
            if path.name == "game.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.module and node.module.startswith(
                    ("scenes", "ui")
                ):
                    violations.append(f"{path.name}:{node.lineno}")

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
