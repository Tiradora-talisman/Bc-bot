"""
BC Color Finder - ONE file, no other files needed except your script (cave_bot_short.txt).

Run:  py color_fix.py

1. Open the game, click Start. The window shows which colors it sees.
2. Play through the bot's states until the "Ever" column says yes.
3. Click Build script. The new script appears in the box: press Copy.
   It is also saved as <name>_FINAL.txt next to the script.
"""
import os
import re
import sys
import math
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ctypes import wintypes

import numpy as np
from PIL import ImageGrab

APP = os.path.dirname(os.path.abspath(__file__))
INTERVAL_MS = 900
CAND_DIST = 40
MAX_RESIDUAL = 25
ACCEPT_DIST = 18
SMALL_AREA = 3000

FIND_RE = re.compile(
    r"findcolor\s*\(\s*(\d+)\s*,?\s*(\d+)\s+(\d+)\s*,?\s*(\d+)\s+"
    r"\(?\s*(\d+|%\w+\[[^\]]*\])\s*\)?\s*(?:\d+\s+)?%"
)
FIND_ANY = re.compile(
    r"findcolor\s*\(\s*(\d+)\s*,?\s*(\d+)\s+(\d+)\s*,?\s*(\d+)\s+"
    r"\(?\s*(\d+|%\w+\[[^\]]*\])\s*\)?\s*%arr\s*\)"
)
SET_COLOR_RE = re.compile(r"^\s*set\s+%color\[\d+\]\s+(\d+)")

