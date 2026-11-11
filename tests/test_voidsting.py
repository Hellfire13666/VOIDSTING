import csv
import io
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
from urllib.request import urlopen, Request
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import voidsting_core as c
import voidsting as cli
import voidsting_dashboard as dashboard

class NameTests(unittest.TestCase):
    def test_valid_names(self):
        for value in ('Rosie','@glitchbyte','YourAnonKarma44','x','abc_def-012.34'):
            self.assertEqual(c.validate_name(value).lower().lstrip('@'),value.strip('@').lower())
    def test_bad_names(self):
        for value in ('','@','foo bar','../../x','-bad','bad/name','@bad@domain','?hi','x'*40,'☣'):
            with self.subTest(value=value),self.assertRaises(ValueError):c.validate_name(value)
    def test_query_encoded(self):
        s=next(s for s in c.SOURCES if s.key=='mastodon')
        self.assertIn('acct%3A',c.make_url(s,'Rosie'))
    def test_bluesky_actor_name(self):
        s=next(s for s in c.SOURCES if s.key=='bluesky')
        self.assertIn('actor=rosie.bsky.social',c.make_url(s,'rosie'))
        self.assertIn('actor=rosie.example',c.make_url(s,'rosie.example'))
    def test_all_fixed_https(self):
        self.assertEqual(len(c.SOURCES),20)
        self.assertEqual(len({x.key for x in c.SOURCES}),20)
        for s in c.SOURCES:
            self.assertTrue(s.endpoint.startswith('https://'))
            self.assertTrue(s.profile.startswith('https://'))
    def test_manual_not_checked(self):
        links=c.manual_links('test')
        self.assertEqual(len(links),25)
        self.assertTrue(all(x['state']=='NOT_CHECKED' for x in links))
    def test_redirect_rule(self):
        good='https://huggingface.co/api/users/test'
        self.assertEqual(c.safe_same_host_redirect(good,good+'/'),good+'/')
        for target in ('https://evil.test/api/users/test','http://huggingface.co/api/users/test',
                       'https://huggingface.co/api/private/test','https://foo@huggingface.co/api/users/test',
                       'https://huggingface.co:8443/api/users/test'):
            self.assertIsNone(c.safe_same_host_redirect(good,target))

