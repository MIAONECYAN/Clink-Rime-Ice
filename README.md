# Clink 雾凇拼音中文语言包

把 [雾凇拼音（rime-ice）](https://github.com/iDvel/rime-ice) 的带注音简体中文词库、拼音和词频转换成 Clink 可安装的社区语言包。

发布资产包含拼音候选表 `zh_cn.cime`，以及用于词典、补全和纠错的 `zh_cn.clex`。例如 `weixin` 的第一候选是“微信”，并包含“语言包”“小红书”“哔哩哔哩”等原 Clink 中文表缺失的词。

## v2026.09.08 修复

旧版错误地把官方 `.cngm` 预测模型直接配在新的雾凇 `.clex` 词典上。预测模型使用词典编号，因此这会让预测关系指向无关的词。新版按词文本重建编号和分组，保留 36,659 条预测关系及原权重，丢弃 3,341 条包含词典外词语的关系。词典、拼音表、Emoji 和 BPE/神经模型内容不变。

已经安装旧版的用户应更新到 `v2026.09.08`，确认实际使用的是社区中文包 `zh_cn`。本版通过文件结构、完整词语对应关系、回归测试和发布文件哈希验证；尚未在用户的 iPhone 上验证实际输入效果。

## 安装

1. 在 Clink 打开 **General → Repositories**。
2. 添加仓库：`MIAONECYAN/Clink-Rime-Ice`。
3. 回到 **Languages**，选择该仓库并安装“中文（中国大陆）”。

社区包使用 `zh_cn` 作为独立语言代码，因此可以与 Clink 官方的 `zh` 中文包同时存在。如果使用同一个 `zh` 代码，已经安装官方中文的设备会在 **Add language** 中把它隐藏。

Clink 只接受公开 GitHub Release，并校验 `manifest.json` 中每个文件的大小与 SHA-256。

## 包含内容

- `zh_cn.cime`：雾凇 `8105 + base + ext + others` 的显式拼音词条，按词频排序，每个读音最多 16 个候选。
- `zh_cn.clex`：同一批词条编译出的 CLEX v1 词典。
- `zh_cn.emoji.json`：由雾凇手工维护的 Emoji 映射转换。
- `zh_cn.cngm`：根据官方中文下一词模型，按当前雾凇词典重映射词编号、删除词典外关系并重新排序。绑定哈希和保留数量见 `PREDICTION_REPORT.json`。
- `zh_cn.bpevocab + zh_cn.mlmodelc`：Clink 官方匹配的中文神经模型与词表，原样保留，仅改文件前缀。

详细来源、固定版本和许可证见 [ATTRIBUTION.md](ATTRIBUTION.md)。

## “完整移植”的边界

本包移植带明确注音的词库数据，不包含 Rime 引擎、Lua 过滤器、用户词典和方案规则。官方 `.cime` 构建器每个读音保留最多 16 个候选；应用可以在该表之上实现连续输入与组句，不能由文件格式推断 Clink 不具备这些能力。实际连续输入、学习和上下文排序由所用 Clink 版本决定。

雾凇的 `tencent.dict.yaml` 没有逐词拼音，依靠 Rime 编译器按字表自动注音。直接用通用拼音库批量推断会制造大量多音字错误，因此本包没有把这部分伪装成可靠数据；已经完整纳入所有带明确拼音的中文主词库。

## 构建与验证

将固定版本的 rime-ice 放到 `vendor/rime-ice`，Clink 官方语言包放到 `vendor/clink-language-packs`（commit 见 `source/upstreams.json`）。在已有模型资产的仓库中运行：

```bash
python3 scripts/build.py --rime-ice vendor/rime-ice
python3 scripts/remap_cngm.py --source-lexicons vendor/clink-language-packs/Lexicons
python3 scripts/validate.py --source-lexicons vendor/clink-language-packs/Lexicons
python3 -B -m unittest discover -s tests -v
```

在 main 分支更新 `source/release-version.txt` 为一个未发布版本，会触发完整重建、预测映射、验证及草稿发布。全部文件上传完成后才公开 Release。也可给验证过的生成物创建新标签：

```bash
git tag vYYYY.MM.DD
git push origin vYYYY.MM.DD
```

## 更新原则

- `source/upstreams.json` 固定两个上游 commit，避免不可复现的“跟随 main”。
- 更新雾凇版本后必须重新构建并运行验证。
- 每次更新 `.clex` 都必须按词文本重新映射 `.cngm`；禁止直接复制其他词典的编号模型。
- 不对无显式拼音的大词库做猜测式注音。
- 不混用不同训练批次的神经模型和 BPE 词表。

## 许可证

Rime 衍生词库与本仓库转换代码按 GPL-3.0 提供；从 Clink 官方仓库原样保留的独立模型资产继续适用其原许可证。第三方来源不因本仓库而改变许可。
