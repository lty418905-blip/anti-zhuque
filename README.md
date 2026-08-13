# Natural Prose Audit

一个可直接安装的 Codex Skill，用于生成、审计和有界修订中文文本，减少过度平滑、过度闭环、人物同声和认知流程复现等模型化规整特征。

仓库名保留为 `anti-zhuque`，但本项目**不复刻朱雀算法，不提供绕过保证，也不把检测分数当作作者身份结论**。它做的是可解释的自然度编辑。

## 适用范围

- 小说、故事、对白、叙事散文
- 中文长回答、评论、博客、公众号文章
- 科普、教程、行业解读与一般非虚构
- 已有文本的自然度审计和保真改稿
- 单一模型从初稿到终稿的分阶段工作流

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
用 $natural-prose-audit 写一篇 2500 字的中文人物特写。先完成完整初稿，再按单模型流程做自然度审计和有界修订。不得虚构采访和数据。
```

```text
用 $natural-prose-audit 审计这章小说。锁住情节、人物知识和结尾接口，只处理认知流程过度规整、对白闭环、动作伴奏和解释尾巴。
```

```text
用 $natural-prose-audit 修改这篇科普。保留全部事实与限定，减少逐项论证、模板过渡和段尾总结，不要为了口语化牺牲准确性。
```

## 单模型模式

Skill 把一次完整任务拆成两个认知阶段：

1. **生成阶段**只读取正向写作卡，不接触详细审计特征。
2. **审计阶段**冻结初稿事实和意图，再检查深层组织方式与表层规律。

这不是物理模型隔离，但能避免单一模型在第一稿里同时执行几十条反检测规则，写出另一种更僵硬的模板。

## 机械脚本

```powershell
python scripts\audit_prose.py example.txt --mode fiction --structure
python scripts\self_test.py
```

脚本输出 JSON 定位提醒。它不会修改输入，不联网，不计算真实困惑度，不返回检测通过结论。

## 方法边界

- 检测器会误报，且版本、阈值与训练数据不可见。
- 高度严谨、术语稳定或结构成熟的人类文本同样可能被判高风险。
- 自然度编辑不能证明文本由谁创作，也不能保证任何平台的分数。
- 事实准确、专业限定和人物一致性始终高于“降低痕迹”。

## 许可

本仓库采用 MIT License。方法参考与未复制内容的边界见 [`references/methodology.md`](references/methodology.md)。
