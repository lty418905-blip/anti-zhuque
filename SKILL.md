---
name: natural-prose-audit
description: Audit and revise Chinese prose for model-like regularity while preserving facts, causality, character voice, and technical accuracy. Use for Chinese fiction or nonfiction when users ask to humanize text, reduce AI or AIGC traces, prepare for Zhuque-style detection, vary overly uniform rhythm, remove templated wording, or perform a post-human-writing audit. Do not claim guaranteed detector evasion or a real Zhuque pass.
---

# Natural Prose Audit

把检测器视为提醒器，不把它当作者。目标是让文字更像一个具体的人在具体处境中写出来，同时保住作品原本成立的事实、人物和节奏。本包已经完整整合 `human-writing` 的核心、分文体参考、改稿流程和检查脚本；不要再要求用户或上游任务另行启用 `human-writing`。

## 选择工作方式

- 新写或实质重写任何正文时，先读 `references/human-writing-core.md`，再按下列文体路由读取参考。
- 小说、故事、虚构散文与对白，读取 `references/human-fiction.md`、`references/fiction-workflow.md`、`references/cognitive-structure.md`和`references/scene-level-audit.md`。若章节由多段连续生成或机械装配，再读取`references/split-chapter-seam.md`。
- 论坛长帖、公众号、博客与中文长回答，读取 `references/human-forum-prose.md`；现实内容再读 `references/human-reality.md`。
- 短内容、口播、教程、剧本、对白或特殊格式，读取 `references/human-formats.md`。
- 初稿完成后才读取 `references/human-revision.md`；不得在第一稿前用详细审稿表压扁声音。
- 新写正文时，只把`references/external-model-card.md`的正向原则交给外部正文模型，不发送本Skill的审计部分。若调用环境已经把这些正向原则嵌入结构化写作输入，只发送当前任务填好的唯一输入，不再重复附加本Skill或正向卡。不要把词表、阈值或检测规则塞进生成提示。
- 已有正文需要改稿时，先冻结事实与结构，再做语义审计和有界改写。
- 用户只问检测原理或策略时，读取 `references/six-dimensions.md`。
- 用户要求检查或清理文本中的不可见Unicode控制字符，或最终正文已经冻结时，读取`references/unicode-layer-a.md`。Layer A只能在所有语义修订完成后执行；任何后续语义改写都会使旧清理结果失效。
- 用户提供检测报告、要求比较检测前后版本、出现微小改动后分数反向或拟据检测结果改稿时，完整读取`references/detector-evidence-and-reverse-effect.md`。先在不看分数和高风险定位的条件下完成独立文学冷读，再核验提交输入、可见文本、报告字符和分段是否可比；单次报告不得直接触发正文改动。报告存在公开分段时，还须把分段文字边界映射到源稿UTF-8字节、场景和作者／轮次边界；没有完成这一步，不得选择局部修复范围。
- 小说、故事、人物对白或第一人称叙事，读取 `references/fiction-workflow.md`。
- 需要解释本 Skill 与 `qoqu/anti-zhuque` 的关系、许可或能力边界时，读取 `references/source-notes.md`。

先冻结事实与章末接口，再按场景写出事件冻结、认知上限和未决残留，检查认知流程复现、对白闭环、动作配对、物件过载、生活后效和结尾总回收；然后按内置 human-writing 规则清理翻案腔、模型黑话、解释尾巴和无功能漂亮句，最后做六维自然度复核。结构与六维代理都不得推翻有效人物声音、必要认识论限定或专业准确性。

## 新写时使用受约束非最优选择

当几个表达都准确时，不必总选最完整、最顺滑、最像范文的那个。优先选择符合说话者年龄、经历、关系距离、当前压力和注意顺序的表达。

允许人物说半句、改口、答偏一点、漏掉作者最想解释的部分。允许普通段落普通结束。允许叙述先看见眼前麻烦，再补背景。

以下内容始终取最准确解：事实、数字、时间、空间、因果、技术术语、医疗与安全信息、人物知识、物品持有和关系阶段。不要故意使用怪词、错字、病句或无法恢复的跳跃。

## 改稿时锁住正文身份

改动前列出不可改变项：

1. 事件、选择、场景顺序、因果和结尾接口。
2. 人物知道什么、与谁处在什么关系、能看见什么。
3. 时间、地点、物品、数字、专业语义和证据强度。
4. 已经成立的幽默、停顿、反复、意象和人物口吻。

