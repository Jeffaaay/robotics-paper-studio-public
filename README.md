# Robotics Paper Studio

每天认真读一篇 robotics 论文，把自己真正理解的一个点讲清楚。

Public research workflow for robotics paper reading, evidence-based notes, short animations, and reviewable social drafts. The aim is a sustained research habit and a credible record of understanding.

<!-- reading-entry:start -->
## [打开最新阅读卡 · 2026-11-18 →](journal/2026-11-18.md)

[浏览阅读日历](journal/README.md) · 在 Codex 选论文、写笔记
<!-- reading-entry:end -->

## 每天怎么用

**每天上午 9:00，America/Los_Angeles**，独立的 Codex 定时任务给出三篇候选：一个首选、两个备选。每天从短的阅读索引开始，不继承旧综合聊天。打开上方阅读卡即可查看推荐、原文链接和阅读入口。你选一篇，也可以换成自己的论文；同一天重跑不会覆盖你的选择或笔记。

**每篇选定论文有一个独立精读任务。** 同一篇可以连续讨论多天；再次推荐已在读论文时回到原任务。新任务先读[简短背景](context/START_HERE.md)与[阅读进度索引](context/READING_INDEX.md)，再按需打开单篇笔记。[UMI 续读记录](papers/umi-2024/PROGRESS.md)已经整理；讲过的内容与用户真正确认读懂的内容分别记录。

