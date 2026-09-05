#!/usr/bin/env python3
import struct
import os
import sys

"""
Xenoblade Chronicles (Wii) to Xenoblade Chronicles: Definitive Edition (Switch) Save File Converter

Converts Wii monado01/02/03 saves to Switch XCDE bfsgame01/02/03.sav files.
"""

XCDE_SAVE_SIZE = 0x153860  # 1,390,688 bytes

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

# XCDE PartyMember array indexes:
# 0: Shulk, 1: Reyn, 2: Fiora, 3: Dunban, 4: Sharla, 5: Riki, 6: Melia, 7: Seven (Fiora_2), 8: Dickson, 9: Mumkhar, 10: Alvis
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

def convert_save(wii_save_path, output_sav_path):
    print(f"\n--- Converting: {os.path.basename(wii_save_path)} -> {os.path.basename(output_sav_path)} ---")
    
    with open(wii_save_path, "rb") as f:
        wii = f.read()

    if len(wii) < 0x28000:
        raise ValueError(f"Invalid Wii save file size: {len(wii)} bytes")

    # Read Wii fields (Big Endian)
    play_hours = struct.unpack(">H", wii[0x2A:0x2C])[0]
    play_mins = struct.unpack(">H", wii[0x2C:0x2E])[0]
    play_secs = wii[0x23]

    money = struct.unpack(">I", wii[0x24048:0x2404C])[0]
    
    p1 = struct.unpack(">H", wii[0xD1FE:0xD200])[0]
    p2 = struct.unpack(">H", wii[0xD202:0xD204])[0]
    p3 = struct.unpack(">H", wii[0xD206:0xD208])[0]

    print(f"Play Time: {play_hours}h {play_mins}m {play_secs}s")
    print(f"Money: {money:,} G")
    print(f"Active Party (Wii Indices): P1={p1}, P2={p2}, P3={p3}")

    # Prepare XCDE save buffer (initialized to zeros)
    xcde = bytearray(XCDE_SAVE_SIZE)

    # 1. Set Money at 0x151B40 (Little Endian uint32)
    xcde[0x151B40:0x151B44] = struct.pack("<I", money)

    # 2. Set Noponstones at 0x10 (Little Endian uint32)
    xcde[0x10:0x14] = struct.pack("<I", 0)

    # 3. Set Party structure at 0x152318
    # 12 x uint16 character IDs, followed by party count at +0x18
    party_ids = [p1, p2, p3]
    active_count = 0
    for idx, cid in enumerate(party_ids):
        if 1 <= cid <= 11:
            xcde[0x152318 + (idx * 2) : 0x152318 + (idx * 2) + 2] = struct.pack("<H", cid)
            active_count += 1
    
    # Fill remaining party slots with None (0)
    for idx in range(active_count, 12):
        xcde[0x152318 + (idx * 2) : 0x152318 + (idx * 2) + 2] = struct.pack("<H", 0)

    # Set PartyMembersCount at 0x152330 (0x152318 + 0x18)
    xcde[0x152330] = active_count

    # 4. Populate PartyMembers array at 0x152368
    # 16 members, each 0x138 (312) bytes
    PARTY_MEMBERS_OFFSET = 0x152368
    PARTY_MEMBER_SIZE = 0x138

    for char_name, wii_offset, char_id in CHARACTER_WII_OFFSETS:
        level = struct.unpack(">I", wii[wii_offset : wii_offset + 4])[0]
        exp = struct.unpack(">I", wii[wii_offset + 0x1C : wii_offset + 0x20])[0]
        ap = struct.unpack(">I", wii[wii_offset + 0x20 : wii_offset + 0x24])[0]

        # Ignore characters with 0 level (e.g. Fiora early game if Seven is present or vice versa)
        if level == 0:
            continue

        pos = XCDE_CHAR_POSITIONS[char_id]
        member_offset = PARTY_MEMBERS_OFFSET + (pos * PARTY_MEMBER_SIZE)

        # Level (0x00)
        xcde[member_offset + 0x00 : member_offset + 0x04] = struct.pack("<I", level)
        # EXP (0x04)
        xcde[member_offset + 0x04 : member_offset + 0x08] = struct.pack("<I", exp)
        # AP (0x08)
        xcde[member_offset + 0x08 : member_offset + 0x0C] = struct.pack("<I", ap)

        # Expert Mode settings (new in XCDE)
        # ExpertModeLevel (0xEC)
        xcde[member_offset + 0xEC : member_offset + 0xF0] = struct.pack("<I", level)
        # ExpertModeEXP (0xF0)
        xcde[member_offset + 0xF0 : member_offset + 0xF4] = struct.pack("<I", exp)
        # ExpertModeReserveEXP (0xF4)
        xcde[member_offset + 0xF4 : member_offset + 0xF8] = struct.pack("<I", 0)

        print(f"  Mapped {char_name:8s} (ID {char_id:2d}) -> Pos {pos:2d} | Level: {level:2d} | EXP: {exp:10d} | AP: {ap:10d}")

    # 5. Populate Arts Levels array at 0x1536E8 (188 arts, 2 bytes each)
    ARTS_OFFSET = 0x1536E8
    for i in range(188):
        art_ptr = ARTS_OFFSET + (i * 2)
        # Default art level 1, max unlocked XII_Master (3) or X_Expert (2)
        xcde[art_ptr] = 1
        xcde[art_ptr + 1] = 3

    # Write converted save file
    os.makedirs(os.path.dirname(output_sav_path), exist_ok=True)
    with open(output_sav_path, "wb") as f:
        f.write(xcde)

    print(f"SUCCESS: Created {output_sav_path} ({len(xcde):,} bytes)")

def main():
    wii_dir = r"c:\Users\teit\Documents\Antigravity\xc games save tool\wii\title\SX4E"
    out_dir = r"c:\Users\teit\Documents\Antigravity\xc games save tool\converted_switch_saves"

    saves = [
        ("monado01", "bfsgame01.sav"),
        ("monado02", "bfsgame02.sav"),
        ("monado03", "bfsgame03.sav"),
    ]

    for wii_name, switch_name in saves:
        wii_path = os.path.join(wii_dir, wii_name)
        switch_path = os.path.join(out_dir, switch_name)
        if os.path.exists(wii_path):
            convert_save(wii_path, switch_path)

if __name__ == "__main__":
    main()
