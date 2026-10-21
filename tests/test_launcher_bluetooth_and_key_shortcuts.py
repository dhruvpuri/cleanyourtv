"""Guard the Bluetooth pill (show_bluetooth_pill) and key shortcuts (key_shortcuts) across resources, code and docs.

The pill needs a string in every locale, a view in both Home layouts and a config.xml default; the key
shortcuts are theme-only, so for them the docs and Config.java are what must agree.

Run from the repository root: python3 -m unittest discover -s tests -v
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "launcher/app/src/main/res"
CONFIG_JAVA = ROOT / "launcher/app/src/main/java/com/gathin/tvhome/Config.java"
MAIN_ACTIVITY_JAVA = ROOT / "launcher/app/src/main/java/com/gathin/tvhome/MainActivity.java"
HOME_KEY_SERVICE_JAVA = ROOT / "launcher/app/src/main/java/com/gathin/tvhome/HomeKeyService.java"
THEMES_README = ROOT / "themes/README.md"
ANDROID = "{http://schemas.android.com/apk/res/android}"


def strings(strings_xml):
    return {s.attrib["name"]: "".join(s.itertext()).strip()
            for s in ET.parse(strings_xml).getroot() if s.tag == "string"}


def bluetooth_pill(layout):
    pills = [v for v in ET.parse(RES / layout / "activity_main.xml").iter()
             if v.get(ANDROID + "id") == "@+id/btnBluetooth"]
    return pills


class BluetoothPillTest(unittest.TestCase):
    def test_every_locale_with_a_settings_string_translates_bluetooth(self):
        checked = 0
        for strings_xml in sorted(RES.glob("values*/strings.xml")):
            names = strings(strings_xml)
            if "settings" not in names:
                continue
            checked += 1
            with self.subTest(locale=strings_xml.parent.name):
                self.assertTrue(names.get("bluetooth"), "missing or empty bluetooth string")
        self.assertGreaterEqual(checked, 16)

    def test_both_home_layouts_define_a_hidden_bluetooth_text_view_with_its_icon(self):
        for layout in ("layout", "layout-iw"):
            with self.subTest(layout=layout):
                pills = bluetooth_pill(layout)
                self.assertEqual(1, len(pills), "btnBluetooth must be defined exactly once")
                pill = pills[0]
                self.assertEqual("TextView", pill.tag)
                self.assertEqual("gone", pill.get(ANDROID + "visibility"))
                self.assertEqual("@drawable/ic_bluetooth", pill.get(ANDROID + "drawableStart"))

    def test_every_locale_translates_the_bluetooth_restart_toast(self):
        for strings_xml in sorted(RES.glob("values*/strings.xml")):
            names = strings(strings_xml)
            if "settings" not in names:
                continue
            with self.subTest(locale=strings_xml.parent.name):
                self.assertTrue(names.get("bluetooth_restarting"), "missing or empty bluetooth_restarting string")

    def test_bluetooth_icon_drawable_exists(self):
        self.assertTrue((RES / "drawable/ic_bluetooth.xml").is_file())

    def test_config_xml_hides_the_pill_by_default(self):
        bools = {b.attrib["name"]: b.text.strip()
                 for b in ET.parse(RES / "values/config.xml").getroot() if b.tag == "bool"}
        self.assertEqual("false", bools.get("show_bluetooth_pill"))


class BluetoothLaunchTest(unittest.TestCase):
    """On Google TV the pill opens TV Settings' pairing screen, whose manifest guard is BLUETOOTH_ADMIN.

    Without the permission the launch throws SecurityException, which crashed Home on every press.
    """

    def test_manifest_declares_the_legacy_bluetooth_permissions_up_to_android_11(self):
        manifest = ET.parse(ROOT / "launcher/app/src/main/AndroidManifest.xml").getroot()
        declared = {p.get(ANDROID + "name"): p.get(ANDROID + "maxSdkVersion")
                    for p in manifest.iter("uses-permission")}
        # ADMIN guards the pairing screen and adapter.enable()/disable(); plain BLUETOOTH reads the adapter state.
        # Both are legacy: Android 12+ replaced them, so they must not be requested there.
        for name in ("android.permission.BLUETOOTH_ADMIN", "android.permission.BLUETOOTH"):
            with self.subTest(permission=name):
                self.assertIn(name, declared)
                self.assertEqual("30", declared[name])

    def test_the_pill_restarts_bluetooth_on_press_and_opens_settings_on_hold(self):
        source = MAIN_ACTIVITY_JAVA.read_text(encoding="utf-8")
        self.assertIn("BluetoothRefresh", source)
        self.assertIn("btnBluetooth.setOnLongClickListener", source)
        self.assertTrue((MAIN_ACTIVITY_JAVA.parent / "BluetoothRefresh.java").is_file())

    def test_open_survives_a_refused_launch_instead_of_crashing_home(self):
        source = MAIN_ACTIVITY_JAVA.read_text(encoding="utf-8")
        body = source.split("private void open(Intent i)", 1)[1].split("\n    }\n", 1)[0]
        self.assertIn("SecurityException", body)


class SettingsScancodesFromThemeTest(unittest.TestCase):
    """A theme can name the Settings button by scancode, so a remote's gear button needs no rebuild."""

    def test_home_key_service_takes_scancodes_from_the_loaded_config(self):
        source = HOME_KEY_SERVICE_JAVA.read_text(encoding="utf-8")
        self.assertIn("config.settingsScancodes", source)
        self.assertNotIn("R.array.settings_key_scancodes", source)


class DocsMatchCodeTest(unittest.TestCase):
    """A key that is documented but not read (or read but not documented) means the two have drifted."""

    def test_theme_readme_documents_both_keys(self):
        readme = THEMES_README.read_text(encoding="utf-8")
        for key in ("show_bluetooth_pill", "key_shortcuts", "settings_key_scancodes"):
            with self.subTest(key=key):
                self.assertIn("`%s`" % key, readme)

    def test_config_reads_both_documented_keys(self):
        # A substring check, not a parse: it only guards against the docs and Config.java drifting apart.
        source = CONFIG_JAVA.read_text(encoding="utf-8")
        for key in ("show_bluetooth_pill", "key_shortcuts", "settings_key_scancodes"):
            with self.subTest(key=key):
                self.assertIn('"%s"' % key, source)


if __name__ == "__main__":
    unittest.main()