改动若触及任一项，停止自然度清理，转回事实或结构审查。

## 执行六维审计

六维之前先做认知结构层与场景级审计：

1. 完整的“观察—枚举—排除—最低结论”只留给真正改变风险、关系、资源或行动的节点；其余按压缩、延迟、中断或行为化呈现。
2. 认识论限制语处理的是成簇和重复翻译，不是词本身；删后造成过度断言就撤销。
3. 对白可以准确但不必当场完整。允许合并回答、搁置、延迟纠正和“回头查证”，关键术语与证据等级仍取最准确解。
4. 动作应有身体、关系或生活功能，不必为每个论证节点伴奏。
5. 章末优先保住必要接口和一处有效余音，不同时总结所有主题、意象、证据与关系意义。
6. 每场核对事件冻结、认知上限和未决残留；残留来自人物没能看全、想全或当场结算，不是固定悬念钩子。
7. 关系对白核对双方即时议程和关系状态认知是否被作者强行同步；关键交接可完成，人物理解不必同时完成。
8. 生活动作核对其对注意、节奏、选择或后续状态的真实影响；纯质感可以存在，但不能成为全章唯一生活层。
9. 先标出全章`PRIMARY_FINDING`与范围，再决定单点动作。同一物件、想法、关系判断或结尾意义若跨三处以上反复承担同一功能，登记`DISTRIBUTED_VOICE / NEXT_AUTHOR_HANDOFF`，锁定该声线并停止同轮局部清洗；不得另挑弱相关单句冒充主病灶已经改善。
10. 比较叙事功能而不只比较字词。同一场景若多次以不同物件、动作或说话人重新完成“重置现场—再次尝试／说明—重新核验—局部收束”，登记`FUNCTIONAL_MICRO_LOOP`；逐次问它是否真的改变行动、风险、关系、知识或资源。没有新增后效的回合不能靠换词冒充新推进。
11. 任何`PATTERN_BOUNDED_REVISION`在改后冷读前必须把冻结基线与候选同时交给脚本比较：`python scripts/audit_prose.py <候选> --mode fiction --structure --baseline <基线> --target-finding-type functional_micro_loop_candidate`。目标代理数量未下降时固定登记`PRIMARY_FINDING_UNRESOLVED`；若候选同时缩短字符或段落，追加`COMPRESSION_INDUCED_EXPOSITIONAL_MONOCULTURE_RISK`，检查是否删掉生活纹理却保留说明骨架。代理数量下降也只写`TARGET_PROXY_REDUCED_REQUIRES_HUMAN_REVIEW`，不得机械宣称改善。

章节分段生成时，先逐段核对硬事实，再把机械装配后的全文作为唯一审计对象检查接缝：删除下半章的重开场／前情复述，避免上半章伪章末，核对时间、位置、持有、知识、说话权和未完成动作是否连续。详细处置见`references/split-chapter-seam.md`；接缝修正只能是`BOUNDED_REPHRASE`，不得借机改写两半结构。

详细处置见 `references/cognitive-structure.md`和`references/scene-level-audit.md`。压缩、延迟、中断与行为化均登记为 `BOUNDED_REPHRASE` 子类型，不改变现有顶层动作枚举。

依次检查：

1. 用词是否总是安全、概括、像标准答案。
2. 句长、停顿和句法是否长时间同速同模。
3. 段落是否依赖模板过渡、完整论证和段尾点题。
4. 作者高频词、连接词和惯用隐喻是否跨人物复现。
5. 不同人物是否被统一润色成同一种声音。
6. 不同场景是否都被同一种精致、沉静或意味深长的声调覆盖。

先运行 `python scripts/check_human_writing.py <文本路径>`和`python scripts/audit_prose.py <文本路径> --mode fiction --structure`获取表层、认知结构与部分场景级定位提醒；脚本只发现形状，不自动清理。活动v3脚本额外定位相邻段落长重合、异常空白装配槽、回到文本时出现的未建立引文、叙述层否定证明簇、背景声与前景停顿重复对齐，以及对白／叙述共享句法签名。这些结果全部是`review_flag`，须先排除合法复沓、版式留白、科研／对象层术语、关系承重非事件与人物稳定声口。脚本仍抓不到物件功能、双方议程、真实生活后效、引文事实真伪和跨场闭合，必须继续人工执行`scene-level-audit.md`。逐项回到上下文决定 `KEEP / DELETE_TAIL / DELAY_OR_DISTRIBUTE_MEANING / BOUNDED_REPHRASE / NEXT_AUTHOR_HANDOFF / REVIEW_FLAG`。不要按命中数量给正文打总分。

