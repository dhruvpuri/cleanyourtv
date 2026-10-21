# Themes

A theme is a folder with a `config.json` and, optionally, a `wallpaper.jpg`. Pushing one changes the
launcher's dock, layout and look on the TV without rebuilding the APK: the launcher reads
`config.json` as an overlay over its built-in `config.xml` the next time it starts.
Choices made in Launcher settings take priority until you choose Follow theme. Pushing a theme or
using `tools/theme.sh --reset` also clears those on-TV column and motion choices.

```bash
TV_HOST=192.168.1.50 tools/theme.sh themes/aurora          # push a theme and restart Home
TV_HOST=192.168.1.50 tools/theme.sh --reset                # back to the built-in config.xml
powershell -ExecutionPolicy Bypass -File tools\theme.ps1 -TvHost 192.168.1.50 themes\aurora
```

| Theme | What it does |
|---|---|
| `default/` | The built-in look written out as JSON, as a starting point for your own |
| `aurora/` | A dark aurora wallpaper (teal and violet on navy, darker at the bottom) with a matching background colour |
| `dussehra/` | Festive skin for Dussehra (ends 21 Oct 2026): a marigold toran, a faint gold rangoli, a diya for Wi-Fi, a bell for Inputs, a marigold for Settings and a petal shower |
| `six-columns/` | Six smaller tiles per row and one grid row visible under the dock |

## Keys

Every key is optional; a missing key keeps the value from `config.xml`, an unknown or wrongly typed key
is ignored, and a file that doesn't parse is ignored as a whole, so a theme can never break Home.

