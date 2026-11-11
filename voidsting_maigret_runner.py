#!/usr/bin/env python3
"""Private opt-in Maigret library adapter, called in isolated package venv.

Maigret is NOT bundled. Installation, if chosen, is local to this ZIP directory.
No profile-page parsing, recursive pivoting, AI analysis, cookies, or CAPTCHA bypass.
"""
import asyncio
import contextlib
import json
import logging
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

MAX_SITES=120

def public_https(url):
    if not isinstance(url,str) or len(url)>2048:return False
    p=urlsplit(url)
    host=(p.hostname or '').lower()
    if p.scheme!='https' or not host or '.' not in host:return False
    if p.username or p.password:return False
    if host in ('localhost','example.com') or host.endswith(('.local','.internal','.onion','.i2p')):return False
    if host.startswith(('127.','10.','192.168.','169.254.')):return False
    return True

def map_results(result_map):
    items=[]
    for name,entry in result_map.items():
        if not isinstance(entry,dict):continue
        state=entry.get('status')
        is_found=getattr(state,'is_found',None)
        try:found=bool(is_found()) if callable(is_found) else False
        except Exception: found=False
        url=entry.get('url_user','')
        if not found or not public_https(url):continue
        if not isinstance(name,str) or not name or len(name)>120:continue
        status=entry.get('http_status')
        items.append({'provider':name,'url':url,'http_status':status if isinstance(status,int) else None})
    return items

def summarize_issues(result_map):
    """Minimum counts from actual HTTP status data, not inferred failures."""
    blocked=server=0
    for entry in result_map.values():
        if not isinstance(entry,dict):continue
        code=entry.get('http_status')
        if not isinstance(code,int):continue
        if code in (401,403,429):blocked+=1
        elif code>=500:server+=1
    return {'blocked_http':blocked,'server_http':server}

def summarize_coverage(result_map, selected):
    """Separate conclusive per-site answers from inconclusive checks.

    MaigretCheckResult.status is a MaigretCheckStatus enum, whereas its
    is_found() method alone cannot distinguish absence from a timeout.
    Only a CLAIMED/AVAILABLE result counts as a conclusive answer.
    """
    counts={'found':0,'not_found':0,'unknown':0,'unsupported':0,'missing':0,'timeouts':0}
    for entry in result_map.values():
        if not isinstance(entry,dict):
            counts['unknown']+=1
            continue
        result=entry.get('status')
        state=getattr(result,'status',None)
        label=(getattr(state,'name',None) or str(state or '')).strip().upper()
        if label in ('CLAIMED','FOUND'):
            counts['found']+=1
        elif label in ('AVAILABLE','NOT_FOUND'):
            counts['not_found']+=1
        elif label=='ILLEGAL':
            counts['unsupported']+=1
        else:
            counts['unknown']+=1
            details=' '.join(str(x or '') for x in (getattr(result,'error',None),getattr(result,'context',None)))
            if 'timeout' in details.lower() or 'timed out' in details.lower():
                counts['timeouts']+=1
    counts['missing']=max(0,int(selected)-len(result_map))
    return counts

def main():
    if len(sys.argv)!=2 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,38}',sys.argv[1]):
        raise SystemExit('Use exactly one validated public handle')
    username=sys.argv[1]
    try:
        import maigret
        from maigret import search as maigret_search
        from maigret.sites import MaigretDatabase
        database_file=Path(maigret.__file__).parent/'resources'/'data.json'
        db=MaigretDatabase().load_from_path(str(database_file))
        sites=db.ranked_sites_dict(top=MAX_SITES,excluded_tags=['nsfw','dating','tor','i2p'],disabled=False)
        # Maigret may append mirrored sites after its top-N slice; stay bounded.
        sites=dict(list(sites.items())[:MAX_SITES])
        print(f'  ◈ WIDE PUBLIC SITE SWEEP · {len(sites)} sites · no recursive search',file=sys.stderr,flush=True)
        with contextlib.redirect_stdout(sys.stderr):
            found=asyncio.run(maigret_search(username=username,site_dict=sites,
                logger=logging.getLogger('maigret'),timeout=18,max_connections=8,
                is_parsing_enabled=False,no_progressbar=True,retries=1))
        print(json.dumps({'checked':len(sites),'hits':map_results(found),'issues':summarize_issues(found),'coverage':summarize_coverage(found,len(sites))}))
    except Exception as exc:
        print(f'Wide search unavailable: {type(exc).__name__}: {str(exc)[:180]}',file=sys.stderr)
        raise SystemExit(3)
if __name__=='__main__':main()
