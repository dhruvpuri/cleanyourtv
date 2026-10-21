"""Guard the sleep-timer pill (show_sleep_pill) across resources, code and docs.

The pill needs strings in every locale, a view in both Home layouts and a config.xml default; the countdown
must live in HomeKeyService (it keeps running over other apps) and end in the lock-screen action.

Run from the repository root: python3 -m unittest discover -s tests -v
"""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "launcher/app/src/main/res"
JAVA = ROOT / "launcher/app/src/main/java/com/gathin/tvhome"
ANDROID = "{http://schemas.android.com/apk/res/android}"
SLEEP_STRINGS = ("sleep_timer", "sleep_minutes", "sleep_warning")


def strings(strings_xml):
    return {s.attrib["name"]: "".join(s.itertext()).strip()
            for s in ET.parse(strings_xml).getroot() if s.tag == "string"}


def source(name):
    return (JAVA / name).read_text(encoding="utf-8")


def top_bar_ids(layout):
    """The ids inside the top bar's button row, in the order the layout lists them."""
    root = ET.parse(RES / layout / "activity_main.xml").getroot()
    bar = next(v for v in root.iter() if v.get(ANDROID + "id") == "@+id/topButtons")
    return [v.get(ANDROID + "id") for v in bar]


class SleepPillResourcesTest(unittest.TestCase):
    def test_every_locale_translates_all_sleep_strings(self):
        checked = 0
        for strings_xml in sorted(RES.glob("values*/strings.xml")):
            names = strings(strings_xml)
            if "settings" not in names:
                continue
            checked += 1
            with self.subTest(locale=strings_xml.parent.name):
                for name in SLEEP_STRINGS:
                    self.assertTrue(names.get(name), "missing or empty %s string" % name)
        self.assertGreaterEqual(checked, 16)

    def test_the_minutes_string_takes_one_number_and_the_warning_none(self):
        for strings_xml in sorted(RES.glob("values*/strings.xml")):
            names = strings(strings_xml)
            if "settings" not in names:
                continue
            with self.subTest(locale=strings_xml.parent.name):
                self.assertEqual(["%1$d"], re.findall(r"%\d+\$[a-zA-Z]", names["sleep_minutes"]))
                self.assertEqual([], re.findall(r"%", names["sleep_warning"]))

    def test_both_home_layouts_define_a_hidden_sleep_text_view_with_its_icon(self):
        for layout in ("layout", "layout-iw"):
            with self.subTest(layout=layout):
                pills = [v for v in ET.parse(RES / layout / "activity_main.xml").iter()
                         if v.get(ANDROID + "id") == "@+id/btnSleep"]
                self.assertEqual(1, len(pills), "btnSleep must be defined exactly once")
                pill = pills[0]
                self.assertEqual("TextView", pill.tag)
                self.assertEqual("gone", pill.get(ANDROID + "visibility"))
                self.assertEqual("@drawable/ic_sleep", pill.get(ANDROID + "drawableStart"))

    def test_the_hebrew_top_bar_mirrors_the_default_order(self):
        default = top_bar_ids("layout")
        self.assertEqual(default[::-1], top_bar_ids("layout-iw"))
        self.assertEqual(default.index("@+id/btnBluetooth") + 1, default.index("@+id/btnSleep"))

    def test_sleep_icon_drawable_exists(self):
        self.assertTrue((RES / "drawable/ic_sleep.xml").is_file())

    def test_config_xml_hides_the_pill_by_default(self):
        bools = {b.attrib["name"]: b.text.strip()
                 for b in ET.parse(RES / "values/config.xml").getroot() if b.tag == "bool"}
        self.assertEqual("false", bools.get("show_sleep_pill"))


class SleepTimerCodeTest(unittest.TestCase):
    def test_home_key_service_counts_down_and_locks_the_screen(self):
        service = source("HomeKeyService.java")
        self.assertIn("GLOBAL_ACTION_LOCK_SCREEN", service)
        self.assertIn("Build.VERSION_CODES.P", service)
        self.assertIn("R.string.sleep_warning", service)
        self.assertIn("R.string.not_available", service.split("private void sleepNow()", 1)[1])

    def test_the_countdown_is_not_run_by_the_activity(self):
        activity = source("MainActivity.java")
        self.assertIn("SleepTimer.cycle()", activity)
        self.assertNotIn("GLOBAL_ACTION_LOCK_SCREEN", activity)
        self.assertNotIn("performGlobalAction", activity)

    def test_the_service_hands_its_countdown_to_the_state_holder_on_connect_and_destroy(self):
        service = source("HomeKeyService.java")
        self.assertIn("SleepTimer.attach(this)", service)
        self.assertIn("SleepTimer.detach(this)", service)

    def test_the_pill_is_keyboard_navigable_like_the_other_pills(self):
        activity = source("MainActivity.java")
        self.assertIn("btnSleep.setOnKeyListener(pillKeys)", activity)

    def test_the_press_cycle_is_off_15_30_60_90_off(self):
        timer = source("SleepTimer.java")
        self.assertIn("{15, 30, 60, 90}", timer)

    def test_the_unverified_device_path_is_marked(self):
        self.assertIn("not yet verified on the projector", source("HomeKeyService.java"))


class SleepPillDocsMatchCodeTest(unittest.TestCase):
    def test_theme_readme_documents_the_key(self):
        self.assertIn("`show_sleep_pill`", (ROOT / "themes/README.md").read_text(encoding="utf-8"))

    def test_readme_mentions_the_key(self):
        self.assertIn("`show_sleep_pill`", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_config_reads_the_documented_key(self):
        # A substring check, not a parse: it only guards against the docs and Config.java drifting apart.
        self.assertIn('"show_sleep_pill"', source("Config.java"))


if __name__ == "__main__":
    unittest.main()