| Key | Type | Meaning |
|---|---|---|
| `dock_apps` | list of package names | The dock row, in order; missing apps are skipped |
| `fill_dock` | bool | Fill the dock slots `dock_apps` leaves free with the first grid apps (true by default); false leaves them empty |
| `hidden_apps` | list of package names | Never shown as tiles |
| `live_tv_package`, `live_tv_action` | string | The Live TV app and, if it has no leanback entry, the action to start it with |
| `source_panel_service`, `source_panel_action` | string | The TV's own source panel, for sets with no TvInputManager |
| `input_action` | string | Action sent with an HDMI/AV row's channel URI when nothing handles the standard `VIEW` (XGIMI: `com.xgimi.action.hdmiPlayer`) |
| `columns` | 1 to 8 | Tiles per row; tiles shrink to fit from 5 up |
| `rows_below_dock` | 0 to 3 | Grid rows left visible under the dock; tiles shrink if the dock, its title and that many rows would not fit the screen height |
| `dock_title` | bool | The focused dock app's name in large type above the dock (`true`); `false` keeps only the glow |
| `dock_row` | bool | The dock as its own row with a band (`true`); `false` makes the dock apps the first tiles of one plain grid |
| `reorder_button` | bool | A reorder button in the top bar (`false` by default); reordering is always in the Settings button's long-press menu |
| `show_bluetooth_pill` | bool | A Bluetooth pill in the top bar, between Wi-Fi and Settings (`false` by default). A press restarts Bluetooth, which makes the TV reconnect its paired devices; hold OK to open Bluetooth settings. Needs Android 11 or older, where apps may still switch Bluetooth |
| `show_sleep_pill` | bool | A sleep-timer pill in the top bar, after the Bluetooth pill (`false` by default). OK steps Off, 15, 30, 60, 90 minutes, Off, and the pill shows the minutes left; the countdown keeps running over other apps and then locks the screen, which puts the TV to sleep, after a toast one minute before. It needs the Home button accessibility service (`HomeKeyService`) to be enabled, because that service does the counting; without it the pill shows "Not available on this TV". Locking the screen needs Android 9 or newer |
| `show_settings_pill` | bool | The Settings pill at the end of the top bar (`true` by default). `false` frees its room, but it also hides the launcher settings menu (hold OK on that pill, which holds Launcher settings, Module cards and Reorder); set it back to `true` to get the menu back. Pair it with `settings_key_scancodes` or `settings_key_keycodes` so the remote's gear button still opens Settings |
| `app_library` | bool | An App library pill after the last Home row: every installed app, add one to Home or take it off (`false` by default). The choices stay on the TV when a theme is pushed or reset; see [docs/app-library.md](../docs/app-library.md) |
| `shamsi_date` | bool | Show the Solar Hijri date above the Gregorian one |
| `module_cards` | bool | Look for module cards and ask about them (`true`); `false` turns the feature off |
| `reduced_motion` | bool | Calmer motion for weak GPUs: stiff highlight spring, no tile overshoot, short fades, no entrance replay |
| `vpn_app` | string | App the network pill opens when a VPN is configured; also shows a red "VPN off" badge while no VPN is up |
| `animations` | bool | Basic focus, glass, title and tile entrance motion; true by default |
| `advanced_effects` | bool | Optional lifted tile, icon zoom, smooth ambient colour and app opening effects; false by default |
| `show_home_settings_shortcut` | bool | Keep the optional Default-home tile visible when the TV has a home picker; false by default |
| `show_stats` | bool | One line under the clock with CPU, free memory and free storage. Off unless set |
| `background_color` | `#RRGGBB` | Colour behind everything; black by default |
| `sky_intensity` | 0 to 100 | Time-of-day backdrop: a dark gradient that follows the clock, 0 hides it (default) |
| `wallpaper` | bool | Show `wallpaper.jpg` from the theme folder (`true`), or ignore it (`false`) |
| `festival` | string | Turns on a festive skin: the network pill becomes a diya whose flame follows the connection, Inputs a temple bell, Settings a marigold, and the first Home of the day gets a petal shower. `dussehra` and `diwali` have built-in greetings |
| `festival_until` | `YYYY-MM-DD` | Last day the festive skin shows; it switches itself off after that. A malformed date turns it off |
| `greeting` | string | Replaces the time-of-day greeting while the festive skin is on |
| `accent_color` | `#RRGGBB` | Colour of the focus glow while the festive skin is on; diya gold if not set |
| `settings_key_scancodes` | list of scancodes | Remote buttons that open Settings by raw scancode, for buttons Android has no keycode for (Xiaomi/Fengmi projector gear: `[384]`; XGIMI Vibe One gear: `[66]`). Find it with `tools/tv.py 'getevent -l -c 8'` while pressing the button |
| `settings_key_keycodes` | list of keycodes | Remote buttons that open Settings, for `HomeKeyService` (TCL Google TV gear: `[83]`) |
| `settings_key_panel` | bool | Those buttons open a small quick settings panel (TV settings, Display, Network, Apps, Launcher settings) instead of the TV's Settings |
| `key_shortcuts` | object | Remote keycode to the package `HomeKeyService` launches when that key is released; theme only, empty by default. See [Key shortcuts](#key-shortcuts) |

## Wallpapers

`wallpaper.jpg` is drawn full screen behind the launcher, centre-cropped. Keep it dark, 1920×1080 and
under about 300 KB: the text, the hero name and the dock band are designed for black, and a 1 GB TV
decodes the picture into memory on every Home start. Pictures larger than the screen are scaled down to
it; a picture that is still over 4K (about 8.4 million pixels) after it is sampled down to the screen is not shown at all, and the plain colour stays.

## Reduced motion

`"reduced_motion": true` keeps the look but calms the movement: the highlight spring is stiff instead
of bouncing, tiles zoom without overshoot, fades are shorter, and Home does not replay the tile
entrance when you come back to it. Use it on TVs whose GPU cannot keep up; a MediaTek MT5895 on
Android 10 is the known case. The default, `false`, keeps the normal motion.

```json
{ "reduced_motion": true }
```

## Time-of-day backdrop

`"sky_intensity": 60` draws a dark gradient over the wallpaper and behind everything else, that follows the
clock: night blues, a soft blue day, then a warm horizon that peaks just before eight in the evening.
The glow near the bottom edge travels from left to right with the sun. The colours stay dark so the
white clock, the hero name and the dock band keep their contrast. It is drawn as one 480×270 bitmap
and redrawn once a minute, never animated, so even a 1 GB TV has nothing to keep up with. `0` keeps
the plain background; the default is off (the reference launcher looks exactly as before).

```json
{ "sky_intensity": 60 }
```

## Key shortcuts

`"key_shortcuts"` maps a remote button to an app. A key is a `KEYCODE_` name or a plain keycode number;
an entry with an unknown key or an empty package is skipped.

```json
{ "key_shortcuts": { "KEYCODE_F4": "io.gh.reisxd.tizentube.cobalt", "KEYCODE_F8": "org.videolan.vlc" } }
```

`HomeKeyService` launches the app when the key is released. It sees the key before the system or the
manufacturer's own key handler does and consumes it, even if the app is not installed (a toast says it
is not available). It only works while the accessibility service is enabled: install with
`HOME_KEY_SERVICE=1`. `tools/theme.sh` restarts the service when it pushes a theme. To find a remote's
keycodes, press its buttons while running `tools/tv.py 'logcat -v time | grep -i keycode'`, or use `getevent`.

## Adding a theme

Open a PR with a new folder here, a one-line row in the table above and a screenshot from a real TV
in the PR description. Keep the dock list generic (the big streaming apps) unless the theme is for a
specific TV, and say which TV you tried it on.
