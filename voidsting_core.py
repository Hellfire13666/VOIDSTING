"""VOIDSTING: original, bounded, public username checking core.

Only explicitly selected, fixed HTTPS public API endpoints are queried. No
login, scraping of private content, large-scale enumeration, retries, or
shared storage with BLACKSWARM. No third-party source code included.
"""
from __future__ import annotations

import csv
import html
import io
import json
import os
import re
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

VERSION = "1.5.1"
NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,38}\Z")
RESULT_STATES = ("EXACT", "RELATED", "NOT_FOUND", "UNCERTAIN", "BLOCKED", "ERROR")
API_MAX_BYTES = 180_000
TIMEOUT_SECONDS = 6.0
SOURCE_PAUSE_SECONDS = 0.30

@dataclass(frozen=True)
class Source:
    key: str
    name: str
    category: str
    endpoint: str
    profile: str

SOURCES = (
    Source("github", "GitHub", "Developer", "https://api.github.com/users/{name}", "https://github.com/{name}"),
    Source("gitlab", "GitLab", "Developer", "https://gitlab.com/api/v4/users?username={name}", "https://gitlab.com/{name}"),
    Source("codeberg", "Codeberg", "Developer", "https://codeberg.org/api/v1/users/{name}", "https://codeberg.org/{name}"),
    Source("dev", "DEV Community", "Developer", "https://dev.to/api/users/by_username?url={name}", "https://dev.to/{name}"),
    Source("codewars", "Codewars", "Developer", "https://www.codewars.com/api/v1/users/{name}", "https://www.codewars.com/users/{name}"),
    Source("scratch", "Scratch", "Creative", "https://api.scratch.mit.edu/users/{name}", "https://scratch.mit.edu/users/{name}/"),
    Source("huggingface", "Hugging Face", "Developer", "https://huggingface.co/api/users/{name}", "https://huggingface.co/{name}"),
    Source("hackernews", "Hacker News", "Community", "https://hacker-news.firebaseio.com/v0/user/{name}.json", "https://news.ycombinator.com/user?id={name}"),
    Source("bluesky", "Bluesky", "Social", "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={actor}", "https://bsky.app/profile/{actor}"),
    Source("mastodon", "Mastodon.social", "Social", "https://mastodon.social/.well-known/webfinger?resource={acct}", "https://mastodon.social/@{name}"),
    Source("reddit", "Reddit", "Community", "https://www.reddit.com/user/{name}/about.json", "https://www.reddit.com/user/{name}/"),
    Source("wikipedia", "Wikipedia", "Knowledge", "https://en.wikipedia.org/w/api.php?action=query&list=users&ususers={name}&format=json", "https://en.wikipedia.org/wiki/Special:Contributions/{name}"),
    Source("chesscom", "Chess.com", "Gaming", "https://api.chess.com/pub/player/{name}", "https://www.chess.com/member/{name}"),
    Source("lichess", "Lichess", "Gaming", "https://lichess.org/api/user/{name}", "https://lichess.org/@/{name}"),
    Source("modrinth", "Modrinth", "Creative", "https://api.modrinth.com/v2/user/{name}", "https://modrinth.com/user/{name}"),
    Source("gitea", "Gitea.com", "Developer", "https://gitea.com/api/v1/users/{name}", "https://gitea.com/{name}"),
    Source("minecraft", "Minecraft Java", "Gaming", "https://api.minecraftservices.com/minecraft/profile/lookup/name/{name}", "https://api.minecraftservices.com/minecraft/profile/lookup/name/{name}"),
    Source("mastodononline", "Mastodon.online", "Social", "https://mastodon.online/.well-known/webfinger?resource={acct_online}", "https://mastodon.online/@{name}"),
    Source("fosstodon", "Fosstodon.org", "Social", "https://fosstodon.org/.well-known/webfinger?resource={acct_fosstodon}", "https://fosstodon.org/@{name}"),
    Source("pixelfed", "Pixelfed.social", "Creative", "https://pixelfed.social/api/v1/accounts/lookup?acct={name}", "https://pixelfed.social/{name}"),
)
QUICK_KEYS = frozenset(("github", "codeberg", "dev", "scratch", "hackernews", "bluesky"))

