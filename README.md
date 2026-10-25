# travel_partner: installing the prerequisites (Windows)

Set these up before building or running the project. Run every command in **PowerShell**.

| Tool | Required version | Why it's needed |
|---|---|---|
| Python | 3.10 or newer | Backend (FastAPI) and the AI agent (`claude-agent-sdk`) |
| pip | comes with Python | Installs the Python packages |
| Node.js + npm | 22 LTS | React frontend (Vite) |
| Git | any recent version | Version control |
| Anthropic API key | — | Lets the agent call Claude |

---

## 1. Python

Check whether it's already installed:
```powershell
python --version
pip --version
```
If the version is **3.10 or newer**, skip to step 2.

Otherwise, install it:
```powershell
winget install Python.Python.3.13
```
Or download it from https://www.python.org/downloads/. **Tick "Add python.exe to PATH"** in the installer.

Close and reopen PowerShell, then check again with `python --version`.

> If a package fails to install later on Python 3.14 because no prebuilt wheel exists yet, install Python 3.13 and create the project's virtual environment with it: `py -3.13 -m venv .venv`.

---

## 2. Node.js and npm

Check:
```powershell
node --version
npm --version
```
If you see `v22.x` or newer, skip to step 3.

Install the LTS release:
```powershell
winget install OpenJS.NodeJS.LTS
```
Or download the **LTS** installer from https://nodejs.org/.

**Close and reopen PowerShell** so the PATH update takes effect, then check again.

> If PowerShell blocks `npm` with *"running scripts is disabled on this system"*, run this once:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

---

## 3. Git

Check:
```powershell
git --version
```
If it isn't installed:
```powershell
winget install Git.Git
```
Set your identity once (it's used in commit messages):
```powershell
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

---

## 4. Anthropic API key

1. Sign in at https://console.anthropic.com/.
2. Go to **Settings → API Keys → Create Key** and copy the key (it starts with `sk-ant-`).
3. Add billing or credits under **Settings → Billing**. The API doesn't work without them.
4. Once the project is set up, put the key in `travel_partner/personal-info/.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

> 🔒 Never paste the key into frontend code, commit it to Git, or share it. `personal-info/` is gitignored. If a key ever leaks, **revoke it in the console and create a new one**. Deleting the file isn't enough.

---

## 5. Optional but recommended

- **VS Code:** `winget install Microsoft.VisualStudioCode`
- **Google Chrome:** used to preview the UI and inspect the design reference site.

The Claude Code CLI that the agent needs is **bundled with the `claude-agent-sdk` Python package**, so it needs no separate install.

---

## Final check

Run all of these in a fresh PowerShell window:
```powershell
python --version   # 3.10+
pip --version
node --version     # v22.x
npm --version
git --version
```
If they all print a version, the prerequisites are done. The project's own setup steps will go in `travel_partner/docs/setup.md`.
