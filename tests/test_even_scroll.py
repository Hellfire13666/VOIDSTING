"""Layout-only regression checks: the read-only Cockpit keeps the right rail filled."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'assets/style.css').read_text()
HTML=(ROOT/'assets/cockpit.html').read_text()
JS=(ROOT/'assets/app.js').read_text()

class EvenScrollTests(unittest.TestCase):
    def test_saved_traces_occupy_right_column(self):
        self.assertIn('v1.2.4 // EVEN SCROLL',CSS)
        self.assertIn('.rainbow-venom .workgrid > .secondary { align-self:stretch;',CSS)
        self.assertIn('.rainbow-venom .secondary > .session-panel {',CSS)
        self.assertIn('flex:1 1 0;',CSS)
        self.assertIn('max-height:none;',CSS)
    def test_no_new_panel_or_behavior(self):
        self.assertEqual(HTML.count('class="panel session-panel"'),1)
        self.assertEqual(HTML.count('id="sessions"'),1)
        self.assertEqual(HTML.count('id="references"'),1)
        self.assertIn('class="panel constellation-panel voidpulse-panel"',HTML)
        self.assertNotIn('<form',HTML.lower())
        self.assertIn('async function loadSession(id)',JS)
    def test_mobile_responsive_rules_preserved(self):
        self.assertIn('@media (min-width:1121px)',CSS)
        self.assertIn('@media(max-width:760px)',CSS)
        self.assertIn('prefers-reduced-motion:reduce',CSS)
        self.assertIn('READ-ONLY',HTML)

if __name__=='__main__':unittest.main()
