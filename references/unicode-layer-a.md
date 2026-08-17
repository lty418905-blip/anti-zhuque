# 保守 Unicode Layer A 文本卫生

本步骤只处理UTF-8纯文本中高置信、没有正文语义的不可见控制字符。脚本`scripts/unicode_layer_a.py`是本Skill的原创实现，以MIT许可证发布；不复制来源不明的清理代码。

## 边界

默认可移除：

- 非文件首位的`U+FEFF`；
- `U+200B ZERO WIDTH SPACE`；
- `U+2060 WORD JOINER`；
- `U+00AD SOFT HYPHEN`；
- bidi嵌入、覆盖、隔离、方向标记和已弃用方向格式控制字符。

默认只报告并保留：

- `U+200C ZERO WIDTH NON-JOINER`；
- `U+200D ZERO WIDTH JOINER`；
- variation selectors；
- emoji tag characters；
- combining grapheme joiner与Mongolian vowel separator。

后两组字符可能参与语言塑形、字形选择或emoji序列，不能只因不可见就删除。本版不提供“高风险模式”开关；如确需处理，先由用户确认具体码点和语言语境，再另建明确规则。

Layer A不会改写可见语言，不处理统计或采样水印，不进行Layer B重写，不处理C2PA、EXIF、XMP、PDF、图片或容器元数据，不调用网络或模型，也不降低或证明任何AI率。

## 顺序

1. 完成所有语义写作与自然度修订。
2. 冻结最终可见文本。
3. 先检查：

```bash
python scripts/unicode_layer_a.py inspect path/to/text.txt
```

4. 再清理到新文件：

```bash
python scripts/unicode_layer_a.py clean path/to/text.txt
```

默认输出为同目录的`<stem>.layer-a-clean<suffix>`。源文件不改；目标已存在时失败关闭。只有明确需要替换已有输出时才加`--overwrite-output`，仍禁止输出路径与源路径相同。

5. 检查JSON中的逐码点计数、`removed_total`和`post_clean_scan.high_confidence_total=0`。
6. 如清理后又发生任何语义重写，丢弃旧清理结果，在新冻结全文上重新执行inspect与clean。

脚本按原始UTF-8字节计算SHA-256，不规范化换行、引号、Unicode组合形式或可见空白。
