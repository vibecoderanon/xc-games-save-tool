# Xenoblade Chronicles 1 → Definitive Edition Save Conversion Suite

[![Source: Nintendo Wii (SX4E)](https://img.shields.io/badge/Source-Nintendo_Wii_(SX4E)-00a4e4.svg)](#)
[![Target: Nintendo Switch (XC:DE)](https://img.shields.io/badge/Target-Nintendo_Switch_(XC:DE)-e60012.svg)](#)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-3776ab.svg)](#)
[![Viewer: HTML5 + CSS3](https://img.shields.io/badge/Viewer-HTML5_%2B_CSS3-e34f26.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-success.svg)](LICENSE)

A binary translation and save migration toolkit for converting *Xenoblade Chronicles* (Nintendo Wii, Title ID `SX4E`) saves into native *Xenoblade Chronicles: Definitive Edition* (Nintendo Switch) save format.

The suite accurately translates character EXP, AP, money, play time, equipment states, party composition, and thumbnail cards, while preserving pre-clear title screen states.

---

## Quick Navigation

- [Conversion Pipeline Overview](#conversion-pipeline-overview)
- [Slot & File Mapping](#slot--file-mapping)
- [Binary Offset & Character Matrix](#binary-offset--character-matrix)
- [Pre-Clear Title Screen Logic](#pre-clear-title-screen-logic)
- [Repository Structure](#repository-structure)
- [Usage & Conversion Guide](#usage--conversion-guide)
- [Interactive Save Inspector](#interactive-save-inspector)
- [Credits & Acknowledgments](#credits--acknowledgments)

---

## Conversion Pipeline Overview

Wii saves (`monado01` through `monado03`) and Switch Definitive Edition saves (`bfsgame00.sav` through `bfsgame02.sav`) use fundamentally different binary layouts, header encodings, and system flag structures:

```
[Wii Save (SX4E)]                   [Switch XC:DE Save]
├── monado01 (Wii Slot 1)    ───►   ├── bfsgame00.sav + bfsgame00.tmb
├── monado02 (Wii Slot 2)    ───►   ├── bfsgame01.sav + bfsgame01.tmb
├── monado03 (Wii Slot 3)    ───►   ├── bfsgame02.sav + bfsgame02.tmb
└── data.bin (Wii Header)    ───►   └── bfssystem.sav (Pre-Clear Flags)
```

The converter extracts character stats, play time counter, inventory money, and party setup from the Big-Endian Wii format, injects them into verified Switch templates, and pairs each save with its `.tmb` thumbnail file for the Switch load game menu.

---

## Slot & File Mapping

| Wii Source File | Target Switch Save | Target Thumbnail | In-Game Slot | Status / Level |
| :--- | :--- | :--- | :--- | :--- |
| `monado01` | `bfsgame00.sav` | `bfsgame00.tmb` | Manual Slot 1 | Melia (Lv 58, 127h 18m) |
| `monado02` | `bfsgame01.sav` | `bfsgame01.tmb` | Manual Slot 2 | Melia (Lv 58–59, 127h 50m) |
| `monado03` | `bfsgame02.sav` | `bfsgame02.tmb` | Manual Slot 3 | Fiora (Lv 55, 111h 45m) |
| Template | `bfssystem.sav` | — | System Data | Pre-clear title state (`ClearFlag = 0`) |

---

## Binary Offset & Character Matrix

### Key Switch XC:DE Offsets
- **Header Play Time:** `0x000004` (Accurately mirrors in-game timer on load card)
- **Money / Gold:** `0x151B40` (4-byte unsigned integer)
- **Active Party Composition:** `0x152318` (Character ID trio)
- **Character Array Base:** `0x152368` (EXP, AP, levels, and Expert Mode toggles)

### Wii Source Character Offsets
| Character | Wii Character ID | Wii Save Offset | Switch DE Position |
| :--- | :---: | :---: | :---: |
| **Shulk** | `1` | `0x0F8D0` | Slot 0 |
| **Reyn** | `2` | `0x0FBD4` | Slot 1 |
| **Fiora** | `3` | `0x0FEC8` | Slot 2 |
| **Dunban** | `4` | `0x101DC` | Slot 3 |
| **Sharla** | `5` | `0x104E0` | Slot 4 |
| **Riki** | `6` | `0x107E4` | Slot 5 |
| **Melia** | `7` | `0x10AE8` | Slot 6 |
| **Seven** | `8` | `0x10DEC` | Slot 7 |
| **Dickson** | `9` | `0x110F0` | Slot 8 |
| **Mumkhar** | `10` | `0x113F4` | Slot 9 |
| **Alvis** | `11` | `0x116F8` | Slot 10 |

---

## Pre-Clear Title Screen Logic

Standard Definitive Edition save converters often blindly transfer cleared/endgame flags into `bfssystem.sav`, which triggers the post-game title screen background and music (spoiling visual story elements).

This conversion suite utilizes a pre-clear template (`vibecoderanon - 2024.09.08 @ 00.35.38b4hx`) with `ClearFlag = 0`. As a result:
1. The title screen retains the classic Meadow & Monado background.
2. All progress, levels, AP, and play time from your Wii campaign remain intact upon loading.

---

## Repository Structure

```
xc games save tool/
├── README.md                              # Technical suite documentation
├── page.html                              # Interactive visual save inspector
├── convert_xc1_to_xcde_final.py           # Production Wii → Switch conversion script
├── verify_converted_saves.py              # Save integrity and offset verification script
├── converted_switch_saves/                # Output folder for generated Switch .sav & .tmb
│   └── .gitkeep
├── wii/                                   # Source Wii save data dumps
│   └── title/SX4E/                        # Monado save files (monado01-03, data.bin)
└── vibecoderanon - .../                          # Reference Switch save templates and thumbnails
```

---

## Usage & Conversion Guide

### 1. Run the Conversion Pipeline
Ensure your Wii save files are placed in `wii/title/SX4E/`:

```bash
python convert_xc1_to_xcde_final.py
```

Converted saves (`bfsgame00.sav`, `bfsgame01.sav`, `bfsgame02.sav`, `bfssystem.sav`) and their `.tmb` thumbnail images will be generated in `converted_switch_saves/`.

### 2. Verify Generated Saves
Run the automated verification suite to validate file sizes, headers, and play times:

```bash
python verify_converted_saves.py
```

### 3. Deploy to Nintendo Switch
Using your preferred Switch homebrew save manager (**JKSV** or **Checkpoint**):
1. Create a backup of your *Xenoblade Chronicles: Definitive Edition* save.
2. Replace the contents of the backup directory with the files from `converted_switch_saves/`.
3. Restore the backup in JKSV.

---

## Interactive Save Inspector

Open [`page.html`](page.html) directly in any web browser to view an interactive visual breakdown of the save files, party stats, and slot previews without needing to launch the game.

---

## Credits & Acknowledgments

- **Monolith Soft & Nintendo**: Creators of *Xenoblade Chronicles* and *Xenoblade Chronicles: Definitive Edition*.
- **vibecoderanon**: Binary reverse-engineering, pre-clear template preservation, and conversion suite implementation.
