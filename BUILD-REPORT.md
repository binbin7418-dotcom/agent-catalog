# 全结构化产品目录层 — 构建报告（2026-11-03 晚，本地文件，未部署、未改任何 listing）

## ① 收录数对账（全部实数）

| 口径 | 数 | 说明 |
|---|---|---|
| Gumroad 店铺页自报总数 | 56 | 店铺内嵌数据 search_results.total |
| 候选 slug 核查 | 67 | 来源：店铺分页窗口＋本地文案/记忆日志枚举＋n8n 批次表 |
| 活页验证在售 | **56** | 逐个产品页 data-page 解析 is_published=true，与店铺自报 56 **完全对上** |
| 未在售候选 | 11 | SubtitleFix 存在但已下架（is_published=false）；404 共 10：第八批未上架 5（Shikaku/Cryptogram/Queens/Binairo/Maze）、n8n 第三批今晚待上 3（Veterinary/Travel/Pest）、EPUBFix（已决定不卖）、ImageBatch（从未落地） |
| Payhip 在售 | 15 | 店铺页实拉全量：工具 5×$29＋n8n 第二批 10×$49 |
| Payhip 与 Gumroad 重复 | 15/15 | 5 个工具与 10 个第二批包在 Gumroad 均有同一产品，全部合并、双 buy_url 保留 |
| **合并后唯一产品** | **55** | 56 个 Gumroad listing 中 PitchReel 讲解/照片两 listing 合并为 1 个产品（8 个变体） |

与任务口径（55＝工具 35＋n8n 16＋PitchReel 2＋体检 1）的差异说明：口径算术实为 54，且与活页实数不符——现行真实结构是 **56 个 listing**：n8n 包 16（第一批 6＋第二批 10）、PitchReel 2、体检 1、其余数字产品 37。37 个里并非全是 $29：DateShift $9、MetaScrub $19、SKU Operations Copilot $19 各 1 个；另 SudokuPress 与 PuzzlePress 两个 Sudoku 产品同时在售。

类目分布（55 唯一产品）：n8n-automation-pack 16、puzzle-book-generator 7、pdf-document-tools 6、photo-image-tools 5、bank-file-converter 4、audio-video-tools 3、data-cleaning 3、csv-tools 2、print-book-generator 2、spreadsheet-repair / product-feed-tools / shopify-store-tools / print-tools / worksheet-generator / video-service / website-monitoring-service 各 1。

## ② 生成文件清单（~/workspace/agent-catalog/）

- `products-source.json` — 全量源数据（55 产品，含全文描述与来源口径）
- `build_catalog.py` — 生成脚本，从 products-source.json 重跑生成下列全部文件
- `catalog.json` — UCP Catalog 形状全量目录（price 以最小单位 amount＋currency；结账如实标 external_link）
- `products/<id>.jsonld.json` × 55 — 每品 schema.org Product（全文 description、sku、category、offers、hasMerchantReturnPolicy、additionalProperty 三项事实）
- `llms.txt`、`agents.md` — 全店 agent 指引（卖家、购买方式=跳转 buy_url 人工结账、退款与支持）
- `.well-known/ucp` — UCP profile 声明（catalog 能力＋结账走外链的如实声明）
- `sitemap.xml` — 计划基址 https://binbin7418-dotcom.github.io/agent-catalog/ 占位，部署时 rebase
- `index.html` — 人类可读目录预览，内嵌全部 55 品 JSON-LD 图
- `platform-fixes/` — refund-policy.md（三类可粘贴英文稿）、description-first150.md（规则＋5 个代表品示例）、fact-block-template.md（五段式模板＋SheetFix 填例）、payhip-about-me.md（正式稿）
- 全部 JSON/XML 已通过解析校验（55 个 JSON-LD 逐个验过 @type 与退款字段）

## ③ 字段完整度（分母 55 唯一产品，实数）

全量齐（55/55）：title、description_full（全文，非平台截断版）、description_facts 四项（what_it_does / delivery / file_format / requirements）、whats_inside（52 个自动抽取＋3 个人工按其自身文案补：DateShift、SKU Ops、体检）、price（amount_minor＋USD）、variants（≥1；PitchReel 8 个）、availability=InStock、category、sku（Gumroad permalink）、seller＋support_email、return_policy、buy_urls.gumroad。

有缺口：
- **image：仅 1/55**（只有 SKU Operations Copilot 在 Gumroad 有真实封面图，其余产品 covers 与 thumbnail 均为空——这是平台 listing 侧缺图，本层如实留空；补图属 listing 改动，不在本轮范围）
- **landing_url：34/55**（33 个 GitHub Pages 落地页经 HTTP 200 实测收录＋PitchReel 官网 1 个；缺 21 个＝n8n 包 16 个全无落地页＋AudiobookSpecFix、PageSmith、Etsy Listing Photo Prep、SKU Ops、体检各 1）
- **buy_urls.payhip：15/55**（其余 40 个未在 Payhip 上架，属事实非缺口）

另注意：SKU Operations Copilot 的 Gumroad 描述只有一句话（其 whats_inside 三条即由该句拆出），是全店文案最薄的一品。

## ④ 支持邮箱查证

**binbin7418@gmail.com** — 出处：~/workspace/video-mcp/web/SUPPORT.md 明文「The one public support address」，且是 PitchReel 全站页脚/support 页公开地址，已接入 Gmail 巡检。n8n 包文案只写「email support is included」未印地址，目录层统一采用这个已公开地址，非新造。全部 55 品 seller.support_email 已填此值，无 TODO 占位。
