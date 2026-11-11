# VOIDSTING: source design notes

This project uses public provider APIs rather than assuming a generated URL is a real account. These are external service endpoints and can change or require authorization at any time.

- GitHub: `GET /users/{username}`; compare returned `login`. [Official REST reference](https://docs.github.com/en/rest/users/users#get-a-user).
- GitLab: `GET /api/v4/users?username=`; exact username query; 403 is blocked, not absence. [Official Users API](https://docs.gitlab.com/api/users/).
- Hacker News: public Firebase user object, whose `id` is case-sensitive. No public activity means it may return null. [Official API reference](https://github.com/HackerNews/API).
- DEV Community: public user-by-username route with returned `username`. [Official Forem API docs](https://developers.forem.com/api/v0).
- Bluesky: public AppView `app.bsky.actor.getProfile` returns `handle` and DID. A 400 unresolved actor is `UNCERTAIN`, not confirmed absence. [Official HTTP API docs](https://docs.bsky.app/docs/api/).
- Remaining configured sources (Codeberg, Codewars, Scratch, Hugging Face, Mastodon.social WebFinger, Reddit, Wikipedia) each require a source-specific JSON identifier before EXACT.

Some providers may change anonymous access or require new API headers. Do not treat a failed call as a missing account. There is no stealth mode, CAPTCHA avoidance, or automated retry of rate-limited sources.

The standalone core is original code. Third-party source code from username research utilities is not bundled or silently reused.


## v1.2.2 additional public API source references (reviewed Nov 2026)

- Chess.com player PubAPI: https://support.chess.com/en/articles/9650547-what-is-the-pubapi-and-how-do-i-use-it
- Lichess users endpoint: https://lichess-org.github.io/api/
- Modrinth user lookup: https://docs.modrinth.com/api/operations/getuser/
- Gitea public user lookup: https://docs.gitea.com/api/

Endpoint JSON identifiers checked: chesscom username, lichess id, modrinth username, gitea login. Each check has no login and one bounded request. Provider restrictions and schema changes are surfaced as BLOCKED or UNCERTAIN rather than assuming an account exists. This is an independent implementation, no source code copied from third-party username scanners.

## v1.2.2 Cockpit-only additions

No new sources were added in v1.2.2. The Reference Atlas generates the same 25 manual link templates as the terminal Option [8]. Those links are NOT CHECKED. No new scan requests are made by the Cockpit.


OPTIONAL WIDE PUBLIC SEARCH (v1.4.0):
Run bash ./SETUP-WIDE-SEARCH.sh ONLY if you choose to install a separate 120-site Maigret engine.
The installation stays inside this extracted folder (.wide-venv). No system installs.
Use existing [3] for 20 API checks + 4 directories, plus the optional public-site sweep.
Maigret findings are labeled RELATED and require independent verification.
No recursion, AI profiling, username permutations, page parsing, login, or browser launching.
