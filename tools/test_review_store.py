"""Approval checks use isolated temporary fixtures, never the real review queue."""
import json
import tempfile
import unittest
from pathlib import Path
from review_store import ReviewStore

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='review-unit-')
        self.root=Path(self.temp.name).resolve()
        (self.root/'content/launch30').mkdir(parents=True)
        (self.root/'output/launch30').mkdir(parents=True)
        self.media=self.root/'output/launch30/a.mp4';self.media.write_bytes(b'test-media-v1')
        self.plan={'days':[{'id':'test-d01','day':1,'title':'Fixture','post_caption':'Fixture caption',
                           'variants':[{'id':'test-a','file':'output/launch30/a.mp4'}]}]}
        self.path=self.root/'content/launch30/plan.json';self.save()
        self.store=ReviewStore(self.root)
    def tearDown(self):
        # TemporaryDirectory owns exactly this resolved, isolated fixture root.
        assert Path(self.temp.name).resolve()==self.root
        self.temp.cleanup()
    def save(self): self.path.write_text(json.dumps(self.plan),encoding='utf-8')
    def current(self): return self.store.snapshot()['days'][0]
    def fp(self): return self.current()['variants'][0]['fingerprint']
    def approve(self): self.store.decide('test-d01','test-a',self.fp(),'approve')
    def test_unreviewed_cannot_be_marked_published(self):
        self.assertFalse(self.current()['approval_current'])
        with self.assertRaises(ValueError): self.store.decide('test-d01','test-a',self.fp(),'published')
    def test_explicit_approval_is_separate_from_publication(self):
        self.approve();item=self.current()
        self.assertTrue(item['approval_current']);self.assertIsNone(item['publication'])
        self.store.decide('test-d01','test-a',self.fp(),'published')
        self.assertEqual(self.current()['status'],'已手动发布')
    def test_video_edit_invalidates_approval(self):
        self.approve();old=self.fp();self.media.write_bytes(b'changed-video')
        self.assertFalse(self.current()['approval_current'])
        self.assertEqual(self.current()['status'],'版本已变，待复审')
        with self.assertRaises(ValueError): self.store.decide('test-d01','test-a',old,'approve')
    def test_caption_edit_invalidates_approval(self):
        self.approve();self.plan['days'][0]['post_caption']='New wording';self.save()
        self.assertFalse(self.current()['approval_current'])
    def test_changes_revoke_approval(self):
        self.approve();self.store.decide('test-d01','test-a',self.fp(),'changes','Shorter labels')
        self.assertFalse(self.current()['approval_current']);self.assertEqual(self.current()['status'],'待修改')
    def test_outside_media_directory_rejected(self):
        self.plan['days'][0]['variants'][0]['file']='README.md';self.save()
        with self.assertRaises(ValueError): self.current()

if __name__=='__main__': unittest.main()
