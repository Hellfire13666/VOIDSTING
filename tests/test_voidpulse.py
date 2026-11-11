"""Read-only, asset-level regression tests for the isolated VOIDPULSE cockpit."""
from pathlib import Path
import re
import unittest
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'assets/cockpit.html').read_text()
JS=(ROOT/'assets/app.js').read_text()
CSS=(ROOT/'assets/style.css').read_text()

class IdParser(HTMLParser):
    def __init__(self): super().__init__();self.ids=[]
    def handle_starttag(self,tag,attrs):
        for key,val in attrs:
            if key=='id':self.ids.append(val)

class VoidpulseTests(unittest.TestCase):
    def test_display_replaces_constellation_heading(self):
        self.assertIn('id="voidpulseTitle">VOIDPULSE',HTML)
        self.assertIn('id="constellation"',HTML)
        self.assertEqual(HTML.count('id="constellation"'),1)
    def test_existing_navigation_and_vault_preserved(self):
        for anchor in ('overview','constellation','evidence','source-guard','traces','references','timeline','control-core'):
            self.assertIn('id="'+anchor+'"',HTML)
        for label in ('PUBLIC REFERENCE ATLAS','VENOM CONTROL CORE','EVIDENCE EXPLORER','SAVED TRACES'):
            self.assertIn(label,HTML)
    def test_saved_signal_placeholders_not_fake_counts(self):
        for ident in ('vpAll','vpExact','vpRelated','vpUncertain','vpOther','vpHandle','vpMode','vpTimestamp','vpLatest'):
            self.assertIn('id="'+ident+'"',HTML)
        self.assertIn('const rows=allRows();const counts={EXACT:0,RELATED:0,UNCERTAIN:0,OTHER:0}',JS)
        self.assertIn("txt($('vpAll'),rows.length)",JS)
    def test_lenses_and_filter_wiring(self):
        for value in ('ALL','EXACT','RELATED','UNCERTAIN','OTHER'):
            self.assertIn('class="voidpulse-lens',HTML)
            self.assertIn('data-filter="'+value+'"',HTML)
        self.assertIn('function updateFilter(next)',JS)
        self.assertIn("document.querySelectorAll('[data-filter]')",JS)
    def test_manual_links_remain_not_checked(self):
        self.assertIn('Generated destinations are <strong>not scans, findings, or evidence</strong>',HTML)
        self.assertIn("if(item.state!=='NOT_CHECKED'||!safeProfile(item.url))continue",JS)
    def test_no_new_search_or_post_controls(self):
        self.assertNotIn('<form',HTML.lower())
        self.assertNotIn("method:'POST'",JS)
        self.assertNotIn("method: 'POST'",JS)
        self.assertIn('SAVED SESSION SIGNAL CORE · NO LIVE NETWORK CALLS',HTML)
    def test_unique_dom_ids(self):
        parser=IdParser();parser.feed(HTML)
        self.assertEqual(len(parser.ids),len(set(parser.ids)))
    def test_responsive_and_reduced_motion(self):
        self.assertIn('max-width:760px',CSS)
        self.assertIn('prefers-reduced-motion:reduce',CSS)
        self.assertIn('voidpulse-stage',CSS)

if __name__=='__main__':unittest.main()