1. **你选读。** 优先贴近正在做的 AMR 和 OpenArm 工作。保留经典论文；新论文不能仅凭 arXiv 上传就标作顶刊。
2. **你写自己的笔记。** 可以在 Codex 用中文、英文或混合输入，原话保留。AI 的解释另标为 assistant synthesis。已有长笔记继续放在 [robotics-research-notes](https://github.com/Jeffaaay/robotics-research-notes)，这里只保存链接，避免重复维护。
3. **共同精读一个关键点。** 弄清问题、改动、机制、证据和边界。公式要对应到机器人具体动作；数字要带来源、条件和比较对象。
4. **做一个视频。** 依据你的笔记和核对过的原文，制作 12–30 秒英文视觉解释。默认无旁白，只有必要短标签；较长解释和引用放在帖文里。动画必须适合当前论文，不能只替换旧片标题。
5. **你看过成片及文案并批准。** 批准绑定具体视频和文案，修改后重新审核。Instagram 由你手动发布；X/Twitter 也单独审核，不自动发。

回复例如：**“今天选 UMI；我读到这里有三个疑问……”**。不必自己运行命令。

每天的候选、个人笔记和阅读进度都能从[阅读日历](journal/README.md)打开。

## 阅读与可信度

日目标是一篇；一天内没有读懂就如实记 `in_progress`，不把摘要阅读、AI 解说或看过演示等同精读。长综述可以继续读多天。每天至少留下一个自己的解释或问题，视频只讲已核对的部分。

建议一轮：选题 5 分钟 → 问题/方法/关键实验 40–60 分钟 → 自己解释与质疑 15–20 分钟 → 对照原文补洞。时间只是起步预算，不是“读懂”的证明。制作时间单独记录。

每篇最后应能回答：

- 以前具体哪里做不好？这篇究竟改变了什么？
- 一个机制、公式或动作为什么能起作用？
- 哪个实验支持它？baseline、硬件、数据和条件是什么？
- 作者没有证明什么？我的判断又是什么？
- 对 AMR / OpenArm 的哪个实际问题有用，下一步可以测什么？

用明确的来源与独立判断建立 credibility；不把作者实验说成自己的复现，不虚构“我认为”，不夸大安全性或泛化。

## Instagram 与 X/Twitter

| 渠道 | 输出 | 核心 |
|---|---|---|
| Instagram | 一个可视化机制/反例/对比；简短英文文案及论文引用 | 让观众看懂一个点 |
| X/Twitter | 一条有来源的个人判断，必要时短 thread | 我原来怎样想、证据怎样改变了看法、还有什么不确定 |

Twitter 草稿只能依据你实际写下的观点。没有个人观点时先问一个具体问题，不生成伪装成你的第一人称心得。两个渠道不必使用同一文案，也不必强行每天都有值得发的观点。

第一轮以 **30 天**作为实验窗口；从第一条手动发布起计，每天目标一条。日读、读懂一个点、成片、审核、实际发布分别计数。可积累 3–5 条逐条批准的片子作为日更缓冲；未获批准的空档保留为空档，不把漏发的一天从日历里抹掉。

## 当前兴趣与选题

- AMR：路径跟踪、模型不确定性、系统延迟、故障恢复与可重复验证。
- OpenArm：双臂夹爪操作、衣物折叠、遥操作数据、模仿学习、低成本复现。
- 灵巧手和弹琴保留为未来兴趣，当前不优先。

来源是本次授权查看的 Codex 研究任务和现有笔记仓库；不上传完整聊天记录或公司源码。候选优先参考 IJRR、T-RO、Science Robotics、RA-L，以及 RSS、CoRL、ICRA、IROS；仍要逐篇检查研究问题、实验质量和可读性。期刊/会议不是结论正确性的保证。公司技术报告与预印本单独标注。

## 目录与运行

```text
config.json                  方向、时间和输出偏好
journal/YYYY-MM-DD.md         GitHub 上直接阅读的每日卡片
journal/YYYY-MM-DD.json       当天推荐、选择、原话笔记和进度
agent/daily-reading.txt       每天的执行规范
agent/paper-reading.txt       单篇精读、续读和任务分流
context/START_HERE.md         新任务的简短背景与读取规则
context/READING_INDEX.md      自动生成的阅读状态与最近推荐
papers/registry.json          每篇论文对应的讨论任务
papers/<paper-id>/PROGRESS.md 单篇阅读位置、疑问和下一步
agent/editorial-prompt.txt    论文到视频的编辑规范
scenes/                      实际 Manim 场景代码
tools/journal.py              不覆盖已有记录的阅读日志工具
tools/reading_view.py         自动更新阅读卡、日历和首页入口
tools/review_*.py             绑定版本的本地审核
content/launch30/plan.json    可播放草稿队列（不是发布计划）
samples/                     我们自己制作的两版 16 秒示意片
```

Python 3.12。日志与审核工具仅使用标准库；渲染另装 `requirements.txt`。

```powershell
python tools/journal.py status --date 2026-10-25
python tools/journal.py select --date 2026-10-25 --paper umi-2024
python tools/journal.py note --date 2026-10-25 --file my-note.txt
python tools/journal.py complete --date 2026-10-25 --confirmation "用户确认精读了方法和关键实验，并能解释 latency matching"
python -m unittest discover -s tools -p "test_*.py"
python tools/start_review.py --port 8893
```

`complete` 仅记录真实用户确认；不得由自动任务自己运行来冒充读完。新增日期通过 `python tools/journal.py create --date YYYY-MM-DD --candidates verified-candidates.json`，候选结构见今日记录。它只记录已核实的推荐，不自行抓论文、不假装已经读过全文。

日志创建、选择、写笔记和确认读完时会同步更新阅读卡和简短索引。如果直接编辑 JSON，运行 `python tools/reading_view.py` 刷新页面；单独刷新索引用 `python tools/reading_context.py`。阅读卡和索引由原始记录生成；单篇 PROGRESS 由讨论任务维护，长笔记仍以原笔记仓库为准。

两版已有样片见 [A 无解释标签](samples/minimal_control_A_no_labels_1080x1920.mp4) / [B 六个英文词](samples/minimal_control_B_three_labels_1080x1920.mp4)。这是手工运动示意，不是论文复现。渲染它们：`python tools/render_minimal_control.py`。新论文必须另写适合的场景。

The repository contains the workflow and example records only. Any local scheduler must be configured separately. This repository has no Instagram/X credentials and never publishes automatically.
