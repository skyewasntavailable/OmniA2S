# Ampero II Stomp firmware V2.5.0 – initial analysis

Source: official updater package (`Ampero II Stomp Firmware V2.5.0.bin`, 11,874,527 bytes, not committed).

## Container
- Magic `HTFW` (0x00), then 0x18326 (?), then **0x00B530DF = total file size**.
- 0x0C: ASCII `MP-300` (Hotone's internal model name for the Stomp).
- 0x1C: `56 02 05 00` – likely version 2.5.0 (+ build 0x56).
- 0x38..0x7C: segment table, boundaries `0x458000 -> 0x4943C0 -> 0x4ACFC0 -> 0xFC1AF4`
  (looks like a 16 MB flash layout; flag/checksum words `0x0100DB0E`, `0x02008E57`, `0x10004476` per entry – meaning unknown).
- 0x90: test pattern `55555555 AAAAAAAA A5A5A5A5`, then a Cortex-M vector table (SP 0x20004000, reset 0x4E9).
- **No encryption signature**: plaintext strings, file paths and float tables are visible. Entropy is 7.2–7.5 over most of the file and ~7.95 over 0x80000–0x17FFFF (compressed or packed data).
- Earlier guess that the strings were byte-interleaved by a compressor was **wrong for the main app**: see "Step 1 findings" below.

## Chips (from firmware strings)
- **Main MCU: NXP i.MX RT1052** (Cortex-M7). Paths like `Drivers\devices\MIMXRT1052\drivers\fsl_*.c`, FlexSPI driver (external QSPI flash), eDMA, ADC_ETC. UI/touch/presets run here (`Drivers\GUI`, `Drivers\audio\PresetInterface`).
- **DSP: Analog Devices SHARC** – embedded ADI executables `MP-300_DSP_Main_Core1.dxe` (~0x2c6692) and `MP-300_DSP_Main_Core2.dxe` (~0x8903f5). `.dxe` is the ADI VisualDSP++/CCES format, so the DSP images are multi-core SHARC(+) executables. Exact part not yet identified.
- **ESP32** co-processor (Bluetooth/WiFi): strings `ESP32_APP`, `ESP32 VER:`, `Drivers\esp32\bluetooth.c`.
- Other strings: `DFU`, `IAP`, `DSP_WORK_STATE_MUTE`, `SetIO_Bypass`.

## Manual facts (V2.0.0 manual, Thomann 529004_en.pdf)
- 24-bit / 44.1 kHz, 460 effects, 12 simultaneous slots, 300 patches, 60 s stereo looper.
- IR: 24-bit/44.1k mono WAV, 1024/2048 points, up to 50 user IRs.
- 4" 800x480 touch screen, USB-C UAC2 8-in/8-out, 5-pin MIDI in/out.
- Updates go through the free "Ampero II" editor software (Release notes: V1.4.0+ for V2.5.0). Force-update mode exists on the pedal.
- Release notes: V2.3.1 added Sound Clone with NAM conversion; V2.5.0 adds a native NAM (A2, Lite) module.

## Next steps
1. Identify the packing/compression and decode the segments.
2. Extract ESP32 app and both SHARC .dxe files (ELF-like); identify SHARC part from the .dxe.
3. Map the effect table and patch/IR storage format.
4. Work out how the updater validates the file (checksums/signature) before any modified flash.

## Step 1 findings: packing / region map (`tools/regionmap.py`)
Result: **no outer compression or encryption layer was found.** Standard decoders (zlib/deflate scan, LZ4 block, gzip/zstd/xz magic) found nothing. The image is a plain container of several differently-typed regions:

| File offset | Content | Evidence |
|---|---|---|
| 0x000000-0x000080 | HTFW header + segment table | see above |
| 0x000080-0x000200 | start-up block: test pattern, Cortex-M vector table | low-level "token" bytes (see open issue) |
| 0x0001EE-~0x07xxxx | **Cortex-M7 application (Thumb-2), plain** | Thumb function-return/prologue markers (`70 47`, `10 b5`, ...) dense only here; clean disassembly of reset handler, `VTOR` literal `0xE000ED08`, Keil-style per-object strings with assert paths |
| 0x080000-0x16FFFF | **high entropy (7.97), unknown** | ~512 KB flat; candidate for encrypted/compressed payload (ESP32 app or DSP image?) |
| 0x170000-0x2FFFFF (mixed) | 7.1-7.4 entropy, no lane structure | not Thumb; likely DSP code/data or a packed resource area. `MP-300_DSP_Main_Core1.dxe` name sits at 0x2C6692 |
| ~0x220000-0x300000 | 4-byte/2-byte lane structure | tables/graphics (RGB565-like) |
| 0x300000-0x61FFFF, 0x890000-0xB4xxxx | **16-bit sample data** (lanes 0/2 ~7.99, lanes 1/3 ~5.7) | looks like PCM/IR (cab) data |
| 0x620000-0x88FFFF | 7.2-7.3 entropy, no lane structure | not Thumb; likely DSP image/data. `MP-300_DSP_Main_Core2.dxe` name at 0x8903F5, right after it |

The two `.dxe` names look like entries of a file table (name followed by metadata and float tables), so the SHARC code is probably in the 0x170000-0x2FFFFF and 0x620000-0x88FFFF areas, but this is unconfirmed.

### Open issues
1. Vector table / start-up area (0x9A-0x1EE and a similar block around 0x2FD-0x3A0) contains short 1-3 byte insertions (frequent `0xAC`, `0x22`) between otherwise plain 32-bit words. File vs. memory layout is not 1:1 there (reset vector 0x4E9 but reset code is at file 0x2B4). Probably an encoding of the vector table / relocation data; undecoded.
2. Load/base address of the app for Ghidra is still unknown; literals show addresses of the form 0x0000xxxx and 0x0001xxxx, i.e. ITCM-like, with the code relocated by the boot stage.
3. 0x80000-0x16FFFF high-entropy block: need to determine whether this is encrypted or compressed (check chi-square, try known AES/XOR keys from the ARM code, look for the decryption routine in the app).

### Suggested next steps
- Disassemble the app in Ghidra (ARM Cortex-M, little-endian) and find the update/IAP/DFU code (`IAP`, `DFU`, `ESP32_APP` strings at 0x1837D / 0x19B968) - it will show how segments are verified and decrypted/decompressed.
- Follow references to the `.dxe` names to learn the file-table format.

## DSP investigation (first pass)
- Only two DSP-related names exist in the image: `MP-300_DSP_Main_Core1.dxe` (0x2C668B) and `MP-300_DSP_Main_Core2.dxe` (0x8903EE). No ELF magic, no `.ldr` names, no `SHARC`/`ADSP` strings.
- Each name sits inside a structured record: neighbouring bytes look like pointers/flags (`... 00 60 80 ...`, `ac 28 00 60 80`) followed by float tables (e.g. sine/coefficient data `3d...`), not instruction streams. They are most likely file-table entries (name + metadata) for DSP/effect resources, not the executables themselves.
- The same kind of 1-3 byte stray tokens (`0xAC`, `0x22`) that appear in the ARM vector table also appear around these records, so the unexplained encoding is probably general and must be decoded before the DSP code can be extracted.
- The 7.1-7.4 entropy blocks have no 4- or 6-byte lane structure, so they are not raw 32-bit or 48-bit SHARC words; they are probably packed.
- Disassembly will also need a SHARC+ instruction decoder; I do not believe stock Ghidra ships one (not verified).
