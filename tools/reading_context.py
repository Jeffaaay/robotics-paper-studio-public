"""Build a compact, deterministic index without changing reading evidence."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_index(root):
    root = Path(root)
    registry_path = root / 'papers/registry.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))['papers'] if registry_path.exists() else {}
    papers = {}
    latest = None
    pending_days = 0
    for path in sorted((root / 'journal').glob('????-??-??.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        day = record['date']
        if path.stem != day:
            raise ValueError('Journal date must match filename')
        latest = day
        selected = record.get('selected_paper_id')
        pending_days += int(not selected)
        for candidate in record['recommendations']:
            key = candidate['id']
            paper = papers.setdefault(key, {
                'id': key, 'title': candidate['title'], 'paper_url': candidate['paper_url'],
                'first_recommended': day, 'last_recommended': day, 'recommendation_count': 0,
                'status': 'recommended', 'selection_journal': None,
                'user_note_count': 0, 'assistant_note_count': 0, 'confirmed_at': None,
            })
            paper['last_recommended'] = day
            paper['recommendation_count'] += 1
            if selected == key:
                paper['selection_journal'] = paper['selection_journal'] or f'journal/{day}.json'
                paper['user_note_count'] += len(record.get('user_notes', []))
                paper['assistant_note_count'] += len(record.get('assistant_notes', []))
                reading = record.get('reading', {})
                # AI notes, a task registry, or a status label alone are not completion evidence.
                confirmed = reading.get('completed_at') if reading.get('confirmation') and record.get('user_notes') else None
                paper['confirmed_at'] = paper['confirmed_at'] or confirmed
                paper['status'] = 'read_confirmed' if paper['confirmed_at'] else 'reading'
        if selected and selected not in {p['id'] for p in record['recommendations']}:
            raise ValueError('Selected paper missing from recommendations')
    for key, entry in registry.items():
        if key not in papers:
            raise ValueError(f'Registered paper lacks journal evidence: {key}')
        papers[key]['task'] = entry
    ordered = sorted(papers.values(), key=lambda p: (p['status'] == 'recommended', p['id']))
    return {'schema_version': 1, 'latest_journal_date': latest,
            'days_awaiting_selection': pending_days,
            'confirmed_paper_count': sum(p['status'] == 'read_confirmed' for p in ordered),
            'papers': ordered}


def write_changed(path, body):
    if not path.exists() or path.read_text(encoding='utf-8') != body:
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(body, encoding='utf-8')
        temporary.replace(path)


def render_context(root=ROOT):
    root = Path(root)
    index = build_index(root)
    folder = root / 'context'
    folder.mkdir(parents=True, exist_ok=True)
    write_changed(folder / 'reading-index.json', json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    lines = ['# 阅读索引', '', '[新任务入口](START_HERE.md) · [阅读日历](../journal/README.md)', '',
             f'最近推荐日期：{index["latest_journal_date"] or "暂无"}。确认读完 {index["confirmed_paper_count"]} 篇；'
             f'{index["days_awaiting_selection"]} 个推荐日仍未选读。', '',
             '由日志和任务登记生成；不把 AI 笔记、历史讨论或推荐次数当作读完。', '',
             '## 正在读 / 已确认读完', '']
    reading = sorted((p for p in index['papers'] if p['status'] == 'reading'), key=lambda p: p['last_recommended'], reverse=True)
    finished = sorted((p for p in index['papers'] if p['status'] == 'read_confirmed'), key=lambda p: p['confirmed_at'], reverse=True)
    active = (reading + finished)[:8]
    for paper in active:
        task = paper.get('task', {})
        state = '已确认读完' if paper['status'] == 'read_confirmed' else '阅读中，尚未确认读完'
        lines += [f'- **{paper["id"]}**：{state}；用户笔记 {paper["user_note_count"]} 条，AI 说明 {paper["assistant_note_count"]} 条。']
        if task.get('progress_path'):
            progress_link = f'  [续读记录](../{task["progress_path"]})'
            if task.get('canonical_notes_url'):
                progress_link += f' · [完整笔记]({task["canonical_notes_url"]})'
            lines += [progress_link]
        if task.get('thread_id'):
            lines += [f'  专属任务：{task["title"]}；ID `{task["thread_id"]}`（host: {task.get("host_id") or "local"}）。']
    if not active:
        lines += ['尚无已选论文。']
    if len(reading) + len(finished) > len(active):
        lines += ['', '最多列出 8 篇，优先在读论文；其余按 ID 查询 reading-index.json，不必整体加载。']
    lines += ['', '## 最近推荐', '', '| 论文 ID | 最近推荐 | 推荐次数 |', '|---|---|---|']
    recent = sorted(index['papers'], key=lambda p: (p['last_recommended'], p['id']), reverse=True)[:12]
    for paper in recent:
        lines += [f'| {paper["id"]} | {paper["last_recommended"]} | {paper["recommendation_count"]} |']
    lines += ['', '仅显示最近 12 篇。去重时用 `reading-index.json` 查询 ID/论文 URL；无需读取所有旧日志正文。',
              '更早的论文笔记目录见新任务入口；不因本索引中没有出现就认定从未讨论。', '']
    write_changed(folder / 'READING_INDEX.md', '\n'.join(lines))
    return index


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    result = render_context(args.root)
    print(f'Indexed {len(result["papers"])} papers; {result["confirmed_paper_count"]} confirmed complete.')
