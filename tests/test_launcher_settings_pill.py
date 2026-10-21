"""Guard the Settings pill switch (show_settings_pill) across config, code and docs.

Hiding the pill must not leave the top bar's focus handling or the launcher menus tied to it.

Run from the repository root: python3 -m unittest discover -s tests -v
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "launcher/app/src/main/res"
JAVA = ROOT / "launcher/app/src/main/java/com/gathin/tvhome"
ANDROID = "{http://schemas.android.com/apk/res/android}"


def main_activity():
    return (JAVA / "MainActivity.java").read_text(encoding="utf-8")


def method_body(source, signature):
    return source.split(signature, 1)[1].split("\n    }\n", 1)[0]


class SettingsPillConfigTest(unittest.TestCase):
    def test_config_xml_shows_the_pill_by_default(self):
        bools = {b.attrib["name"]: b.text.strip()
                 for b in ET.parse(RES / "values/config.xml").getroot() if b.tag == "bool"}
        self.assertEqual("true", bools.get("show_settings_pill"))

    def test_config_reads_the_key(self):
        self.assertIn('"show_settings_pill"', (JAVA / "Config.java").read_text(encoding="utf-8"))

    def test_both_home_layouts_still_define_the_pill_visible_by_default(self):
        for layout in ("layout", "layout-iw"):
            with self.subTest(layout=layout):
                pills = [v for v in ET.parse(RES / layout / "activity_main.xml").iter()
                         if v.get(ANDROID + "id") == "@+id/btnSettings"]
                self.assertEqual(1, len(pills))
                self.assertIsNone(pills[0].get(ANDROID + "visibility"))


class SettingsPillDocsTest(unittest.TestCase):
    def test_docs_name_the_key(self):
        for doc in ("themes/README.md", "README.md"):
            with self.subTest(doc=doc):
                self.assertIn("`show_settings_pill", (ROOT / doc).read_text(encoding="utf-8"))

    def test_theme_readme_says_the_launcher_menu_goes_with_the_pill(self):
        row = next(line for line in (ROOT / "themes/README.md").read_text(encoding="utf-8").splitlines()
                   if line.startswith("| `show_settings_pill`"))
        self.assertIn("hides the launcher settings menu", row)


class SettingsPillCodeTest(unittest.TestCase):
    def test_the_activity_hides_the_pill_from_config(self):
        self.assertIn("btnSettings.setVisibility(cfg.showSettingsPill", main_activity())

    def test_pill_keys_trap_the_edges_of_the_visible_pills_not_the_settings_pill(self):
        source = main_activity()
        start = source.index("View.OnKeyListener pillKeys")
        keys = source[start:source.index("btnInputs.setOnKeyListener(pillKeys)", start)]
        self.assertIn("edgePill(", keys)
        self.assertNotIn("R.id.btnSettings", keys)
        self.assertNotIn("R.id.btnInputs", keys)

    def test_edge_pill_skips_pills_that_are_gone(self):
        body = method_body(main_activity(), "private static View edgePill(")
        self.assertIn("View.VISIBLE", body)

    def test_the_menus_do_not_hang_from_a_pill_that_may_be_gone(self):
        source = main_activity()
        for signature in ("private void showSettingsMenu()", "private void showModuleCardsNow()"):
            with self.subTest(method=signature):
                body = method_body(source, signature)
                self.assertIn("menuAnchor()", body)
                self.assertNotIn("R.id.btnSettings", body)


if __name__ == "__main__":
    unittest.main()
