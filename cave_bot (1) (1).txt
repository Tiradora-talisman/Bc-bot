// Cave bot (short version)
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


// SUBROUTINES

// Hold the remove everyone key, skipped if the key is blank
:remove_everyone
if_not $key_remove_everyone = $empty
    send_down $key_remove_everyone
end_if
return

// Close the open windows and prepare the game screen
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

// Press the attack key in $k only if it is not blank
:press_attack
if_not $k = $empty
    send $k 1200
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

// Mana check used during the boss fight
// If the mana color is not found (mana bar has dropped), press the quick mana key once,
// same style as the non-healer HP quick heal check
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

// Sell 10 items
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
// The boss floor check is disabled for now.
// Add it back once the boss floor color and region are confirmed.

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

// Attack loop: keeps attacking non stop until the boss color is missing 2 rounds in a row
// HP and mana are checked after every attack inside use_attacks
// Safety limit of 500 rounds so it can never run forever
set #miss 0
set #rounds 0
while 1
    send $key_target
    send $key_target
    gosub use_attacks
    gosub use_attacks
    gosub use_attacks

    // Count the rounds in a row without the boss color
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
