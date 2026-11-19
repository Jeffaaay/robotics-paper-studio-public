"""Workflow regressions; fixtures never touch the user's real reading state."""
import json
import tempfile
import unittest
from pathlib import Path
from journal import Journal


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='reading-fixture-')
        self.journal = Journal(self.temp.name)
        self.day = '2026-10-25'
        self.candidates = json.loads((Path(__file__).resolve().parents[1] / 'journal/2026-10-25.json').read_text(encoding='utf-8'))['recommendations']
        self.journal.create(self.day, self.candidates)

    def tearDown(self):
        self.temp.cleanup()

    def test_retry_keeps_user_selection_and_notes(self):
        self.journal.select(self.day, self.candidates[0]['id'])
        self.journal.note(self.day, 'My actual observation.')
        changed = json.loads(json.dumps(self.candidates))
        changed[0]['title'] = 'Changed recommendation'
        state, created = self.journal.create(self.day, changed)
        self.assertFalse(created)
        self.assertEqual(state['user_notes'][0]['text'], 'My actual observation.')
        self.assertEqual(state['recommendations'][0]['title'], self.candidates[0]['title'])

    def test_no_notes_before_user_choice(self):
        with self.assertRaises(ValueError):
            self.journal.note(self.day, 'Text')

    def test_assistant_notes_do_not_count_as_user_reading(self):
        self.journal.select(self.day, self.candidates[0]['id'])
        self.journal.note(self.day, 'AI explanation', author='assistant')
        with self.assertRaises(ValueError):
            self.journal.complete(self.day, 'Done')

    def test_cannot_silently_switch_paper_after_notes(self):
        self.journal.select(self.day, self.candidates[0]['id'])
        self.journal.note(self.day, 'My notes about the first paper')
        with self.assertRaises(ValueError):
            self.journal.select(self.day, self.candidates[1]['id'])

    def test_note_retry_does_not_duplicate_or_claim_completion(self):
        self.journal.select(self.day, self.candidates[0]['id'])
        self.journal.note(self.day, 'Question?')
        state = self.journal.note(self.day, 'Question?')
        self.assertEqual(len(state['user_notes']), 1)
        self.assertIsNone(state['reading']['completed_at'])

    def test_completion_does_not_approve_or_publish(self):
        self.journal.select(self.day, self.candidates[0]['id'])
        self.journal.note(self.day, 'I can explain the mechanism, evidence and boundary.')
        state = self.journal.complete(self.day, 'Explicit user confirmation fixture')
        self.assertEqual(state['status'], 'read_confirmed')
        self.assertEqual(state['content']['video_status'], 'not_started')
        self.assertIsNone(state['publication']['instagram_url'])

    def test_invalid_date_cannot_escape_journal(self):
        with self.assertRaises(ValueError):
            self.journal.path('../private')

    def test_compact_index_tracks_multi_day_reading_without_inventing_completion(self):
        root = Path(self.temp.name)
        paper_id = self.candidates[0]['id']
        self.journal.select(self.day, paper_id)
        self.journal.note(self.day, 'AI explanation is not user understanding', author='assistant')
        self.journal.create('2026-10-26', self.candidates)
        index = json.loads((root / 'context/reading-index.json').read_text(encoding='utf-8'))
        paper = next(p for p in index['papers'] if p['id'] == paper_id)
        self.assertEqual(len(index['papers']), 3)
        self.assertEqual(paper['recommendation_count'], 2)
        self.assertEqual(paper['status'], 'reading')
        self.assertEqual(paper['selection_journal'], 'journal/2026-10-25.json')
        self.assertEqual(index['confirmed_paper_count'], 0)
        self.assertEqual(index['days_awaiting_selection'], 1)
        self.journal.note(self.day, 'My actual explanation')
        self.journal.complete(self.day, 'Explicit user confirmation fixture')
        index = json.loads((root / 'context/reading-index.json').read_text(encoding='utf-8'))
        self.assertEqual(index['confirmed_paper_count'], 1)
        self.assertFalse(self.journal.read('2026-10-26')['selected_paper_id'])
        self.assertIsNone(self.journal.read(self.day)['publication']['instagram_url'])


if __name__ == '__main__':
    unittest.main()
