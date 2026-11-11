"""Optional 120-site public username discovery adapter for VOIDSTING.

Third-party Maigret findings are candidates, not VOIDSTING API exact verification.
No automatic pip install, no browser, no use of BLACKSWARM storage.
"""
import json
import time
import subprocess
from pathlib import Path
from urllib.parse import urlsplit,unquote
from voidsting_core import Signal,validate_name

HERE=Path(__file__).resolve().parent
VENV_PY=HERE/'.wide-venv'/'bin'/'python'
RUNNER=HERE/'voidsting_maigret_runner.py'

def is_installed():
    return VENV_PY.is_file()

# These URLs are searches, URL shorteners or third-party people directories,
# not positive evidence of a public account at the requested handle.
NON_PROFILE_HOSTS = frozenset({
    'bit.ly', 'tinyurl.com', 'is.gd', 'cutt.ly', 't.co',
    'twitchtracker.com', 'www.twitchtracker.com',
})
GENERIC_PATH_SEGMENTS = frozenset({'search', 'filter', 'results', 'lookup'})

def is_account_shaped_url(name, url):
    """Conservatively admit direct username-shaped URLs, never search pages.

    This is a shape check ONLY. It cannot independently verify an account.
    """
    if not isinstance(url,str) or len(url)>2048:
        return False
    p=urlsplit(url)
    host=(p.hostname or '').casefold()
    if p.scheme!='https' or not host or '.' not in host or p.username or p.password:
        return False
    if host in NON_PROFILE_HOSTS or host.endswith(('.onion','.local','.internal','.i2p')):
        return False
    if host.startswith(('127.','10.','169.254.','192.168.')):
        return False
    parts=[unquote(x).casefold() for x in p.path.split('/') if x]
    if any(x in GENERIC_PATH_SEGMENTS for x in parts):
        return False
    wanted=name.casefold()
    direct=any(x == wanted or x == '@'+wanted for x in parts)
    hosted=(len(host.split('.'))>=3 and host.split('.')[0]==wanted)
    return direct or hosted

def convert_hits(name, data):
    validate_name(name)
    if not isinstance(data,dict):return [],0
    hits=data.get('hits',[])
    if not isinstance(hits,list):return [],0
    checked=data.get('checked',0)
    checked=max(0,min(120,checked)) if isinstance(checked,int) else 0
    results=[];seen=set()
    for item in hits[:120]:
        if not isinstance(item,dict):continue
        provider=item.get('provider');url=item.get('url')
        if not isinstance(provider,str) or not provider or len(provider)>120:continue
        if not is_account_shaped_url(name,url):continue
        status=item.get('http_status')
        if isinstance(status,int) and not 200<=status<300:continue
        if url.casefold() in seen:continue
        seen.add(url.casefold())
        results.append(Signal('Wide · '+provider[:70],'Public site','RELATED',name,url,
            'Direct username-shaped URL; wide-site detector flagged possible presence. REVIEW NEEDED; not independently verified.',
            status if isinstance(status,int) else None,0,
            'EXTERNAL_PROFILE_CANDIDATE'))
    return results,checked

def _run_runner(name, say, timeout, heartbeat=18):
    """Keep the terminal responsive during the optional subprocess scan.

    A hard process cap prevents a stuck third-party checker from blocking
    VOIDSTING forever. We keep its output in pipes until the end so partial
    third-party errors can't masquerade as final results.
    """
    try:
        p=subprocess.Popen([str(VENV_PY),str(RUNNER),name],stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,text=True)
    except OSError as ex:
        say('  ! Wide sweep could not start ('+type(ex).__name__+').')
        return None
    began=time.monotonic()
    with p:
        while True:
            elapsed=time.monotonic()-began
            remaining=timeout-elapsed
            if remaining <= 0:
                p.kill()
                out,err=p.communicate()
                say(f'  ! Wide sweep stopped after {int(timeout)}s safety limit; its incomplete candidates were not saved.')
                return None
            try:
                out,err=p.communicate(timeout=min(heartbeat,remaining))
                break
            except subprocess.TimeoutExpired:
                if time.monotonic()-began >= timeout:
                    p.kill()
                    p.communicate()
                    say(f'  ! Wide sweep stopped after {int(timeout)}s safety limit; its incomplete candidates were not saved.')
                    return None
                say(f'  ◈ WIDE SWEEP RUNNING · {int(time.monotonic()-began)}s · waiting for public-site responses…')
    return p.returncode,out,err


def run_wide(name, say=print, timeout=240):
    validate_name(name)
    if not is_installed():
        say('  ◈ 120-site expansion NOT INSTALLED (optional).')
        say('  Run SETUP-WIDE-SEARCH.sh from this extracted directory to enable it.')
        return [],0
    say('  ◈ Starting optional 120-site public presence sweep (no account linking).')
    say('  ◈ Bounded checks · one retry for transient failures · live progress every ~18s.')
    started=time.monotonic()
    response=_run_runner(name,say,timeout)
    if response is None:return [],0
    returncode,raw,stderr=response
    elapsed=time.monotonic()-started
    if returncode != 0:
        if stderr:
            say('  ! Wide checker: '+stderr.splitlines()[-1][:180])
        say('  ! Wide sweep did not finish; existing API/directory evidence is still saved.')
        return [],0
    try:data=json.loads(raw)
    except ValueError:
        say('  ! Wide sweep returned invalid report; no extra candidates counted.')
        return [],0
    results,checked=convert_hits(name,data)
    raw_count=len(data.get('hits',[])) if isinstance(data,dict) and isinstance(data.get('hits'),list) else 0
    rejected=max(0,raw_count-len(results))
    say(f'  ◈ WIDE SWEEP: {checked} sites selected · {len(results)} profile-shaped candidates · {rejected} generic/invalid hits excluded · {elapsed:.1f}s total')
    coverage=data.get('coverage',{}) if isinstance(data,dict) else {}
    if isinstance(coverage,dict) and coverage:
        def n(key):
            val=coverage.get(key,0)
            return max(0,int(val)) if isinstance(val,int) and not isinstance(val,bool) else 0
        positive=n('found');negative=n('not_found');unknown=n('unknown');unsupported=n('unsupported');missing=n('missing')
        say(f'  ◈ WIDE RESPONSES: {positive} presence indicators · {negative} site-level absences · {unknown} unresolved · {unsupported} invalid-for-site · {missing} missing reports')
        if unknown or missing:
            say('  ! INCOMPLETE WIDE COVERAGE: unresolved checks are NOT proof the username is absent.')
        elif not positive and not negative:
            say('  ! No conclusive public-site answers returned; do not interpret as username absence.')
        if positive>len(results):
            say(f'  ◈ EVIDENCE GUARD: {positive-len(results)} positive indicators were not accepted as direct profile candidates.')
    else:
        say('  ! Wide response coverage unavailable; candidate count alone cannot prove absence.')
    stats=data.get('issues',{}) if isinstance(data,dict) else {}
    if isinstance(stats,dict):
        blocked=stats.get('blocked_http',0)
        server=stats.get('server_http',0)
        if isinstance(blocked,int) and isinstance(server,int) and (blocked or server):
            say(f'  ! WIDE SITE RESPONSES: {blocked} blocked HTTP statuses · {server} server-error HTTP statuses (partial counts)')
    say('  ◈ Native API verdict remains separate; no wide-site identity claims.')
    return results,checked
