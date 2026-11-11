import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import voidsting_wide as w
from voidsting_core import count_states,Signal
class WideTests(unittest.TestCase):
    def test_ranked_results_are_candidates(self):
        a,n=w.convert_hits('yourAnonKarma',{'checked':120,'hits':[{'provider':'SomeSite','url':'https://example.org/u/yourAnonKarma','http_status':200}]})
        self.assertEqual(n,120);self.assertEqual(len(a),1);self.assertEqual(a[0].state,'RELATED')
        self.assertEqual(a[0].evidence_type,'EXTERNAL_PROFILE_CANDIDATE')
        self.assertEqual(count_states(a)['EXACT'],0)
    def test_invalid_or_unsafe_not_counted(self):
        a,n=w.convert_hits('glitchbyte',{'checked':120,'hits':[{'provider':'A','url':'http://127.0.0.1/u'},{'provider':'B','url':'file:///etc/passwd'},{'provider':'C','url':'https://x.onion/a'},{'provider':'D','url':'https://safe.example/glitchbyte'},{'provider':'D','url':'https://safe.example/glitchbyte'}]})
        self.assertEqual(len(a),1)
    def test_invalid_count_and_json(self):
        a,n=w.convert_hits('glitchbyte',{'checked':10000,'hits':[]})
        self.assertEqual(n,120)
        self.assertEqual(w.convert_hits('glitchbyte',[]) ,([],0))
    def test_runner_mapping(self):
        from voidsting_maigret_runner import map_results
        class S:
            def __init__(self,x):self.x=x
            def is_found(self):return self.x
        r=map_results({'Yes':{'status':S(True),'url_user':'https://one.example/a','http_status':200},'No':{'status':S(False),'url_user':'https://two.example/b'},'Local':{'status':S(True),'url_user':'http://127.0.0.1/a'}})
        self.assertEqual(len(r),1);self.assertEqual(r[0]['provider'],'Yes')
if __name__=='__main__':unittest.main()

class IntegratedWideTests(unittest.TestCase):
    def test_opt_in_results_saved_to_existing_schema(self):
        import io,tempfile
        from unittest.mock import patch
        from contextlib import redirect_stdout
        from voidsting import Console,scan_and_save
        from voidsting_core import open_vault,session_record
        with tempfile.TemporaryDirectory() as td:
            conn=open_vault(Path(td)/'vault.sqlite3')
            native=[Signal('GitHub','Developer','NOT_FOUND','glitchbyte','','test',404,10)]
            external=[Signal('Wide · Site','Public site','RELATED','glitchbyte','https://new.example/user/glitchbyte',
                  'third-party detected; review',200,0,'EXTERNAL_PROFILE_CANDIDATE')]
            with patch('voidsting.perform_scan',return_value=native),patch('voidsting_wide.run_wide',return_value=(external,120)):
                with redirect_stdout(io.StringIO()):
                    sid=scan_and_save(Console('never'),conn,'glitchbyte','full',discover=True)
            report=session_record(conn,sid)
            self.assertEqual(report['scan_mode'],'FULL_WITH_WIDE_PUBLIC_SWEEP')
            self.assertEqual(report['counts']['RELATED'],1)
            self.assertEqual(report['counts']['EXACT'],0)
            self.assertEqual(report['checked_count'],2)
            conn.close()
    def test_exact_duplicates_are_not_repeated(self):
        import io,tempfile
        from unittest.mock import patch
        from contextlib import redirect_stdout
        from voidsting import Console,scan_and_save
        from voidsting_core import open_vault,session_record
        with tempfile.TemporaryDirectory() as td:
            conn=open_vault(Path(td)/'vault.sqlite3')
            native=[Signal('GitHub','Developer','EXACT','glitchbyte','https://github.com/glitchbyte','test',200,10)]
            external=[Signal('Wide · GitHub','Public site','RELATED','glitchbyte','https://github.com/glitchbyte','needs review',200,0,'EXTERNAL_PROFILE_CANDIDATE')]
            with patch('voidsting.perform_scan',return_value=native),patch('voidsting_wide.run_wide',return_value=(external,120)):
                with redirect_stdout(io.StringIO()):
                    sid=scan_and_save(Console('never'),conn,'glitchbyte','full',discover=True)
            self.assertEqual(session_record(conn,sid)['checked_count'],1)
            conn.close()