class SourceClassifierTests(unittest.TestCase):
    def test_exact_cases(self):
        fixtures={
            'github':{'login':'glitchbyte','type':'User'},
            'gitlab':[{'username':'GlitchByte'}],
            'codeberg':{'login':'glitchbyte'},
            'dev':{'username':'glitchbyte'},
            'codewars':{'username':'glitchbyte'},
            'scratch':{'username':'glitchbyte'},
            'huggingface':{'name':'glitchbyte'},
            'hackernews':{'id':'glitchbyte'},
            'bluesky':{'handle':'glitchbyte.bsky.social','did':'did:plc:abc'},
            'mastodon':{'subject':'acct:glitchbyte@mastodon.social','links':[{'rel':'self'}]},
            'reddit':{'data':{'name':'glitchbyte'}},
            'wikipedia':{'query':{'users':[{'name':'glitchbyte','userid':1337}]}},
            'chesscom':{'username':'GlitchByte','player_id':42},
            'lichess':{'id':'glitchbyte','username':'GlitchByte'},
            'modrinth':{'username':'glitchbyte','id':'12345'},
            'gitea':{'login':'glitchbyte','type':'User'},
            'minecraft':{'name':'glitchbyte','id':'0123456789abcdef0123456789abcdef'},
            'mastodononline':{'subject':'acct:glitchbyte@mastodon.online','links':[{'rel':'self','href':'https://mastodon.online/users/glitchbyte'}]},
            'fosstodon':{'subject':'acct:glitchbyte@fosstodon.org','links':[{'rel':'self','href':'https://fosstodon.org/users/glitchbyte'}]},
            'pixelfed':{'username':'glitchbyte','acct':'glitchbyte','id':'12345'},
        }
        self.assertEqual(set(fixtures),{s.key for s in c.SOURCES})
        for key, data in fixtures.items():
            with self.subTest(key=key):self.assertEqual(c.classify(key,'glitchbyte',200,data)[0],'EXACT')
    def test_false_positives_rejected(self):
        data={'login':'someoneelse','type':'User'}
        self.assertEqual(c.classify('github','glitchbyte',200,data)[0],'UNCERTAIN')
        self.assertEqual(c.classify('github','glitchbyte',200,{'login':'glitchbyte','type':'Repo'})[0],'UNCERTAIN')
        self.assertEqual(c.classify('dev','glitchbyte',200,{'username':'notglitchbyte'})[0],'UNCERTAIN')
        self.assertEqual(c.classify('bluesky','glitchbyte',200,{'handle':'glitchbyte.bsky.social'})[0],'UNCERTAIN')
        self.assertEqual(c.classify('mastodon','glitchbyte',200,{'subject':'acct:glitchbyte@mastodon.social'})[0],'UNCERTAIN')
        self.assertEqual(c.classify('reddit','glitchbyte',200,{'data':{'name':'someoneelse'}})[0],'UNCERTAIN')
        for key,field in [('chesscom','username'),('lichess','id'),('modrinth','username'),('gitea','login')]:
            with self.subTest(key=key):
                self.assertEqual(c.classify(key,'glitchbyte',200,{field:'someoneelse'})[0],'UNCERTAIN')
        self.assertEqual(c.classify('gitea','glitchbyte',200,{'login':'glitchbyte','type':'Repository'})[0],'UNCERTAIN')
    def test_blocked_never_missing(self):
        for http in (401,403,429):
            self.assertEqual(c.classify('github','test',http,None)[0],'BLOCKED')
    def test_bluesky_http400_not_missing(self):
        self.assertEqual(c.classify('bluesky','test',400,None)[0],'UNCERTAIN')
    def test_307_not_found_false(self):
        self.assertEqual(c.classify('huggingface','test',307,None)[0],'UNCERTAIN')
    def test_404_only_one_provider(self):
        state,msg=c.classify('github','test',404,None)
        self.assertEqual(state,'NOT_FOUND')
        self.assertIn('Provider',msg)
    def test_special_empty_cases(self):
        self.assertEqual(c.classify('gitlab','test',200,[])[0],'NOT_FOUND')
        self.assertEqual(c.classify('hackernews','test',200,None)[0],'NOT_FOUND')
        self.assertEqual(c.classify('wikipedia','test',200,{'query':{'users':[{'name':'test','missing':True}]}})[0],'NOT_FOUND')
    def test_upstream_unknown(self):
        for code in (503,598,599,418):
            self.assertNotEqual(c.classify('github','test',code,None)[0],'EXACT')

class NetworkTests(unittest.TestCase):
    def test_transport_mock_exact(self):
        s=c.SOURCES[0]
        r=c.check(s,'Rosie',lambda url:(200,{'login':'Rosie','type':'User'}))
        self.assertEqual(r.state,'EXACT')
        self.assertEqual(r.http_status,200)
    def test_exception_error(self):
        r=c.check(c.SOURCES[0],'Rosie',lambda url:(_ for _ in ()).throw(URLError('x')))
        self.assertEqual(r.state,'ERROR')
    def test_quick_has_six(self):
        results=c.perform_scan('test',source_keys=c.QUICK_KEYS,transport=lambda url:(404,None),delay=0)
        self.assertEqual(len(results),6)
    def test_full_has_sixteen(self):
        results=c.perform_scan('test',transport=lambda url:(404,None),delay=0)
        self.assertEqual(len(results),20)
    def test_directory_classification(self):
        def response(url):
            if '/search/users' in url:return (200,{'items':[{'login':'foo'},{'login':'glitchbyte'},{'login':'glitchbyte-dev'},{'login':'abcd'}]})
            return (200,{'actors':[{'handle':'glitchbyte.bsky.social'},{'handle':'other.bsky.social'}]})
        results=c.bounded_discovery('glitchbyte',transport=response,delay=0)
        self.assertEqual(len(results),3)
        self.assertTrue(all(x.state=='RELATED' for x in results))
    def test_directory_no_loose_two_character_match(self):
        def response(url):return (200,{'items':[{'login':'abc'}],'actors':[{'handle':'ab.bsky.social'}]})
        self.assertFalse(any(x.state=='RELATED' for x in c.bounded_discovery('ab',transport=response,delay=0)))
    def test_duplicate_api_directory_excluded(self):
        def response(url):
            if 'api.github.com/users/' in url:return (200,{'login':'glitchbyte','type':'User'})
            if '/search/users' in url:return (200,{'items':[{'login':'glitchbyte'}]})
            if 'searchActors' in url:return (200,{'actors':[]})
            return (404,None)
        records=c.perform_scan('glitchbyte',source_keys={'github'},transport=response,discover=True,delay=0)
        self.assertEqual(sum(x.state=='RELATED' for x in records),0)
        self.assertEqual(sum(x.state=='EXACT' for x in records),1)
    def test_directory_403_is_not_exact(self):
        records=c.bounded_discovery('test',lambda url:(403,None),delay=0)
        self.assertTrue(all(x.state=='BLOCKED' for x in records))

class VaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'voidsting.sqlite3';self.conn=c.open_vault(self.db);self.addCleanup(self.conn.close)
        self.demo=cli.demo_signals('glitchbyte')
    def test_new_local_only(self):
        self.assertTrue(self.db.exists())
        self.assertNotIn('blackswarm',str(self.db).lower())
    def test_save_and_count(self):
        sid=c.save_session(self.conn,'glitchbyte','OFFLINE_DEMO',self.demo)
        rec=c.session_record(self.conn,sid)
        self.assertEqual(rec['counts']['EXACT'],1)
        self.assertEqual(rec['counts']['RELATED'],1)
        self.assertEqual(len(rec['signals']),5)
    def test_session_id_increasing(self):
        a=c.save_session(self.conn,'one','DEMO',self.demo)
        b=c.save_session(self.conn,'two','DEMO',self.demo)
        self.assertGreater(b,a)
        self.assertEqual(c.sessions(self.conn)[0]['id'],b)
    def test_compare(self):
        a=c.save_session(self.conn,'glitchbyte','DEMO',self.demo)
        b=c.save_session(self.conn,'glitchbyte','DEMO',self.demo[:1])
        rec=c.compare_sessions(self.conn,a,b)
        self.assertEqual(len(rec['not_seen_in_second']),1)
        self.assertTrue(rec['same_username'])
    def test_export_json_csv_html(self):
        sid=c.save_session(self.conn,'glitchbyte','DEMO',self.demo)
        for ext in ('.json','.csv','.html'):
            name=Path(self.tmp.name)/('export'+ext)
            c.export_session(self.conn,sid,name)
            self.assertTrue(name.is_file())
            with self.assertRaises(FileExistsError):c.export_session(self.conn,sid,name)
        data=json.loads((Path(self.tmp.name)/'export.json').read_text())
        self.assertEqual(data['username'],'glitchbyte')
        with (Path(self.tmp.name)/'export.csv').open() as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),5)
    def test_no_escape_in_html_export(self):
        item=c.Signal('<b>x</b>','Other','UNCERTAIN','test','', '<script>alert(1)</script>',200,1)
        sid=c.save_session(self.conn,'test','TEST',[item])
        dest=Path(self.tmp.name)/'safe.html';c.export_session(self.conn,sid,dest)
        html=dest.read_text()
        self.assertIn('&lt;script&gt;',html)
        self.assertNotIn('<script>alert(1)</script>',html)
    def test_not_found_session(self):
        self.assertIsNone(c.session_record(self.conn,999))
        with self.assertRaises(ValueError):c.export_session(self.conn,999,Path(self.tmp.name)/'x.json')
    def test_readonly_dashboard(self):
        c.save_session(self.conn,'demo','DEMO',self.demo)
        # Use a readonly SQLite connection as intended for HTTP handlers.
        uri=f'file:{self.db}?mode=ro'
        ro=sqlite3.connect(uri,uri=True,check_same_thread=False)
        ro.row_factory=sqlite3.Row
        server=dashboard.create_server(ro)
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}'
            for route in ('/','/assets/style.css','/assets/app.js','/api/sessions','/api/session/1','/api/health'):
                with self.subTest(route=route),urlopen(url+route,timeout=3) as r:
                    self.assertEqual(r.status,200)
            from urllib.error import HTTPError
            with self.assertRaises(HTTPError) as context:urlopen(Request(url+'/api/sessions',data=b'test',method='POST'),timeout=3)
            self.assertEqual(context.exception.code,405)
            with self.assertRaises(sqlite3.OperationalError):ro.execute('DELETE FROM sessions')
        finally:
            server.shutdown();server.server_close();t.join(timeout=3);ro.close()