# Generated links are reference ideas, not checked evidence. These are never
# saved to the main results table nor included in result totals.
REVIEW_LINKS = (
    ("YouTube", "https://www.youtube.com/@{name}"),
    ("Twitch", "https://www.twitch.tv/{name}"),
    ("TikTok", "https://www.tiktok.com/@{name}"),
    ("Instagram", "https://www.instagram.com/{name}/"),
    ("X", "https://x.com/{name}"),
    ("Pinterest", "https://www.pinterest.com/{name}/"),
    ("Pastebin", "https://pastebin.com/u/{name}"),
    ("SoundCloud", "https://soundcloud.com/{name}"),
    ("Itch.io", "https://{name}.itch.io/"),
    ("Medium", "https://medium.com/@{name}"),
    ("Bandcamp", "https://bandcamp.com/{name}"),
    ("Flickr", "https://www.flickr.com/people/{name}/"),
    ("GitHub Gists", "https://gist.github.com/{name}"),
    ("Hackaday", "https://hackaday.io/{name}"),
    ("HackerOne", "https://hackerone.com/{name}"),
    ("Behance", "https://www.behance.net/{name}"),
    ("Dribbble", "https://dribbble.com/{name}"),
    ("Kofi", "https://ko-fi.com/{name}"),
    ("WordPress.org", "https://profiles.wordpress.org/{name}/"),
    ("OpenStreetMap", "https://www.openstreetmap.org/user/{name}"),
    ("Letterboxd", "https://letterboxd.com/{name}/"),
    ("Substack", "https://{name}.substack.com/"),
    ("Steam Community", "https://steamcommunity.com/id/{name}/"),
    ("Linktree", "https://linktr.ee/{name}"),
    ("Replit", "https://replit.com/@{name}"),
)

@dataclass
class Signal:
    provider: str
    category: str
    state: str
    username: str
    profile_url: str
    reason: str
    http_status: int | None
    latency_ms: int
    evidence_type: str = "API_IDENTIFIER"

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

OPENER = build_opener(NoRedirect())

def validate_name(name: str) -> str:
    name = name.strip()
    if name.startswith("@"):
        name = name[1:]
    if not NAME_PATTERN.fullmatch(name):
        raise ValueError("Enter one public username (1–39 letters, digits, dot, dash or underscore).")
    return name

def substitutions(name: str) -> dict:
    actor = name if "." in name else name + ".bsky.social"
    return {"name": quote(name, safe=""), "actor": quote(actor, safe="."),
            "acct": quote(f"acct:{name}@mastodon.social", safe=""),
            "acct_online": quote(f"acct:{name}@mastodon.online", safe=""),
            "acct_fosstodon": quote(f"acct:{name}@fosstodon.org", safe="")}

def make_url(source: Source, name: str) -> str:
    return source.endpoint.format(**substitutions(name))

def make_profile(source: Source, name: str) -> str:
    return source.profile.format(**substitutions(name))

def equals_field(data, field, expected) -> bool:
    return (isinstance(data, dict) and isinstance(data.get(field), str)
            and data[field].casefold() == expected.casefold())

