from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "chunk-status",
    "five-a-side",
    "grill-me",
    "implement-issues",
    "next-batch",
    "ship",
    "tdd",
    "to-issues",
    "to-prd",
)


class AgentCompatibilityTests(unittest.TestCase):
    def test_codex_discovery_links_cover_every_canonical_skill(self):
        discovery = ROOT / ".agents" / "skills"
        self.assertTrue(discovery.is_dir())

        for skill in SKILLS:
            link = discovery / skill
            self.assertTrue(link.is_symlink(), f"{skill} is not a Codex discovery symlink")
            self.assertEqual(link.resolve(), (ROOT / skill).resolve())

    def test_skill_frontmatter_names_match_directory_names(self):
        for skill in SKILLS:
            text = (ROOT / skill / "SKILL.md").read_text()
            name = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
            description = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
            self.assertIsNotNone(name, f"{skill} has no name")
            self.assertIsNotNone(description, f"{skill} has no description")
            self.assertEqual(name.group(1), skill)
            self.assertIn(f"Codex ${skill}", description.group(1))

    def test_five_a_side_declares_its_codex_adapter(self):
        skill = (ROOT / "five-a-side" / "SKILL.md").read_text()
        adapter = ROOT / "five-a-side" / "references" / "codex-adapter.md"
        self.assertTrue(adapter.is_file())
        self.assertIn("references/codex-adapter.md", skill)


if __name__ == "__main__":
    unittest.main()
