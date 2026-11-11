# VOIDSTING v1.5.1 // Wide Reliability Fix (isolated test build)

This fixes incomplete search coverage reporting, not a guarantee of username matches.

- Native 20 public API checks, 4 opt-in directories, 10 menus and original local vault stay unchanged.
- Optional 120-site sweep stays bounded, no recursive pivots or automated browser.
- Maigret now uses 18-second site timeout and one retry for transient failures (was 12 seconds, zero retries); scans can be slower.
- During a long sweep the terminal shows a progress heartbeat approximately every 18 seconds.
- Wide report distinguishes **site-level presence indicators**, **conclusive provider absences**, **unresolved**, **username unsupported by provider**, and **no result returned**. These are separate from native VOIDSTING API verdict and do not prove global account absence.
- A zero-candidate report with unresolved checks now explicitly warns about incomplete coverage.
- Existing conservative Evidence Guard filter stays in place. Search pages and unverified links never become EXACT.
- Wide checker errors and incomplete scans never remove or modify existing session results.

If `inv523` is not present on these particular public sites, no amount of error handling will create results; the accurate outcome may still be zero candidates.

Maigret is an optional external library installed only by user action via SETUP-WIDE-SEARCH.sh in this extracted copy. Upstream documentation: https://maigret.readthedocs.io/en/latest/library-usage.html

This test build is not live-network validated in our packaging environment. Test on known-public usernames and inspect the per-site coverage counts.

The approved Cockpit assets, dashboard server, existing vault schema, and BLACKSWARM are unchanged.