def classify(source_key: str, name: str, status: int, data) -> tuple[str, str]:
    if status in (401, 403, 429):
        return "BLOCKED", f"HTTP {status}: authentication, restriction or rate-limit; no absence claim"
    if 300 <= status < 400:
        return "UNCERTAIN", f"HTTP {status}: redirect not verified"
    if status >= 500:
        return "ERROR", f"HTTP {status}: provider error"
    if status == 400 and source_key == "bluesky":
        return "UNCERTAIN", "Bluesky could not resolve this actor; not global absence"
    if status == 400 and source_key == "pixelfed":
        return "UNCERTAIN", "Pixelfed HTTP 400: missing or suspended accounts share this response; no absence claim"
    if status == 204 and source_key == "minecraft":
        return "NOT_FOUND", "Minecraft lookup returned no public profile for this exact name"
    if status == 404:
        return "NOT_FOUND", "Provider returned HTTP 404 for this exact lookup only"
    if status in (598, 599):
        return "UNCERTAIN", "Provider response invalid or too large to validate"
    if status != 200:
        return "UNCERTAIN", f"HTTP {status}: unexpected response"
    try:
        if source_key == "github":
            valid = equals_field(data, "login", name) and data.get("type") in ("User", "Organization")
        elif source_key in ("codeberg", "codewars", "dev", "scratch", "huggingface", "chesscom", "lichess", "modrinth", "gitea"):
            field = {"codeberg":"login", "codewars":"username", "dev":"username",
                     "scratch":"username", "huggingface":"name", "chesscom":"username",
                     "lichess":"id", "modrinth":"username", "gitea":"login"}[source_key]
            valid = equals_field(data, field, name)
            if valid and source_key == "gitea" and data.get("type") not in ("User", "Organization", "Bot", None):
                valid = False
        elif source_key == "gitlab":
            if isinstance(data, list) and not data:
                return "NOT_FOUND", "Provider returned an empty exact-username query"
            valid = isinstance(data, list) and any(equals_field(item, "username", name) for item in data)
        elif source_key == "hackernews":
            if data is None:
                return "NOT_FOUND", "No publicly active username returned by this API"
            valid = equals_field(data, "id", name)
        elif source_key == "bluesky":
            expected = name if "." in name else name + ".bsky.social"
            valid = equals_field(data, "handle", expected) and str(data.get("did", "")).startswith("did:")
        elif source_key == "mastodon":
            expected = f"acct:{name}@mastodon.social"
            valid = equals_field(data, "subject", expected) and any(
                isinstance(link, dict) and link.get("rel") == "self"
                for link in data.get("links", [])
            )
        elif source_key == "minecraft":
            valid = (equals_field(data, "name", name)
                     and isinstance(data.get("id"), str)
                     and re.fullmatch(r"[0-9a-fA-F]{32}", data["id"]) is not None)
        elif source_key in ("mastodononline", "fosstodon"):
            domain = "mastodon.online" if source_key == "mastodononline" else "fosstodon.org"
            valid = (equals_field(data, "subject", f"acct:{name}@{domain}")
                     and isinstance(data.get("links"), list)
                     and any(isinstance(link, dict) and link.get("rel") == "self"
                         and isinstance(link.get("href"), str)
                         and urlsplit(link["href"]).scheme == "https"
                         and urlsplit(link["href"]).hostname == domain
                         for link in data["links"]))
        elif source_key == "pixelfed":
            # Only local exact accounts, never remote accounts with the same local part.
            valid = (equals_field(data, "username", name)
                     and isinstance(data.get("id"), (str, int))
                     and bool(str(data["id"]).strip())
                     and isinstance(data.get("acct"), str)
                     and data["acct"].casefold() in (name.casefold(), f"{name}@pixelfed.social".casefold()))
        elif source_key == "reddit":
            valid = isinstance(data, dict) and equals_field(data.get("data"), "name", name)
        elif source_key == "wikipedia":
            users = data.get("query", {}).get("users", []) if isinstance(data, dict) else []
            if any(equals_field(u, "name", name) and "missing" in u for u in users if isinstance(u, dict)):
                return "NOT_FOUND", "Provider explicitly flagged username missing"
            valid = any(equals_field(u, "name", name) and "userid" in u
                        for u in users if isinstance(u, dict))
        else:
            return "UNCERTAIN", "No validation rule available"
    except (KeyError, TypeError, ValueError, AttributeError):
        valid = False
    return (("EXACT", "Returned account identifier matches the requested handle") if valid
            else ("UNCERTAIN", "Provider responded but exact username evidence was missing"))

def safe_same_host_redirect(current: str, destination: str) -> str | None:
    """Allow one normal, same-host HTTPS canonicalization; no host switching."""
    joined = urljoin(current, destination)
    src, dst = urlsplit(current), urlsplit(joined)
    if (src.scheme == dst.scheme == "https" and dst.hostname == src.hostname
            and dst.port in (None, 443) and not dst.username and not dst.password
            and dst.path.rstrip("/") == src.path.rstrip("/") and dst.query == src.query):
        return joined
    return None

