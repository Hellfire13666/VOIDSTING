"""VOIDSTING local read-only Cockpit. Binds only to 127.0.0.1."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from voidsting_core import sessions,session_record,manual_links

ASSETS = Path(__file__).with_name("assets")
_SERVER=None
_SERVER_THREAD=None

def handler_for(conn):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,format,*args):
            return  # avoid printing usernames/addresses in automatic request logs
        def _send(self,status,data,mime):
            self.send_response(status)
            self.send_header("Content-Type",mime)
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Referrer-Policy","no-referrer")
            self.send_header("X-Frame-Options","DENY")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def do_POST(self):
            self.send_error(405)
        def do_GET(self):
            route=urlsplit(self.path).path
            if route=="/":
                self._send(200,(ASSETS/"cockpit.html").read_bytes(),"text/html; charset=utf-8")
            elif route=="/assets/app.js":
                self._send(200,(ASSETS/"app.js").read_bytes(),"application/javascript; charset=utf-8")
            elif route=="/assets/style.css":
                self._send(200,(ASSETS/"style.css").read_bytes(),"text/css; charset=utf-8")
            elif route=="/api/sessions":
                self._send(200,json.dumps(sessions(conn,40),ensure_ascii=False).encode(),"application/json; charset=utf-8")
            elif route.startswith("/api/session/") and route[len("/api/session/"):].isdecimal():
                sid=int(route.split("/")[-1]);item=session_record(conn,sid)
                if item is None:self._send(404,b'{"error":"Session not found"}',"application/json")
                else:self._send(200,json.dumps(item,ensure_ascii=False).encode(),"application/json; charset=utf-8")
            elif route.startswith("/api/references/") and route[len("/api/references/"):].isdecimal():
                sid=int(route.split("/")[-1]);item=session_record(conn,sid)
                if item is None:
                    self._send(404,b'{"error":"Session not found"}',"application/json")
                else:
                    # Generated manual references are NEVER scanned, stored as results,
                    # counted as hits or promoted to evidence.
                    refs=manual_links(item["username"])
                    self._send(200,json.dumps({"username":item["username"],"status":"NOT_CHECKED","references":refs},ensure_ascii=False).encode(),"application/json; charset=utf-8")
            elif route=="/api/health":
                self._send(200,b'{"status":"ok","mode":"read-only"}',"application/json")
            else:self._send(404,b"Not Found", "text/plain; charset=utf-8")
    return Handler

def create_server(conn):
    # Separate connection for the HTTP server thread; read-only operations
    # and never an arbitrary supplied endpoint or public bind address.
    return ThreadingHTTPServer(("127.0.0.1",0), handler_for(conn))

def start_server(conn):
    global _SERVER,_SERVER_THREAD
    if _SERVER is not None:return f"http://127.0.0.1:{_SERVER.server_port}/"
    # SQLite connections are not shared across threads by default. Make a
    # read-only separate connection in the server rather than using CLI conn.
    from voidsting_core import open_vault
    row=conn.execute("PRAGMA database_list").fetchone()
    db_path=row[2]
    if db_path==":memory:":raise OSError("Dashboard requires a file-backed vault")
    # sqlite URI mode=ro means GET requests cannot mutate the vault.
    import sqlite3
    from urllib.parse import quote
    ro=sqlite3.connect("file:"+quote(db_path,safe="/")+"?mode=ro",uri=True,check_same_thread=False)
    ro.row_factory=sqlite3.Row
    server=create_server(ro)
    _SERVER=server
    _SERVER_THREAD=threading.Thread(target=server.serve_forever,daemon=True,name="voidsting-local-cockpit")
    _SERVER_THREAD.start()
    return f"http://127.0.0.1:{server.server_port}/"

def serve_forever(conn):
    url=start_server(conn)
    print("  ☣ VOIDSTING // READ-ONLY COCKPIT")
    print("  LOCAL URL "+url)
    print("  Open this address yourself. Browser will NOT auto-open.")
    print("  Press Ctrl+C to close the local dashboard.")
    global _SERVER,_SERVER_THREAD
    try:
        _SERVER_THREAD.join()
    except KeyboardInterrupt:
        print("\n  VOIDSTING cockpit shutting down.")
    finally:
        if _SERVER is not None:
            _SERVER.shutdown();_SERVER.server_close();_SERVER=None
