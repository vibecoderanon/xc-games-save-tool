#!/usr/bin/env python3
import struct
import os
import shutil

"""
Clean Xenoblade Chronicles (Wii) to Switch Converter

1. Uses `bfsgame02.sav` from `vibecoderanon - 2024.09.08 @ 00.35.38b4hx` as the template:
   - Story progress is pre-clear / around Chapter 7-13.
   - ClearFlag is 0 (normal title screen).
   - Full equipment (weapons & armor) is populated for all party members (Shulk, Reyn, Dunban, Sharla, Riki, Melia, Seven).
2. Extracts all 7 unlocked party members from Wii save array (p1..p7) and sets
   PartyMembersCount (at 0x152330) to 7, unlocking ALL characters in the party menu.
3. Updates Money (0x151B40), Header Play Time (0x04), and Party Member Level, EXP, AP (0x152368).
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(BASE_DIR, "vibecoderanon - 2024.09.08 @ 00.35.38b4hx")
WII_DIR = os.path.join(BASE_DIR, "wii", "title", "SX4E")
OUT_DIR = os.path.join(BASE_DIR, "converted_switch_saves")

CHARACTER_WII_OFFSETS = [
    ("Shulk", 0xF8D0, 1),
    ("Reyn", 0xFBD4, 2),
    ("Fiora", 0xFEC8, 3),
    ("Dunban", 0x101DC, 4),
    ("Sharla", 0x104E0, 5),
    ("Riki", 0x107E4, 6),
    ("Melia", 0x10AE8, 7),
    ("Seven", 0x10DEC, 8),
    ("Dickson", 0x110F0, 9),
    ("Mumkhar", 0x113F4, 10),
    ("Alvis", 0x116F8, 11)
]

XCDE_CHAR_POSITIONS = {
    1: 0,   # Shulk
    2: 1,   # Reyn
    3: 2,   # Fiora
    4: 3,   # Dunban
    5: 4,   # Sharla
    6: 5,   # Riki
    7: 6,   # Melia
    8: 7,   # Seven
    9: 8,   # Dickson
    10: 9,  # Mumkhar
    11: 10  # Alvis
}

def convert_slot(wii_filename, out_sav_filename, out_tmb_filename):
    wii_path = os.path.join(WII_DIR, wii_filename)
    ref_sav_path = os.path.join(REF_DIR, "bfsgame02.sav") # Using mid-game equipped template
    ref_tmb_path = os.path.join(REF_DIR, "bfsgame02.tmb")

    out_sav_path = os.path.join(OUT_DIR, out_sav_filename)
    out_tmb_path = os.path.join(OUT_DIR, out_tmb_filename)

    print(f"\n========================================================")
    print(f" Converting {wii_filename} -> {out_sav_filename} & {out_tmb_filename}")
    print(f"========================================================")

    # 1. Read Wii save
    with open(wii_path, "rb") as f:
        wii = f.read()

    play_hours = struct.unpack(">H", wii[0x2A:0x2C])[0]
    play_mins = struct.unpack(">H", wii[0x2C:0x2E])[0]
    play_secs = wii[0x23]
    total_play_seconds = play_hours * 3600 + play_mins * 60 + play_secs
    money = struct.unpack(">I", wii[0x24048:0x2404C])[0]

    raw_p_list = [
        struct.unpack(">H", wii[0xD1FE:0xD200])[0], # p1
        struct.unpack(">H", wii[0xD202:0xD204])[0], # p2
        struct.unpack(">H", wii[0xD206:0xD208])[0], # p3
        struct.unpack(">H", wii[0xD20A:0xD20C])[0], # p4
        struct.unpack(">H", wii[0xD20E:0xD210])[0], # p5
        struct.unpack(">H", wii[0xD212:0xD214])[0], # p6
        struct.unpack(">H", wii[0xD216:0xD218])[0], # p7
    ]

    unlocked_char_ids = [cid for cid in raw_p_list if 1 <= cid <= 11]
    unlocked_count = len(unlocked_char_ids)

    print(f"Wii Play Time   : {play_hours}h {play_mins}m {play_secs}s ({total_play_seconds:,} sec)")
    print(f"Wii Money       : {money:,} G")
    print(f"Unlocked Party  : {unlocked_char_ids} (Total Unlocked: {unlocked_count})")

    # 2. Read reference template into bytearray
    with open(ref_sav_path, "rb") as f:
        sav = bytearray(f.read())

    # 3. Ensure ClearFlag = 0 (Normal Pre-Clear Title Screen)
    sav[0x4C:0x50] = struct.pack("<I", 0)

    # 4. Update Header Play Time at offset 0x04
    sav[0x04:0x08] = struct.pack("<I", total_play_seconds)

    # 5. Update Money at 0x151B40
    sav[0x151B40:0x151B44] = struct.pack("<I", money)

    # 6. Update Party structure at 0x152318
    for idx, cid in enumerate(unlocked_char_ids):
        sav[0x152318 + (idx * 2) : 0x152318 + (idx * 2) + 2] = struct.pack("<H", cid)
    for idx in range(unlocked_count, 12):
        sav[0x152318 + (idx * 2) : 0x152318 + (idx * 2) + 2] = struct.pack("<H", 0)

    # Set total unlocked party count (7)
    sav[0x152330] = unlocked_count

    # 7. Update PartyMembers array at 0x152368
    PARTY_MEMBERS_OFFSET = 0x152368
    PARTY_MEMBER_SIZE = 0x138

    for char_name, wii_offset, char_id in CHARACTER_WII_OFFSETS:
        level = struct.unpack(">I", wii[wii_offset : wii_offset + 4])[0]
        exp = struct.unpack(">I", wii[wii_offset + 0x1C : wii_offset + 0x20])[0]
        ap = struct.unpack(">I", wii[wii_offset + 0x20 : wii_offset + 0x24])[0]

        if level == 0:
            continue

        pos = XCDE_CHAR_POSITIONS[char_id]
        member_offset = PARTY_MEMBERS_OFFSET + (pos * PARTY_MEMBER_SIZE)

        # Level (0x00)
        sav[member_offset + 0x00 : member_offset + 0x04] = struct.pack("<I", level)
        # EXP (0x04)
        sav[member_offset + 0x04 : member_offset + 0x08] = struct.pack("<I", exp)
        # AP (0x08)
        sav[member_offset + 0x08 : member_offset + 0x0C] = struct.pack("<I", ap)

        # Expert Mode Level & EXP (0xEC, 0xF0)
        sav[member_offset + 0xEC : member_offset + 0xF0] = struct.pack("<I", level)
        sav[member_offset + 0xF0 : member_offset + 0xF4] = struct.pack("<I", exp)

        print(f"  Character {char_name:8s} (ID {char_id:2d}) -> Level: {level:2d} | EXP: {exp:10d} | AP: {ap:10d}")

    # Write converted .sav
    with open(out_sav_path, "wb") as f:
        f.write(sav)
    print(f"Saved: {out_sav_path} ({len(sav):,} bytes)")

    # Copy companion thumbnail
    shutil.copyfile(ref_tmb_path, out_tmb_path)
    print(f"Copied Thumbnail: {out_tmb_path}")

def main():
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR, exist_ok=True)

    saves = [
        ("monado01", "bfsgame00.sav", "bfsgame00.tmb"), # Slot 1
        ("monado02", "bfsgame01.sav", "bfsgame01.tmb"), # Slot 2
        ("monado03", "bfsgame02.sav", "bfsgame02.tmb"), # Slot 3
    ]

    for wii_file, out_sav, out_tmb in saves:
        convert_slot(wii_file, out_sav, out_tmb)

    # Copy pre-clear bfssystem.sav
    ref_system = os.path.join(REF_DIR, "bfssystem.sav")
    if os.path.exists(ref_system):
        shutil.copyfile(ref_system, os.path.join(OUT_DIR, "bfssystem.sav"))
        print(f"\nCopied pre-clear bfssystem.sav to {OUT_DIR}")

if __name__ == "__main__":
    main()
