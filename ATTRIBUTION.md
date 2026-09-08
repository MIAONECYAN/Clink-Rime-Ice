# 来源、修改与许可证

## 雾凇拼音

- 上游：<https://github.com/iDvel/rime-ice>
- 固定 commit：`fbb516b2786e4d5444383706d13c31c2e4d10c08`
- 上游版本日期：2026-08-31
- 上游许可证：GNU GPL v3；完整文本见 `LICENSE`。

本仓库从以下文件生成 `Lexicons/zh_cn.cime` 与 `Lexicons/zh_cn.clex`：

- `cn_dicts/8105.dict.yaml`
- `cn_dicts/base.dict.yaml`
- `cn_dicts/ext.dict.yaml`
- `cn_dicts/others.dict.yaml`

`Lexicons/zh_cn.emoji.json` 由 `others/emoji-map.txt` 转换而来。主要修改是：合并重复词条、保留最高权重、移除拼音音节间空格、将相同无空格拼音的候选合并并截取前 16 项、生成 CLEX v1 二进制结构、将 Emoji 反向映射转换为 Clink aliases JSON。

未使用 `cn_dicts/tencent.dict.yaml`。该文件没有逐词拼音，Rime 在部署时借助自身字表和词典编译器推导；脱离 Rime 引擎的批量转写无法可靠处理多音字。

雾凇词库自身汇集的字表、词表和数据来源（包括通用规范汉字表、华宇野风词库、THUOCL、简化字八股文等）以雾凇仓库的 `others/docs/Credits.md` 为准，相关第三方许可继续适用。

## Clink language packs

- 上游：<https://github.com/anti-ltd/clink-language-packs>
- 固定 commit：`3a6a666bfff0e85466ea40acdca0137808167b50`
- 上游版本：Clink 1.4.6 language assets

以下独立资产从该 commit 保留原始内容，发布时前缀由 `zh` 改为 `zh_cn`：

- `Lexicons/zh.bpevocab`
- `Lexicons/zh.mlmodelc/**`

神经模型与 BPE 词表保持为同一次官方训练的匹配组合，没有重新训练。`zh_cn.cngm` 则由上游 `zh.cngm` 与其配套的 `zh.clex` 解码，再按词文本映射到新词典：保留原权重、剔除词典外关系、重排词编号分组。此修改未重新训练模型，不能增加来源中不存在的预测关系。完整源文件及目标文件哈希见 `PREDICTION_REPORT.json`。许可证与数据来源声明见 `LICENSES/CLINK-LEXICONS-LICENSE.txt`；Clink 社区材料许可证见 `LICENSES/CLINK-COMMUNITY-ASSETS-LICENSE.md`。

## 本仓库

`scripts/`、`tests/` 和发布工作流是为本次转换编写的实现。它们随 Rime 衍生包统一以 GPL-3.0 发布。仓库与 Clink、Anti Limited、雾凇拼音维护者均无官方隶属或背书关系。