class ExpansionIntegrityTests(unittest.TestCase):
    def test_new_sources_have_exact_lookup_paths(self):
        by_key={s.key:s for s in c.SOURCES}
        expected={
            'chesscom':'https://api.chess.com/pub/player/glitchbyte',
            'lichess':'https://lichess.org/api/user/glitchbyte',
            'modrinth':'https://api.modrinth.com/v2/user/glitchbyte',
            'gitea':'https://gitea.com/api/v1/users/glitchbyte',
        }
        for key,url in expected.items():
            with self.subTest(key=key): self.assertEqual(c.make_url(by_key[key],'glitchbyte'),url)
    def test_new_providers_do_not_count_http_200_without_id(self):
        for key in ('chesscom','lichess','modrinth','gitea'):
            with self.subTest(key=key):self.assertNotEqual(c.classify(key,'glitchbyte',200,{'status':'ok'})[0],'EXACT')
    def test_empty_responses_do_not_claim_account(self):
        for key in ('chesscom','lichess','modrinth','gitea'):
            with self.subTest(key=key):self.assertNotEqual(c.classify(key,'glitchbyte',200,{})[0],'EXACT')
    def test_expanded_sources_keep_quick_constant(self):
        self.assertEqual(len(c.SOURCES),20)
        self.assertEqual(len(c.QUICK_KEYS),6)
        self.assertTrue(c.QUICK_KEYS.issubset({s.key for s in c.SOURCES}))
    def test_cockpit_has_working_dom_targets(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        markup=(root/'assets'/'cockpit.html').read_text()
        source=(root/'assets'/'app.js').read_text()
        for target in ('signalMap','sourceMatrix','evidenceFind','resultList','sessions','mapHandle','countExact'):
            self.assertIn('id="'+target+'"',markup)
            self.assertIn(target,source)
        self.assertIn('role',source)

class RainbowVenomTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'voidsting-rainbow.sqlite3'
        self.conn=c.open_vault(self.path);self.addCleanup(self.conn.close)
        self.sid=c.save_session(self.conn,'Rose','OFFLINE_DEMO',cli.demo_signals('Rose'))

    def test_readonly_reference_atlas_api(self):
        ro=sqlite3.connect('file:'+str(self.path)+'?mode=ro',uri=True,check_same_thread=False)
        ro.row_factory=sqlite3.Row
        server=dashboard.create_server(ro)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}'
            with urlopen(url+f'/api/references/{self.sid}',timeout=3) as response:
                result=json.load(response)
                self.assertEqual(response.headers.get('Cache-Control'),'no-store')
                self.assertEqual(response.headers.get('X-Frame-Options'),'DENY')
            self.assertEqual(result['username'],'Rose')
            self.assertEqual(len(result['references']),25)
            self.assertTrue(all(r['state']=='NOT_CHECKED' for r in result['references']))
            self.assertEqual(c.session_record(self.conn,self.sid)['counts']['EXACT'],1)
            self.assertEqual(len(c.session_record(self.conn,self.sid)['signals']),5)
            from urllib.error import HTTPError
            with self.assertRaises(HTTPError) as bad:
                urlopen(url+'/api/references/999999',timeout=3)
            self.assertEqual(bad.exception.code,404)
            with self.assertRaises(sqlite3.OperationalError):ro.execute('DELETE FROM signals')
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3);ro.close()

    def test_cockpit_new_sections_are_read_only_and_labeled(self):
        root=Path(__file__).resolve().parents[1]
        html=(root/'assets'/'cockpit.html').read_text()
        js=(root/'assets'/'app.js').read_text()
        css=(root/'assets'/'style.css').read_text()
        for target in ('timelineTrack','referenceList','referenceCount','pulseStrip'):
            self.assertIn('id="'+target+'"',html)
            self.assertIn(target,js)
        self.assertIn('NOT CHECKED',html)
        self.assertIn('not scans, findings, or evidence',html)
        self.assertIn('prefers-reduced-motion',css)
        self.assertIn('rainbowShift',css)
        self.assertIn('rainbow-beam',css)

    def test_unchanged_terminal_features(self):
        self.assertEqual(len(c.SOURCES),20)
        self.assertEqual(len(c.QUICK_KEYS),6)
        self.assertEqual(len(c.REVIEW_LINKS),25)
        self.assertEqual(c.VERSION,'1.5.1')

    def test_reference_does_not_autoscan(self):
        root=Path(__file__).resolve().parents[1]
        js=(root/'assets'/'app.js').read_text()
        dash=(root/'voidsting_dashboard.py').read_text()
        self.assertIn('renderReferences',js)
        self.assertIn('manual_links(item["username"])',dash)
        self.assertNotIn('perform_scan(',dash)
        self.assertIn("link.target='_blank'",js)

