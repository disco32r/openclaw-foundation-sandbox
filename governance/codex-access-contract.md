# Codex Access Contract

This project must not use Windows PowerShell as the project logic layer.

## Source Paths

- Canonical VM repo: `/opt/openclaw`
- SSH login starts in: `/opt/openclaw`
- Windows mount for direct file reads and edits: `Q:\opt\openclaw`
- Codex SSH launcher: `C:\Users\Ryan\.codex\openclaw\ocssh.cmd`
- Active runtime root: `/opt/openclaw-data/runtime/oc`
- Active runtime compose env: `/opt/openclaw-data/runtime/oc/compose.env`
- Active runtime compose override: `/opt/openclaw-data/runtime/oc/compose.override.yml`
- Active Docker project/network/container: `oc`, `oc-net`, `openclaw-gateway`

The forked OpenClaw source repo is the source of truth. Codex session context, local scratch folders, and runtime workspace files are not authority.

## Allowed Access Pattern

- Read and edit source files through the mounted `Q:` repo path or direct SSH/SFTP as the `openclaw` user.
- Run repo commands through `C:\Users\Ryan\.codex\openclaw\ocssh.cmd` or an equivalent direct SSH/SFTP session that starts in `/opt/openclaw`.
- Use Git branches and commits for durable state.
- Use `python3 tools/validate_governance.py` from the VM repo before claiming a gate is valid.
- Use the VM's persistent Git credential helper for GitHub operations; do not paste tokens into ad hoc push commands.
- Use the sudo helper only for protected VM/runtime/system operations.

## Forbidden Access Pattern

- Do not tunnel large JSON, Python, patches, or generated source through PowerShell quoting.
- Do not use PowerShell text transforms to rewrite repo-owned source files.
- Do not hand-write complex inline SSH payloads when `ocssh.cmd --file` or `ocssh.cmd --stdin` can send the remote POSIX shell body directly.
- Do not put GitHub tokens in the origin/upstream remote URL.
- Do not treat the Codex local workspace as source authority.
- Do not use sudo for normal source edits.
- Do not edit runtime workspace files as substitutes for source-repo governance.

## Durable GitHub Auth

- VM credential helper: `store --file ~/.git-credentials-openclaw`
- Credential file owner/mode: `openclaw`, `0600`
- Remote URLs stay token-free:
  - `origin`: `https://github.com/disco32r/openclaw-foundation-sandbox.git`
  - `upstream`: `https://github.com/openclaw/openclaw.git`
- Prove auth with `git ls-remote --heads origin codex/foundation-governance-bootstrap` and `git push --dry-run origin codex/foundation-governance-bootstrap`.

## Command Boundary

The Windows Codex host may still launch commands, but launched commands must hand off quickly to the proper project surface:

- file edits through the mounted repo path,
- repo validation through remote POSIX shell,
- protected operations through the existing sudo helper.

PowerShell mount maintenance is allowed only for repairing `Q:` itself. It is not project management, governance, or build logic.

Historical evidence files may mention retired runtime paths or project slugs. They are records only; they are not current operating instructions. Current authority is the source/runtime table above plus `governance/gate-ledger.json`.