EMBEDDED_SCRIPT = r'''// Cave bot (short version)
// Change the keys in the SETTINGS block below to match your hotbar.

// SETTINGS

// Class: 1 = healer (fairy), 0 = any other class
set #healer 1

// Hotbar keys
// Leave a key blank (nothing after the name) if you do not use it, for example the mana keys on a class with no mana
// Do not change $empty, the script uses it to detect blank keys
set $empty
// Up to 4 attack keys, used in order. Leave unused ones blank
set $key_attack1 1
set $key_attack2 1
set $key_attack3 1
set $key_attack4 1
// How many attack rounds per pass (each round uses all attack keys once)
set #attack_rounds 300
set $key_target tab
set $key_teleport 4
set $key_mountspeed 3
set $key_mount 0
set $key_hp 8
set $key_hp_quick 7
// Healer (fairy) heal key, used instead of $key_hp_quick when #healer = 1
set $key_fairy_heal 2
set $key_mana 9
set $key_mana_quick 6
set $key_team F
set $key_inventory I

// Key held down the whole run to remove everyone. Keep the braces, for example {F12} or {F11}
// Leave it blank to skip
set $key_remove_everyone {F12}

// Where to click the item to sell (x and y in the game window, use ctrl+a to get them)
set #sell_x 483
set #sell_y 326

// Wait between teleport clicks in ms. Set it to whatever works for your mount (example: 2700)
set #tpwait 2200

// Mount speed: while it is active, #tpwait is reduced by #speed_reduction
// (example: the wait drops from 2700 to 2200 for 30s, then goes back to 2700)
set #speed_reduction 0
// How long the speed lasts in ms: 30s minus about 3s of safety
set #speed_time 2500

wait 1s

// MAIN FLOW
// Repeats forever: after the loot the bot starts again from the top
while 1

    gosub remove_everyone
    gosub setup
    gosub wait_for_account
    gosub invite_team
    gosub heal

    // Select the transport fairy, equip the mount, go to the 45 level map
    gosub select_fairy

    // Sell items, walk to the cave and enter it
    gosub sell_items
    gosub auto_path
    gosub enter_cave
    gosub remove_everyone

    // Leave the team and follow the teleport route to the boss floor
    gosub leave_team
    gosub cave_route
    gosub remove_everyone

    // Fight the boss and pick up the loot
    gosub boss_fight
    gosub loot
end_while


// SUBROUTINES

// Hold the remove everyone key, skipped if the key is blank
:remove_everyone
if_not $key_remove_everyone = $empty
    send_down $key_remove_everyone
end_if
return

:setup
repeat 3
    left 997, 97
end_repeat
left 864, 55
wait 1s
return

// Press the teleport key until the account is close
:wait_for_account
while 1
    set #a findcolor (964, 111 1142, 571 6908994  %arr)
    if #a > 0
        break
    end_if
    send $key_teleport
    wait 50
end_while
return

// Invite the team members, repeat until the color is found
:invite_team
while 1
    set #a findcolor (55 193 63 224 (65699) %arr)
    if #a > 0
        break
    end_if
    send $key_team 1000
    left 708, 198
    wait 1s
    right 601, 253
    wait 1s
    left 642, 323
    wait 1s
    send $key_team
    wait 1s
    wait 50
end_while
return

// Press the key in $k only if it is not blank
:press_optional_key
if_not $k = $empty
    send $k
end_if
return

// Quick heal (the healer uses its own key)
:press_quick_heal
if #healer = 1
    send $key_fairy_heal
else
    send $key_hp_quick
end_if
return

// Press the attack key in $k only if it is not blank, then switch target
:press_attack
if_not $k = $empty
    send $k 1200
    send $key_target
end_if
return

// Use every assigned attack once, in order, and check HP and mana after each key that was pressed
:use_attacks
set $k $key_attack1
gosub press_attack
if_not $k = $empty
    gosub check_heal
    gosub check_mana
end_if
set $k $key_attack2
gosub press_attack
if_not $k = $empty
    gosub check_heal
    gosub check_mana
end_if
set $k $key_attack3
gosub press_attack
if_not $k = $empty
    gosub check_heal
    gosub check_mana
end_if
set $k $key_attack4
gosub press_attack
if_not $k = $empty
    gosub check_heal
    gosub check_mana
end_if
return

// One round: all attacks (each followed by a target switch), then a final heal check
:attack_round
gosub use_attacks
gosub check_heal
return

// HP check used during the fight
// Healers: if HP is low, click self and heal until the mark point is found (max 10 heals)
// Other classes: if HP is low, press the quick heal key once
:check_heal
if #healer = 0
    set #b findcolor (106, 43 114, 74 425 %arr)
    if #b = 0
        send $key_hp_quick
    end_if
    return
end_if

set #b findcolor (155, 42 898, 468 131246 %arr)
if #b = 0
    set #heals 0
    set #stop findcolor (215, 41 958, 467 65693 %arr)
    while #stop = 0
        left 46, 37
        send $key_fairy_heal
        wait 500

        set #stop findcolor (215, 41 958, 467 65693 %arr)
        set #heals #heals + 1
        if #heals >= 10
            break
        end_if
    end_while
end_if
return

// If the mana color is not found (mana bar has dropped), press the quick mana key once
:check_mana
set #m findcolor (148, 53 976, 471 11229696 %arr)
if #m = 0
    send $key_mana_quick
end_if
return

// Heal until the mark point is found, keep using mana while the mana color is detected,
// then hold the down arrow key
:heal
while 1
    // Healers click themselves first
    if #healer = 1
        left 46, 37
    end_if

    gosub press_quick_heal
    set $k $key_mana_quick
    gosub press_optional_key

    send $key_hp
    set $k $key_mana
    gosub press_optional_key
    wait 500

    set #a findcolor (215, 41 958, 467 65693 %arr)
    if #a > 0
        break
    end_if
end_while

set #a findcolor (206, 53 302, 506 3676432 %arr)
while #a > 0
    set $k $key_mana_quick
    gosub press_optional_key
    set $k $key_mana
    gosub press_optional_key
    wait 500
    set #a findcolor (206, 53 302, 506 3676432 %arr)
end_while

send_down {down}
wait 1s
left 867, 53
wait 1s
return

// Select the transport fairy, equip the mount and go to the 45 level map
:select_fairy
set #tries 0
set #a findcolor (260, 227 268, 258 12047615 %arr)
while #a = 0
    double_right 463, 474

    set #a findcolor (260, 227 268, 258 12047615 %arr)
    set #tries #tries + 1
    if #tries >= 30
        break
    end_if
end_while

send $key_mount
wait 3s

left 311, 552
wait 2s
return

// Sell the items and go to the 48 level map
:sell_items
// Open the seller (max 30 tries)
set #tries 0
set #a findcolor (388, 655 396, 686 3504050 %arr)
while #a = 0
    right 300, 220
    right 307, 207
    right 322, 255
    right 300, 220
    wait 2s

    set #a findcolor (388, 655 396, 686 3504050 %arr)
    set #tries #tries + 1
    if #tries >= 30
        break
    end_if
end_while

left 279, 392
wait 2s

repeat 10
    left #sell_x #sell_y
    wait 100

    // Accept the weapon confirmation window if it opens
    set #a findcolor (457, 334 465, 365 3636666 %arr)
    if #a > 0
        left 445, 325
    end_if
end_repeat

left 498, 711
wait 2s

// Select the NPC for the 48 level map (max 30 tries)
set #tries 0
set #a findcolor (385, 659 1118, 1063 2379641 %arr)
while #a = 0
    right 473, 377
    right 479, 333
    right 473, 377
    right 468, 357
    wait 1s

    set #a findcolor (385, 659 1118, 1063 2379641 %arr)
    set #tries #tries + 1
    if #tries >= 30
        break
    end_if
end_while

left 317, 381
wait 1s

// Open the auto path window
left 979, 62
wait 1s
left 594, 415
wait 1s
return

// Use the auto path until the map color is found (max 30 rounds)
:auto_path
repeat 30
    set #a findcolor (916, 133 924, 164 1644972 %arr)
    if #a > 0
        break
    end_if
    left 359, 273
    wait 10s
end_repeat
wait 2s

left 448, 536
wait 1s
return

// Repeat the entry clicks until we teleport into the cave
:enter_cave

set %sx[1] 495
set %sy[1] 383
set %sx[2] 470
set %sy[2] 411
set %sx[3] 496
set %sy[3] 350
set #i 1
set #known 0

set #a findcolor (916, 133 924, 164 1644972 %arr)

while #a > 0

    if #known = 0

        double_right %sx[#i] %sy[#i]
        wait 50
        set #b findcolor (389, 655 1113, 1083 3504050 %arr)

        if #b > 0
            set #known 1
        else
            set #i #i + 1
            if #i > 3
                set #i 1
            end_if
        end_if

    else

        repeat 3
            double_right %sx[#i] %sy[#i]
        end_repeat

        wait 50
        set #b findcolor (389, 655 1113, 1083 3504050 %arr)

        if #b > 0
            left 266, 366
        end_if

    end_if

    set #a findcolor (916, 133 924, 164 1644972 %arr)

end_while

wait 2s
return

:leave_team
right 50, 52
wait 500
left 104, 94
wait 500
return

// Follow the teleport route to the boss floor
:cave_route
// Only run the route if this color is found (first floor)
set #a findcolor (931 110 939 141 (1189) %arr)
if #a = 0
    return
end_if

right 878, 103
wait #tpwait
right 882, 83
wait #tpwait
right 867, 100
wait #tpwait
right 896, 75
wait #tpwait
right 896, 75
send $key_hp_quick
wait 100
wait #tpwait
right 890, 80
wait #tpwait
right 888, 79
wait #tpwait
right 911, 72
wait #tpwait
right 899, 80
wait #tpwait
right 889, 83
send $key_hp_quick
wait 100
wait #tpwait
right 879, 102
wait #tpwait
right 872, 124
wait #tpwait
right 886, 148
wait #tpwait
right 868, 123
wait #tpwait
right 872, 109
send $key_hp_quick
wait 100
wait #tpwait
right 880, 99
wait #tpwait
right 867, 115
wait #tpwait
right 874, 115
wait #tpwait
right 864, 113
wait #tpwait
right 862, 109
send $key_hp_quick
wait 100
wait #tpwait
right 885, 148
wait #tpwait
right 890, 150
wait #tpwait
right 891, 149
wait #tpwait
right 895, 142
wait #tpwait
right 926, 158
send $key_hp_quick
wait 100
wait #tpwait
right 893, 154
wait #tpwait
right 896, 154
wait #tpwait
right 884, 150
wait #tpwait
right 940, 155
wait #tpwait
right 943, 151
send $key_hp_quick
wait 100
wait #tpwait
right 941, 155
wait #tpwait
right 956, 147
wait #tpwait
right 947, 152
wait #tpwait
right 902, 159
wait #tpwait
right 916, 158
send $key_hp_quick
wait 100
wait #tpwait
right 950, 148
wait #tpwait
right 950, 148
wait #tpwait
right 950, 146
wait #tpwait
right 950, 146
wait #tpwait
right 943, 150
send $key_hp_quick
wait 100
wait #tpwait
right 966, 125
wait #tpwait
right 971, 110
wait #tpwait
right 954, 75
wait #tpwait
right 928, 62
wait #tpwait
right 950, 73
send $key_hp_quick
wait 100
wait #tpwait
right 969, 101
wait #tpwait
right 949, 147
wait #tpwait
right 938, 158
wait #tpwait
right 959, 141
wait #tpwait
right 970, 106
send $key_hp_quick
wait 100
wait #tpwait
right 944, 77
wait #tpwait
right 961, 81
wait #tpwait
right 938, 69
wait #tpwait
right 940, 64
wait #tpwait
right 913, 65
send $key_hp_quick
wait 100
wait #tpwait
right 912, 69
wait #tpwait
right 897, 116
wait #tpwait

// Mount speed skill, then cut the wait by 30% for the tower section only
send $key_mountspeed
set #reduction #tpwait * 30
set #reduction #reduction / 100
set #tower_wait #tpwait - #reduction

// Tower section: quick heal after every click
right 907, 67
send $key_hp_quick
wait #tower_wait

right 881, 85
send $key_hp_quick
wait #tower_wait

right 871, 108
send $key_hp_quick
wait #tower_wait

right 880, 119
send $key_hp_quick
wait #tower_wait

right 863, 117
send $key_hp_quick
wait #tower_wait

right 899, 77
send $key_hp_quick
wait #tower_wait

right 923, 67
send $key_hp_quick
wait #tower_wait

right 873, 113
send $key_hp_quick
wait #tower_wait

right 861, 116
send $key_hp_quick
wait #tower_wait + 200

right 862, 112
send $key_hp_quick
wait #tower_wait +1000

right 892, 137
send $key_hp_quick
wait #tower_wait +1000

right 921, 156
send $key_hp_quick
wait #tower_wait +1000

right 918, 140
send $key_hp_quick
wait #tower_wait +1000

right 960, 112
send $key_hp_quick
wait #tower_wait +1000

right 920, 159
send $key_hp_quick
wait #tower_wait +1000

right 934, 146
send $key_hp_quick
wait #tower_wait +1000

right 970, 110
send $key_hp_quick
wait #tower_wait +600

right 956, 84
send $key_hp_quick
wait #tower_wait +1000

right 918, 90
send $key_hp_quick
wait #tower_wait +1400

right 865, 116
send $key_hp_quick
wait #tower_wait +1000

return

// Walk to the boss NPC, enter the boss area and fight the boss
:boss_fight
// Click the NPC path until the color is found (max 20 tries)
set #tries 0

double_right 240, 171
double_right 260, 182
double_right 216, 220
double_right 214, 215
wait 1s

set #a findcolor (386, 653 972, 965 3436970 %arr)
while #a = 0
    double_right 240, 171
    double_right 260, 182
    double_right 216, 220
    double_right 214, 215
    double_right 216, 135
    double_right 227, 203
    double_right 240, 124
    double_right 229, 190
    wait 1s

    set #a findcolor (386, 653 972, 965 3436970 %arr)
    set #tries #tries + 1
    if #tries >= 20
        break
    end_if
end_while
left 278, 332
wait 2s

// Heal before the boss
if #healer = 1
    // Healer: remove the mount, heal until the mark point, equip the mount again
    send $key_mount
    wait 1s

    set #heals 0
    set #stop findcolor (215, 41 958, 467 65693 %arr)
    while #stop = 0
        left 46, 37
        send $key_fairy_heal
        wait 500

        set #stop findcolor (215, 41 958, 467 65693 %arr)
        set #heals #heals + 1
        if #heals >= 30
            break
        end_if
    end_while

    send $key_mount
    wait 3s
else
    // Other classes: heal and wait until HP is full
    gosub press_quick_heal
    wait 16s
    gosub press_quick_heal
    wait 500
    set $k $key_mana
    gosub press_optional_key
    wait 13s
end_if

right 921, 118
wait 2200

// Click towards the boss until the color is found (max 20 rounds of 5 clicks)
set #max 20
set #tries 0

set #a findcolor (871, 103 879, 134 1130096 %arr)
while #a = 0
    repeat 5
        right 887, 114
        wait 2s
    end_repeat

    set #a findcolor (871, 103 879, 134 1130096 %arr)
    set #tries #tries + 2
    if #tries >= #max
        break
    end_if
end_while

// Remove the mount
send $key_mount

// Attack loop: #attack_rounds rounds per pass, each round ends with a heal check and a target switch
// Stops when the boss color is missing 2 passes in a row
// Safety limit of 500 passes so it can never run forever
set #miss 0
set #rounds 0
send $key_target
while 1
    set #r 0
    while #r < #attack_rounds
        gosub attack_round
        set #r #r + 1
    end_while

    set #c findcolor (465, 48 473, 79 185 %arr)
    if #c = 0
        set #miss #miss + 4
    else
        set #miss 0
    end_if
    if #miss >= 10
        break
    end_if

    set #rounds #rounds + 1
    if #rounds >= 500
        break
    end_if
end_while
wait 1s
return

// Pick up the loot from the inventory
:loot
send $key_inventory
set %color[1] 5391624
set #size size(%color)
for #i 1 #size
    // Find the item color and double right click it
    set #a findcolor (5 7 1008 718 (%color[#i]) %arr)
    if #a > 0
        double_right %arr[1 1] %arr[1 2]
        wait 500
    end_if
    send $key_inventory
    wait 1s
end_for
send $key_teleport
wait 2s
return
'''

