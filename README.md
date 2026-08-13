# Natural Prose Audit

一个可直接安装的 Codex Skill。它把完整的 Human Writing 1.1.0 通用中文写作能力作为底座，再增加初稿后的认知结构审计与保真修订流程。

仓库名保留为 `anti-zhuque`，但本项目**不复刻朱雀算法，不提供绕过保证，也不把检测分数当作作者身份结论**。它做的是可解释的中文写作和自然度编辑。

## 完整能力范围

嵌入的 Human Writing 内容没有为公开版做功能删减，包括：

- 知乎回答、论坛长帖、公众号、博客、评论、人物、历史与行业解读
- 真人、新闻、产品、数据、评测、教程、商业与用户亲历的事实边界
- 小说、故事、对白、叙事视角、人物选择、场景与设定
- 短文、个人叙事、口播、演讲、剧本、诗歌等形式适配
- 完整的七遍修订流程、硬禁用项与原版机械检查脚本
- 材料不足时研究、追问或缩短，不用重复解释凑篇幅

本仓库额外加入：

- 认知流程重复审计
- 认识论限制语簇审计
- 单元测试式问答审计
- 动作与论证一一配对审计
- 结尾过度闭合审计
- 单模型“先生成、后审计”的上下文隔离流程

## 安装

在 Codex 中使用 `skill-installer` 安装这个 GitHub 仓库，或手动克隆到个人 Skills 目录：

```powershell
git clone https://github.com/lty418905-blip/anti-zhuque.git "$env:CODEX_HOME\skills\natural-prose-audit"
```

重启 Codex 后即可通过 `$natural-prose-audit` 调用。

也可以先克隆到任意目录，再把仓库根目录复制为：

```text
%CODEX_HOME%\skills\natural-prose-audit\
```

根目录必须直接包含 `SKILL.md`。

## 使用示例

```text
用 $natural-prose-audit 写一篇 2500 字的中文人物特写。使用完整 Human Writing 流程，先完成完整初稿，再做自然度审计和有界修订。不得虚构采访和数据。
```

```text
用 $natural-prose-audit 审计这章小说。锁住情节、人物知识和结尾接口，执行 Human Writing 全量改稿检查，再处理认知流程过度规整、对白闭环、动作伴奏和解释尾巴。
```

```text
用 $natural-prose-audit 修改这篇科普。保留全部事实与限定，减少逐项论证、模板过渡和段尾总结，不要为了口语化牺牲准确性。
```

## 单模型模式

Skill 把一次完整任务拆成两个认知阶段：

1. **生成阶段**读取完整 Human Writing 正向规则、适用文体参考和一张简短生成卡，不接触详细修订与深层审计特征。
2. **审计阶段**冻结初稿事实和意图，再加载 Human Writing 修订流程与认知结构审计。

这不是物理模型隔离，但能避免单一模型在第一稿里同时执行几十条审稿规则，写出另一种更僵硬的模板。

## 机械脚本

Human Writing 原版检查：

```powershell
python references\human-writing\scripts\check_prose.py example.txt
```

认知结构与自然度代理检查：

```powershell
python scripts\audit_prose.py example.txt --mode fiction --structure
python scripts\self_test.py
```

脚本只定位待人工判断的形状。它们不会修改输入，不联网，不计算真实困惑度，不返回检测通过结论。

## 目录说明

- `references/human-writing/`：完整、保持原目录关系的 Human Writing 1.1.0，含入口、全部参考、脚本、版本与 MIT 许可证。
- `references/generation-card.md`：单模型首稿阶段的简短正向补充。
- `references/deep-audit.md`：初稿完成后才读取的深层审计流程。
- `references/fiction.md`、`references/nonfiction.md`：本仓库新增的深层审计分文体参考。
- `scripts/audit_prose.py`：只读定位认知结构和表层代理。
- `scripts/self_test.py`：验证两套检查器的基本边界。

## 方法边界

- 检测器会误报，且版本、阈值与训练数据不可见。
- 高度严谨、术语稳定或结构成熟的人类文本同样可能被判高风险。
- 自然度编辑不能证明文本由谁创作，也不能保证任何平台的分数。
- 事实准确、专业限定和人物一致性始终高于“降低痕迹”。

## 许可

本仓库采用 MIT License。嵌入的 Human Writing 1.1.0 也采用 MIT License，其原始许可保留在 [`references/human-writing/LICENSE`](references/human-writing/LICENSE)。来源与未复制内容的边界见 [`references/methodology.md`](references/methodology.md)。
