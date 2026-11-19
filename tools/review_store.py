"""Local, explicit user review of an exact video + post-caption revision.

There is no Instagram client or scheduled publisher in this module.
"""
import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class ReviewStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.folder = self.root / 'content/launch30'
        self.plan_path = self.folder / 'plan.json'
        self.review_path = self.folder / 'reviews.json'
        self.lock = threading.Lock()

    def plan(self):
        return json.loads(self.plan_path.read_text(encoding='utf-8'))

    def reviews(self):
        if self.review_path.exists():
            return json.loads(self.review_path.read_text(encoding='utf-8'))
        return {'events': [], 'decisions': {}, 'published': {}}

    def media_path(self, variant):
        p = (self.root / variant['file']).resolve()
        allowed = (self.root / 'output/launch30').resolve()
        if not p.is_relative_to(allowed):
            raise ValueError('Media must be inside output/launch30')
        return p

    def fingerprint(self, item, variant):
        p = self.media_path(variant)
        if not p.is_file():
            return None
        payload = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                   'caption': item['post_caption'], 'title': item['title'],
                   'variant': variant['id']}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def snapshot(self):
        plan = self.plan()
        reviews = self.reviews()
        for item in plan['days']:
            for v in item.get('variants', []):
                v['fingerprint'] = self.fingerprint(item, v)
                v['ready'] = bool(v['fingerprint'])
                v['media_url'] = '/media/' + v['id']
                v['cover_url'] = '/cover/' + v['id'] if v.get('cover') else None
            decision = reviews['decisions'].get(item['id'])
            published = reviews['published'].get(item['id'])
            current = next((v for v in item.get('variants', []) if decision and v['id'] == decision['variant_id']), None)
            valid = bool(current and current['ready'] and current['fingerprint'] == decision['fingerprint'])
            item['decision'] = decision
            item['publication'] = published
            item['approval_current'] = bool(valid and decision['action'] == 'approve')
            if published:
                item['status'] = '已手动发布' if item['approval_current'] and published['fingerprint'] == current['fingerprint'] else '发布后已修改'
            elif item['approval_current']:
                item['status'] = '已批准，待手动发布'
            elif decision and decision['action'] == 'changes':
                item['status'] = '待修改'
            elif decision and decision['action'] == 'approve':
                item['status'] = '版本已变，待复审'
            else:
                item['status'] = '待你审核' if any(v['ready'] for v in item.get('variants', [])) else '待制作'
        return plan

    def decide(self, item_id, variant_id, fingerprint, action, note=''):
        if action not in ('approve', 'changes', 'published'):
            raise ValueError('Unknown review action')
        with self.lock:
            snap = self.snapshot()
            item = next((i for i in snap['days'] if i['id'] == item_id), None)
            variant = next((v for v in item.get('variants', []) if v['id'] == variant_id), None) if item else None
            if not variant or not variant['ready'] or fingerprint != variant['fingerprint']:
                raise ValueError('文件或文案已变化，请刷新后重新看这一版。')
            reviews = self.reviews()
            if action == 'published':
                old = reviews['decisions'].get(item_id)
                if not old or old['action'] != 'approve' or old['variant_id'] != variant_id or old['fingerprint'] != fingerprint:
                    raise ValueError('该版本尚未获得你的批准，不能记为已发布。')
            event = {'item_id': item_id, 'variant_id': variant_id, 'fingerprint': fingerprint,
                     'action': action, 'note': str(note)[:2000],
                     'at': datetime.now(timezone.utc).isoformat(), 'actor': 'user_local_review'}
            reviews['events'].append(event)
            if action == 'published':
                reviews['published'][item_id] = event
            else:
                reviews['decisions'][item_id] = event
            self.folder.mkdir(parents=True, exist_ok=True)
            temp = self.review_path.with_suffix('.tmp')
            temp.write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding='utf-8')
            temp.replace(self.review_path)
            return event