若提纲或任务功能本身包含分类、定义、证据排除或规则语言，先建立`natural_prose_audit_exemptions_v1` JSON，以源文件路径绑定每个对象层行区间、适用finding类型和人工理由，再使用`--exemptions <清单.json>`。该清单只抑制完整落在声明区间内的对应提醒，不能豁免整篇文本、不能覆盖融合接缝与事实错误，也不承担文件身份结论；需要严格身份绑定时，应由调用环境另行记录源稿与豁免清单的可信哈希。带`--baseline`的比较不得复用同一豁免清单，基线和候选必须分别审计。

## 有界改写

每个可见文本改动先回答两个问题：没有检测器时是否仍会改；该改动是否直接处理本轮主病灶。任一答案为否，不执行。若已登记`NEXT_AUTHOR_HANDOFF`，不得用同轮次要单点改动生成“自然度修订”版本；只能真正进入现行作者门，或保持正文不变并标记`PRIMARY_FINDING_UNRESOLVED`。若独立冷读把病灶锁定在一个连续区域，检测分段与该区域及既有作者／轮次边界相互吻合，而且用户明确要求有界修正，可执行一次`BOUNDED_REGION_REAUTHOR`：以源稿SHA、精确UTF-8起止锚点和区域外锁定字节SHA限定作者级重写。它仍是作者级处理，不得拆成多处局部润色；锁定区域任何字节变化都使本轮失败关闭。

模式性有界修改不能只检查候选本身。必须比较基线与候选的主病灶代理、字符数、段落数和人工场景功能：若目标微循环仍在，而课堂噪声、生活动作、人物打断或物件后效被大量压缩，禁止以“更紧凑”放行；先判断这些被删内容是否原本承担外部节奏压力。只有目标功能序列确实被重排或关闭、受保护声口仍在、区外锁定通过，才可由人工冷读考虑`IMPROVED`。

- 优先删除动作后的重复解释和普通段落后的漂亮尾句。
- 把跨人物复现的作者词还原为眼前动作、物件、口语反应或后果。
- 让节奏变化来自赶路、争执、犹豫、观察和任务压力，不来自数值配额。
- 保留人物合理的笨拙、误解、抢话、不完全回应和有功能反复。
- 保护人物偶发的自我拆台、偏心辩解和不够圆滑的声口；不能仅因它像“解释尾”就删除。
- “算账”“这笔账”“把账算清”等抽象隐喻应降频。场景真有价钱、预算、欠款、交易或账本时可保留本义。

禁止随机同义替换、故意错别字、强制句长差、固定段长、感官配额、主动被动句配额和为了“自然跳跃”打断因果。

## 冷读与交付

改完后暂时忘掉规则，回答：

- 能否辨认谁在说，他此刻要做什么。
- 每段是否带来动作、信息、关系、风险或理解变化。
- 哪句话换一个模型或人物也能原样使用。
- 哪处不够漂亮，却恰好属于这个人物。
- 文章是否已经在更早一句结束。

若用户只要成稿，只交成稿。若用户要求审计，简要列出有证据的位置、处理动作和保留理由。不得声称“通过朱雀”“不可检测”或给出无真实检测依据的成功率。

## 最终文本 Layer A

所有语义写作、作者级重修、有界改写与全文回归完成后，先冻结最终可见文本，再执行：

```bash
python scripts/unicode_layer_a.py inspect path/to/text.txt
python scripts/unicode_layer_a.py clean path/to/text.txt
```

clean默认写入新文件，不原地覆盖，并在输出中给出逐码点计数、移除总数和清理后复检。ZWJ、ZWNJ、variation selectors与emoji tag等可能承载语言或emoji语义的字符默认只报告并保留。若Layer A后发生任何语义改写，必须对新冻结全文重新inspect与clean。

Layer A只清理高置信不可见文本控制字符，不做Layer B统计重写，不处理C2PA、EXIF、PDF或图片元数据，不降低采样水印或AI率，也不证明人工写作。完整边界见`references/unicode-layer-a.md`。
