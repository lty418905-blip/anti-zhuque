# Anti-Zhuque Writing Skills

这个仓库提供两项可独立安装的通用Codex写作Skill。它们帮助模型减少机械化表达、保护事实与人物声音，并让生活事件真正参与场景因果。检测器只能作为提醒器；任何Skill都不能证明作者身份，也不能保证通过朱雀或其他AIGC检测。

## 1. Natural Prose Audit

仓库根目录是`natural-prose-audit`的最新通用版。它整合Human Writing写作规则，并增加：

- 中文虚构与非虚构的分文体写作、冷读与有界修订；
- 认知流程、解释尾巴、对白闭环、动作配对、功能微循环与分布式声线审计；
- 多段生成和机械装配后的章节接缝检查；
- 基线与候选的目标代理比较，以及反向效果防护；
- 检测报告的可比性、UTF-8边界和区域级作者重写边界；
- 高置信不可见Unicode控制字符的Layer A检查与非覆盖式清理。

安装根Skill：

```powershell
git clone https://github.com/lty418905-blip/anti-zhuque.git "$env:CODEX_HOME\skills\natural-prose-audit"
```

重启Codex后使用`$natural-prose-audit`。

## 2. Scene Event Weaver

`scene-event-weaver/`是独立事件库Skill。装载它的Agent必须先读取当前文章、场景或批准提纲，建立任务专属`scene-profile.json`，然后生成新的`scene-event-library.jsonl`。内置24条内容只是机制种子，不能直接写入正文，也不是事实源。

它提供：

- 单场景6—12条、章节或多场景12—30条专属候选生成流程；
- 每个候选至少两个当前文本锚点；
- 默认0—5个事件选择，零个合法；
- 单根事件的2—6步因果链、状态握手、中止点、结算和后效；
- 场景锚点、重复ID、选择上限、链结构和后效的机械校验；
- 虚构与叙事非虚构的事实边界，以及科研、医学、法律和关系升级的返回上层规则。

安装第二个Skill时，把仓库中的`scene-event-weaver/`目录复制到：

```text
%CODEX_HOME%\skills\scene-event-weaver\
```

该目录必须直接包含自己的`SKILL.md`。重启Codex后使用`$scene-event-weaver`。

## 验证

```powershell
python scripts\self_test.py
python scene-event-weaver\scripts\self_test.py
```

两个Skill的机械脚本都只提供待人工判断的代理提醒或结构检查，不会联网、修改输入或承诺检测结果。

## 许可

仓库采用MIT License。Human Writing来源、许可和方法边界见根Skill的`references/source-notes.md`及`LICENSE-human-writing`。
