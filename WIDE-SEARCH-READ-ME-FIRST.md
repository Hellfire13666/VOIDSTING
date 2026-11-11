# VOIDSTING v1.5.1 // WIDE PUBLIC SEARCH

This is a **separate testing build**. The approved v1.2.4 Cockpit and previous ZIPs remain untouched.

## Why this is an actual expansion

The native v1.3 API engine checks 20 fixed endpoints, so many legitimate accounts on unrelated sites were never searched. This optional adapter uses the independent MIT-licensed open-source **Maigret** presence-check engine and its bundled curated site definitions to check up to 120 ranked public websites in addition to the native 20 APIs and four search directories. It does not try to guess that one handle means one person.

## Setup: explicit installation only

After extracting the ZIP, run `bash SETUP-WIDE-SEARCH.sh` **only if you approve** adding an isolated `.wide-venv` inside this extraction. It uses network pip installation of `maigret==0.6.6` and its Python dependencies. No system-wide installs, `sudo`, auto-browser, or modification to an installed VOIDSTING.

Launching `RUN-VOIDSTING.sh` never installs third-party software automatically.

## Search

Launch `bash RUN-VOIDSTING.sh --color always`; select existing option `[3]`, enter a single username. It first runs the 20 API validations and four opt-in directories, then the 120-site presence sweep if installed. A new private session stores only bounded public profile URL candidates from the external sweep.

The sweep is bounded to 120 sites, eight simultaneous requests, one retry for transient failures, no recursive username pivots, no collecting private content, and no AI profiling. Site existence signals are tagged **RELATED** (review needed) rather than API-verified EXACT. False positives can occur. Sites blocking checks stay unverified.

Vault schema, directory, exports, terminal menu count and dashboard assets remain unchanged.

## Limits

The bundled dependency is **not** in this ZIP. No live integration test was possible in the creation environment because network package installation and live checks were unavailable. The local unit tests mock third-party output. Changes in the Maigret API or dependent packages may require troubleshooting. Provider names and URLs are from Maigret; no claim of same person or linked identity.

Upstream: https://github.com/soxoj/maigret (MIT License).


EVIDENCE GUARD v1.5.1: See EVIDENCE-GUARD-RELEASE-NOTES.md. Legacy Cockpit assets remain unchanged; wider site hits are review-needed only.

WIDE RELIABILITY v1.5.1: see WIDE-RELIABILITY-RELEASE-NOTES.md; progress + conclusive/inconclusive checks; one retry, 18-second site timeout.