HINTS = {
    (964, 111, 1142, 571): "Account window close by",
    (55, 193, 63, 224): "Team formed",
    (106, 43, 114, 74): "HP bar (non healer)",
    (155, 42, 898, 468): "Healer HP bar check",
    (215, 41, 958, 467): "Mark point found after healing",
    (148, 53, 976, 471): "Mana bar check",
    (206, 53, 302, 506): "Mana color while using mana",
    (260, 227, 268, 258): "Transport fairy selected",
    (388, 655, 396, 686): "Seller window open",
    (457, 334, 465, 365): "Weapon confirmation window",
    (385, 659, 1118, 1063): "NPC window for the 48 level map",
    (916, 133, 924, 164): "Auto path map color",
    (389, 655, 1113, 1083): "NPC window to enter the cave",
    (931, 110, 939, 141): "First floor of the cave",
    (386, 653, 972, 965): "Boss NPC window",
    (871, 103, 879, 134): "Boss area reached",
    (465, 48, 473, 79): "Boss target bar",
    (5, 7, 1008, 718): "Loot item in the inventory",
}


# ------------------------------------------------------------------ colors
def rgb(c):
    return (c & 255, (c >> 8) & 255, (c >> 16) & 255)


def hx(c):
    r, g, b = rgb(c)
    return "#%02X%02X%02X" % (r, g, b)


