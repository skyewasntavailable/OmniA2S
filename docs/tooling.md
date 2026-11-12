# Analysis tooling setup (cloud sandbox)

Reproducible notes; none of the tools below are committed to the repo.

## REA (morluto/rea, "Reverse Engineer Anything")
- Installed the CLI only, pinned to the version in the repo's `mcp.json`:
  `npm install --global --prefix "$HOME/.local" rea-agents@6.8.0` (Node 22.23.4 meets the engine floor).
- Did **not** run `rea setup` (it rewrites agent config such as `~/.claude.json`); the CLI is used directly. Add `$HOME/.local/bin` to `PATH`.
- Source clone for reference: `GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/morluto/rea /home/user/morluto/rea` (outside this repo).
- `rea doctor` status: Node OK. Missing analysis engines: Ghidra (`GHIDRA_INSTALL_DIR`), Hopper, IDA, JADX, Kuna.

## Firmware extraction
- `unblob` from PyPI in a venv, wired in with `REA_UNBLOB_COMMAND=<venv>/bin/unblob`. `rea extract-firmware <bin> <absent-dir>` then runs end to end.
- Result on the V2.5.0 image: **unblob extracts nothing** (file magic is just `data`), consistent with a proprietary `HTFW` container.
- apt provides `radare2 5.5.0` and `binwalk 2.3.4` (installed). REA wants Rizin (`REA_RIZIN_COMMAND`) and binwalk 3, so these are only used directly.

## Blocked: Ghidra
- Ghidra 12.1.x is not on apt/PyPI/npm. github.com release downloads return 403 from the sandbox ("GitHub access to this repository is not enabled for this session"): this is the per-repository GitHub policy, not the host allowlist. Needs another route (a Ghidra release zip uploaded by the user, or attaching the repo with access if that is permitted).
