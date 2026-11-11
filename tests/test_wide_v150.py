import unittest,sys,io,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from voidsting_wide import convert_hits,is_account_shaped_url
from voidsting_maigret_runner import summarize_issues
from voidsting import Console
from voidsting_core import Signal
from contextlib import redirect_stdout

class EvidenceGuardTests(unittest.TestCase):
    def test_generic_search_pages_rejected(self):
        for u in ('https://stackoverflow.com/users/filter?search=Rosie',
                  'https://op.gg/lol/summoners/search?q=Rosie&region=na',
                  'https://bit.ly/Rosie',
                  'https://twitchtracker.com/Rosie'):
            self.assertFalse(is_account_shaped_url('Rosie',u),u)
    def test_direct_account_shape_admitted_but_unverified(self):
        for u in ('https://www.mixcloud.com/yourAnonKarma/',
                  'https://www.youtube.com/@yourAnonKarma/about',
                  'https://Rosie.deviantart.com',
                  'https://www.threads.com/@Rosie'):
            name='Rosie' if 'Rosie' in u else 'yourAnonKarma'
            self.assertTrue(is_account_shaped_url(name,u),u)
    def test_one_token_is_not_substring(self):
        self.assertFalse(is_account_shaped_url('Rosie','https://example.org/users/RosieFan'))
        self.assertFalse(is_account_shaped_url('Rosie','https://example.org/rosemary'))
        self.assertFalse(is_account_shaped_url('Rosie','https://rosie.com'))
    def test_response_rejection_and_review_label(self):
        a,n=convert_hits('Rosie',{'checked':120,'hits':[
            {'provider':'SomeSite','url':'https://example.org/Rosie','http_status':200},
            {'provider':'Blocked','url':'https://example.org/@Rosie','http_status':403},
            {'provider':'Search','url':'https://example.org/users/search?q=Rosie'},
            {'provider':'Duplicate','url':'https://example.org/Rosie','http_status':200},
        ]})
        self.assertEqual(n,120)
        self.assertEqual(len(a),1)
        self.assertEqual(a[0].state,'RELATED')
        self.assertIn('REVIEW NEEDED',a[0].reason)
        self.assertNotIn('Maigret',a[0].reason)
    def test_issue_counts_from_http_status_only(self):
        self.assertEqual(summarize_issues({'a':{'http_status':403},'b':{'http_status':429},'c':{'http_status':502},'d':{'http_status':404},'e':{'http_status':200}}),{'blocked_http':2,'server_http':1})
    def test_no_false_zero_ms_for_wide(self):
        c=Console('never')
        s=Signal('Wide · Site','Public site','RELATED','Rosie','https://example.org/Rosie','Review needed',200,0,'EXTERNAL_PROFILE_CANDIDATE')
        f=io.StringIO()
        with redirect_stdout(f):c.signal(s)
        self.assertNotIn('0 ms',f.getvalue())
        self.assertIn('review',f.getvalue())

if __name__=='__main__':unittest.main()