def from_rgb(r, g, b):
    return int(r) | (int(g) << 8) | (int(b) << 16)


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(rgb(a), rgb(b))))


def fit_channels(pairs):
    old = np.array([rgb(o) for o, _ in pairs], float)
    new = np.array([rgb(n) for _, n in pairs], float)
    coef = []
    for ch in range(3):
        o, n = old[:, ch], new[:, ch]
        a = 1.0
        if len(pairs) >= 3 and np.ptp(o) >= 40:
            a = min(1.25, max(0.75, float(np.polyfit(o, n, 1)[0])))
        coef.append((a, float(np.mean(n - a * o))))
    return coef


def apply_coef(c, coef):
    v = [int(round(min(255, max(0, a * x + b)))) for x, (a, b) in zip(rgb(c), coef)]
    return from_rgb(*v)


# ------------------------------------------------------------------ script
def parse_script(text):
    lines = text.splitlines(keepends=True)
    checks, color_sets, var_regions, sub = [], [], [], "start"
    for i, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith("//"):
            continue
        if s.startswith(":"):
            sub = s[1:].strip()
            continue
        m = SET_COLOR_RE.match(raw)
        if m:
            color_sets.append({"line": i, "span": m.span(1), "color": int(m.group(1)), "sub": sub})
            continue
        for m in FIND_RE.finditer(raw):
            region = tuple(int(m.group(k)) for k in (1, 2, 3, 4))
            tok = m.group(5)
            if tok.isdigit():
                checks.append({"line": i, "span": m.span(5), "color": int(tok), "region": region, "sub": sub})
            elif tok.startswith("%color"):
                var_regions.append(region)
    for cs in color_sets:
        cs["region"] = var_regions[0] if var_regions else None
        checks.append(cs)
    return lines, checks


