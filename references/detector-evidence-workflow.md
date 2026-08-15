# 检测证据、主病灶与改后验证

本文件用于任何第三方AIGC检测报告、前后分数比较、分段定位或“微小改动后反向恶化”的场景。报告只提供外部定位证据，不证明作者身份，不解释私有算法，也不自动产生修订目标。

## 1. 先做盲态全文冷读

阅读检测分数和高风险区以前，完整通读实际待审文本并固定：

- `PRIMARY_FINDING`：本轮最影响阅读、声音或表达功能的单一主病灶。
- `FINDING_SCOPE=LOCALIZED_SURFACE|DISTRIBUTED_VOICE|STRUCTURAL|UNKNOWN`。
- `FINDING_RANGE`：精确连续区间、跨全文位置组或结构层级。
- `VOICE_PROTECTION`：不够漂亮但属于具体作者、人物、关系或场景的表达。
- `DETECTOR_INDEPENDENT_REASON`：假设没有任何报告，为什么仍应修改；没有理由则不改。

只允许一个主病灶。其他问题作为次要观察，不得抢走本轮修订目标。

## 2. 固定并核验检测对象

尽可能登记实际提交输入、可见文本、格式、报告、检测时间、报告字符数、分段数和逐段边界。无法取得的字段明确写`NOT_AVAILABLE`。

将可比性分为：

- `PASS`：前后输入、可见文本、格式和操作条件足以比较。
- `FAILED`：确认输入或解析条件不同。
- `UNRESOLVED`：缺少旧输入、报告字符合计不符、格式变化或检测端版本未知。

可见文本相同不等于提交字节、文件解析和检测条件相同。可比性不是`PASS`时，不得宣称某一句导致分数变化。

## 3. 使用报告的最低证据等级

- `D0_NO_REPORT`：只有文学冷读。
- `D1_SINGLE_RUN`：单次报告只能标记复看优先级，不能单独触发改文。
- `D2_REPEATED_SAME_INPUT`：同一输入与格式的重复运行；稳定落在同一区域的信号可提高复看优先级。
- `D3_CONTROLLED_AB`：A/B输入与唯一差分、格式和运行条件均闭合，并有足够重复运行估计波动。

即使达到D3，报告也不能证明作者身份，不能替代文学理由，不能承诺下一次结果。

## 4. 把公开分段限定在对应区间

报告给出分段时，将每段首尾定位回源稿，记录精确文本边界；能绑定原始字节时再记录UTF-8字节区间。然后核对：

1. 盲态主病灶是否与该分段重合。
2. 分段是否只覆盖一个连续区域，还是切穿多个场景、章节或生成轮次。
3. 低风险区是否存在独立文学硬伤；没有时默认锁定，不因接缝便利重写。

分段报告只能说明该次报告如何切分该次输入。不得把一个分段的结论推广到全文、另一篇文本或另一轮生成。

## 5. 选择修订级别

### LOCALIZED_SURFACE

同时满足以下条件才可有界修订：

- 问题位于一个连续局部；
- 没有同一声线或功能跨多处复现；
- 修改后不需要第二处连动；
- 不损害`VOICE_PROTECTION`；
- 有检测器无关的文学理由；
- 实际差分直接命中`PRIMARY_FINDING`。

使用`KEEP | DELETE_TAIL | BOUNDED_REPHRASE | REVIEW_FLAG`。有界意味着改完这一处即可合上文档。

### DISTRIBUTED_VOICE

同一语调、物件用途、解释程序、段落闭合或判断功能跨多个位置复现时：

1. 停止同轮局部清洗。
2. 不挑一两句弱相关文字充当替代目标。
3. 不把机械纠错、格式修复或次要删句命名为自然度改善。
4. 转为`AUTHOR_LEVEL_REWRITE`，让同一作者级过程重建全文或完整失败区域的注意顺序、材料选择与声音；若未获授权，保持正文不变并登记`PRIMARY_FINDING_UNRESOLVED`。

作者级重写不是多点润色的集合。它仍须冻结事实、因果、立场、人物知识、必要结构和交付接口。

### STRUCTURAL 或 UNKNOWN

结构性问题先回到大纲、材料组织或论证设计；证据不足则保留。两者都不得用检测分数强行转为局部改句。

## 6. 防止修订反向恶化

修改前后逐项回答：

- 差分是否直接处理`PRIMARY_FINDING`。
- 是否删掉了作者或人物独有的笨拙、自嘲、偏心、停顿或有效反复。
- 是否把准确限定改成过度断言。
- 是否用另一套整齐话术覆盖原来的整齐话术。
- 是否让相邻段落承担重复功能，或把局部问题扩散到全文。

若只处理次要问题，结论必须是`LOCAL_CHANGE_ONLY`。若反而削弱声音、事实或阅读节奏，撤销该差分，不继续叠加删句。

## 7. 改后重新冻结与验证

修订后把完整文本视为新对象，而不是只复看改句：

1. 重新冻结全文身份和实际差分。
2. 回归事实、数字、来源、因果、立场、人物或说话者知识、叙事视角、口吻与结尾接口。
3. 通读改动前后至少一个完整上下文单元，再冷读全文，确认没有接缝、声线或结构反噬。
4. 核对`TARGET_ALIGNMENT`：差分是否真实命中主病灶。
5. 只有用户授权时才进行新检测；新报告继续按本文件重新登记，不继承旧分数结论。

允许的文学结论：

- `IMPROVED`：主病灶被实际处理，冷读确认声音与功能更好。
- `LOCAL_CHANGE_ONLY`：完成合法局部改动，但未处理分布式或结构性主病灶。
- `UNCHANGED`：审计后决定保留。
- `PRIMARY_FINDING_UNRESOLVED`：需要作者级处理或证据不足。
- `REGRESSION`：改动削弱事实、因果、声音或阅读功能，应撤销或重新设计。

以上结论都不是检测器PASS，也不能换算为AI率。

## 8. 最小记录

```text
SOURCE_TEXT=<identity>
BLIND_FULL_READ=true|false
PRIMARY_FINDING=<single finding>
FINDING_SCOPE=<enum>
FINDING_RANGE=<range>
VOICE_PROTECTION=<items>
DETECTOR_EVIDENCE_LEVEL=D0|D1|D2|D3
INPUT_COMPARABILITY=PASS|FAILED|UNRESOLVED
DETECTOR_INDEPENDENT_REASON=<reason or NONE>
ACTION=<action>
TARGET_ALIGNMENT=PASS|FAIL|NOT_APPLICABLE
FULL_TEXT_REGRESSION_CHECK=PASS|FAIL|NOT_EXECUTED
EDITORIAL_OUTCOME=<enum>
UNKNOWN_CAUSES=<explicit unknowns>
```
