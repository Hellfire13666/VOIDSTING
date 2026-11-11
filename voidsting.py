#!/usr/bin/env python3
"""VOIDSTING // standalone GlitchByte public username research console."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from voidsting_core import (
    VERSION,SOURCES,QUICK_KEYS, RESULT_STATES,Signal, open_vault,perform_scan,
    save_session, session_record,sessions,compare_sessions,manual_links,export_session,
    count_states,validate_name,default_vault,
)

COLORS=("\033[92m","\033[96m","\033[95m","\033[93m","\033[94m","\033[91m")
OFF="\033[0m"

class Console:
    def __init__(self,mode="auto"):
        self.color=mode=="always" or (mode=="auto" and sys.stdout.isatty() and os.getenv("NO_COLOR") is None)
    def paint(self,s,i=0):return COLORS[i%len(COLORS)]+s+OFF if self.color else s
    def say(self,s="",i=None):print(self.paint(s,i) if i is not None else s,flush=True)
    def header(self):
        self.say(self.paint("\n╔══════════════════════════════════════════════════════╗",0))
        self.say(self.paint("║  ☣  VOIDSTING  // GLITCHBYTE PHANTOM LABS            ║",2))
        self.say(self.paint("║  PUBLIC PROFILE SIGNALS · ORIGINAL RESEARCH ENGINE   ║",1))
        self.say(self.paint("╚══════════════════════════════════════════════════════╝",0))
        self.say("  ▰▰▰▰▰▰▰▰▰▰▰▰  🌈 RAINBOW SIGNALS")
        self.say("  Terminal-first  |  local private vault  |  browser never auto-opens")
    def signal(self,r:Signal,i=0,total=0):
        glyph={"EXACT":"✓", "RELATED":"◈", "NOT_FOUND":"·", "UNCERTAIN":"?", "BLOCKED":"✕", "ERROR":"!"}[r.state]
        # A wide result is a review-needed candidate. The external library did
        # not provide per-site duration, so never misreport this as 0 ms.
        suffix='review' if r.evidence_type=='EXTERNAL_PROFILE_CANDIDATE' else f'{r.latency_ms:>5} ms'
        msg=f"  {glyph} {r.provider:<19} {r.state:<11} {suffix}"
        self.say(msg,i)
        if r.state in ("EXACT","RELATED"):
            self.say("     ↳ "+r.profile_url,i)
        if r.state in ("UNCERTAIN","BLOCKED","ERROR"):
            self.say("     └ "+r.reason)
    def summary(self,results,sid=None):
        c=count_states(results)
        self.say(self.paint("\n  ══════════ SIGNAL VERDICT ══════════",1))
        self.say(f"  EXACT {c['EXACT']}  ·  RELATED {c['RELATED']}  ·  NOT FOUND {c['NOT_FOUND']}")
        self.say(f"  UNCERTAIN {c['UNCERTAIN']}  ·  BLOCKED {c['BLOCKED']}  ·  ERROR {c['ERROR']}")
        if sid is not None:self.say(self.paint(f"  ◉ PRIVATE VAULT SESSION #{sid} SAVED",0))
        self.say("  Different accounts can share a handle. A match never proves common ownership.")

def scan_and_save(console,conn,username,mode="quick",discover=False,offline=False):
    name=validate_name(username)
    keys=QUICK_KEYS if mode=="quick" else None
    num=len(QUICK_KEYS) if mode=="quick" else len(SOURCES)
    console.say(console.paint(f"\n  ☣ VOIDSTING // {mode.upper()} PROFILE SCAN",2))
    console.say(f"  HANDLE {name}  |  {num} selected public APIs" + (" + 4 opt-in directories" if discover else ""))
    console.say("  Profiles require matching API identifiers; generated links are never counted.")
    if offline:
        results=demo_signals(name)
        console.say("  DEMO ONLY: fictional responses, no internet requests made.")
        for i,r in enumerate(results):console.signal(r,i)
        session_mode="OFFLINE_DEMO"
    else:
        results=perform_scan(name,source_keys=keys,discover=discover,
                             on_start=lambda label,i,n:console.say("  ↗ CHECKING "+label.upper()+" PUBLIC SIGNAL…",i),
                             on_result=lambda r,i,n:console.signal(r,i))
        session_mode=mode.upper()+("_WITH_DIRECTORY" if discover else "")
        if discover:
            # The existing opt-in [3] runs the optional expansion only if enabled.
            from voidsting_wide import run_wide
            wide,checked=run_wide(name,console.say)
            prior={r.profile_url.casefold() for r in results if r.state in ('EXACT','RELATED')}
            for r in wide:
                if r.profile_url.casefold() in prior:continue
                prior.add(r.profile_url.casefold())
                results.append(r)
                console.signal(r,len(results))
            if checked:
                session_mode='FULL_WITH_WIDE_PUBLIC_SWEEP'
    if not offline and discover:
        wide_count=sum(1 for r in results if r.evidence_type=='EXTERNAL_PROFILE_CANDIDATE')
        if wide_count:
            console.say(f'  ◈ REVIEW QUEUE: {wide_count} wide candidates, included under RELATED until independently confirmed.')
    sid=save_session(conn,name,session_mode,results,notes="Fictional offline test" if offline else "Public existence checks; wide findings are unconfirmed candidates only")
    console.summary(results,sid)
    return sid

def demo_signals(name):
    return [
        Signal("Demo Code Forge","Developer","EXACT",name,"https://example.org/demo/code", "Fictional API returned a matching identifier",200,42),
        Signal("Demo Social","Social","RELATED",name+"-studio","https://example.org/demo/social", "Fictional related public handle, not identity",200,53,"DIRECTORY_CANDIDATE"),
        Signal("Demo Community","Community","NOT_FOUND",name,"https://example.org/demo/community", "Fictional provider-specific missing response",404,39),
        Signal("Demo Gallery","Creative","BLOCKED",name,"", "Fictional HTTP 429",429,15),
        Signal("Demo Archive","Knowledge","UNCERTAIN",name,"", "Fictional unvalidated response",307,18),
    ]

def source_list(c):
    c.say(c.paint("\n  ☣ VERIFIED API DIRECTORY // FIXED SOURCES",2))
    for i,s in enumerate(SOURCES):c.say(f"  {i+1:>2}  {s.name:<19} {s.category:<12}"+(" QUICK" if s.key in QUICK_KEYS else ""),i)
    c.say("  API status is not global availability. No social-platform login required.")

def prompt(label):
    try:return input(label).strip()
    except (EOFError,KeyboardInterrupt):print();return ""

def show_history(conn,c):
    rows=sessions(conn,24)
    if not rows:c.say("  No saved sessions yet. Try [9] OFFLINE DEMO.");return
    c.say(c.paint("\n  ═════════ VOIDSTING // PRIVATE SESSIONS ═════════",1))
    for row in rows:
        c.say(f"  #{row['id']:<4}  {row['username']:<22} {row['scan_mode']:<22} {row['created_at']}")

def review_session(conn,c,sid):
    record=session_record(conn,sid)
    if not record:c.say("  Session not found.");return
    c.say(c.paint(f"\n  ═════ SESSION #{sid} // {record['username']} ═════",1))
    c.say(f"  {record['scan_mode']}  |  {record['created_at']}  |  {record['checked_count']} stored entries")
    for i,r in enumerate(record['signals']):
        c.say(f"  {i+1:>2}. [{r['state']:<9}] {r['provider']:<20} {r['reason']}",i)
        if r['profile_url'] and r['state'] in ("EXACT","RELATED"):
            c.say("       ↳ "+r['profile_url'])
    c.say("  Handle reuse is not identity evidence. NOT_FOUND applies to one API only.")

def manual_menu(c):
    name=prompt("  Public username: ")
    if not name:return
    try:items=manual_links(name)
    except ValueError as exc:c.say(str(exc));return
    c.say("  OPTIONAL REFERENCE LINKS // NOT CHECKED · NOT RESULTS")
    for item in items:c.say(f"  {item['provider']:<19} {item['url']}")

def run_menu(console,conn):
    console.header()
    while True:
        console.say(console.paint("\n  ════════════ VOIDSTING // COMMAND DECK ════════════",2))
        console.say("  [1] QUICK VERIFY // 6 public APIs")
        console.say("  [2] FULL VERIFY // 20 public API checks")
        console.say("  [3] PUBLIC DIRECTORY + WIDE // optional 120-site sweep")
        console.say("  [4] SAVED SESSION HISTORY")
        console.say("  [5] REVIEW SAVED SESSION + EVIDENCE")
        console.say("  [6] COMPARE TWO SESSIONS // READ-ONLY")
        console.say("  [7] EXPORT SESSION // JSON / CSV / HTML")
        console.say("  [8] LIST SOURCES + MANUAL REFERENCE LINKS")
        console.say("  [9] OFFLINE DEMO // fictional results")
        console.say(" [10] OPTIONAL COCKPIT // local URL; no auto-browser")
        console.say("  [0] QUIT")
        selection=prompt("  VOIDSTING ❯ ")
        if selection=="0" or not selection:return
        if selection in ("1","2","3","9"):
            name=prompt("  Public username (one only): ")
            if name:
                try:scan_and_save(console,conn,name,"full" if selection in ("2","3") else "quick",discover=selection=="3",offline=selection=="9")
                except (ValueError,OSError) as exc:console.say("  ERROR: "+str(exc))
        elif selection=="4":show_history(conn,console)
        elif selection=="5":
            sid=prompt("  Session #ID: ")
            if sid.isdecimal():review_session(conn,console,int(sid))
        elif selection=="6":
            pair=prompt("  Two session IDs (example: 1 2): ").split()
            if len(pair)==2 and all(x.isdecimal() for x in pair):
                try:
                    data=compare_sessions(conn,*map(int,pair))
                    console.say(f"  New signals in #{data['second']}: {len(data['added'])}")
                    for r in data['added']:console.say("    + "+r['provider']+" "+r['profile_url'])
                    console.say(f"  Earlier signals not seen: {len(data['not_seen_in_second'])}")
                    for r in data['not_seen_in_second']:console.say("    - "+r['provider']+" "+r['profile_url'])
                    if not data['same_username']:console.say("  CAUTION: These sessions have different username queries.")
                    console.say("  "+data['disclaimer'])
                except ValueError as exc:console.say("  ERROR: "+str(exc))
        elif selection=="7":
            sid=prompt("  Session #ID: ")
            if not sid.isdecimal():continue
            dest=prompt("  New filename ending .json, .csv or .html: ")
            if dest:
                try:console.say("  ✓ WROTE "+str(export_session(conn,int(sid),Path(dest))))
                except (ValueError,FileExistsError,OSError) as exc:console.say("  ERROR: "+str(exc))
        elif selection=="8":
            source_list(console)
            if prompt("  Show NOT-CHECKED manual reference links? [y/N]: ").lower()=="y":manual_menu(console)
        elif selection=="10":
            from voidsting_dashboard import start_server
            try:
                host=start_server(conn)
                console.say(console.paint(f"  ◈ COCKPIT ONLINE: {host}",0))
                console.say("  Open manually in your browser. The dashboard is read-only.")
            except OSError as exc:console.say("  COCKPIT UNAVAILABLE: "+str(exc))
        else:console.say("  Choose a number shown above.")

def main(argv=None):
    parser=argparse.ArgumentParser(description="VOIDSTING independent public profile research, standard library only")
    parser.add_argument("username",nargs="?",help="one username; omit for interactive menu")
    parser.add_argument("--full",action="store_true",help="all 20 fixed public API checks (default 6)")
    parser.add_argument("--discover",action="store_true",help="add four opt-in bounded public username directory searches")
    parser.add_argument("--offline-demo",action="store_true",help="use fictional offline evidence, no network")
    parser.add_argument("--vault",metavar="PATH",help="use a separate VOIDSTING SQLite vault path")
    parser.add_argument("--save",metavar="REPORT.json|REPORT.csv|REPORT.html",help="export new file after scan, no overwrite")
    parser.add_argument("--dashboard",action="store_true",help="serve local read-only Cockpit; no browser automatically opens")
    parser.add_argument("--list-sources",action="store_true")
    parser.add_argument("--color",choices=("auto","always","never"),default="auto")
    args=parser.parse_args(argv)
    c=Console(args.color)
    if args.list_sources:source_list(c);return 0
    conn=open_vault(Path(args.vault) if args.vault else None)
    try:
        if args.dashboard:
            from voidsting_dashboard import serve_forever
            serve_forever(conn);return 0
        if args.username:
            try:
                sid=scan_and_save(c,conn,args.username,"full" if args.full else "quick",args.discover,args.offline_demo)
                if args.save:c.say("  EXPORTED: "+str(export_session(conn,sid,Path(args.save))))
            except (ValueError,FileExistsError,OSError) as err:
                print("  ERROR: "+str(err),file=sys.stderr);return 2
        else:run_menu(c,conn)
    finally:conn.close()
    return 0

if __name__=="__main__":raise SystemExit(main())
