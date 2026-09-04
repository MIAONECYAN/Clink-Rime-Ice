# Clink 雾凇拼音中文语言包

把 [雾凇拼音（rime-ice）](https://github.com/iDvel/rime-ice) 的简体中文词库、拼音和词频转换成 Clink 可安装的完整社区语言包。

这不是普通的“导入词表”：发布资产包含真正控制拼音候选的 `zh.cime`，以及用于词典、补全和纠错的 `zh.clex`。例如 `weixin` 的第一候选是“微信”，并包含“语言包”“小红书”“哔哩哔哩”等原 Clink 中文表缺失的词。

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
- `zh_cn.cngm`：Clink 官方中文下一词模型，原样保留，仅改文件前缀以匹配社区语言代码。
- `zh_cn.bpevocab + zh_cn.mlmodelc`：Clink 官方匹配的中文神经模型与词表，原样保留，仅改文件前缀。

详细来源、固定版本和许可证见 [ATTRIBUTION.md](ATTRIBUTION.md)。

## “完整移植”的边界

这是 **Clink 语言包格式所能表达的完整移植**，不是把 Rime 引擎嵌入 Clink。Clink 的 `.cime` 是静态“完整拼音 → 最多 16 个候选”表，无法承载 Rime 的动态组句、用户词典学习、Lua 过滤器、模糊音、双拼 algebra 和长句上下文排序。

雾凇的 `tencent.dict.yaml` 没有逐词拼音，依靠 Rime 编译器按字表自动注音。直接用通用拼音库批量推断会制造大量多音字错误，因此本包没有把这部分伪装成可靠数据；已经完整纳入所有带明确拼音的中文主词库。

## 构建与验证

将固定版本的 rime-ice 放到 `vendor/rime-ice`，然后运行：

```bash
python3 scripts/build.py --rime-ice vendor/rime-ice
python3 scripts/validate.py
```

创建版本标签后，GitHub Actions 会生成 Release manifest、计算哈希并发布全部资产：

```bash
git tag v2026.09.05
git push origin v2026.09.05
```

## 更新原则

- `source/upstreams.json` 固定两个上游 commit，避免不可复现的“跟随 main”。
- 更新雾凇版本后必须重新构建并运行验证。
- 不对无显式拼音的大词库做猜测式注音。
- 不混用不同训练批次的神经模型和 BPE 词表。

## 许可证

Rime 衍生词库与本仓库转换代码按 GPL-3.0 提供；从 Clink 官方仓库原样保留的独立模型资产继续适用其原许可证。第三方来源不因本仓库而改变许可。
