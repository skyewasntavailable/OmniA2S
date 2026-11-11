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
- The code/strings look byte-interleaved (stray bytes inside strings, many 0x22 bytes), so some regions use an unidentified compression/packing scheme. Next step: identify it.

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
