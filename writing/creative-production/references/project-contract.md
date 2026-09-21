# 前期專案契約 v1

這是自己的中介格式，不是 CineAgent、Hypit 或供應商的原生 schema。修改 JSON 不能取代使用者確認紀錄。

## 共通欄位

- `schema_version`: 整數 1。
- `project_id`: 非空字串。
- `domain`: `narrative` 或 `nonfiction`。
- `mode`: `writing` 或 `screen`。
- `versions`: 目前核准／採用的規劃版本映射，至少 `outline`；敘事另有 `characters`，影片另有 `script`。單篇無角色時請用 nonfiction，或將 narrative 的 characters 記為有明確含義的 `none-v1` 並在 brief 說明無角色，不虛構人物。
- `consumed_versions`: 本稿實際使用的版本，須與 versions 完整一致；比對前必須真的讀取對應文件。
- `units`: 非空陣列，每項 `id` 唯一、`file` 為專案內相對 UTF-8 稿件路徑、`status` 為 draft/approved、`length` 含整數 min/max。範圍由使用者要求或明示假設決定。

`length` 使用非空白 Unicode 字元數，包含標點；不是 token、中文詞數或平台審核字數。檔案若含 Markdown 標記也會計入，因此稿件盡量只放正文。

## 影片欄位

- `continuity_level`: A0/A1/A2/A3。
- `generation`: 明確 `{"requested": false}`。這只是前期檢查檔，不是生成操作指令。
- `scenes`: 非空陣列，每項唯一 `id`。
- `assets`: 陣列，可空。每項有唯一 `id`、`kind`（CHR/SCN/PRP/AUD）、`version`、`status`、`file`。被引用的資產必須 approved 且檔案存在。
- `shots`: 非空陣列，每項唯一 `id`、已存在的 `scene_id`、`asset_refs`（id/version 陣列）、`duration`。
- `duration`: 有限正數 `seconds`；`source` 為 estimated/authored/measured。measured 另必須有專案內 `evidence_file`。

A2/A3 的每鏡至少需要一個有效資產引用；這是基本結構門禁，不是完整語義檢查。被列但未引用的 draft 資產可保留待辦，不代表可投產。

## 輸出

exit 0：`ok:true`；exit 1：`ok:false` 及繁體中文 errors。`checks` 提供本次實際掃到的物件數；`executed:false` 表示不曾生成或發布。

所有本機檔案必須位於 project.json 所在資料夾內。禁止絕對路徑、向外跳轉或逃出專案的符號連結；外部來源先取得合適使用權，再把必要素材複製進專案，不將來源憑證或簽名網址寫入。

不檢查：實際授權真偽、素材版權、圖片內容、音訊真實秒數、劇情品質、供應商支援格式、影片可否播放。這些另由主代理及使用者複核。範例和 tests 只驗證契約，不是正式作品。
