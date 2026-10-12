# SCDA Recomp Save Resigner

A fast, lightweight tool to fix the **"This profile appears to be damaged and cannot be used"** error when transferring original Xbox or [xemu](https://xemu.app/) emulator saves to **[SCDA-XBERecomp](https://github.com/TGP482/SCDA-XBERecomp)** (*Tom Clancy's Splinter Cell: Double Agent* Xbox static recompiler).

---

## The Problem

When copying your save files from an original Xbox console or xemu into the recomp's save directory (`hdd/E/UDATA/5553005e/<account_id>/`), the game will reject the profile with:

> **Damaged Profile**  
> *"This profile appears to be damaged and cannot be used. Select OK to delete this profile or CANCEL to keep it."*

---

## Root Cause

On original Xbox hardware and xemu, game saves are verified through a two-stage HMAC-SHA1 signature:
1. **Roamable Signature**: `HMAC-SHA1(TitleSignatureKey, payload)`
2. **Non-Roamable Signature**: `HMAC-SHA1(XboxHDKey, RoamableSig)`

In `SCDA-XBERecomp`:
- `XboxSignatureKey` (`KERNEL_DATA` ordinal 325) is uninitialized in the recompiled kernel and defaults to **16 zeroes** (`00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00`).
- `XboxHDKey` (`KERNEL_DATA` ordinal 323) is also **16 zeroes**.
- The recomp validates saves at `vtable[0x54]` (`0x0003F683` / `XCalculateSignatureEnd`) against:
  $$\text{Expected Signature} = \text{HMAC}_{16\times 00}(\text{HMAC}_{16\times 00}(\text{payload}))$$

Because authentic Xbox and xemu saves were signed using the genuine title signature key (`61676F08B31D71DCF8E02903CB5164BB`), the signature check fails and the game marks the profile as damaged.

This tool re-computes the HMAC-SHA1 signatures using the double 16-zero key required by the recompiler.

---

## Installation & Requirements

- Python 3.6+
- No third-party dependencies required (uses standard library `hmac`, `hashlib`, `os`).

Clone the repository:
```bash
git clone https://github.com/Gabarsolon/scda-recomp-save-resigner.git
cd scda-recomp-save-resigner
```

---

## Usage

### 1. Re-sign a specific profile directory
Point the script at your profile folder inside `UDATA/5553005e/`:

```bash
# Windows
python scda_resign.py "D:\SCDA\hdd\E\UDATA\5553005e\7BA18D20FCE6"

# Linux / Steam Deck / Batocera
python3 scda_resign.py "/path/to/SCDA.pc/hdd/E/UDATA/5553005e/7BA18D20FCE6"
```

### 2. Optional: Create backups
Pass `--backup` to create `.bak` copies before overwriting:
```bash
python scda_resign.py "D:\SCDA\hdd\E\UDATA\5553005e\7BA18D20FCE6" --backup
```

---

## Files Handled

The script will scan and resign:
- `profile.sav` (Player profile and checkpoint index)
- `single0.sav` – `single5.sav` (Single-player campaign checkpoints)
- `single0image.sav` – `single5image.sav` (Checkpoint slot thumbnails)

---

## License

MIT License. See [LICENSE](LICENSE) for details.
