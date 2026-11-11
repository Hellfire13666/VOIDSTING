"""Offline regression checks for the standalone search-core expansion."""
import hashlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import voidsting_core as c
import voidsting as cli

class SearchCore130Tests(unittest.TestCase):
    def test_fixed_sources_unique_and_quick_still_six(self):
        self.assertEqual(len(c.SOURCES),20)
        self.assertEqual(len({s.key for s in c.SOURCES}),20)
        self.assertEqual(len(c.QUICK_KEYS),6)
    def test_four_new_endpoints_fixed_https(self):
        by={s.key:s for s in c.SOURCES}
        self.assertEqual(c.make_url(by['minecraft'],'Rosie'),
            'https://api.minecraftservices.com/minecraft/profile/lookup/name/Rosie')
        self.assertIn('acct%3ARosie%40mastodon.online',c.make_url(by['mastodononline'],'Rosie'))
        self.assertIn('acct%3ARosie%40fosstodon.org',c.make_url(by['fosstodon'],'Rosie'))
        self.assertEqual(c.make_url(by['pixelfed'],'Rosie'),
            'https://pixelfed.social/api/v1/accounts/lookup?acct=Rosie')
        for key in ('minecraft','mastodononline','fosstodon','pixelfed'):
            self.assertTrue(by[key].endpoint.startswith('https://'))
    def test_minecraft_requires_exact_name_and_real_uuid(self):
        good={'name':'GlitchByte','id':'a'*32}
        self.assertEqual(c.classify('minecraft','glitchbyte',200,good)[0],'EXACT')
        for obj in ({'name':'other','id':'a'*32},{'name':'glitchbyte','id':'x'},
                    {'name':'glitchbyte'},{'id':'a'*32},{}):
            with self.subTest(obj=obj):
                self.assertNotEqual(c.classify('minecraft','glitchbyte',200,obj)[0],'EXACT')
    def test_minecraft_empty_204_is_specific_absence(self):
        self.assertEqual(c.classify('minecraft','rose',204,None)[0],'NOT_FOUND')
    def test_minecraft_invalid_username_skips_network(self):
        seen=[]
        def do_fetch(url): seen.append(url);raise AssertionError('must not fetch')
        s=next(s for s in c.SOURCES if s.key=='minecraft')
        for name in ('glitch-byte','x'*17,'ab'):
            row=c.check(s,name,do_fetch)
            self.assertEqual(row.state,'UNCERTAIN')
            self.assertIn('no request',row.reason)
        self.assertEqual(seen,[])
    def test_mastodon_domains_do_not_cross_match(self):
        for key,host in (('mastodononline','mastodon.online'),('fosstodon','fosstodon.org')):
            yes={'subject':f'acct:Rosie@{host}', 'links':[{'rel':'self','href':f'https://{host}/users/Rosie'}]}
            self.assertEqual(c.classify(key,'Rosie',200,yes)[0],'EXACT')
            for obj in (
                {'subject':'acct:Rosie@wrong.example','links':yes['links']},
                {'subject':yes['subject'],'links':[]},
                {'subject':yes['subject'],'links':[{'rel':'self','href':'https://evil.example/@Rosie'}]},
                {'subject':yes['subject'],'links':[{'rel':'self','href':f'http://{host}/users/Rosie'}]}
            ):
                self.assertNotEqual(c.classify(key,'Rosie',200,obj)[0],'EXACT')
    def test_pixelfed_requires_local_exact_account(self):
        good={'username':'Rose','acct':'Rose','id':'55'}
        self.assertEqual(c.classify('pixelfed','Rose',200,good)[0],'EXACT')
        remote={'username':'Rose','acct':'Rose@mastodon.social','id':'66'}
        self.assertNotEqual(c.classify('pixelfed','Rose',200,remote)[0],'EXACT')
        self.assertNotEqual(c.classify('pixelfed','Rose',200,{'username':'Rose','acct':'Rose'})[0],'EXACT')
        self.assertEqual(c.classify('pixelfed','Rose',400,{'error':'not available'})[0],'UNCERTAIN')
        self.assertEqual(c.classify('pixelfed','Rose',429,None)[0],'BLOCKED')
    def test_pixelfed_too_short_no_request(self):
        s=next(s for s in c.SOURCES if s.key=='pixelfed')
        row=c.check(s,'ab',lambda _:(_ for _ in ()).throw(AssertionError('unexpected request')))
        self.assertEqual(row.state,'UNCERTAIN')
    def test_all20_responses_cant_accidentally_be_exact(self):
        items=c.perform_scan('testhandle',transport=lambda _:(200,{'success':True}),delay=0)
        self.assertEqual(len(items),20)
        self.assertFalse(any(s.state=='EXACT' for s in items))
    def test_four_opt_in_directory_queries(self):
        urls=[]
        def lookup(url):
            urls.append(url)
            if 'search/users' in url:return 200,{'items':[{'login':'rosie-dev'},{'login':'other'}]}
            if 'searchActors' in url:return 200,{'actors':[{'handle':'rosie.bsky.social'}]}
            if 'gitlab.com' in url:return 200,[{'username':'Rosie-dev'},{'username':'someoneelse'}]
            if 'gitea.com' in url:return 200,{'data':[{'login':'rosiecode'}]}
            return 200,{}
        hints=c.bounded_discovery('rosie',transport=lookup,delay=0)
        self.assertEqual(len(urls),4)
        self.assertEqual(sum(x.state=='RELATED' for x in hints),4)
        self.assertFalse(any(x.state=='EXACT' for x in hints))
    def test_directory_denials_no_retry_and_no_false_match(self):
        requests=[]
        def deny(url):requests.append(url);return 403,None
        rows=c.bounded_discovery('Rosie',transport=deny,delay=0)
        self.assertEqual(len(requests),4)
        self.assertEqual(len(rows),4)
        self.assertTrue(all(x.state=='BLOCKED' for x in rows))
    def test_empty_204_response_stays_valid(self):
        class FakeResponse:
            status=204
            def __enter__(self):return self
            def __exit__(self,*x):pass
            def read(self,*args):raise AssertionError('should not parse a 204 body')
        class FakeOpener:
            def open(self,*args,**kwargs):return FakeResponse()
        with patch.object(c,'OPENER',FakeOpener()):
            self.assertEqual(c.fetch_json('https://api.minecraftservices.com/minecraft/profile/lookup/name/test'),(204,None))
    def test_older_vault_schema_unchanged(self):
        import sqlite3,tempfile
        with tempfile.TemporaryDirectory() as d:
            conn=c.open_vault(Path(d)/'sample.db')
            try:
                sid=c.save_session(conn,'Rosie','FULL',c.perform_scan('Rosie',transport=lambda _: (404,None),delay=0))
                self.assertEqual(len(c.session_record(conn,sid)['signals']),20)
                self.assertEqual(c.session_record(conn,sid)['username'],'Rosie')
            finally:conn.close()
    def test_no_new_menu_options(self):
        source=(ROOT/'voidsting.py').read_text()
        self.assertEqual(source.count('console.say("  [1] QUICK VERIFY'),1)
        self.assertIn(' [10] OPTIONAL COCKPIT',source)
        self.assertNotIn('  [11] ',source)
    def test_cockpit_assets_untouched_except_metadata(self):
        self.assertTrue((ROOT/'assets/style.css').is_file())
        self.assertTrue((ROOT/'assets/app.js').is_file())
        self.assertIn('VOIDPULSE',(ROOT/'assets/cockpit.html').read_text())

if __name__=='__main__':unittest.main()
