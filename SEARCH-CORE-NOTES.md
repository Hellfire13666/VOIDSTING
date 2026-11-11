# VOIDSTING v1.3.0 // PUBLIC PROFILE SEARCH CORE

The Cockpit design, CSS, JavaScript, 10-command menu, SQLite schema and
BLACKSWARM separation are retained. Only backend source rules, safe validation,
source counts and displayed release labels change.

Full Verify now includes 20 individual public API checks (16 original plus 4
new checks). Optional Public Directory Hints now has four bounded sources:
GitHub, Bluesky, GitLab and Gitea.com. Auth-restricted results are BLOCKED,
not retried or bypassed. Directory candidates never become exact verification. These are *not* 20 different social networks: two are independent
Mastodon instances. Quick Verify still makes only six checks.

New sources:
- Minecraft Java: public username-to-UUID lookup, rejects malformed IDs.
- Mastodon.online: exact local WebFinger account with self-link evidence.
- Fosstodon.org: another distinct local WebFinger domain.
- Pixelfed.social: public no-token account lookup, exact local account only.

Rules: sequential bounded GET requests, no private access, no account linking,
no redirects to other hosts, no attempts to evade 403/429, no auto-browser.
Pixelfed limits its public lookup to 50/day/IP. Requests are opt-in via Full
Verify; only one per run. Invalid usernames are marked uncertain rather than
missing. Empty/missing per-platform results never mean global absence.

Sources: https://minecraft.wiki/w/Mojang_API
https://docs.joinmastodon.org/spec/webfinger/
https://developers.pixelfed.org/api/accounts
https://docs.gitlab.com/api/users/
https://docs.gitea.com/api/1.25/operations/user-search/

No live external source claims. Offline validation uses simulated source data.
