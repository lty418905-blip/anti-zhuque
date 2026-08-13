---
name: natural-prose-audit
description: Generate, audit, and revise Chinese prose to reduce model-like regularity while preserving facts, reasoning accuracy, author intent, and voice. Use for Chinese fiction or nonfiction when users ask to humanize text, reduce AI or AIGC traces, diagnose overly polished or formulaic prose, or run a post-draft naturalness audit. Supports a single-model workflow from first draft through bounded revision. Never promise detector evasion or a Zhuque pass.
---

# Natural Prose Audit

写出自然中文，减少模型化的规整感，同时保住事实、逻辑、人物、立场和专业准确性。检测器只能当提醒器，不能当作者，也不能当真实性裁判。

本 Skill 默认考虑一种常见场景：**全文由装载本 Skill 的同一个模型完成**。为避免模型在第一稿阶段一边写一边机械自审，严格分开生成与审计。

## 选择任务阶段

### A. 从零生成或整体重写

1. 只读取 `references/generation-card.md`。
2. 按用户给定的事实、体裁、读者、口吻和长度完成一份完整初稿。
3. 初稿完成前，不读取 `references/deep-audit.md`，不运行脚本，不展示检测词表或风险标签。
4. 将初稿视为冻结输入，再进入阶段 B。

如果用户只要快速初稿，可以在阶段 A 后停止。不要为了预防检测而边写边随机扰动。

### B. 审计已有文本

1. 读取 `references/deep-audit.md`。
2. 小说、故事、对白和叙事散文再读 `references/fiction.md`。
3. 论说、科普、教程、评论、报告和长回答再读 `references/nonfiction.md`。
4. 先建立不可改变项，再检查深层组织方式，最后检查表层节奏和措辞。
5. 需要机械定位时运行：

```bash
python scripts/audit_prose.py path/to/text.txt --mode fiction --structure
python scripts/audit_prose.py path/to/text.txt --mode nonfiction --structure
```

脚本只输出代理提醒，不判定作者身份，不自动改文，不给“AI率”。

### C. 有界修订

先冻结这些内容：

1. 事实、数字、时间、地点、因果、专业术语和证据强度。
2. 核心观点、作者立场、人物知识、关系和叙事视角。
3. 必须保留的例子、引语、情节节点、结论与交付格式。
4. 原文已经成立的幽默、停顿、笨拙、意象和个人口吻。

逐项使用以下动作：

- `KEEP`：形状可疑但内容必要，或本来就是作者声音。
- `DELETE_TAIL`：删除动作、例子或前句已经表达过的解释尾巴。
- `BOUNDED_REPHRASE`：只改表达和呈现顺序，不改冻结内容。
- `REVIEW_FLAG`：无法安全判断，保留并说明需要作者决定什么。

改动若触及冻结项，停止自然度修订，向用户说明这是事实、结构或立场修改。

## 单模型工作纪律

- 第一稿只接收正向写作要求，不接收详细风险词表、阈值、检测分数和逐项审稿清单。
- 第一稿完成后再切换到编辑身份。先冷读全文，再打开深层审计参考。
- 不把同一句来回同义改写；每处改动必须能说明删掉了什么重复功能，或恢复了什么具体声音。
- 修订后再读一遍全文，确认事实、因果和口吻没有因“去 AI”被破坏。
- 如果用户只要成稿，只交成稿；用户要审计时，再给简短的证据位置和处理理由。

## 不可采用的捷径

- 不故意加错字、病句、冷僻词、无意义跳跃、虚假经历或错误事实。
- 不按固定比例强制长短句、段长、感官词、口语词或标点。
- 不随机替换同义词，不用另一套套话覆盖原套话。
- 不伪造来源、引语、数据、个人经验和人工编辑记录。
- 不声称“通过朱雀”“不可检测”“降低到某个百分比”。

## 交付前冷读

- 能否看出是谁在说、他为什么现在说。
- 每段是否带来事实、动作、判断、关系或理解变化。
- 哪些句子过分完整，像替读者把所有推理都做完了。
- 哪些转折、限定、总结和动作长期按同一节拍复现。
- 删掉最后一句解释后，意思是否仍然成立。
- 哪处不够漂亮，却恰好属于这个作者、人物或场景。

方法与能力边界见 `references/methodology.md`。
