# Handoff (moving from cloud session to local)

## Goal
Reverse engineer Ampero II Stomp firmware to see what modifications are possible. Particular interest: **Bluetooth** (ESP32 co-processor is present but not in the manual).

## User constraints
- Only has the official updater/editor; recovery = the pedal's force-update mode.
- User does not know whether the firmware is encrypted (it is not, at the outer level).
- Primary device so far was a phone; the PC has Ghidra 12.1.4 (REA requires 12.1.x), the editor software and the pedal.

## Established facts (see docs/firmware-analysis.md for evidence)
- `HTFW` container, no outer encryption/compression found; header has total size, `MP-300`, version, 4-segment table.
- Main MCU NXP i.MX RT1052 (Cortex-M7) app is plain Thumb-2 in file offsets ~0x1EE-0x7xxxx.
- SHARC DSP: `MP-300_DSP_Main_Core1/2.dxe` names at 0x2C6692 / 0x8903F5; DSP code probably in the medium-entropy regions, unconfirmed.
- ESP32 co-processor: `ESP32_APP`, `Drivers\\esp32\\bluetooth.c`, `BLES_DATA_PACK_MAX` (suggests BLE).
- 0x80000-0x16FFFF is a 512 KB high-entropy block (unknown: encrypted or compressed).
- 0x300000-0x61FFFF and 0x890000-0xB4xxxx are 16-bit sample data (probably cab IRs).
- Open: undecoded vector-table/startup block (0x9A-0x1EE, ~0x2FD-0x3A0), unknown app base address.

## Estimated feasibility (gut estimates)
UI/strings ~65%, footswitch/MIDI tweaks ~45-50%, BLE MIDI via existing ESP32 ~30-35%, new ESP32 firmware ~15%, new DSP effects ~5%. Everything depends on how the updater validates images (unknown).

## Next steps
1. Install Ghidra 12.1.4, set `GHIDRA_INSTALL_DIR`, re-run `rea doctor` (REA CLI 6.8.0, see docs/tooling.md).
2. Import the app region as ARM Cortex-M LE; find update/IAP/DFU code (strings near 0x1837D, 0x19B968) and the Bluetooth driver.
3. Determine how segments are validated and what the 512 KB block is.
4. Analyze the editor software's updater (install folder) and, if wanted, capture USB traffic during an update.

## Not in the repo (re-obtain locally)
Firmware zip, manual PDFs, Ghidra, REA clone, unblob venv.
