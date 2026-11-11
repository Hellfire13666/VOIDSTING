# ☣ VOIDSTING v1.5.1 // GLITCHBYTE PHANTOM LABS

**Public profile signals. Precise evidence. Your own research vault.**

VOIDSTING is an independent, terminal-first username research tool created for the GlitchByte universe. It does not use or modify BLACKSWARM, its 20-option command deck, its Cockpit, saved sessions, or database.

## Start here (Linux)

Extract the ZIP anywhere you choose. In the extracted folder:

```bash
bash RUN-VOIDSTING.sh --color always
```

Or launch from Downloads (after extracting the full folder there):

```bash
bash "$HOME/Downloads/VOIDSTING-v1.5.1/RUN-VOIDSTING.sh" --color always
```

**Recommended first action: [9] OFFLINE DEMO.** You can see a fictional test session without internet access, then use [1] QUICK VERIFY for a real public handle.

## New in v1.4.0 // SEARCH CORE

- Full Verify: 20 bounded public API checks (16 original, four new); Quick Verify remains 6.
- Added public Minecraft Java lookup, Mastodon.online, Fosstodon.org, Pixelfed.social.
- Public Directory Hints now includes four limited directory sources: GitHub, Bluesky, GitLab, Gitea.com.
- No anonymous account linking, no forced browsing, no retries or access-control bypass.
- Exact profile verification requires account identifiers, not just a 200 OK page.
- Cockpit layout, CSS, JS, ten menu choices, and existing vault schema preserved.
- Pixelfed explicitly limits its public lookup to 50/day/IP; run only on request.
- All external sources can refuse requests; results must be verified on your computer.

## Earlier release: v1.2.4 // EVEN SCROLL

**Right-hand layout correction only:** On desktop, the existing Saved Traces panel expands to the same bottom edge as the center column while keeping its actual saved sessions visible and scrollable. Saved-session cards take more room when the panel is tall. No additional data, search commands, providers, or vault changes. Tablets and phones preserve their stacked layout.

## Retained from v1.2.3 // VOIDPULSE

**New full-size center display:** VOIDPULSE replaces the narrow constellation panel with a much larger, interactive visualization of the selected saved session. It shows a dynamic signal network, read-only saved session identity, exact/related/uncertain/other evidence distribution, timestamp, and category buttons connected to the existing Evidence Explorer. It does not run a search, change database data, or imply common ownership. Existing Venom Control Core in the left rail is preserved.

## Retained from v1.2.2 // VENOM CONTROL CORE

**Left-sidebar expansion only:** The new rainbow VENOM CONTROL CORE reuses the original venom emblem as a compact signal radar. It displays the **selected saved handle, scan mode, exact/related/unresolved counts, and latest session number**, all from already-saved local vault data. History, Evidence and Sources are working anchor links to the existing Cockpit sections. Nothing in this panel runs a search or alters the vault.

The Control Core sits below The Observatory navigation. At narrower mobile widths it is hidden alongside the collapsed navigation, preserving a compact mobile header. At desktop widths the left rail remains independently scrollable.

## Retained from v1.2.1 // BALANCED RAINBOW VENOM

**Layout-only corrective release:** The original 25-link manual Reference Atlas and saved-session Timeline now appear under the center Evidence Explorer. The right column retains Venom Signal Tower, Provider Matrix, Source Guard, and Saved Traces. This fills the former large empty center gap as you scroll without adding data, queries, or navigation items. At desktop widths the center is wider, with two-column timeline and three-column manual references; smaller widths stack responsively.

The original 16 public API checks plus four bounded new checks, all 10 menu choices, saved SQLite schema, no-auto-browser rule, and BLACKSWARM independence are retained. The Reference Atlas is still **NOT CHECKED** and never counts towards discoveries.

## Previously introduced in v1.2.0 (retained)

- **Full Verify grows from 12 to 16 checks.** Four newly documented public API sources: Chess.com, Lichess, Modrinth and Gitea.com. Each uses an exact returned username field; a 200 alone never counts as FOUND. Live responses and endpoint availability depend on the sites.
- **Quick Verify stays at 6** for a familiar, fast first check.
- **Cockpit redesign.** Cyber-violet/acid-green Venom Signal header and radar, a real evidence Constellation with clickable nodes, a provider-status matrix, a search-within-evidence input, and mobile-friendly layouts. No scans run from the browser.
- **Existing vault schema unchanged**, so old v1.0.0 sessions remain readable. New scans append sessions as before.
- **No automatic browser opening, no dependencies, and no change to BLACKSWARM.**

The menu offers:

| Menu | Action |
|---|---|
| 1 | QUICK VERIFY: six public profile APIs, sequential |
| 2 | FULL VERIFY: sixteen public profile APIs, sequential |
| 3 | PUBLIC DIRECTORY HINTS: 16 API checks + 2 bounded public directory queries |
| 4 | Saved sessions, newest first |
| 5 | Inspect evidence and source responses for one session |
| 6 | Compare two saved sessions (read-only) |
| 7 | Export a session to JSON, CSV, or self-contained HTML (new file only) |
| 8 | See checked sources and optional *unverified* manual link templates |
| 9 | Fictional offline demo, clearly marked |
| 10 | Start optional local Cockpit, print URL, **never auto-open browser** |
| 0 | Quit |

## Exact API checking, not invented accounts

