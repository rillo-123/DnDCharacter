# PySheet – D&D 5e Character Sheet

PySheet is a browser-first character sheet for Dungeons & Dragons 5th Edition. It is written with HTML/CSS and powered by [PyScript](https://pyscript.net), allowing you to run Python directly in the browser—perfect for platforms such as Chromebooks that do not allow native executables.

## Features

- Live ability modifier, proficiency, saving throw, and skill calculations
- Spellcasting DC/attack computations with selectable spellcasting ability
- Integrated spell library search (powered by Open5e) with filters by name, level, and class
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
        └── character.py    # PyScript logic executed in the browser
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

## Tracking Health & Class Resources

- In the **Combat** tab, use the quick buttons to apply damage or healing and to manage hit-dice spending. Values are clamped between zero and your maximum/level automatically.
- The status badges next to each tracker update live, including temporary hit points for reference.
- Under **Manage → Resource Trackers**, create counters for class features (e.g., Rage, Ki, Superiority Dice). Each tracker stores name, remaining uses, and maximum; use the ± buttons or edit fields directly.
- A maximum of 12 custom resources are stored per character. Trackers are saved with the rest of the sheet data in `localStorage` and exports/imports.

## Development Notes

- The application runs entirely client-side; no backend or traditional Python environment is required.
- Spell data is fetched at runtime from Open5e and cached client-side. If you need offline access, download the Open5e spells JSON and serve it locally via the same API shape, then refresh the cache with Alt+Load.
- If you want linting or testing on the Python file, you can create a virtual environment, but it is optional. The PyScript runtime ignores standard virtual environments since the Python code executes inside the browser’s Pyodide engine.
- When updating dependencies, track PyScript releases and update the CDN URLs in `index.html` as needed.

## Ideas for Future Enhancements

- Add spell slot tracking, conditions, or inventory weight calculations
- Provide multiple character slots with quick switching
- Integrate dice rolling via PyScript or Web APIs
- Offer print-friendly or PDF export layouts

Enjoy crafting heroes with PySheet! 🎲