def build_entries(checks):
    entries, seen = [], set()
    for ch in checks:
        reg = ch["region"]
        if reg is None:
            continue
        k = (reg, ch["color"])
        if k in seen:
            continue
        seen.add(k)
        x1, y1, x2, y2 = reg
        entries.append({"name": HINTS.get(reg, ch["sub"]), "region": reg, "color": ch["color"],
                        "area": (x2 - x1 + 1) * (y2 - y1 + 1)})
    return entries


def swap_colors(lines, checks, mapping):
    edits = {}
    for ch in checks:
        new = mapping.get(ch["color"])
        if new is not None and new != ch["color"]:
            edits.setdefault(ch["line"], []).append((ch["span"], new))
    out = list(lines)
    for i, items in edits.items():
        s = out[i]
        for (a, b), new in sorted(items, key=lambda t: -t[0][0]):
            s = s[:a] + str(new) + s[b:]
        out[i] = s
    return "".join(out)


def add_tolerance(text, percent):
    def sub(m):
        x1, y1, x2, y2, col = m.groups()
        return "findcolor (%s %s %s %s 1 1 (%s) %%arr 1 1 %d)" % (x1, y1, x2, y2, col, percent)

    out, n = [], 0
    for line in text.splitlines(keepends=True):
        if line.strip().startswith("//"):
            out.append(line)
            continue
        new, k = FIND_ANY.subn(sub, line)
        n += k
        out.append(new)
    return "".join(out), n


