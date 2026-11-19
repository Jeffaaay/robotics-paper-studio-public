"""Generate GitHub-rendered reading cards from the existing journal records."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import quote, urlparse
from reading_context import render_context

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'awaiting_selection': '待你选读', 'reading': '阅读中',
            'in_progress': '阅读中', 'read_confirmed': '已确认读完'}
PUBLICATIONS = {'peer_reviewed_conference': '同行评审会议',
                'peer_reviewed_journal': '同行评审期刊',
                'peer_reviewed_review': '期刊综述', 'preprint': '预印本',
                'company_report': '公司技术报告'}


def text(value):
    """Render data as visible text, without turning its markup into commands/HTML."""
    result = escape(str(value or ''), quote=False)
    return re.sub(r'([\\`*_[\]#|])', r'\\\1', result).replace('\n', ' ')


def link(label, url):
    parsed = urlparse(str(url or ''))
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return text(label)
    return f'[{text(label)}](<{quote(url, safe=":/?&=%#@+,-._~") }>)'


def short_title(paper):
    return paper.get('display_name') or paper['title'].split(':', 1)[0]


def status(record):
    return STATUSES.get(record.get('status'), '进度待核实')


def card(record):
    day = record['date']
    papers = record['recommendations']
    selected = next((p for p in papers if p['id'] == record.get('selected_paper_id')), None)
    lines = [f'# {day} · 论文阅读', '',
             '[← 阅读日历](README.md) · [项目首页](../README.md)', '',
             f'**{status(record)}** · {len(papers)} 篇候选 · 选一篇，讲清一个点', '']
    if selected:
        lines += [f'> 已选：**{text(short_title(selected))}**', '',
                  '在 Codex 里继续写你的理解和疑问，中英文都可以。', '']
    else:
        lines += ['> **今天先选一篇。** 在 Codex 回复编号或论文名即可；你的笔记也直接写在那里。', '']
    lines += ['| 选择 | 论文 | 今天想弄懂的问题 |', '|---|---|---|']
    for i, paper in enumerate(papers, 1):
        label = f'{i} · 首选' if i == 1 else f'{i} · 备选'
        if paper['id'] == record.get('selected_paper_id'):
            label += ' · 已选'
        lines += [f'| {label} | [{text(short_title(paper))}](#paper-{i}) | {text(paper.get("one_question"))} |']
    lines += ['']
    for i, paper in enumerate(papers, 1):
        priority = '首选' if i == 1 else '备选'
        sources = [link('阅读论文 ↗', paper['paper_url']),
                   link('作者 / 出版方页面 ↗', paper['source_url'])]
        for field, label in [('project_url', '项目页面 ↗'), ('code_url', '作者代码 ↗')]:
            if paper.get(field):
                sources.append(link(label, paper[field]))
        lines += [f'<a id="paper-{i}"></a>', '',
                  f'## {i}. {text(short_title(paper))} · {priority}', '',
                  text(paper['title']), '',
                  f'**{text(paper["venue"])}**  ',
                  f'{text(PUBLICATIONS.get(paper.get("publication_status"), paper.get("publication_status")))} · {paper["year"]}', '',
                  '　 ·　 '.join(sources), '',
                  f'> **想弄懂：** {text(paper.get("one_question"))}', '',
                  f'**为什么适合你**  \n{text(paper.get("recommendation"))}', '',
                  f'**从这里开始**  \n{text(paper.get("start_here"))}', '',
                  f'**阅读时间**  \n{text(paper.get("reading_estimate"))}', '',
                  '<details>', '<summary>视频切入点与来源核查</summary>', '',
                  f'**动画可以怎么讲：** {text(paper.get("visual_idea"))}', '',
                  f'**之前的讨论：** {text(paper.get("history_status"))}', '',
                  f'**已核对：** {text(paper.get("evidence_checked"))}', '',
                  f'**作者：** {text(paper.get("authors"))}', '',
                  f'核查日期：{text(paper.get("verified_on"))}', '', '</details>', '']
    lines += ['---', '', '## 我的阅读笔记', '']
    if record.get('canonical_notes_url'):
        lines += [link('打开完整论文笔记 ↗', record['canonical_notes_url']), '']
    notes = record.get('user_notes', [])
    if notes:
        for note in notes:
            lines += [f'**{text(note.get("at", "我的笔记"))}**', '']
            lines += ['> ' + text(part) for part in note['text'].splitlines()]
            lines += ['']
    else:
        lines += ['还没有记录你的笔记。选好后，可以从下面三句话开始：', '',
                  '- 我理解这篇解决的问题是……', '- 我觉得最有意思 / 最不确定的是……',
                  '- 我想用一个动画讲清楚……', '']
    if record.get('assistant_notes'):
        lines += ['<details>', '<summary>AI 辅助解释</summary>', '']
        for note in record['assistant_notes']:
            lines += ['> ' + text(part) for part in note['text'].splitlines()]
            lines += ['']
        lines += ['</details>', '']
    lines += ['## 从阅读到发布', '',
              f'- [{"x" if selected else " "}] 我已选定论文',
              f'- [{"x" if notes else " "}] 已保存我的笔记',
              f'- [{"x" if record.get("reading", {}).get("completed_at") else " "}] 我已确认读懂方法与关键实验', '']
    content = record.get('content', {})
    if content.get('one_point'):
        lines += [f'**准备讲的一个点：** {text(content["one_point"])}', '']
    if content.get('video_status') == 'not_started':
        lines += ['视频待制作。选题和笔记到位后，再做成片供你审核。', '']
    else:
        lines += ['视频制作与逐版本审核见本地审核队列。', '']
    for key, label in [('instagram_caption', 'Instagram 文案草稿'), ('twitter_draft', 'X / Twitter 观点草稿')]:
        if content.get(key):
            lines += ['<details>', f'<summary>{label}</summary>', '', '> ' + text(content[key]), '', '</details>', '']
    for key, label in [('instagram_url', '查看已记录的 Instagram 发布'), ('twitter_url', '查看已记录的 X 发布')]:
        if record.get('publication', {}).get(key):
            lines += [link(label, record['publication'][key]), '']
    lines += ['每条视频与文案都由你看过、批准后再手动发布。', '',
              '<details>', '<summary>记录文件</summary>', '',
              f'[查看原始记录]({day}.json)。本页随阅读记录更新。', '', '</details>', '']
    return '\n'.join(lines)


def write_changed(path, body):
    if not path.exists() or path.read_text(encoding='utf-8') != body:
        path.write_text(body, encoding='utf-8')


def render_views(root=ROOT):
    root = Path(root)
    render_context(root)
    folder = root / 'journal'
    records = []
    for path in sorted(folder.glob('????-??-??.json'), reverse=True):
        date.fromisoformat(path.stem)
        record = json.loads(path.read_text(encoding='utf-8'))
        if record['date'] != path.stem:
            raise ValueError('Journal date must match its filename')
        records.append(record)
        write_changed(path.with_suffix('.md'), card(record))
    if not records:
        return 0
    latest = records[0]['date']
    lines = ['# 阅读日历', '', '[← 项目首页](../README.md)', '',
             f'## [打开最新阅读卡 · {latest} →]({latest}.md)', '',
             '每天上午 9 点更新推荐。选一篇、留下自己的笔记，再把一个点做成视频。', '',
             '| 日期 | 阅读进度 | 已选论文 |', '|---|---|---|']
    for record in records:
        selected = next((p for p in record['recommendations'] if p['id'] == record.get('selected_paper_id')), None)
        title = short_title(selected) if selected else '等你选择'
        lines += [f'| [{record["date"]}]({record["date"]}.md) | {status(record)} | {text(title)} |']
    lines += ['', '点击日期打开阅读卡；笔记、草稿和发布进度都在卡片中查看。', '']
    write_changed(folder / 'README.md', '\n'.join(lines))
    readme = root / 'README.md'
    if readme.exists():
        body = readme.read_text(encoding='utf-8')
        entry = f'<!-- reading-entry:start -->\n## [打开最新阅读卡 · {latest} →](journal/{latest}.md)\n\n[浏览阅读日历](journal/README.md) · 在 Codex 选论文、写笔记\n<!-- reading-entry:end -->'
        body = re.sub(r'<!-- reading-entry:start -->.*?<!-- reading-entry:end -->', lambda _: entry, body, flags=re.S)
        write_changed(readme, body)
    return len(records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(f'Rendered {render_views(args.root)} reading card(s).')
