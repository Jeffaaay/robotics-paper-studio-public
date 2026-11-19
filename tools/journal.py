"""Small persistent reading log. No model, network call or publisher.

User selection, notes and completion commands are for recording actual user
input. They are never evidence that a person read a paper by themselves.
"""
import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from reading_view import render_views

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Journal:
    def __init__(self, root=ROOT):
        self.folder = Path(root) / 'journal'

    def path(self, day):
        parsed = date.fromisoformat(day)
        if parsed.isoformat() != day:
            raise ValueError('Use YYYY-MM-DD')
        return self.folder / f'{day}.json'

    def read(self, day):
        return json.loads(self.path(day).read_text(encoding='utf-8'))

    def save(self, day, data):
        target = self.path(day)
        temporary = target.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temporary.replace(target)
        render_views(self.folder.parent)

    def create(self, day, candidates):
        target = self.path(day)
        if target.exists():
            render_views(self.folder.parent)
            return self.read(day), False
        if len(candidates) != 3:
            raise ValueError('Provide exactly three checked candidates')
        required = ('id', 'title', 'authors', 'year', 'venue', 'publication_status',
                    'paper_url', 'source_url', 'recommendation', 'one_question',
                    'start_here', 'reading_estimate', 'evidence_checked', 'verified_on')
        ids = set()
        for candidate in candidates:
            if any(not candidate.get(field) for field in required):
                raise ValueError('Missing recommendation metadata or evidence provenance')
            if candidate['id'] in ids:
                raise ValueError('Duplicate paper ID')
            ids.add(candidate['id'])
            for field in ('paper_url', 'source_url'):
                url = urlparse(candidate[field])
                if url.scheme != 'https' or not url.netloc:
                    raise ValueError('Paper and evidence URLs must use HTTPS')
        data = {
            'schema_version': 1, 'date': day, 'timezone': 'America/Los_Angeles',
            'status': 'awaiting_selection', 'selected_paper_id': None,
            'recommendations': candidates, 'user_notes': [], 'assistant_notes': [],
            'canonical_notes_url': None,
            'reading': {'completed_at': None, 'confirmation': None},
            'content': {'one_point': None, 'evidence': [], 'video_status': 'not_started',
                        'review_item_id': None, 'instagram_caption': None,
                        'twitter_draft': None, 'twitter_status': 'not_started'},
            'publication': {'instagram_url': None, 'twitter_url': None},
            'events': [{'type': 'recommendations_created', 'at': now()}]
        }
        self.folder.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also prevents a second process from replacing a day.
        try:
            with target.open('x', encoding='utf-8') as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write('\n')
        except FileExistsError:
            render_views(self.folder.parent)
            return self.read(day), False
        render_views(self.folder.parent)
        return data, True

    def select(self, day, paper):
        data = self.read(day)
        if paper not in {item['id'] for item in data['recommendations']}:
            raise ValueError('Paper must be a checked candidate; add a user-supplied paper with verified metadata first')
        if data['selected_paper_id'] == paper:
            return data
        if data['user_notes'] or data['reading']['completed_at'] or data['content']['video_status'] != 'not_started':
            raise ValueError('This day already has reading work. Preserve it; do not attach notes to another paper')
        data['selected_paper_id'] = paper
        data['status'] = 'reading'
        data['events'].append({'type': 'user_selected', 'paper_id': paper, 'at': now()})
        self.save(day, data)
        return data

    def note(self, day, text, author='user', source='user-provided note'):
        data = self.read(day)
        if not data['selected_paper_id']:
            raise ValueError('Wait for the user to select a paper')
        if not text.strip():
            raise ValueError('Empty notes do not count as reading')
        if author not in ('user', 'assistant'):
            raise ValueError('Unknown author')
        key = 'user_notes' if author == 'user' else 'assistant_notes'
        # An exact retry is a no-op; preserve actual wording instead of rewriting.
        if any(item['text'] == text and item['source'] == source for item in data[key]):
            return data
        data[key].append({'text': text, 'source': source, 'at': now()})
        data['events'].append({'type': f'{author}_note_added', 'at': now()})
        self.save(day, data)
        return data

    def complete(self, day, confirmation):
        data = self.read(day)
        if not data['selected_paper_id'] or not data['user_notes']:
            raise ValueError('Selection and the user\'s own notes are required; AI notes alone do not count')
        if not confirmation.strip():
            raise ValueError('Record the explicit user confirmation; never infer it')
        if data['reading']['completed_at']:
            return data
        data['reading'] = {'completed_at': now(), 'confirmation': confirmation}
        data['status'] = 'read_confirmed'
        data['events'].append({'type': 'user_confirmed_reading', 'at': now()})
        self.save(day, data)
        return data


def summary(data):
    return {key: data[key] for key in ('date', 'status', 'selected_paper_id', 'reading', 'content', 'publication')} | {
        'user_note_count': len(data['user_notes']),
        'assistant_note_count': len(data['assistant_notes']),
        'candidates': [{'id': c['id'], 'title': c['title']} for c in data['recommendations']]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('create', 'select', 'note', 'complete', 'status'):
        child = sub.add_parser(name)
        child.add_argument('--date', required=True)
        if name == 'create':
            child.add_argument('--candidates', type=Path, required=True)
        elif name == 'select':
            child.add_argument('--paper', required=True)
        elif name == 'note':
            child.add_argument('--file', type=Path, required=True)
            child.add_argument('--author', choices=('user', 'assistant'), default='user')
            child.add_argument('--source', default='user-provided note')
        elif name == 'complete':
            child.add_argument('--confirmation', required=True)
    args = parser.parse_args()
    journal = Journal()
    try:
        if args.command == 'create':
            candidates = json.loads(args.candidates.read_text(encoding='utf-8-sig'))
            data, created = journal.create(args.date, candidates)
            result = summary(data) | {'created': created}
        elif args.command == 'select':
            result = summary(journal.select(args.date, args.paper))
        elif args.command == 'note':
            result = summary(journal.note(args.date, args.file.read_text(encoding='utf-8-sig'), args.author, args.source))
        elif args.command == 'complete':
            result = summary(journal.complete(args.date, args.confirmation))
        else:
            result = summary(journal.read(args.date))
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