# ----------------------------------------------------------------- windows
def set_dpi():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def list_windows():
    out = []
    u = ctypes.windll.user32
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def cb(h, _):
        if u.IsWindowVisible(h):
            n = u.GetWindowTextLengthW(h)
            if n > 0:
                buf = ctypes.create_unicode_buffer(n + 1)
                u.GetWindowTextW(h, buf, n + 1)
                out.append((buf.value, h))
        return True

    u.EnumWindows(proc(cb), 0)
    return out


def client_bbox(h):
    u = ctypes.windll.user32
    r = wintypes.RECT()
    u.GetClientRect(h, ctypes.byref(r))
    p = wintypes.POINT(0, 0)
    u.ClientToScreen(h, ctypes.byref(p))
    return p.x, p.y, p.x + r.right, p.y + r.bottom


def display_line():
    try:
        u, g = ctypes.windll.user32, ctypes.windll.gdi32
        dc = u.GetDC(0)
        bits = g.GetDeviceCaps(dc, 12) * g.GetDeviceCaps(dc, 14)
        dpi = g.GetDeviceCaps(dc, 88)
        u.ReleaseDC(0, dc)
        s = "Display: %d bit color, %d%% scaling" % (bits, round(dpi * 100 / 96))
        if bits < 32:
            s += "  (WARNING: set Windows color to 32 bit)"
        return s
    except Exception:
        return "Display: unknown"


