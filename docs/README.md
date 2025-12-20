# PySheet – D&D 5e Character Sheet

PySheet is a browser-first character sheet for Dungeons & Dragons 5th Edition. It is written with HTML/CSS and powered by [PyScript](https://pyscript.net), allowing you to run Python directly in the browser—perfect for platforms such as Chromebooks that do not allow native executables.

## Features

- Live ability modifier, proficiency, saving throw, and skill calculations
- Spellcasting DC/attack computations with selectable spellcasting ability
- Integrated spell library search (powered by Open5e) with filters by name, level, and class
- Interactive spellbook manager with add/remove controls, automatic class-level validation, and spell slot tracking with long-rest reset
- Quick hit point buttons, hit-dice tracking, and customizable resource counters for class abilities
- Tabbed layout for overview, skills, combat, inventory, spells, and data management
- Local storage persistence so your sheet survives refreshes and offline sessions
- JSON export/import to move characters between browsers or share with friends
- Responsive, dark-themed UI designed for tablet and laptop use

## Project Structure

```
DnDCharacter/
├── index.html              # Entry point that loads PyScript and the sheet UI
└── assets/
    ├── css/
    │   └── styles.css      # Styling for the application
    └── py/
      ├── character_models.py  # Domain models used by the PyScript controller
      └── character.py         # PyScript logic executed in the browser
```

> Tip: VS Code may flag the `js` and `pyodide` imports in `character.py`. These modules are provided by PyScript at runtime, so those warnings can be ignored for this project.

## Getting Started

1. **Open the sheet**
   - Double-click `index.html`, or
   - Serve the folder with a simple web server (avoids CORS issues in some browsers):
     ```powershell
     pwsh -NoLogo -Command "python -m http.server"
     ```
   - Then visit `http://localhost:8000` in your browser.


### Developing in WSL or with a Dev Container ✅

If you develop inside WSL2 or use a Dev Container, VS Code can attach directly to the Linux environment so terminals, tests, and extensions run inside the same system as your app.

- WSL (recommended):
  - Install the **Remote - WSL** extension in VS Code.
  - From a WSL shell in the project folder:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    code .  # opens VS Code attached to the WSL environment
    ```
  - Start the Flask server in WSL: `python backend.py` and open `http://localhost:5000` on your host browser (WSL2 forwards ports to localhost).

- Dev Container (reproducible):
  - A minimal devcontainer is included in `.devcontainer/devcontainer.json` which installs Python and your pip dependencies automatically (`pip install -r requirements.txt`).
  - Recommended extensions are declared in `.vscode/extensions.json` and the devcontainer config so VS Code will prompt to install them when you open the workspace or the container.

- Installing extensions in bulk: use `code --list-extensions > extensions.txt` to export and `cat extensions.txt | xargs -L 1 code --install-extension` to install from a file.

These options ensure consistent tooling and make onboarding easier for future contributors.

2. **Use the app**
   - Fill in your character details; totals update automatically.
   - Click **Save to Browser** to persist data in `localStorage`.
   - Export or import JSON files to move characters between devices.

3. **Resetting**
   - Use the **Reset** button to restore defaults and clear saved data.

## Spell Library Reference

- Open the **Spells** tab and click **Load Spells** to pull the 5e SRD spell list from the [Open5e API](https://open5e.com/). An internet connection is required for the initial fetch.
- When the catalog loads, PySheet automatically narrows the results to the spell levels your detected caster classes can actually use; update the **Class & Level** fields to refresh the filtered list.
- Filter the results instantly by entering text, selecting a spell level, or choosing a character class. Up to 200 matches are rendered at once to keep the UI responsive.
- Once fetched, the normalized spell catalog is cached in `localStorage` so it’s available next session without reloading.
- Hold the **Alt** key while clicking **Load Spells** to force a refresh if you want to pull the latest Open5e data.
- The spell catalog is saved in browser `localStorage`; clear site data or force-refresh to remove or update it.
- Use the **Add**/**Remove** buttons on each spell card to curate your prepared list. The right-hand panel groups selections by level, tracks slots spent/recovered, and includes a **Long Rest Reset** control that instantly restores all slots.

## Tracking Health & Class Resources

- In the **Combat** tab, use the quick buttons to apply damage or healing and to manage hit-dice spending. Values are clamped between zero and your maximum/level automatically.
- The status badges next to each tracker update live, including temporary hit points for reference.
- Under **Manage → Resource Trackers**, create counters for class features (e.g., Rage, Ki, Superiority Dice). Each tracker stores name, remaining uses, and maximum; use the ± buttons or edit fields directly.
- A maximum of 12 custom resources are stored per character. Trackers are saved with the rest of the sheet data in `localStorage` and exports/imports.

## Managing Exports & Storage

- Each time you click **Export JSON**, a new timestamped file is created in the `/exports/` folder
- Over time, this folder can accumulate many old backup files
- **Storage Info** shows your current usage and estimated number of exports
- **Cleanup Old Exports** maintains browser logs and shows cleanup status; for the `/exports/` folder itself:
  - **On Desktop**: Open your file manager, navigate to the project folder, and manually delete old files from `/exports/`
  - **On Chromebook**: The `/exports/` folder is managed by the browser's File System API. Use the browser's download manager or clear site data to manage exports
  - **Recommended practice**: Keep 5-10 recent exports per character as backups, delete the rest

### Log Management & Rolling Window

PySheet automatically maintains a **rolling 60-day log window** in browser storage:

- **Automatic pruning**: Logs older than 60 days are automatically removed when new logs are written
- **Per-day limits**: Maximum 1000 log entries per day prevents unlimited growth from heavy usage
- **Storage key**: Logs are stored in `localStorage` under `"pysheet_logs_v2"` 
- **Statistics**: Click "Cleanup Old Exports" to see log stats including total entries, days covered, and storage used
- **Zero configuration**: The system works automatically—no manual intervention needed

Log entries capture:
- Timestamp (ISO format with milliseconds)
- Log level: INFO, WARNING, ERROR
- Message and exception details (for errors)

This ensures your browser storage stays manageable even with weeks of active gameplay.

To prevent folder bloat:
1. Periodically review the `/exports/` folder
2. Keep only recent backups (last 2-3 weeks)
3. Move important character milestones to a backup folder if you want to preserve them
4. Use Git or cloud storage for permanent version control of favorite characters
## Command-Line Interface

### Setup Scripts

All setup scripts automatically create a venv and install dependencies:

**Python (Cross-Platform):**
```bash
python activate-env.py                      # Setup only, show instructions
python activate-env.py --server             # Setup and start Flask server
```

**PowerShell (Windows):**
```powershell
.\activate-env.ps1                          # Setup only, show instructions
.\activate-env.ps1 -StartServer             # Setup and start Flask server
```

**Bash (Linux/macOS):**
```bash
./activate-env.sh                           # Setup only, show instructions
./activate-env.sh --server                  # Setup and start Flask server
```

### Flask Backend Server

Start the Flask server with optional configuration:

```bash
python backend.py                           # Start on localhost:8080 (default)
python backend.py --port 5000               # Use port 5000
python backend.py --host 0.0.0.0            # Listen on all network interfaces
python backend.py --debug                   # Enable Flask debug mode (auto-reload)
python backend.py --help                    # Show all available options
```

### Virtual Environment Management

```bash
# Activate the venv
# Windows PowerShell:
& ".\.venv\Scripts\Activate.ps1"

# Linux/macOS:
source .venv/bin/activate

# Install/update packages
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Deactivate when done
deactivate
```

### Testing & Development

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_character_models.py -v

# Run tests with coverage
python -m pytest tests/ --cov
```
## Development Notes

- The application runs entirely client-side; no backend or traditional Python environment is required.
- Spell data is fetched at runtime from Open5e and cached client-side. If you need offline access, download the Open5e spells JSON and serve it locally via the same API shape, then refresh the cache with Alt+Load.
- If you want linting or testing on the Python file, you can create a virtual environment, but it is optional. The PyScript runtime ignores standard virtual environments since the Python code executes inside the browser’s Pyodide engine.
- When updating dependencies, track PyScript releases and update the CDN URLs in `index.html` as needed.

## Ideas for Future Enhancements

- Add condition tracking, automated consumable management, or inventory weight calculations
- Provide multiple character slots with quick switching
- Integrate dice rolling via PyScript or Web APIs
- Offer print-friendly or PDF export layouts

Enjoy crafting heroes with PySheet! 🎲