The 16 providers are GitHub, GitLab, Codeberg, DEV Community, Codewars, Scratch, Hugging Face, Hacker News, Bluesky, Mastodon.social, Reddit, Wikipedia, Chess.com, Lichess, Modrinth, and Gitea.com. API responses are checked for source-specific username identifiers. An HTTP 200 alone does not qualify as an account match.

Results mean:

- `EXACT`: public source returned a matching account identifier. **Not proof of identity across sites.**
- `RELATED`: a public directory suggested a related public handle. Not exact verification.
- `NOT_FOUND`: that particular API supplied a missing/empty response. Not evidence of global absence.
- `UNCERTAIN`: a redirect, unrecognized response, Bluesky unresolved actor, malformed JSON or similar ambiguous case.
- `BLOCKED`: authentication restriction, forbidden response or rate limit. No bypass or retry.
- `ERROR`: provider/network failure.

No automatic searching of links in the manual-reference list. These are `NOT_CHECKED`, explicitly separate from findings.

## Commands for advanced use

```bash
# Six API checks, new local vault session
bash RUN-VOIDSTING.sh glitchbyte --color always

# Sixteen API checks
bash RUN-VOIDSTING.sh glitchbyte --full --color always

# Optional two public directory lookups, not treated as exact matches
bash RUN-VOIDSTING.sh glitchbyte --full --discover --color always

# Create a fresh exported report after the scan
bash RUN-VOIDSTING.sh glitchbyte --save my-research.json --color always

# Open your dashboard yourself using the printed URL
bash RUN-VOIDSTING.sh --dashboard --color always

# Offline demo with an independent disposable vault
bash RUN-VOIDSTING.sh phantomdemo --offline-demo --vault ./demo-voidsting.sqlite3

# List configured public API sources
bash RUN-VOIDSTING.sh --list-sources
```

## The Cockpit

Menu [10] starts a local read-only server on `127.0.0.1` using an ephemeral free port. It prints the link and leaves your browser closed. The new Venom Signal Cockpit displays saved sessions, a session evidence constellation, provider-status matrix, color-coded source results, clickable node-driven filters, a keyword filter, and a redesigned tall Signal Tower. The constellation is a visualization of saved evidence, not evidence of relationships between accounts. It does not run searches itself.

Close the terminal app to stop the dashboard, or use `--dashboard` and Ctrl+C. It binds only to your own computer's loopback interface; no external web service, account or API key is used for the interface.

## Privacy and safety seal

- **BLACKSWARM untouched.** VOIDSTING never imports, reads or writes BLACKSWARM files or vault tables.
- Standalone database: `~/.local/share/voidsting/voidsting.sqlite3`. Existing file is reused; a `--vault` path can isolate a demo/research session.
- No login, credentials, cloud upload, private-page traversal, cross-account identity merging, proxy rotation or rate-limit evasion.
- One username per scan. Fixed HTTPS public APIs, requests one after another with small gaps, 6-second per-request timeout, bounded reply size and no retries. Certain same-site canonical redirects may be followed once, while cross-domain redirects are not followed.
- No browser auto-opening, shell configuration modifications, desktop environment assumptions, package installation, background scheduling or external dependencies.
- Saved results contain provider, verdict, account handle, public URL, brief reason, HTTP status and response timing. **No raw personal profile payloads** are archived.
- Export is opt-in and will refuse to overwrite existing report files.
- A matched handle cannot establish common account ownership. Use only for appropriate public research, respect applicable policies and laws, and manually review consequential findings.

## Limitations

This is a standalone second release, not a 200-site checker. Competitor results cannot be compared fairly without identical handles, sources, account states and live network measurements. Even a source returning 404 may hide accounts or reject anonymous queries. Some APIs may rate-limit or change. Honest uncertainty is a feature.

All tests simulate provider responses offline. Live outcomes are subject to the actual services on the day you run a search.

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

## Credits and licensing

Original GlitchByte-oriented implementation using the Python standard library. The high-level idea of site-specific username checking was informed by publicly documented approaches from multiple research utilities; no Sherlock, Maigret, Blackbird or other tool code is included. No third-party attribution has been removed or disguised.

## v1.2.4 // RAINBOW VENOM COCKPIT

- Rainbow-spectrum panels, constellation, provider tiles, glow halo and accent bands.
- Read-only Signal Timeline for previously saved sessions.
- Provider Pulse shows accurate saved status counts for the selected session.
- Reference Atlas lists all 25 **NOT CHECKED** manual reference destinations for the selected handle.
  These links are not scanned, never become evidence, and open only on a deliberate click.
- Same 10 terminal menu options, 16 exact public APIs and private SQLite schema.
- Respects reduced-motion settings.
- Separate ZIP/folder. BLACKSWARM is untouched.


OPTIONAL WIDE PUBLIC SEARCH (v1.4.0):
Run bash ./SETUP-WIDE-SEARCH.sh ONLY if you choose to install a separate 120-site Maigret engine.
The installation stays inside this extracted folder (.wide-venv). No system installs.
Use existing [3] for 20 API checks + 4 directories, plus the optional public-site sweep.
Maigret findings are labeled RELATED and require independent verification.
No recursion, AI profiling, username permutations, page parsing, login, or browser launching.


EVIDENCE GUARD v1.5.1: See EVIDENCE-GUARD-RELEASE-NOTES.md. Legacy Cockpit assets remain unchanged; wider site hits are review-needed only.

## v1.5.1 Wide Reliability Fix
See `WIDE-RELIABILITY-RELEASE-NOTES.md`. This release only adjusts the optional wide-sweep reporting and transient-failure handling.