def fetch_json(url: str, transport=None):
    """Small fixed-response GET. transport(URL) injection supported for offline tests."""
    if transport is not None:
        return transport(url)
    current = url
    for redirect_count in range(2):
        request = Request(current, headers={
            "User-Agent":"VOIDSTING-PublicResearch/1.1 (one bounded public GET per source; no login)",
            "Accept":"application/json",
        })
        try:
            response = OPENER.open(request, timeout=TIMEOUT_SECONDS)
        except HTTPError as exc:
            if 300 <= exc.code < 400 and redirect_count == 0:
                location = exc.headers.get("Location", "")
                next_url = safe_same_host_redirect(current, location) if location else None
                if next_url and next_url != current:
                    current = next_url
                    continue
            return exc.code, None
        with response:
            status = response.status
            if status == 204:
                return status, None
            raw = response.read(API_MAX_BYTES + 1)
            if len(raw) > API_MAX_BYTES:
                return 599, None
            try:
                return status, json.loads(raw.decode("utf-8"))
            except (UnicodeError, ValueError):
                return 598, None
    return 599, None

def check(source: Source, name: str, transport=None) -> Signal:
    started = time.monotonic()
    # Minecraft Java usernames have an independent 3-16-character rule.
    # Do not turn an invalid-platform username into a misleading NOT_FOUND.
    if source.key == "minecraft" and re.fullmatch(r"[A-Za-z0-9_]{3,16}", name) is None:
        return Signal(source.name, source.category, "UNCERTAIN", name, "",
                      "Unsupported Minecraft username format; no request made", None, 0)
    # Pixelfed's published local lookup requires at least three characters.
    if source.key == "pixelfed" and len(name) < 3:
        return Signal(source.name, source.category, "UNCERTAIN", name, "",
                      "Unsupported Pixelfed username length; no request made", None, 0)
    try:
        status, data = fetch_json(make_url(source, name), transport)
        state, reason = classify(source.key, name, status, data)
    except (URLError, TimeoutError, OSError) as err:
        status, state, reason = None, "ERROR", f"Network unavailable ({type(err).__name__})"
    return Signal(source.name, source.category, state, name,
                  make_profile(source, name), reason, status,
                  int((time.monotonic() - started) * 1000))

def bounded_discovery(name: str, transport=None, limit=10, delay=SOURCE_PAUSE_SECONDS, on_start=None):
    """Four explicitly opt-in, bounded public directories; only handle candidates.

    These never claim identity verification and never retrieve private profiles.
    """
    results=[]
    targets=(
        ("GitHub Directory", "Developer", "https://api.github.com/search/users?q=" + quote(name,safe="") + "&per_page=10", "github"),
        ("Bluesky Directory", "Social", "https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors?q=" + quote(name,safe="") + "&limit=10", "bluesky"),
        ("GitLab Directory", "Developer", "https://gitlab.com/api/v4/users?search=" + quote(name,safe="") + "&per_page=10", "gitlab"),
        ("Gitea Directory", "Developer", "https://gitea.com/api/v1/users/search?q=" + quote(name,safe="") + "&limit=10", "gitea"),
    )
    seen=set()
    cleaned=lambda x: re.sub(r"[^a-z0-9]", "", x.casefold())
    for i,(provider,category,url,key) in enumerate(targets):
        if on_start:on_start(provider,i,len(targets))
        started=time.monotonic()
        try:
            status,data=fetch_json(url,transport)
            if status!=200:
                results.append(Signal(provider,category,
                    "BLOCKED" if status in (401,403,429) else "UNCERTAIN",name,"",
                    f"Directory HTTP {status}; no match claim",status,
                    int((time.monotonic()-started)*1000),"DIRECTORY_HEALTH"))
            else:
                if key=="github":
                    candidates=data.get("items",[]) if isinstance(data,dict) else []
                elif key=="bluesky":
                    candidates=data.get("actors",[]) if isinstance(data,dict) else []
                elif key=="gitlab":
                    candidates=data if isinstance(data,list) else []
                else:
                    candidates=data.get("data",[]) if isinstance(data,dict) else []
                if not isinstance(candidates,list):candidates=[]
                for item in candidates[:min(max(int(limit),1),10)]:
                    if not isinstance(item,dict):continue
                    handle=item.get("handle") if key=="bluesky" else item.get("login") if key in ("github","gitea") else item.get("username")
                    if not isinstance(handle,str) or len(handle)>120:continue
                    candidate_name=handle.split(".",1)[0] if key=="bluesky" else handle
                    if len(cleaned(name))<3 or cleaned(name) not in cleaned(candidate_name):continue
                    profile=("https://bsky.app/profile/"+quote(handle,safe=".") if key=="bluesky" else
                             "https://github.com/"+quote(handle,safe="") if key=="github" else
                             "https://gitlab.com/"+quote(handle,safe="") if key=="gitlab" else
                             "https://gitea.com/"+quote(handle,safe=""))
                    if profile.casefold() in seen:continue
                    seen.add(profile.casefold())
                    reason=("Directory handle equals query; still not API-verified"
                           if cleaned(candidate_name)==cleaned(name) else
                           "Directory returned a related public handle")
                    results.append(Signal(provider,category,"RELATED",handle,profile,reason,
                        200,int((time.monotonic()-started)*1000),"DIRECTORY_CANDIDATE"))
        except (URLError,TimeoutError,OSError) as err:
            results.append(Signal(provider,category,"ERROR",name,"",
                f"Directory error: {type(err).__name__}",None,
                int((time.monotonic()-started)*1000),"DIRECTORY_HEALTH"))
        if delay and i+1<len(targets):time.sleep(delay)
    return results

