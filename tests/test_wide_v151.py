"""Local regression tests: resilient reporting without live enumeration."""
import io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import voidsting_wide as wide
from voidsting_maigret_runner import summarize_coverage
from enum import Enum

class Status(Enum):
    CLAIMED='Claimed'
    AVAILABLE='Available'
    UNKNOWN='Unknown'
    ILLEGAL='Illegal'
class Result:
    def __init__(self,status,error=None):self.status=status;self.error=error
    def is_found(self):return self.status==Status.CLAIMED

class CoverageTests(unittest.TestCase):
    def test_separate_absence_from_unknown(self):
        data={'yes':{'status':Result(Status.CLAIMED),'http_status':200},
              'no':{'status':Result(Status.AVAILABLE),'http_status':404},
              'timeout':{'status':Result(Status.UNKNOWN,'Request timeout')},
              'badname':{'status':Result(Status.ILLEGAL)},
              'server':{'status':Result(Status.UNKNOWN),'http_status':503}}
        c=summarize_coverage(data,6)
        self.assertEqual([c[k] for k in ('found','not_found','unknown','unsupported','missing','timeouts')],[1,1,2,1,1,1])
    def test_zero_candidates_is_not_certified_absence(self):
        data={'checked':120,'hits':[],'coverage':{'found':0,'not_found':100,'unknown':18,'unsupported':2,'missing':0},'issues':{'blocked_http':4,'server_http':1}}
        output=[]
        with patch.object(wide,'is_installed',return_value=True),patch.object(wide,'_run_runner',return_value=(0,json.dumps(data),'test')):
            results,checked=wide.run_wide('inv523',say=output.append)
        t='\n'.join(output)
        self.assertEqual((len(results),checked),(0,120))
        self.assertIn('100 site-level absences',t)
        self.assertIn('18 unresolved',t)
        self.assertIn('INCOMPLETE WIDE COVERAGE',t)
        self.assertIn('4 blocked HTTP statuses',t)
        self.assertNotIn('ERROR 0',t)
    def test_direct_candidate_still_review_only(self):
        data={'checked':120,'hits':[{'provider':'MixCloud','url':'https://www.mixcloud.com/inv523/','http_status':200}],
              'coverage':{'found':1,'not_found':119,'unknown':0,'unsupported':0,'missing':0},
              'issues':{'blocked_http':0,'server_http':0}}
        with patch.object(wide,'is_installed',return_value=True),patch.object(wide,'_run_runner',return_value=(0,json.dumps(data),'test')):
            results,_=wide.run_wide('inv523',say=lambda x:None)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0].state,'RELATED')
        self.assertIn('REVIEW NEEDED',results[0].reason)
    def test_unfinished_checker_never_adds_candidates(self):
        with patch.object(wide,'is_installed',return_value=True),patch.object(wide,'_run_runner',return_value=None):
            self.assertEqual(wide.run_wide('inv523',say=lambda x:None),([],0))
    def test_popen_progress_and_result(self):
        class Proc:
            returncode=0
            def __init__(self):self.calls=0
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def communicate(self,timeout=None):
                self.calls+=1
                if self.calls==1:raise wide.subprocess.TimeoutExpired('runner',2)
                return ('{"checked":0,"hits":[]}', 'no errors')
        buf=[]
        with patch.object(wide.subprocess,'Popen',return_value=Proc()):
            status=wide._run_runner('inv523',buf.append,timeout=40,heartbeat=2)
        self.assertEqual(status[0],0)
        self.assertTrue(any('RUNNING' in v for v in buf))

if __name__=='__main__':unittest.main()
