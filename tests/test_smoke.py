"""Portfolio standard checks: the required files exist and no grade is public.

No lock test: the repo is not pre-registered (PROPOSAL.md), so there is
no locked proposal file to pin.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["README.md", "PROPOSAL.md", "REPORT.md", "CHANGELOG.md", "CITATION.cff", "SECURITY.md", "LICENSE",
            "docs/decisions/0001-keep-stage-folders.md", "docs/publicity.md",
            "level-1-learn/run_learn.py", "level-1-learn/results_learn.json",
            "level-2-build/run_build.py", "level-2-build/results_build.json",
            "level-3-deep/run_deep.py", "level-3-deep/sweep_deep.py", "level-3-deep/scenario_deep.json",
            "level-3-deep/results_deep.json", "level-3-deep/results_sweep.json"]
# Public grade forms: "8,200 of 10,000", "x/10000", "Grade: ...", "grade 8,700", "Total /1000".
GRADE = re.compile(r"of 10,000|/ ?10,?000|\bGrade:|\bgrade \d|/1000\b", re.IGNORECASE)
SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__", "tests"}


def public_text_files():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith((".md", ".jsx", ".js", ".mjs", ".html", ".cff", ".yml")):
                yield os.path.join(d, f)


class LayoutTest(unittest.TestCase):
    def test_required_files_exist(self):
        missing = [p for p in REQUIRED if not os.path.exists(os.path.join(ROOT, p))]
        self.assertEqual(missing, [], "missing: " + ", ".join(missing))

    def test_no_public_grade(self):
        hits = []
        for path in public_text_files():
            with open(path, encoding="utf-8") as fh:
                for n, line in enumerate(fh, 1):
                    if GRADE.search(line):
                        hits.append(f"{os.path.relpath(path, ROOT)}:{n}: {line.strip()}")
        self.assertEqual(hits, [], "grades are internal:\n" + "\n".join(hits))

    def test_grade_pattern_catches_the_old_forms(self):
        for old in ("Grade: 8,700 of 10,000", "fan-out grade: 9,533 of 10,000", "(grade 8,600 of 10,000)",
                    "| Total /1000 |"):
            self.assertRegex(old, GRADE)
        self.assertNotRegex("grades are internal", GRADE)


if __name__ == "__main__":
    unittest.main()
