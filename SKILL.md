---
name: natural-prose-audit
description: Generate, audit, and revise Chinese prose with the complete Human Writing workflow plus a post-draft cognitive-structure audit. Use for Chinese fiction, long answers, forum posts, public-account articles, blogs, comments, profiles, history, news, industry analysis, popular science, tutorials, reviews, personal narratives, dialogue, scripts, speeches, or other Chinese prose when users ask to write naturally, humanize text, reduce AI or AIGC traces, diagnose overly polished or formulaic writing, or preserve voice during revision. Supports one model from first draft through bounded revision. Never promise detector evasion or a Zhuque pass.
---

# Natural Prose Audit

本 Skill 完整嵌入通用 `human-writing` 1.1.0 作为写作底座，再增加初稿后的认知结构与模型化规整审计。它面向中文虚构与非虚构，不只服务 AIGC 检测场景。

检测器只能当提醒器，不能当作者、事实裁判或作者身份鉴定器。

本 Skill 默认考虑一种常见场景：全文由装载本 Skill 的同一个模型完成。为避免模型在第一稿阶段一边写一边机械自审，必须分开生成与审计。

复杂新写、整体重写或带多项冻结约束的改稿，优先复制并填写`assets/structured-single-model-input-v2-split.xml`。它兼容一次完整生成，也支持同一个模型用`PART_1→PART_2`完成同一草稿轮次；把说话位置、材料资格、冻结内容、输出契约、结构展开、同稿上文、接缝状态和阶段切换集中为一个可检查的输入，同时只向初稿阶段暴露正向生成约束。旧V1模板保留兼容。填写后可运行：

```bash
python scripts/validate_structured_input.py path/to/filled-input.xml
```

校验只检查结构、占位符、枚举、长度预算和必要字段，不联网，也不判断文本质量。简单短答可以直接依据用户请求执行，不强制套模板。

## 完整 Human Writing 底座

嵌入版入口是 `references/human-writing/SKILL.md`。它及其全部参考、脚本、版本和 MIT 许可证均保留在 `references/human-writing/` 下。

所有新写、整体重写和实质改稿任务都先完整读取该入口，再按它的路由读取所需文件：

- 知乎回答、论坛长帖、公众号、博客、评论、人物、历史和行业解读读取 `references/human-writing/references/forum-prose.md`。
- 真人、历史、新闻、产品、数据、评测、教程、商业与用户亲历读取 `references/human-writing/references/reality.md`。
- 小说、故事、对白与虚构叙事读取 `references/human-writing/references/fiction.md`。
- 短文、个人叙事、教程、评测、口播、演讲、剧本、对白、诗歌等指定形式读取 `references/human-writing/references/formats.md`。
- 初稿完成前不得读取 `references/human-writing/references/revision.md`。

同一任务可能需要两份参考。例如现实人物长文同时读取论坛长文与现实核验，历史小说同时读取虚构与现实部分。

## 选择任务阶段

### A. 从零生成或整体重写

1. 复杂任务先把用户材料与要求填入`assets/structured-single-model-input-v2-split.xml`，复制结构单元使其覆盖当前生成范围，随后运行离线校验；不要为了填字段编造事实。一次写完使用`FULL_TEXT/SINGLE_PASS/1_OF_1`；长文本分两次写时使用`PART_1/TWO_PART_CONTINUATION/1_OF_2`，再把同模型同轮完整上半部与冻结接缝状态交给`PART_2/TWO_PART_CONTINUATION/2_OF_2`。
2. 完整读取 `references/human-writing/SKILL.md`。
3. 按上面的任务路由读取全部适用的 Human Writing 正向参考。
4. 读取 `references/generation-card.md`。它只补充单模型首稿所需的正向自然度要求，不取代 Human Writing；使用结构化模板时，不再另抄一份同义生成规则进用户输入。
5. 按用户给定的事实、体裁、读者、口吻和长度完成一份完整初稿。若采用双段，另读`references/split-longform.md`，先完成并冻结`PART_1`，再用同一模型、同一draft_round_id和完整上半部生成`PART_2`，机械装配后才算完整初稿。现实材料不足时先研究、追问或缩短，不能靠复述灌字数。
6. 初稿完成前，不读取 Human Writing 的 `revision.md`、本 Skill 的 `deep-audit.md`，不运行任何审稿脚本，也不把检测词表、风险标签或阈值塞进首稿提示。
7. 将完整初稿冻结，再进入阶段 B。

用户只要快速初稿时可以在阶段 A 后停止。不要为了预防检测而边写边随机扰动。

### B. 审计已有文本

1. 复杂改稿可先填写结构化模板，选择`AUDIT_AND_REVISE`或`WHOLE_REWRITE_THEN_AUDIT`，把原文放入`source_text`并明确冻结项；已有文本也先完整读取 `references/human-writing/SKILL.md` 及适用的文体参考，确认说话位置、事实边界、文体与人物规则。
2. 冻结事实、因果、立场、人物知识、叙事视角、必要情节、格式和原文已经成立的声音。双段文本还须冻结两部分身份与接缝状态，先按`references/split-longform.md`检查接缝，再审全篇。
3. 读取 `references/human-writing/references/revision.md`，执行完整 Human Writing 改稿流程。
4. 需要机械定位时运行：

```bash
python references/human-writing/scripts/check_prose.py path/to/text.txt
```

5. 再读取 `references/deep-audit.md`。
6. 小说、故事、对白和叙事散文另读 `references/fiction.md`；论说、科普、教程、评论、报告和长回答另读 `references/nonfiction.md`。
7. 需要深层结构定位时运行：

```bash
python scripts/audit_prose.py path/to/text.txt --mode fiction --structure
python scripts/audit_prose.py path/to/text.txt --mode nonfiction --structure
```

两个脚本都只输出代理提醒。它们不判定作者身份，不自动改文，不给“AI率”，也不能替代冷读。

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

- 第一稿只接收完整 Human Writing 正向写作要求和生成卡，不接收详细风险词表、阈值、检测分数和逐项审稿清单。
- 第一稿完成后再切换到编辑身份。先冷读全文，再打开 Human Writing 修订参考与深层审计参考。
- 不把同一句来回同义改写。每处改动都要能说明删掉了什么重复功能，或恢复了什么具体声音。
- 修订后再读一遍全文，确认事实、因果和口吻没有因“去 AI”被破坏。
- 用户只要成稿时只交成稿。用户要求审计时，再给简短的证据位置和处理理由。
- 双段不是两个作者。`PART_2`必须读取同一模型同一草稿轮次的完整`PART_1`和接缝状态；只给摘要无法保证精确连续。
- 双段装配只标准化一个接缝换行。任何补写、删写或重排都属于后置修订，不得静默发生。

## 不可采用的捷径

- 不故意加错字、病句、冷僻词、无意义跳跃、虚假经历或错误事实。
- 不按固定比例强制长短句、段长、感官词、口语词或标点。
- 不随机替换同义词，不用另一套套话覆盖原套话。
- 不伪造来源、引语、数据、个人经验和人工编辑记录。
- 不声称“通过朱雀”“不可检测”“降低到某个百分比”。

## 交付前冷读

- 能否看出是谁在说，他为什么现在说。
- 每段是否带来事实、动作、判断、关系或理解变化。
- 哪些句子过分完整，像替读者把所有推理都做完了。
- 哪些转折、限定、总结和动作长期按同一节拍复现。
- 删掉最后一句解释后，意思是否仍然成立。
- 哪处不够漂亮，却恰好属于这个作者、人物或场景。

方法、来源、许可与能力边界见 `references/methodology.md`。
