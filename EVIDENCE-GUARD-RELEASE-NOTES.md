# VOIDSTING v1.5.1 // Evidence Guard (test build)

This is a NEW, separate extraction. No approved Cockpit layout, original prior ZIP, running tool, or BLACKSWARM installation is changed.

## Why the results were noisy

The optional Maigret 0.6.6 integration checks up to 120 public sites, in addition to the native 20 API checks and four directories. The previous v1.4 adapter accepted every Maigret "found" flag as a RELATED result, including search pages, redirect shortcuts, and third-party profile aggregators. It also printed the Maigret name in each candidate's reason and displayed "0 ms" for every wide result. Those choices were too generous and misleading.

## Evidence Guard improvements

- Accept only HTTPS URLs directly containing the requested username as a path component or account-style subdomain. This is a conservative **shape filter**, NOT independent verification that an account exists.
- Drop generic search/result pages, URL shorteners, known third-party tracker examples, duplicate URLs, and reported non-2xx HTTP status candidates. Some legitimate sites may be excluded; the filter intentionally favors precision over breadth.
- Wide results remain RELATED with evidence_type EXTERNAL_PROFILE_CANDIDATE and the explicit warning REVIEW NEEDED. No shared identity inference and no API EXACT promotion.
- Print `review` instead of fictional per-site `0 ms` timings; include measured overall sweep duration.
- Report count of candidate URLs admitted and filtered, and any known HTTP 401/403/429 or 5xx statuses as partial diagnostic tallies. The wide engine's other DNS, bot-defense and timeout errors are NOT included in native verdict totals; the terminal says this explicitly.
- Remove repeated Maigret attribution from candidate results. Keep proper attribution here and in documentation: optional backend is the independently authored open-source Maigret project (MIT license) maintained at https://github.com/soxoj/maigret. VOIDSTING's original engine, local research vault and Cockpit remain separate.

## What stays exactly the same

Twenty native source APIs, four directory providers, ten menu choices, established local SQLite schema and path, 120-site opt-in cap, no browser auto-open, and immutable approved Cockpit assets (`assets/app.js`, `assets/style.css`, `assets/cockpit.html`). Existing saved historical results are NOT rewritten or erased. Older sessions retain their original labels and link candidates.

## Installation

Unzip this archive under `~/Downloads`. Optional Maigret must be installed in the **new release directory** if you want the 120-site sweep. The installer is explicit and does not install globally:

    bash "$HOME/Downloads/VOIDSTING-v1.5.1/SETUP-WIDE-SEARCH.sh"
    bash "$HOME/Downloads/VOIDSTING-v1.5.1/RUN-VOIDSTING.sh" --color always

Then select [3] for directories + wide search. This build has only offline/mocked integration coverage. Live source behavior and package installation on the user's computer must be checked separately. No user-provided machine details are embedded.