# -------------------------------------------------------------------- scan
def scan(img, entries):
    H, W = img.shape[:2]
    res = []
    for e in entries:
        x1, y1, x2, y2 = e["region"]
        r = {"found": False, "count": 0, "cands": [], "outside": x2 >= W or y2 >= H}
        cx1, cx2, cy1, cy2 = max(0, x1), min(W - 1, x2), max(0, y1), min(H - 1, y2)
        if cx2 >= cx1 and cy2 >= cy1:
            crop = img[cy1:cy2 + 1, cx1:cx2 + 1]
            packed = crop[..., 0] | (crop[..., 1] << 8) | (crop[..., 2] << 16)
            n = int(np.count_nonzero(packed == e["color"]))
            if n:
                r["found"], r["count"] = True, n
            else:
                d2 = ((crop - np.array(rgb(e["color"]))) ** 2).sum(axis=2)
                mask = d2 <= CAND_DIST * CAND_DIST
                if mask.any():
                    vals, cnts = np.unique(packed[mask], return_counts=True)
                    cands = [(int(v), int(n)) for v, n in zip(vals, cnts)]
                    cands.sort(key=lambda t: dist(t[0], e["color"]))
                    r["cands"] = cands[:6]
        res.append(r)
    return res


def calibrate(entries, ever):
    colors, group = [], {}
    for e, ev in zip(entries, ever):
        c = e["color"]
        if c not in group:
            colors.append(c)
            group[c] = {"found": False, "cands": {}, "area": e["area"]}
        g = group[c]
        g["found"] = g["found"] or ev["found"]
        g["area"] = min(g["area"], e["area"])
        for k, n in ev["cands"].items():
            g["cands"][k] = max(g["cands"].get(k, 0), n)

    pairs = []
    for c in colors:
        g = group[c]
        if g["found"]:
            pairs.append((c, c))
        elif g["cands"] and g["area"] <= SMALL_AREA:
            best = min(g["cands"], key=lambda k: dist(k, c))
            if dist(best, c) <= 25:
                pairs.append((c, best))
    coef = None
    for _ in range(3):
        if not pairs:
            break
        coef = fit_channels(pairs)
        keep = [(o, n) for o, n in pairs if dist(apply_coef(o, coef), n) <= MAX_RESIDUAL]
        if len(keep) == len(pairs):
            break
        pairs = keep
    same_pc = len(pairs) >= 3 and all(dist(o, n) <= 2 for o, n in pairs)

    rows, mapping = [], {}
    for c in colors:
        g = group[c]
        if g["found"]:
            new, how = c, "SAME"
        elif same_pc:
            new, how = c, "kept (same as yours)"
        elif coef is not None:
            pred = apply_coef(c, coef)
            if g["cands"]:
                best = min(g["cands"], key=lambda k: dist(k, pred))
                if dist(best, pred) <= ACCEPT_DIST:
                    new, how = best, "READ"
                else:
                    new, how = pred, "ESTIMATED"
            else:
                new, how = pred, "ESTIMATED"
        elif g["cands"]:
            best = min(g["cands"], key=lambda k: dist(k, c))
            new, how = best, "GUESS"
        else:
            new, how = c, "not seen, kept"
        if new != c:
            mapping[c] = new
        rows.append((c, new, how))
    return rows, mapping, same_pc


# ---------------------------------------------------------------------- UI
TOLERANCE = 3


