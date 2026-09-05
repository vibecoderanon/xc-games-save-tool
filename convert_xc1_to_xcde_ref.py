#!/usr/bin/env python3
import struct
import os
import shutil

"""
Xenoblade Chronicles (Wii) to Xenoblade Chronicles: Definitive Edition (Switch) Save File Converter

Switch Manual Save Slots:
- bfsgame00.sav / bfsgame00.tmb : Manual Slot 1 (from monado01)
- bfsgame01.sav / bfsgame01.tmb : Manual Slot 2 (from monado02)
- bfsgame02.sav / bfsgame02.tmb : Manual Slot 3 (from monado03)
- bfssystem.sav : Global System Save
(Autosave slot bfsgame00a is intentionally omitted)
"""

REF_DIR = r"c:\Users\teit\Documents\Antigravity\xc games save tool\vibecoderanon - 2024.10.26 @ 22.50.00b4ngpaftrfc"
WII_DIR = r"c:\Users\teit\Documents\Antigravity\xc games save tool\wii\title\SX4E"
OUT_DIR = r"c:\Users\teit\Documents\Antigravity\xc games save tool\converted_switch_saves"

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

def convert_with_template(wii_filename, switch_sav_name, switch_tmb_name, ref_tmb_source_name="bfsgame01.tmb"):
    wii_path = os.path.join(WII_DIR, wii_filename)
    ref_sav_path = os.path.join(REF_DIR, "bfsgame01.sav")
    ref_tmb_path = os.path.join(REF_DIR, ref_tmb_source_name if os.path.exists(os.path.join(REF_DIR, ref_tmb_source_name)) else "bfsgame01.tmb")

    out_sav_path = os.path.join(OUT_DIR, switch_sav_name)
    out_tmb_path = os.path.join(OUT_DIR, switch_tmb_name)

    print(f"\n========================================================")
    print(f" Converting {wii_filename} -> {switch_sav_name} & {switch_tmb_name}")
    print(f"========================================================")

    # 1. Read Wii save
    with open(wii_path, "rb") as f:
        wii = f.read()

    play_hours = struct.unpack(">H", wii[0x2A:0x2C])[0]
    play_mins = struct.unpack(">H", wii[0x2C:0x2E])[0]
    play_secs = wii[0x23]
    money = struct.unpack(">I", wii[0x24048:0x2404C])[0]

    p1 = struct.unpack(">H", wii[0xD1FE:0xD200])[0]
    p2 = struct.unpack(">H", wii[0xD202:0xD204])[0]
    p3 = struct.unpack(">H", wii[0xD206:0xD208])[0]

    print(f"Wii Play Time : {play_hours}h {play_mins}m {play_secs}s")
    print(f"Wii Money     : {money:,} G")
    print(f"Wii Party     : P1={p1}, P2={p2}, P3={p3}")

    # 2. Read reference working Switch save into bytearray
    with open(ref_sav_path, "rb") as f:
        sav = bytearray(f.read())

    # 3. Update Money (at 0x151B40)
    sav[0x151B40:0x151B44] = struct.pack("<I", money)

    # 4. Update Party structure at 0x152318
    party_ids = [p1, p2, p3]
    active_count = 0
    for idx, cid in enumerate(party_ids):
        if 1 <= cid <= 11:
            sav[0x152318 + (idx * 2) : 0x152318 + (idx * 2) + 2] = struct.pack("<H", cid)
            active_count += 1
    for idx in range(active_count, 12):
        sav[0x152318 + (idx * 2) : 0x152318 + (idx * 2) + 2] = struct.pack("<H", 0)
    sav[0x152330] = active_count

    # 5. Update PartyMembers array at 0x152368
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
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(out_sav_path, "wb") as f:
        f.write(sav)
    print(f"Saved: {out_sav_path} ({len(sav):,} bytes)")

    # Copy thumbnail .tmb file
    shutil.copyfile(ref_tmb_path, out_tmb_path)
    print(f"Copied Thumbnail: {out_tmb_path}")

def main():
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR, exist_ok=True)

    saves = [
        ("monado01", "bfsgame00.sav", "bfsgame00.tmb", "bfsgame00.tmb"), # Manual Slot 1
        ("monado02", "bfsgame01.sav", "bfsgame01.tmb", "bfsgame01.tmb"), # Manual Slot 2
        ("monado03", "bfsgame02.sav", "bfsgame02.tmb", "bfsgame02.tmb"), # Manual Slot 3
    ]

    for wii_file, switch_sav, switch_tmb, ref_tmb_src in saves:
        convert_with_template(wii_file, switch_sav, switch_tmb, ref_tmb_src)

    # Copy bfssystem.sav
    ref_system = os.path.join(REF_DIR, "bfssystem.sav")
    if os.path.exists(ref_system):
        shutil.copyfile(ref_system, os.path.join(OUT_DIR, "bfssystem.sav"))
        print(f"\nCopied bfssystem.sav to {OUT_DIR}")

if __name__ == "__main__":
    main()
