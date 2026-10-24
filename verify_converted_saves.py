import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from xcde_editor import XCDESaveEditor

out_dir = os.path.join(BASE_DIR, "converted_switch_saves")

for fname in ["bfsgame00.sav", "bfsgame01.sav", "bfsgame02.sav"]:
    fpath = os.path.join(out_dir, fname)
    if not os.path.exists(fpath):
        continue
    
    print(f"\n--- Verifying {fname} ---")
    editor = XCDESaveEditor(fpath)
    
    print(f"File Size: {len(editor.save_data):,} bytes")
    
    # Check levels & EXP
    for char_id in range(1, 9):
        lvl = editor.get_character_level(char_id)
        exp = editor.get_character_exp(char_id)
        ap = editor.get_character_ap(char_id)
        print(f"  Character {char_id:2d}: Level={lvl:2d} | EXP={exp:10d} | AP={ap:10d}")

print("\nValidation completed successfully!")