class App:
    def __init__(self, root):
        self.root = root
        root.title("BC Color Finder")
        root.geometry("900x700")
        self.running = False
        self.last_found = -1
        self.script_path = os.path.join(APP, "cave_bot_short.txt")
        self.load_text(EMBEDDED_SCRIPT)

        bar = ttk.Frame(root, padding=8)
        bar.pack(fill="x")
        self.btn_start = ttk.Button(bar, text="Start", command=self.toggle)
        self.btn_start.pack(side="left")

        self.status = tk.StringVar(value=display_line())
        ttk.Label(root, textvariable=self.status, padding=(8, 0)).pack(fill="x")

        cols = ("n", "check", "expected", "now", "ever")
        self.tree = ttk.Treeview(root, columns=cols, show="headings", height=10)
        for c, t, w in (("n", "#", 35), ("check", "Check", 300), ("expected", "Expected", 90),
                        ("now", "Now", 110), ("ever", "Ever", 60)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="x", padx=8, pady=6)
        self.fill_tree()

        head = ttk.Frame(root, padding=(8, 4))
        head.pack(fill="x")
        ttk.Label(head, text="New script", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(head, text="Copy script", command=self.copy).pack(side="left", padx=(12, 6))
        ttk.Button(head, text="Clear", command=self.clear).pack(side="left")

        box = ttk.Frame(root)
        box.pack(fill="both", expand=True, padx=8, pady=4)
        self.text = tk.Text(box, wrap="none", font=("Consolas", 9))
        sb = ttk.Scrollbar(box, command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self.msg = tk.StringVar()
        ttk.Label(root, textvariable=self.msg, padding=8).pack(fill="x")

    def load_text(self, text):
        text = text.replace("\r\n", "\n")
        self.lines, self.checks = parse_script(text)
        self.entries = build_entries(self.checks)
        self.reset_seen()

    def reset_seen(self):
        self.ever = [{"found": False, "cands": {}, "outside": False} for _ in self.entries]
        self.last_found = -1

    def fill_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, e in enumerate(self.entries):
            self.tree.insert("", "end", iid=str(i), values=(i + 1, e["name"], hx(e["color"]), "-", "no"))

    # -- buttons
    def toggle(self):
        self.running = not self.running
        self.btn_start.config(text="Stop" if self.running else "Start")
        if self.running:
            self.tick()

    def copy(self):
        t = self.text.get("1.0", "end-1c")
        if not t:
            self.msg.set("Nothing to copy yet. Click Start with the game open.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(t)
        self.msg.set("Copied the whole script")

    def clear(self):
        self.text.delete("1.0", "end")
        self.reset_seen()
        self.fill_tree()
        self.msg.set("Cleared")

    # -- capture
    def tick(self):
        if not self.running:
            return
        try:
            hwnd = next((h for t, h in list_windows() if "talisman" in t.lower()), None)
            if not hwnd:
                self.status.set("%s | Game window not found. Open the game." % display_line())
            else:
                shot = ImageGrab.grab(bbox=client_bbox(hwnd), all_screens=True)
                img = np.asarray(shot.convert("RGB"), dtype=np.int32)
                note = "Game window found"
                if img.mean() < 3:
                    note += " | WARNING: capture is black"
                res = scan(img, self.entries)
                for i, (ev, r) in enumerate(zip(self.ever, res)):
                    if r["found"]:
                        ev["found"] = True
                    for c, n in r["cands"]:
                        ev["cands"][c] = max(ev["cands"].get(c, 0), n)
                    now = "FOUND %d" % r["count"] if r["found"] else "-"
                    self.tree.item(str(i), values=(i + 1, self.entries[i]["name"],
                                                   hx(self.entries[i]["color"]), now,
                                                   "yes" if ev["found"] else "no"))
                n_ok = sum(1 for ev in self.ever if ev["found"])
                self.status.set("%s | %s | %d of %d found" % (display_line(), note, n_ok, len(self.entries)))
                if n_ok != self.last_found:
                    self.last_found = n_ok
                    self.build()
        except Exception as ex:
            self.status.set("Capture error: %s" % ex)
        self.root.after(INTERVAL_MS, self.tick)

    def build(self):
        rows, mapping, same_pc = calibrate(self.entries, self.ever)
        text = swap_colors(self.lines, self.checks, mapping)
        text, n = add_tolerance(text, TOLERANCE)
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        try:
            out = os.path.splitext(self.script_path)[0] + "_FINAL.txt"
            with open(out, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(text)
        except Exception:
            pass
        est = sum(1 for r in rows if r[2] in ("ESTIMATED", "GUESS"))
        self.msg.set("New script ready: %d colors changed, %d estimated. Click Copy script." % (len(mapping), est))


if __name__ == "__main__":
    set_dpi()
    root = tk.Tk()
    App(root)
    root.mainloop()
