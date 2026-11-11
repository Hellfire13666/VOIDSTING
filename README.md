<p align="center"><img src="docs/assets/voidsting-icon.png" alt="VOIDSTING neon scorpion icon" width="175" /></p>

![VOIDSTING neon scorpion release artwork](docs/assets/voidsting-hero.webp)

# ☣ VOIDSTING // VOIDPULSE COCKPIT

**Public profile signals · Clear evidence · Local research vault**  
**GlitchByte Phantom Labs · Linux / Python 3 · Rainbow terminal + VOIDPULSE**

VOIDSTING is independent public-username research software. It is a separate sister to [BLACKSWARM](https://github.com/Hellfire13666/BLACKSWARM-SKULL-SWARM). Both have local visual Cockpits, but **they do not share a database, installation, or backend**.

## VOIDPULSE Launch Viewer

<p align="center">
  <img src="docs/assets/voidsting-icon.png" alt="VOIDSTING neon scorpion" width="105" />
</p>

**🦂 START · VERIFY · EXPLORE · SAVE**

This is the **working quick-start viewer directly on the repository page**. It does not open a source-code file or run scans on GitHub.

### Start VOIDSTING

Already inside the VOIDSTING application folder? Copy this command:

```bash
bash RUN-VOIDSTING.sh --color always
```

Downloading from this repository for the first time? In your Linux terminal:

```bash
cd "$HOME/Downloads"
git clone https://github.com/Hellfire13666/VOIDSTING.git
cd VOIDSTING
bash RUN-VOIDSTING.sh --color always
```

### Keep the wide search enabled

Run this **once** inside your downloaded VOIDSTING folder if you want the optional 120-site Maigret search under menu **[3]**:

```bash
bash SETUP-WIDE-SEARCH.sh
bash RUN-VOIDSTING.sh --color always
```

This installs the optional dependency in VOIDSTING's private environment only. You don't need to repeat the setup on every launch.

### Easy terminal choices

| Choose | What it does |
|:--:|---|
| **[1]** | **QUICK VERIFY** · 6 public API checks |
| **[2]** | **FULL VERIFY** · 20 public API checks |
| **[3]** | **DIRECTORY + WIDE** · 4 directories and optional 120-site sweep |
| **[4]** | Browse saved session history |
| **[5]** | Review saved evidence |
| **[6]** | Compare two sessions |
| **[7]** | Export saved results |
| **[8]** | List sources and reference links |
| **[9]** | Offline demo |
| **[10]** | **VOIDPULSE COCKPIT** · displays your local URL without opening a browser |
| **[0]** | Quit |

<p align="center">
<img src="docs/assets/voidsting-cockpit.png" alt="VOIDPULSE Cockpit simulated preview, not real findings" width="860" />
</p>

*Simulated Cockpit preview only. Your actual VOIDPULSE is local; your private vault and saved sessions never appear on GitHub.*

**Website status:** The separate decorative home-page files are stored in `docs/`, but they require **Repository Settings → Pages → Deploy from a branch → main → /docs → Save**. Until Pages is live, this README is the public quick-start viewer. Do not open `docs/index.html` through GitHub expecting a rendered website.

---

## Dependencies and source credit

The optional Maigret integration uses third-party **Maigret 0.6.6**, licensed MIT: <https://github.com/soxoj/maigret>. It is not bundled in the repository. Public sites may have rate limits or bot protections; candidates need independent review, and matching handles do not establish a shared identity.

## The local Cockpit

![Simulated VOIDSTING Cockpit preview; no live account findings](docs/assets/voidsting-cockpit.png)

The **VOIDPULSE** Cockpit shows saved public username evidence, sessions, status labels, and a constellation of findings. Its data remains local and private. The website hosted through GitHub Pages is a **static showcase only**. It cannot run username searches.

**[Use the VOIDPULSE Launch Viewer above](#voidpulse-launch-viewer)**. The decorative website still requires Pages activation.

## Results are not identities

- `EXACT`: API returns a matching handle. Not proof that two accounts are owned by one person.
- `RELATED`: a directory result or wide-site candidate requiring independent review.
- `NOT_FOUND`: absence indicated on that specific endpoint only.
- `UNCERTAIN` / `BLOCKED` / `ERROR`: unresolved, access-restricted or failed requests.

One handle is checked at a time. No credential capture, private-profile access, account-linking conclusions, or automatic browser activity.

## Safety and data protection

All saved sessions go to a **local SQLite vault**, never the public Pages site. Do not commit `.wide-venv`, `~/.local/share/voidsting/`, exported evidence, or private configuration. The `.gitignore` excludes common local research and credential formats. Manually review all files before first publication.

## Project guide

The commands above cover quick scans, full verification, the optional 120-site sweep, and the locally hosted VOIDPULSE Cockpit. The [VOIDPULSE Launch Viewer](#voidpulse-launch-viewer) showcases the interface; source code, automated tests, and setup scripts remain in this repository.

Review public-profile candidates individually. A username match is not evidence that accounts share an owner, and inaccessible sites are not proof of absence.

© GlitchByte Phantom Labs. No new software license is granted merely by publishing these files. Any reuse or licensing decision belongs to the repository owner.