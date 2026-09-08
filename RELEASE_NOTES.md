# v2026.09.08：修复中文下一词预测错配

旧版直接复用了官方下一词模型中的词编号，但雾凇词典的编号已经不同，导致预测关系可能指向无关词语。本版根据词文本重新映射编号并重排分组，保留 36,659 条预测关系和原有权重；3,341 条包含词典外词语的关系被剔除。

- `zh_cn.cngm` 已与当前 888,485 词的 `zh_cn.clex` 正确绑定。
- 新增完整词语对应关系验证、绑定哈希报告和回归测试，阻止编号错配文件再次发布。
- 拼音候选表、词典、Emoji、BPE 词表和神经模型内容保持不变。
- 仍使用社区语言代码 `zh_cn`；请在 Clink 中更新该社区中文包至本版本。

本版已完成离线验证和自动构建验证，实际 iPhone 输入体验仍需用户验证。此修复不等于移植 Rime 引擎，也不声称解决所有连续输入或候选排序问题。

词库来自 [iDvel/rime-ice](https://github.com/iDvel/rime-ice)，预测数据来自 [anti-ltd/clink-language-packs](https://github.com/anti-ltd/clink-language-packs)。固定版本、修改说明和许可证见仓库的 `ATTRIBUTION.md`、`source/upstreams.json` 与 `LICENSES/`。