if __name__=='__main__':unittest.main(verbosity=2)

class BalancedCockpitTests(unittest.TestCase):
    def test_panel_placement_keeps_center_filled(self):
        from pathlib import Path
        html = (Path(__file__).resolve().parents[1] / 'assets' / 'cockpit.html').read_text()
        center = html[html.index('class="primary"'):html.index('class="secondary"')]
        right = html[html.index('class="secondary"'):html.index('<footer>')]
        self.assertLess(center.index('id="constellation"'), center.index('id="evidence"'))
        self.assertLess(center.index('id="evidence"'), center.index('id="timeline"'))
        self.assertLess(center.index('id="timeline"'), center.index('id="references"'))
        self.assertLess(right.index('class="sources-panel"') if 'class="sources-panel"' in right else right.index('sources-panel'), right.index('id="source-guard"'))
        self.assertLess(right.index('id="source-guard"'),right.index('id="traces"'))

    def test_no_duplicate_panels_or_event_targets(self):
        from pathlib import Path
        html = (Path(__file__).resolve().parents[1] / 'assets' / 'cockpit.html').read_text()
        for ident in ['signalMap', 'timelineTrack', 'referenceList', 'resultList', 'sourceMatrix', 'sessions']:
            self.assertEqual(html.count('id="'+ident+'"'),1,ident)

    def test_reference_atlas_keeps_not_checked_label(self):
        from pathlib import Path
        html = (Path(__file__).resolve().parents[1] / 'assets' / 'cockpit.html').read_text()
        atlas=html[html.index('id="references"'):html.index('id="referenceCount"')]
        self.assertIn('NOT CHECKED',atlas)
        self.assertNotIn('<form',atlas)

    def test_venom_engine_and_menu_unchanged(self):
        from pathlib import Path
        p = Path(__file__).resolve().parents[1]
        self.assertIn('VOIDSTING', (p/'voidsting.py').read_text())
        self.assertIn('exec python3', (p/'RUN-VOIDSTING.sh').read_text())
        self.assertIn('10', (p/'voidsting.py').read_text())



class VenomControlCoreTests(unittest.TestCase):
    def test_sidebar_core_targets_and_read_only_actions(self):
        root = Path(__file__).resolve().parents[1]
        html = (root/'assets/cockpit.html').read_text()
        js = (root/'assets/app.js').read_text()
        for target in ('control-core','coreStatus','coreHandle','coreMode','coreExact','coreRelated','coreUnresolved','coreLatest'):
            self.assertEqual(html.count('id="'+target+'"'),1,target)
            if target!='control-core': self.assertIn(target,js)
        self.assertIn('renderControlCore()',js)
        self.assertIn('NO AUTO SEARCH',html)
        self.assertNotIn('<form',html[html.index('id="control-core"'):html.index('class="rail-notice"')])
    def test_shortcuts_link_existing_sections(self):
        html = (Path(__file__).resolve().parents[1]/'assets'/'cockpit.html').read_text()
        core = html[html.index('id="control-core"'):html.index('class="rail-notice"')]
        for target in ('traces','evidence','source-guard'):
            self.assertIn('href="#'+target+'"',core)
            self.assertIn('id="'+target+'"',html)
    def test_original_features_and_engine_preserved(self):
        self.assertEqual(len(c.SOURCES),20)
        self.assertEqual(len(c.QUICK_KEYS),6)
        self.assertEqual(len(c.REVIEW_LINKS),25)
        html=(Path(__file__).resolve().parents[1]/'assets'/'cockpit.html').read_text()
        for target in ('signalMap','resultList','timelineTrack','sourceMatrix','referenceList'):
            self.assertEqual(html.count('id="'+target+'"'),1)
        self.assertEqual(c.VERSION,'1.5.1')