def perform_scan(username: str, source_keys=None, transport=None, discover=False,
                 delay=SOURCE_PAUSE_SECONDS, on_result=None, on_start=None):
    name=validate_name(username)
    sources=[s for s in SOURCES if source_keys is None or s.key in source_keys]
    results=[]
    for i,source in enumerate(sources):
        if on_start: on_start(source.name, i, len(sources)+(4 if discover else 0))
        signal=check(source,name,transport)
        results.append(signal)
        if on_result:on_result(signal,len(results),len(sources)+(4 if discover else 0))
        if delay and i+1<len(sources):time.sleep(delay)
    if discover:
        # Directory results are separate from exact verification; add candidates,
        # not raw API response bodies. NO identity association is performed.
        for signal in bounded_discovery(name,transport,delay=delay,on_start=on_start):
            if signal.state=="RELATED" and any(r.profile_url.lower()==signal.profile_url.lower() and r.state=="EXACT" for r in results):
                continue
            results.append(signal)
            if on_result:on_result(signal,len(results),len(results))
    return results

def count_states(results):
    return {s:sum(r.state==s for r in results) for s in RESULT_STATES}

def default_vault() -> Path:
    return Path.home()/".local"/"share"/"voidsting"/"voidsting.sqlite3"

def open_vault(path: Path | None=None):
    destination=Path(path) if path else default_vault()
    destination=destination.expanduser()
    destination.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    if not destination.exists():
        # The tool alone writes here; no relationship to BLACKSWARM's files.
        oldmask=os.umask(0o077)
        try:
            conn=sqlite3.connect(destination)
        finally:
            os.umask(oldmask)
    else:conn=sqlite3.connect(destination)
    conn.row_factory=sqlite3.Row
    conn.execute("PRAGMA busy_timeout=3000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            scan_mode TEXT NOT NULL,
            created_at TEXT NOT NULL,
            checked_count INTEGER NOT NULL,
            notes TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            provider TEXT NOT NULL, category TEXT NOT NULL,
            state TEXT NOT NULL, username TEXT NOT NULL,
            profile_url TEXT NOT NULL, reason TEXT NOT NULL,
            http_status INTEGER, latency_ms INTEGER NOT NULL,
            evidence_type TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_signals_session ON signals(session_id);
    """)
    conn.commit()
    return conn

def save_session(conn, username: str, mode: str, results, notes=""):
    now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn:
        cursor=conn.execute("INSERT INTO sessions(username,scan_mode,created_at,checked_count,notes) VALUES (?,?,?,?,?)",
                            (validate_name(username),mode,now,len(results),notes[:300]))
        sid=int(cursor.lastrowid)
        conn.executemany("""INSERT INTO signals(session_id,provider,category,state,username,profile_url,reason,http_status,latency_ms,evidence_type)
                         VALUES (?,?,?,?,?,?,?,?,?,?)""",
                         ((sid,r.provider,r.category,r.state,r.username,r.profile_url,r.reason,r.http_status,r.latency_ms,r.evidence_type)
                          for r in results))
    return sid

def sessions(conn,limit=40):
    return [dict(row) for row in conn.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (min(max(int(limit),1),100),))]

def session_record(conn,sid):
    row=conn.execute("SELECT * FROM sessions WHERE id=?",(int(sid),)).fetchone()
    if not row:return None
    values=[dict(r) for r in conn.execute("SELECT * FROM signals WHERE session_id=? ORDER BY id",(int(sid),))]
    return {**dict(row),"signals":values,"counts":count_states([Signal(**{k:v for k,v in sig.items() if k not in ("id","session_id")}) for sig in values])}

def compare_sessions(conn,first,second):
    a,b=session_record(conn,first),session_record(conn,second)
    if a is None or b is None:raise ValueError("Session ID not found")
    def matching(rec):
        return {(r["provider"],r["profile_url"].casefold()):r for r in rec["signals"]
                if r["state"] in ("EXACT","RELATED")}
    x,y=matching(a),matching(b)
    added=[y[k] for k in sorted(y.keys()-x.keys())]
    removed=[x[k] for k in sorted(x.keys()-y.keys())]
    return {"first":a["id"],"second":b["id"],"same_username":a["username"].casefold()==b["username"].casefold(),
            "first_username":a["username"],"second_username":b["username"],
            "added":added,"not_seen_in_second":removed,
            "disclaimer":"A missing signal on a later scan does not prove account deletion."}

def manual_links(name):
    n=quote(validate_name(name),safe="")
    return [{"provider":provider,"state":"NOT_CHECKED","url":url.format(name=n)}
            for provider,url in REVIEW_LINKS]

def export_session(conn, sid: int, path: Path):
    record=session_record(conn,sid)
    if not record:raise ValueError("Session ID not found")
    target=Path(path).expanduser()
    if target.suffix.lower() not in (".json",".csv",".html"):
        raise ValueError("Choose an export ending in .json, .csv or .html")
    if target.exists():raise FileExistsError("File already exists; exports never overwrite")
    if target.suffix.lower()==".json":
        content=json.dumps(record,ensure_ascii=False,indent=2)+"\n"
    elif target.suffix.lower()==".csv":
        out=io.StringIO()
        fields=("provider","category","state","username","profile_url","reason","http_status","latency_ms","evidence_type")
        writer=csv.DictWriter(out,fieldnames=fields,extrasaction="ignore")
        writer.writeheader();writer.writerows(record["signals"])
        content=out.getvalue()
    else:
        rows=[]
        for s in record["signals"]:
            link=(f'<a href="{html.escape(s["profile_url"],quote=True)}" rel="noopener noreferrer">View profile</a>'
                  if s["profile_url"].startswith("https://") and s["state"] in ("EXACT","RELATED") else "")
            rows.append("<tr>"+"".join(f"<td>{html.escape(str(s[f]))}</td>" for f in ("provider","state","reason"))+f"<td>{link}</td></tr>")
        content=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>VOIDSTING Session {sid}</title>
<style>body{{background:#090b14;color:#e8e9fb;font:16px system-ui;margin:40px}}h1{{color:#ac8cff}}table{{border-collapse:collapse;width:100%}}td,th{{padding:12px;border-bottom:1px solid #45415c;text-align:left}}a{{color:#64f4d5}}</style>
<h1>VOIDSTING // Session {sid}</h1><p>Username: {html.escape(record["username"])}</p><p>Public handle matches do not establish shared identity.</p>
<table><thead><tr><th>Provider</th><th>Result</th><th>Evidence</th><th>Link</th></tr></thead><tbody>{''.join(rows)}</tbody></table></html>'''
    with target.open("x",encoding="utf-8",newline="") as f:f.write(content)
    return target
