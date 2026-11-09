# 1955 开国将帅录

<div align="center">

**一个离线查询中国人民解放军首次授衔（1955 年）开国将帅的安卓应用**

`Android` · `Java` · `WebView` · `纯前端 UI` · `内置离线数据`

[![Platform](https://img.shields.io/badge/Platform-Android-3ddc84?logo=android&logoColor=white)]()
[![Language](https://img.shields.io/badge/Language-Java-orange?logo=openjdk&logoColor=white)]()
[![Min SDK](https://img.shields.io/badge/minSdk-21-brightgreen)]()
[![Target SDK](https://img.shields.io/badge/targetSdk-34-blue)]()
[![Version](https://img.shields.io/badge/version-1.0-informational)]()
[![Entries](https://img.shields.io/badge/%E5%BD%95%E5%85%A5%E5%B0%86%E5%B8%85-1614-red)]()

</div>

---

## 简介

本项目是一个**完全离线**的安卓应用，收录 **1955 年中国人民解放军首次实行军衔制**时授予及此后至 1965 年军衔制取消前晋升、补授的开国将帅，共 **1614 位**，覆盖：

| 衔级 | 人数 | 说明 |
| :---: | :---: | :--- |
| 元帅 | 10 | 朱德、彭德怀、林彪、刘伯承、贺龙、陈毅、罗荣桓、徐向前、聂荣臻、叶剑英 |
| 大将 | 10 | 粟裕、徐海东、黄克诚、陈赓、谭政、萧劲光、张云逸、罗瑞卿、王树声、许光达 |
| 上将 | 57 | 含 1956 年补授王建安、1958 年补授李聚奎 |
| 中将 | 177 | 含 1956 年补授聂鹤亭、1958 年补授贺诚 |
| 少将 | 1360 | 1955 年首批 798 人，后陆续晋升、补授累计 1360 人 |

应用采用 **WebView 壳 + 内置数据** 架构：界面与交互由纯 HTML/CSS/JS 实现，数据以静态 `data.js` 打包进 Assets，**无需网络、无第三方 SDK**，安装即可离线使用。

## 功能特性

- 🔍 **多条件搜索** — 支持按姓名、籍贯、生平等关键词实时模糊检索。
- 🗺️ **按省份筛选** — 已为全部元帅、大将、上将、中将及 1054 位少将标注籍贯省份，可按省一键筛选（如"将军县"红安、兴国、平江等）。
- ⛰️ **按革命老区（山头）筛选** — 已按主要建军根据地 / 方面军序列归类（井冈山与中央苏区、鄂豫皖与川陕、湘鄂西与湘鄂川黔、陕北与陕甘、百色与左右江、南方游击与新四军、琼崖、东北抗联、宁都起义、起义将领等），可查看各大"山头"代表。
- 📇 **详情页** — 底部弹层展示生平简介、历史功绩、籍贯、授衔时间、所属革命根据地等。
- 📖 **授衔档案** — 内置"授衔背景 / 各衔级规模 / 将军县分布 / 让衔佳话 / 女将军与外籍将军 / 校官说明"等史料专页。
- 🏷️ **按授衔年份分组** — 少将名录按 1955/1956/1958/1961/1964 等授晋年份分组展示。
- 📴 **完全离线** — 数据内置，无任何联网请求。

> 注：校官（大校/上校等）数量以万计且无完整公开权威名单，故不设总名录，仅收录肖锋、尹先炳等部分 1955 年授大校的知名人物生平供参考。

## 数据覆盖

| 衔级 | 总人数 | 有生平简介 | 有籍贯省份 | 已归类革命老区 |
| :---: | :---: | :---: | :---: | :---: |
| 元帅 | 10 | 10 | 10 | 10 |
| 大将 | 10 | 10 | 10 | 10 |
| 上将 | 57 | 57 | 57 | 57 |
| 中将 | 177 | 177 | 177 | 177 |
| 少将 | 1360 | 1360 | 1054 | 274 |
| **合计** | **1614** | **1614** | **1308** | **528** |

## 目录结构

```
1955开国将帅录-源码/
├── app/                          # 安卓工程（WebView 壳）
│   ├── AndroidManifest.xml       # 清单：minSdk 21 / targetSdk 34
│   ├── src/com/workbuddy/kaijy/
│   │   └── MainActivity.java     # WebView 宿主，加载 assets/index.html
│   ├── assets/
│   │   ├── index.html            # 全部界面与交互（纯 HTML/CSS/JS）
│   │   └── data.js               # 由 gen/gen_data.py 生成的离线数据
│   └── res/                      # 应用图标与字符串资源
├── gen/                          # 数据生成脚本（Python）
│   ├── bios1.py ~ bios6.py       # 手写生平数据（元帅/大将/上将/中将/少将）
│   ├── gen_data.py               # 数据合并主脚本 → 生成 app/assets/data.js
│   ├── scrape_baike_seq.py       # 百度百科生平抓取脚本（Playwright）
│   └── fetch_baike*.py / fetch_*.py  # 各来源抓取脚本
├── data/                         # 抓取与整理的原始数据缓存（JSON）
├── build_apk.sh                  # 一键构建签名 APK 脚本
└── README.md
```

## 快速开始

### 构建 APK

依赖：**JDK 17+**、**Android SDK**（`cmdline-tools` + `platforms;android-34` + `build-tools;34.0.0`），并设置环境变量 `ANDROID_HOME` 指向 SDK 目录。

```bash
export ANDROID_HOME=/opt/android-sdk
bash build_apk.sh
# 输出：1955开国将帅录.apk（已 zipalign + apksigner 签名）
```

`build_apk.sh` 会依次执行：生成最新数据 → `aapt2` 编译/链接资源 → `javac` 编译 → `d8` 转 dex → 打包 → `zipalign` 对齐 → `apksigner` 签名（自动生成调试密钥）。

### 重新生成数据

依赖：**Python 3.10+**（合并数据无需第三方库；在线抓取脚本需 `playwright`）。

```bash
cd gen
python3 gen_data.py   # 读取 bios*.py 与 data/*.json，生成 ../app/assets/data.js
```

## 直接修改内容

- **改界面 / 交互** → 编辑 `app/assets/index.html`
- **改某人的生平** → 编辑 `app/assets/data.js`（或改 `gen/` 中对应数据后重新生成）
- **改名单** → 编辑 `gen/gen_data.py`（名单解析段）后重新生成
- **改授衔档案** → 编辑 `gen/gen_data.py` 中的 `ABOUT` 常量后重新生成

## 数据来源

- **名单**：中红网《中国人民解放军开国将帅名录（组图）》（并交叉核对多个公开来源）。
- **生平**：主要摘编自百度百科相应词条，部分来自人民网、搜狗百科快照；元帅、大将、上将、中将及部分少将为按党史资料编写的简编生平，体例参照《中国人民解放军将帅名录》。
- **分类**：籍贯省份、革命根据地（山头）由脚本按生平关键词自动归类，并对元帅、大将、中将等进行了人工校正。

> ⚠️ **资料说明**：同名少将的词条摘要在个别情况下可能存在混同；个别早年史料可能与最新党史文献表述存在差异。深度查询请参考《中国人民解放军将帅名录》。

## 技术栈

| 层 | 技术 |
| :--- | :--- |
| 安卓壳 | Java `Activity` + `WebView`，minSdk 21 / targetSdk 34 |
| 前端 | 原生 HTML5 / CSS3 / JavaScript（无框架） |
| 数据 | 静态 `data.js`（JSON + 模板字符串），打包进 Assets |
| 数据生成 | Python 3.10+（`gen/gen_data.py`） |
| 构建 | aapt2 + javac + d8 + zipalign + apksigner |

## 相关链接

- [中国人民解放军军官服役条例（1955）](https://www.gov.cn/) — 1955 年 2 月 8 日第一届全国人大常委会第六次会议通过
- [中红网·开国将帅名录](http://www.crt.com.cn/) — 名单原始来源

## License

本项目为历史资料整理与学习参考用途，收录内容来源于公开史料。如有版权或内容问题，欢迎通过 Issue 反馈。

---

<div align="center">
小虫工作室@2026 · 致敬开国将帅
</div>
