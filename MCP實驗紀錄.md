# 失語者 階段 1：MCP 實驗紀錄

- 日期：2026-10-02
- 環境：macOS（Apple M2 Pro）、Godot 4.7.2 stable、Node 26、Claude Code
- 目標：用 Claude Code + Godot MCP 把 Kivy 版選項式遊戲重做成 Godot 網頁版，並觀察 MCP 能幫上多少忙。
- 結果：**階段 1 的 7 項完成標準全部達成**，網頁版已由使用者在瀏覽器實測（含聲音）。

---

## 1. 結論摘要

| 問題 | 觀察 |
|---|---|
| MCP 能不能建出整個 UI？ | 能。換成 Godot MCP Toolkit 後，步驟 4～6 的節點、版面、主題覆寫、音效資源**全部用 MCP 完成，沒有手改 `.tscn`**。 |
| MCP 能不能自己驗證？ | 能，而且是最大的收穫：`runtime_screenshot` + `input_simulate` + `runtime_get_script_vars` 讓 Claude 自己點、自己看、自己讀狀態，找出問題。 |
| 哪些還是要靠一般檔案編輯？ | GDScript 本身、`.import` 匯入參數、`export_presets.cfg`、長流程的自動測試。 |
| 哪些一定要人？ | **聽聲音**（BGM 換曲、音效好不好聽）、在外掛 UI 裡啟用外掛、安裝匯出模板、在真正的瀏覽器裡玩。 |
| 最大的坑 | MCP 工具本身的不穩定（截圖回傳舊畫面、runtime 登錄被覆蓋），而不是遊戲程式。 |

---

## 2. 兩套 MCP 的比較

一開始照 README 用 **Coding-Solo/godot-mcp**，步驟 3 之後換成 **Godot MCP Toolkit**（v1.0.2，MIT）。

| 項目 | Coding-Solo/godot-mcp | Godot MCP Toolkit |
|---|---|---|
| 架構 | 每次呼叫另開 headless Godot，執行一個操作就結束 | 編輯器外掛，透過 WebSocket 操作**開著的編輯器** |
| 編輯器要開著嗎 | 不用 | 一定要 |
| 修改根節點／掛腳本 | ✗（根節點固定叫 `root`） | ✓ `node_set_script`、`node_set_property` |
| 刪除／改名／排序節點 | ✗ 只有 `add_node` | ✓ `scene_delete_node`、`node_manage` |
| 主題覆寫、資源屬性 | ✗ 只能設數值 | ✓ 字型大小、顏色、陰影、AudioStream 都能直接設 |
| 專案設定 | ✗ | ✓ `project_set_setting` |
| 截圖 | ✗ | ✓ `runtime_screenshot` |
| 模擬輸入 | ✗ | ✓ `input_simulate`（click、key、click_node…） |
| 讀執行中變數 | ✗ | ✓ `runtime_get_script_vars`、`runtime_get_node_state`、`execute_code` |
| 腳本錯誤 | ✗ 解析錯誤只出現在 stdout，`errors` 欄位是空的 | ✓ `script_check`、`lsp_project_diagnostics` |
| 與編輯器衝突 | 會：MCP 直接寫 `.tscn`，編輯器存檔可能蓋掉 | 不會：改動經由編輯器並可復原 |

換掉的直接原因：步驟 1～3 中，**8 件事裡有 6 件必須繞過 MCP**（手改 `.tscn`、`project.godot`，或寫在 `_ready()`），而且 Claude 看不到畫面，使用者回報「按下沒反應」時只能靠推理和自寫測試。

---

## 3. 各步驟使用的工具

| 步驟 | 內容 | 用到的 MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| 0 | 確認連線 | `get_godot_version`、`get_project_info`（舊） | — |
| 1 | 讀劇本、顯示場景 1 | `create_scene`、`add_node`×6、`run_project`、`get_debug_output`（舊） | 根節點改名、掛腳本、設主場景、StyleBox（舊 MCP 不支援） |
| 2 | 選項與跳轉 | `add_node`×2（舊） | Hint 改成 RichTextLabel（舊 MCP 不能改型別） |
| 3 | 回應文字、選過的變暗 | `add_node`（舊） | — |
| — | **換 MCP** | — | 下載外掛並審查程式碼、使用者在編輯器啟用外掛 |
| 4 | 打字機、換場淡入淡出 | `scene_create_node`、`control_set_layout`、`node_manage`、`editor_save_scene`、`script_check`、`game_start`、`input_simulate`、`runtime_screenshot`、`debugger_get_log` | 無 |
| 5 | 標題畫面、BGM、音效 | 同上 ＋ 主題覆寫屬性、AudioStream 資源、`editor_refresh`、`runtime_get_node_state` | `click.ogg.import` 改成不循環（沒有改單一檔案匯入參數的工具） |
| 6 | 結局、回標題 | 同上 ＋ `execute_code`（直接跳到場景 17）、`lsp_project_diagnostics` | — |
| 7 | 網頁匯出 | — | `export_presets.cfg`、headless 匯出、Chrome 自動化（MCP 沒有匯出工具） |

---

## 4. 遇到的問題與解法

### 遊戲本身

| 問題 | 發現方式 | 原因 | 解法 |
|---|---|---|---|
| `StoryData` 找不到 | debug 輸出出現 `Debugger Break` | `scripts/` 裡多了一份 `project.godot`，Godot 把整個資料夾當成別的專案而略過 | 移除；寫進 CLAUDE.md 禁止事項 |
| 「按下沒反應」 | 使用者回報 | 選到 `next_id` 等於自己的選項，畫面原地重畫 | 先顯示 response（步驟 3），選過的變暗 |
| 選項讓故事「重複循環」 | 使用者回報 | 劇本本身：場景 11～14 重演 5/7/8/10 的事件 | 程式不處理，留給作者調整劇本 |
| click 音效一直響 | 使用者回報 | 專案把所有 ogg 匯入預設都設成循環，連 click.ogg 也是 | 只對 click.ogg 關掉循環 |
| 音效太單調 | 使用者回饋 | — | 打字時每 2～4 字隨機響一次，音高和音量隨機，標點不出聲 |

### MCP 工具

| 問題 | 原因 | 解法（已寫進 CLAUDE.md） |
|---|---|---|
| 舊 MCP 回報「沒有錯誤」，實際上有解析錯誤 | 錯誤只在 `output`，不在 `errors`；而且剛啟動就讀，錯誤還沒印出來 | 換工具；讀 log 前先等幾秒 |
| `game_start` 之後 `GAME_NOT_RUNNING` | **自己跑的 headless 測試也會啟動外掛 runtime，覆蓋共用的登錄檔** | headless 測試改在拿掉外掛的專案副本上執行；必要時用 `runtime_poll: true` 重新連線 |
| 截圖拿到舊畫面 | inline 回傳的圖片超過約 1MB 傳輸上限 | 一律用 `image_response_mode: "disk"` |
| 只更新單一檔案，匯入設定沒有生效 | 只改 `.import` 不會觸發重新匯入 | 用不帶參數的 `editor_refresh` 整個專案重新掃描 |
| Chrome 自動化測試很慢 | 自動化分頁在背景（`document.hidden`），畫面更新被節流 | 實際遊玩由使用者在前景瀏覽器測試 |

---

## 5. 人與 Claude 的分工

**Claude（透過 MCP 與檔案編輯）**
- 建立全部場景與節點、寫兩支 GDScript（約 370 行）
- 每個步驟執行遊戲、截圖、模擬點擊、讀變數來驗證
- 寫 headless 測試，跑過三條結局路線（每一步都檢查 response、打字跳過、換場、BGM）
- 查出 MCP 本身的問題並記錄解法；更新 CLAUDE.md／README／PROMPTS

**使用者**
- 在 Godot 編輯器裡啟用外掛、產生 `.mcp.json`、安裝匯出模板
- **聽聲音**：確認 BGM 換曲、指出 click 音效太煩、要求鍵盤感
- 發現遊玩體驗問題（「按下沒反應」「故事重複循環」）
- 在瀏覽器實際玩網頁版

使用者回報的 4 個問題中，有 3 個是**體驗或聲音**（反應回饋、音效、劇情重複），自動測試和截圖都抓不到。

---

## 6. 給階段 3（可走動的地圖）的建議

1. **繼續用 Godot MCP Toolkit**。地圖需要的 `tilemap`、`tileset`、`spriteframes`、`animation_authoring`、`navigation` 工具群組都有，用 `discover_tools` 開啟需要的就好。
2. **驗證以 MCP 為主**：`input_simulate` 可以送方向鍵、`runtime_get_node_state` 可以讀角色座標，比截圖更準確。截圖記得用 disk 模式。
3. **headless 測試一律用專案副本**，不要直接對專案執行，否則會干擾 MCP。
4. **聲音和手感還是要人來確認**，每一步保留讓使用者試玩的時間。
5. 新增任何 ogg 音效時記得關掉循環（專案預設是循環）。
6. 劇本調整後的流程見 PROMPTS.md「之後：劇本調整後」。

---

## 7. 最終狀態

- 節點樹：與 CLAUDE.md 建議架構一致，另外多了 `TypeSfx`（打字音效）
- `scripts/main.gd`：狀態機 TITLE／TRANSITION／TYPING／CHOOSING／RESPONSE
- `build/web/`：`index.pck` 約 48MB、`index.wasm` 約 40MB，不含 `addons/`、`tools/`、`.mcp.json`
- 完成標準：7／7 ✅
- 尚未處理：劇本重複（等作者調整）、標題文字與背景字跡重疊（可選的視覺調整）

---
---

# Lv1：停車場可走動（橫向捲軸、替代美術）

- 日期：2026-10-02
- MCP：Godot MCP Toolkit（只用這一個）
- 結果：Lv1 完成標準 8 項全部達成。網頁版在瀏覽器確認可以進入停車場；作者在 Godot 中試玩確認手感。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| Lv1-0 | 對話框加高、直式持握提示 | `node_set_property`（batch）、`scene_create_node`、`control_set_layout`、`execute_code`（跳到場景 14、代入直式尺寸）、`input_simulate`、`runtime_screenshot` | `main.gd`（GDScript） |
| Lv1-1 | 讀規格、提出計畫 | — | — |
| Lv1-2 | UI 搬進 CanvasLayer | `scene_create_node`（CanvasLayer、Node2D）、`node_manage`（reparent `keep_global_transform: false`、reorder）、`node_set_property`（18 個 unique name） | `main.gd` 改用 `%Name` |
| Lv1-3 | 輸入設定、區域資料 | `input_map_action`、`input_map_event`、`script_check`、`editor_refresh` | `area_data.gd`、`validate_story.gd`；headless 驗證與反向測試 |
| Lv1-4 | 停車場、主角、鏡頭 | `scene_create`、`scene_create_node`（CharacterBody2D、CollisionShape2D＋`NewResource`、Camera2D、TextureRect、ColorRect）、`node_set_script`、`node_set_property`、`input_simulate`（action）、`execute_code` 讀座標 | `area.gd`、`player.gd` |
| Lv1-5 | 4 個互動點 | `scene_create_node`（Area2D＋碰撞形狀）、`node_set_script`、`node_set_property`（point_id、offset）、`node_manage` | `interact_point.gd`、`main.gd` 狀態 |
| Lv1-6 | 接上主流程 | `game_start`、`input_simulate`、`runtime_get_script_vars`、`runtime_screenshot`、`lsp_project_diagnostics` | `main.gd`；headless 三輪完整流程測試 |
| Lv1-7 | 匯出、紀錄 | — | headless 匯出（專案副本）；Chrome 自動化確認網頁版 |

**節點與場景**：Lv1 的所有節點（Main 的圖層搬移、停車場整個場景、互動點、提示文字）都用 MCP 建立，**沒有手改 `.tscn`**。繞過 MCP 的只有 GDScript、`.import`／匯出設定，以及 headless 測試。

## 2. Claude 自己發現並修好的問題

| 問題 | 怎麼發現的 | 解法 |
|---|---|---|
| `scene_create_node` 帶入版面屬性（`position`／`size`／`offset_*`）時，位置被重設成 (0,0)：地面跑到畫面上方、色塊沒對齊腳底 | MCP 回報成功，但**讀 `.tscn` 檢查**才發現（Lv1-4、Lv1-5 各一次） | 先建立，再用 `node_set_property` 設 offset |
| MCP 警告 anchor「存檔後可能不會保留」 | 工具回傳的 warning | 讀 `.tscn` 確認其實有保留（誤報） |
| 新腳本 `class_name` 在 `script_check` 中找不到 | `script_check` 錯誤訊息 | `editor_refresh` 後通過 |
| 移動距離異常（2 秒走 711px，之後自己往左） | 讀座標與遊戲狀態，發現遊戲被點進了場景 1 | 判斷為**使用者同時在操作遊戲視窗**；排除後重測正確（2 秒 = 280.0px） |
| 模擬按鍵能不能驅動 `Input.is_action_pressed()` | 計畫階段列為風險，**讀外掛原始碼**確認 | `action` 類型會呼叫 `Input.action_press`，不用改寫 |
| runtime 工具常回報 `GAME_NOT_RUNNING` | 多次重現；檢查登錄檔內容是正確的 | `game_start` 之後**等 3～5 秒**再呼叫 |
| 網頁版能否讀到 `data/areas/` | 計畫階段列為風險 | 匯出後在 Chrome 實際確認可以進入停車場 |
| 作者提出「按鍵衝突可能一按就開又關」 | — | 依「同一事件只處理一次」實作，MCP 驗證按一次 E 後狀態是打字中 |

## 3. 自動驗證的範圍

- **MCP 實玩**：移動（1 秒 137.7px、2 秒 280.0px）、左右邊界 16／2288、鏡頭限制 576～1728、UI 不隨鏡頭移動、4 個互動點的提示與文字、婦人只觸發一次、對話中不能移動、出口接場景 3、結局 → 標題 → 第二輪重新觸發。
- **headless**：三輪完整流程（停車場 → 場景 3～17 → 結局 A／B／C → 標題），全部通過。
- **劇本檢查**：區域資料 8 種錯誤的反向測試全部抓到；場景與 JSON 的 point_id 一一對應。
- **編譯**：`lsp_project_diagnostics` 7 個腳本 0 個問題（含警告）。

## 4. 作者試玩的回饋

| 項目 | 回饋 |
|---|---|
| 走路速度 | 很好，維持現在的節奏（140 px/秒） |
| 空白鍵／Enter 衝突 | 沒有問題 |
| 互動點 | OK |
| 提示文字 | 清楚 |
| **切換感** | **落差很大**：從可走動的停車場切回視覺小說很突兀。以第一版來說成果不錯，但**希望之後都用停車場這種可走動的方式進行** |

只有「切換感」需要人判斷，而且自動測試完全不會發現：它不是 bug，是體驗。這再次符合階段 1 的結論：**手感與整體體驗要靠人**。

## 5. 觀察與結論

1. **MCP 能自己驗證「移動與觸發」**：模擬按鍵＋讀座標的方式非常準確（誤差來自計時），比截圖可靠。Lv1 規格裡的驗證表全部由 Claude 自己完成。
2. **MCP 回報成功不代表結果正確**：版面屬性跑位兩次都是讀 `.tscn` 才發現。結論：**每次用 MCP 建立或修改節點後，都要讀檔或讀屬性確認**。
3. **與使用者同時操作會互相干擾**：MCP 驅動的是作者也看得到、點得到的同一個遊戲視窗。驗證時要先說明「請勿操作」，結果異常時先懷疑外部輸入。
4. **資料引用的設計有效**：區域文字用 `from` 引用 `story.json`，劇本統一用詞（靜語者）時區域不用改；劇本檢查也能同時把關兩邊。

## 6. 給下一級的建議

- **作者的回饋（切換落差大）建議提早處理**：目前路線是 Lv2（視差光影）→ Lv3（像素角色）→ v1.5 → Lv4（多區域）。如果更在意整體可走動的體驗，可以考慮把「多區域」提前，或在 Lv2 先做一個過渡（例如視覺小說畫面也顯示主角剪影）。是否調整順序由作者決定。
- MCP 建節點：先建立，再設版面屬性，最後讀 `.tscn` 確認。
- 測試前請作者不要操作遊戲視窗。

## 7. Lv1 最終狀態

- 新增：`scenes/areas/ParkingLot.tscn`、`scripts/area_data.gd`、`area.gd`、`player.gd`、`interact_point.gd`；Main 加入 `BgLayer`／`World`／`UILayer`／`PromptLabel`／`RotateHint`。
- 狀態機：TITLE／TRANSITION／TYPING／CHOOSING／RESPONSE／EXPLORE／AREA_TEXT。
- `build/web/`：`index.pck` 約 48MB，包含 `data/areas/`，不含 `addons/`、`tools/`、`.mcp.json`。

---
---

# Lv2：景深分層與光影（2.5D 的感覺）

- 日期：2026-10-02
- MCP：Godot MCP Toolkit（只用這一個）
- 狀態：**Lv2 完成**（完成標準 5/5）。作者在 Godot 與瀏覽器試玩確認，瀏覽器流暢沒有卡頓。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| Lv2-2 | 三層視差 | `scene_create_node`（Parallax2D、ColorRect）、`node_manage`（reparent、reorder）、`node_set_property`（offset）、`execute_code`（讀 `get_screen_position()`） | `area.gd` 的視差參數（GDScript） |
| Lv2-3 | 黑暗＋手電筒 | `scene_create_node`（CanvasModulate、PointLight2D＋**巢狀 `NewResource`**：Gradient → GradientTexture2D）、`node_set_property`（`light_mask`）、`execute_code`（執行中直接改數值） | `area.gd` 的光影參數 |
| Lv2-4 | 紅色警示燈 | `scene_create_node`（PointLight2D）、`node_set_script`、`execute_code`（取樣 energy、執行中調整） | `flicker_light.gd` |
| Lv2-5 | 標題畫面 | `execute_code`（執行中切換三種版面並截圖）、`node_set_property`（寫入選定版本） | — |

所有節點與資源都用 MCP 建立，**沒有手改 `.tscn`**。

## 2. 調整了幾輪

| 項目 | 誰發現 | 輪數 | 經過 |
|---|---|---|---|
| 前景柱子擋住出口的主角 | Claude（截圖） | 1 | 前景移動 1.3 倍，鏡頭到底時第 4 根柱子剛好停在出口 → 移到 2240～2360 |
| 手電筒太弱 | Claude（截圖） | 1 | 半徑 256px＋背景已調暗 → 亮度 1.6、大小 1.5 |
| **背景只看到黑黑一片** | **作者** | 1 | 背景圖本身 55% × 世界 20% ≈ 11% → 背景改回原亮度、世界亮度 0.32（Claude 截 A／B 兩種，作者選 B） |
| 紅燈幾乎看不見 | Claude（截圖） | 2 | 先調大仍看不見 → 查出「2D 燈光 = 燈色 × 表面顏色」，暗青色的停車場反射不出紅色 → 亮度 5.0、範圍 2.0 |
| 標題壓在 HERE 上 | 階段 1 檢查 | 1 | Claude 做 A／B／C 三種版本截圖，作者選 A（下方置中） |

合計：Claude 自己發現並調整 **4 次**，作者回饋 **1 次**，作者做選擇 **2 次**（亮度方案、標題版本）。

## 3. 哪些描述方式對 AI 最有效

- **「看不到 X」比「調亮一點」有用**：作者說「背景只看到黑黑一片」，Claude 能直接去找「為什麼背景會黑」，結果找到是兩層調暗疊加，而不是單純把數值調大。
- **給選項讓作者挑，比 AI 自己決定好**：亮度（A／B）與標題（A／B／C）都是先截多張圖再讓作者選。主觀的東西，AI 負責產生候選，人負責選。
- **執行中直接改數值再截圖**（`execute_code`）是調整氛圍最快的方式：不用改檔、不用重啟，一輪只要幾秒。

## 4. 哪些只能靠人判斷

- 「背景太黑」是作者發現的。Claude 截圖時有看到「暗」，但以為那就是想要的氛圍，**無法判斷暗到什麼程度算過頭**。
- 標題版面的偏好（A 最接近原本的版面，B／C 風格較強），只能由作者決定。
- 紅燈的強度、閃爍頻率是否舒服，作者試玩確認沒問題。

這符合階段 1 與 Lv1 的結論：**AI 能找出「有沒有作用」與「為什麼沒作用」，但「好不好看」要靠人**。

## 5. AI 自己查出原因的例子

紅燈第一次調大後還是看不見，Claude 沒有繼續盲目加大數值，而是：
1. 讀 `.tscn` 確認設定和手電筒完全相同（排除設定錯誤）。
2. 推論「燈色 × 表面顏色」：暗青色表面的紅色成分很少。
3. 把亮度拉到 6 做驗證，確認判斷正確後才定案，並把原因寫進 `area.gd` 的註解。

## 6. 給作者調整的參數（ParkingLot 的屬性面板）

| 群組 | 參數 | 目前值 |
|---|---|---|
| 景深（視差） | `far_scroll`／`mid_scroll`／`front_scroll` | 0.3／0.7／1.3 |
| 光影 | `world_brightness` | 0.32 |
| 光影 | `flashlight_scale`／`flashlight_energy` | 1.5／1.6 |
| 光影 | `red_light_energy`／`red_light_speed` | 5.0／1.6 |

## 7. 效能與 Web 版（Lv2-6）

| 項目 | 結果 |
|---|---|
| Godot 內 FPS（debug 版，`main.gd` 的 `debug_fps()`） | 標題 60、移動中 60、出口附近紅燈最亮時 60（螢幕更新率上限） |
| Web 版匯出 | `index.pck` 約 47.8MB，含區域資料、停車場場景、閃爍腳本；不含外掛與 `.mcp.json` |
| 瀏覽器流暢度 | **作者確認流暢，沒有卡頓**（Compatibility 渲染器＋ 2 盞 2D 燈光＋ 3 層視差） |
| 陰影（`LightOccluder2D`） | 選做，這一級不做 |

- `execute_code` 不能存取 `Engine`，所以在 `main.gd` 加了只在 debug 版回傳數值的 `debug_fps()`。
- 網頁版的流暢度只能由作者判斷：自動化的瀏覽器分頁在背景會被降速，量不出真實 FPS。

## 8. Lv2 結論

1. **MCP 能建出完整的 2.5D 視覺結構**：Parallax2D、CanvasModulate、PointLight2D（含巢狀資源）全部用 MCP 建立。
2. **MCP 很適合「量化驗證」**：視差倍率用讀座標驗證，與設定完全吻合；燈光閃爍用取樣 energy 驗證。
3. **「執行中改數值 → 截圖」是調整主觀效果最快的方法**，並讓作者從多個候選中選擇。
4. **主觀判斷仍然要靠人**：「背景太黑」是作者發現的。

---
---

# Lv3 準備：安裝 Pixelorama MCP（第二個 MCP）

- 日期：2026-10-02
- 結果：**安裝完成**，`/mcp` 看得到 pixelorama，擴充功能在 `127.0.0.1:7373` 回應正常（93 個工具）。
- 安裝細節見 `docs/Lv製作流程.md` 的 Lv3「實際安裝紀錄」。

## 1. 安裝前的安全檢查（Claude）

| 檢查 | 結果 |
|---|---|
| npm 安裝時腳本（`postinstall` 等） | 沒有；正式相依套件只有官方 MCP SDK 與 zod |
| MCP 伺服器 | 只連 `127.0.0.1:7373`，不執行系統指令；寫檔只發生在匯出工具 |
| Pixelorama 外掛（約 5000 行 GDScript） | 只監聽 `127.0.0.1`，不執行系統指令；**沒有驗證機制**（本機任何程式都能下指令），不用時要關掉 Pixelorama |
| 附帶的 `PixMcpBridge.pck`（二進位） | 比對後 5 個原始檔一字不差包含在內，沒有多餘程式 |
| 根目錄的 `Pixelorama.pck` | 用途不明，不使用 |

## 2. 遇到的問題與解法

| # | 問題（症狀） | 原因 | 解法 | 誰發現 |
|---|---|---|---|---|
| 1 | `npm install` 失敗（ERESOLVE） | 作者 `package.json` 的 eslint 版本衝突（只影響開發工具），連帶裝不到 TypeScript | 用專案附的 lock 檔：`npm ci --legacy-peer-deps` | Claude |
| 2 | `npm audit` 有 3 個漏洞 | MCP SDK 內建 HTTP 功能的相依套件（本 MCP 走 stdio，用不到） | `npm audit fix --omit=dev --legacy-peer-deps` → 0 個漏洞 | Claude |
| 3 | Pixelorama 無法開啟 | App 只有 ad-hoc 簽章，Gatekeeper 阻擋 | 作者自行在「系統設定 → 隱私權與安全性」允許（安全設定由作者決定，Claude 不繞過） | — |
| 4 | **Preferences → Extensions 看不到 pix-MCP Bridge** | 紀錄檔：`Pack version unsupported: 4`。附帶的 `.pck` 是 **Godot 4.7** 打包（格式第 4 版），Pixelorama 1.1.10 內建 **Godot 4.6.2**，只讀得懂第 3 版。作者附的檔案與他文件指定的版本不相容 | 查 Pixelorama 原始碼，確認它也讀 `.zip` → 用已驗證的 5 個原始檔打包成 `PixMcpBridge.zip`（zip 沒有版本問題） | Claude（讀紀錄檔＋.pck 檔頭） |
| 5 | 換成 zip 後仍看不到／伺服器沒啟動 | 擴充功能資料夾被加入了 8MB 的 `Pixelorama.pck`（Pixelorama **自己的程式資料**），被當成擴充功能載入而跳出錯誤視窗，干擾畫面 | 刪除那份 `Pixelorama.pck`、清空 `Monitoring.ini` 的可疑紀錄 | Claude |
| 6 | 擴充功能載入了卻沒動作 | Pixelorama 的擴充功能**預設是停用的** | 在 Preferences → Extensions 勾選啟用（等同 `config.ini` 的 `[extensions] PixMcpBridge=true`）；紀錄檔出現 `HTTP server listening on 127.0.0.1:7373` 即成功 | Claude（讀 Pixelorama 原始碼） |
| 7 | `claude mcp list` 有 pixelorama，但 `/mcp` 看不到 | 用 **local 範圍**註冊，只在 Claude Code 判定的專案路徑相符時載入；啟動方式對不上就不會出現（godot-mcp-toolkit 寫在 `.mcp.json`，所以不受影響） | 改成 **user 範圍**：`claude mcp add -s user pixelorama -- node ~/Tools/pixelorama-mcp/mcp-server/dist/index.js`。不放 `.mcp.json`：那個檔案由 Godot 外掛管理、會進 git，且這是本機路徑 | 作者回報，Claude 查設定檔 |

## 3. Claude 判斷錯誤、事後更正的地方

| 一開始的判斷 | 實際情況 | 怎麼發現的 |
|---|---|---|
| 擴充功能資料夾裡的 `Pixelorama.pck` 是「作者修改過、來源不明的版本」 | 與 `/Applications/Pixelorama.app/Contents/Resources/Pixelorama.pck` **完全相同**，就是 Pixelorama 自己的程式資料 | `cmp` 比對 |
| 「Pixelorama 每次啟動都會把自己裝成擴充功能」（Pixelorama 的 bug） | 重新啟動後**沒有重現**；比較可能是透過 Preferences 的 Add Extension 選到了 App 內的同名檔案 | 再啟動一次觀察 |

教訓：**推論出原因後，要先重現或比對確認，再下結論**。這兩次都是先說了結論，後來才用比對／重現推翻。

## 4. 觀察

1. **第二個 MCP 的安裝難度比第一個高很多**：Godot MCP Toolkit 從 Asset Store 下載後啟用即可；Pixelorama MCP 是個人專案，遇到 7 個問題，其中 4 個是作者的檔案或文件本身的問題（版本不相容、依賴衝突、未說明預設停用）。
2. **「讀紀錄檔＋讀原始碼」是排除問題最有效的方式**：版本不相容、預設停用都是從 Pixelorama 的紀錄檔和原始碼找到的，而不是靠猜。
3. **自己從原始碼打包，比使用附帶的二進位檔更安全**：裝進去的就是檢查過的程式碼。
4. **需要作者的地方**：允許未認證的 App 開啟（安全設定）、在 App 介面中操作、確認 `/mcp` 的顯示。

---
---

# Lv3：用 Pixelorama MCP 畫主角（第一次兩個 MCP 配合）

- 日期：2026-10-05
- MCP：**pixelorama**（畫圖、動畫、匯出）＋ **godot-mcp-toolkit**（匯入、SpriteFrames、場景、驗證）
- 成果：32×48 像素、放大 2 倍的主角（感染者造型）。左右各一套，共 **20 格**：待機 4 格（4 fps）＋行走 6 格（8 fps）× 2 個方向。
- 狀態：**Lv3 完成**（完成標準 4/4）。作者在 Godot 與瀏覽器試玩確認（`index.pck` 約 47.8MB），並決定之後**繼續用 Pixelorama**。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| Lv3-2 | 待機第 1 格 | pixelorama `draw_pixels`（一次 497 像素、16 色）、`capture_canvas_image`、`export_image`（放大 8 倍自我檢查）、`save_project` | 造型用 Python 以形狀設計並自動加外框（MCP 沒有「設計」能力，只負責畫）；Godot 預覽用 Toolkit 建立暫時的 Sprite2D |
| Lv3-3 | 待機 4 格 | `duplicate_frame`、`select_rect`＋`transform_selection`（上半身下沉 1px、頭再下垂 1px）、`add_animation_tag`、`set_fps` | — |
| Lv3-4 | 面向右行走 6 格 | `add_frame`、`draw_pixels`（第 1 格整格）、**`copy_cel`＋只送差異像素**（擦除用 `#00000000`）、`get_pixel`、`export_gif`、`delete_animation_tag`／`add_animation_tag` | 腿部姿勢用 Python 依姿勢表產生；放大 GIF 用 ImageMagick 製作 |
| Lv3-4b | 面向左 10 格 | 同上；9 格依「與哪一格差最少」排順序再用 `copy_cel` | 翻轉與修正（血跡換手、陰影換邊、遠側的手）用 Python 計算 |
| Lv3-5 | 放進遊戲 | pixelorama `export_animation`（spritesheet）；Toolkit `editor_refresh`、**`spriteframes_from_spritesheet`**、`scene_create_node`、`node_set_property`、`scene_delete_node`、`editor_save_scene`、`script_check`、`lsp_project_diagnostics`；驗證用 `game_start`、`input_simulate`（action）、`execute_code`、`runtime_screenshot`、`debugger_get_log` | `player.gd`（GDScript）、`.import` 改無損、`export_presets.cfg` |
| Lv3-6 | 匯出 | — | headless 匯出（專案副本，MCP 沒有匯出工具） |

所有節點與 SpriteFrames 都用 MCP 建立，**沒有手改 `.tscn`／`.tres`**。

## 2. 畫了幾次、改了幾輪

| 項目 | 誰發現 | 經過 |
|---|---|---|
| 第 1 版沒有駝背、兩腿黏在一起 | Claude（文字格線預覽） | 重畫第 2 版 |
| 後腦勺有兩格膚色（像耳朵長在後面） | Claude（放大 8 倍檢查） | 改成頭髮 |
| 待機第 3 格頭部移動後，下巴外框缺口、血跡少一格 | Claude（逐像素比對） | 補 2 格 |
| 「沒有走路的移動感、轉向沒有另一方向的像素」 | **作者** | Lv3-4／3-4b 處理；作者決定左右各畫一套（不用鏡像） |
| 行走後半步的步幅比前半步窄 | Claude（並排圖） | 兩腿的髖部差 2px，用相同偏移會不對稱 → 加大後半步的偏移 |
| 左向的外框變成兩層 | Claude（文字格線預覽） | 補外框時把舊外框當成身體 → 改成只看非外框像素 |
| 行走速度 8 fps 或 12 fps | **作者選擇** | Claude 做兩個 GIF，作者選 8 fps |

作者**沒有手動在 Pixelorama 修改任何像素**，全部透過 MCP 完成。

合計：Claude 自己發現並修正 **5 次**，作者回饋 **1 次**、做選擇 **3 次**（造型方案、左右畫法、行走速度），作者確認 **5 次**（造型、待機、行走、左向、試玩）。

## 3. 兩個 MCP 的配合

```
Python 設計像素 ──▶ pixelorama 畫格、標籤、存 .pxo
                     │ export_gif → 放大 GIF 給作者確認
                     │ export_animation（spritesheet）
                     ▼
            assets/sprites/player.png
                     │ Toolkit editor_refresh（匯入）
                     │ spriteframes_from_spritesheet（切成 4 個動畫）
                     ▼
     ParkingLot 的 Player/Sprite（AnimatedSprite2D）→ Toolkit 執行、操作、讀狀態驗證
```

- 兩個 MCP 之間**沒有直接連結**，靠檔案交接（spritesheet）。交接前用 ImageMagick 把 spritesheet 和已確認的畫格逐像素比對（0 差異），避免傳錯版本。
- 原本計畫用 pixelorama 的 `export_godot_spriteframes`，但它只能把**整個畫布**匯出成**一個**動畫，所以改用「spritesheet ＋ Toolkit 切割」。結果 Toolkit 的 `spriteframes_from_spritesheet` 一次呼叫就切好 4 個動畫，比預期簡單。

## 4. Pixelorama MCP 的穩定度與特性

| 觀察 | 內容 |
|---|---|
| 穩定度 | 整個 Lv3 呼叫了數十次，**沒有斷線或失敗**。需要 Pixelorama 一直開著 |
| 繪圖精確度 | 每一步都匯出後逐像素比對，**20 格全部 0 差異**：送出什麼就畫出什麼 |
| 傳送量 | 每格約 500 像素（約 17KB JSON）。改成「`copy_cel` 複製最相近的格 → 只送差異」後，每格只需 0～157 像素，**行走與左向共 16 格的傳送量約少了 3 分之 2**（約 2,600 像素，整格送出要約 7,800） |
| 擦除 | `draw_pixels` 的顏色用 `#00000000` 就能擦除（文件沒寫，用 `get_pixel` 驗證過） |
| **標籤會自動延伸** | 在最後一個標籤後面 `add_frame`，該標籤會被延長到包含新畫格（發生 2 次）。新增畫格後一定要 `get_animation_tags` 檢查 |
| fps 是整個專案共用 | 各動畫不同速度無法存在 `.pxo` 裡，改在 Godot 的 SpriteFrames 設定 |

## 5. AI 畫像素圖的方式

- **AI 不是「看著畫」，而是「算出來」**：用 Python 以形狀（橢圓、矩形、每列寬度表）組出角色 → 自動加外框 → 印成文字格線檢查 → 再送給 MCP。姿勢用數字表描述（膝蓋與腳踝的偏移、身體下沉量）。
- **好處**：修改很精準（「後半步偏移加大 2px」）、左右兩套可以從同一份資料推導，且每格都能驗證。
- **限制**：「好不好看」AI 判斷不了。造型方案、動作是否自然、播放速度，都是作者看 GIF 後決定的。
- **給作者看的形式很重要**：原尺寸 32×48 太小，一律放大 8 倍並做成 GIF；兩種速度並排讓作者比較，比文字描述有效。

## 6. Godot 端的重點

- 圖片匯入改成**無損**（專案預設有損 0.82，像素圖會糊）；節點用 Nearest 濾鏡、放大 2 倍。
- 角色在畫格中偏左 1px，左右兩套互為翻轉，所以 Sprite 的 x 在面向右時是 3、面向左時是 −1，轉身時身體中心才不會跳動。
- 動畫依「**實際**有沒有移動」切換（不是看有沒有按鍵），走到區域邊緣被擋住時會回到待機。
- `editor_refresh` 指定單一**新**檔案時不會匯入，要用全專案掃描。

## 7. Lv3 結論

1. **兩個 MCP 能完成「畫圖 → 進遊戲」的完整流程**，中間只靠一張 spritesheet 交接。
2. **Pixelorama MCP 很精確也很穩定**，但它只是「畫筆」：造型與動作要另外用程式設計，AI 的優勢在精確修改與驗證。
3. **「複製相近的格＋只送差異」是畫動畫的關鍵技巧**，傳送量大幅減少。
4. **主觀判斷仍然靠人**：作者指出「沒有走路感、沒有轉向」，並選了左右分開畫和 8 fps。

---
---

# Lv4：多區域、物品與旗標

- 日期：2026-10-05
- MCP：**godot-mcp-toolkit**（區域場景、autoload、SpriteFrames 以外的節點、驗證）＋ **pixelorama**（6 個像素道具）
- 成果：停車場（改成 v1.5）→ 街道 → 診所三個區域可以來回走；錄音筆「拿到前後事件不同」；數值（記憶、人性）與旗標在背景記錄；離開診所接回 1.0 的場景 6。
- 狀態：**Lv4 完成**（完成標準 5/5）。自動測試 24/24 通過；作者在 Godot 與瀏覽器試玩確認（`index.pck` 約 47.9MB）。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| Lv4-0 | 範圍與資料格式 | — | 寫文件 |
| Lv4-1 | GameState、新格式、劇本檢查 | `autoload_manage`（註冊 GameState）、`script_check`、`lsp_project_diagnostics` | GDScript；劇本檢查與單元測試在專案副本上跑 |
| Lv4-2 | 區域切換 | `execute_code` 以 `Dictionary.merge` **在記憶體裡加一個測試區域**（不建檔案）、`input_simulate`、`runtime_screenshot` | `main.gd`／`area.gd`／`player.gd` |
| Lv4-3 | choice／item／variants、停車場 v1.5 | `scene_create_node`（醒來的地方）、`input_simulate` 的 `key`（方向鍵＋Enter 測選項） | `main.gd`、`parking_lot.json` |
| Lv4-4 | 街道 | **`editor_save_scene` 另存**停車場 → `node_manage`（改名、排序）、`scene_delete_node`、`node_set_property`（批次） | `street.json` |
| Lv4-5 | 診所 | 同上；`node_manage` duplicate（**子節點沒存進檔案**，改成重建） | `clinic.json`、`area_data.gd`（variant 分開記錄） |
| Lv4-6 | 像素道具 | pixelorama `create_canvas`／`draw_pixels`／`import_image`／`save_project`／`export_image`；Toolkit 建立 Sprite2D | Python 設計格線、ImageMagick 比對 |
| Lv4-7 | 測試與匯出 | — | headless 自動測試（副本，載入真正的 Main.tscn）、headless 匯出 |

## 2. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 街道的 `spawns` 指向還沒建立的診所 | 劇本檢查 | 先拿掉，診所建好再加回 |
| 2 | 背景圖重複拼接在中段有接縫 | 截圖 | 遠景只以 0.3 倍速移動，只需約 1500 寬 → 一張圖等比例蓋滿；**素材尺寸因此改成 1536×768** |
| 3 | 複製的互動點存檔後缺子節點 | 讀 `.tscn` | Toolkit 的 duplicate 不保存子節點 → 重建 |
| 4 | **先看過診療椅，拿到錄音筆後的選項版本不會出現** | MCP 照設計的流程實際走一遍 | 自動旗標讓「只觸發一次」誤判 → 每個 variant 的完成紀錄與數值來源分開（`clinic.chair#0`） |
| 5 | 藥櫃擋住主角 | 截圖 | 區域場景裡 `Points` 排在 `Player` 前面 |
| 6 | 藥櫃色塊太高（主角的兩倍），錄音筆高過頭頂 | 截圖 | 降到 120 |
| 7 | 照片、啟事、字卡的人臉用了主角的灰青膚色 | 放大預覽 | 改成一般膚色（感染前／圖畫） |
| 8 | `import_image` 匯入後 1 個像素變成相近的顏色 | 逐像素比對 | `draw_pixels` 補回 |

作者回饋 3 次（媽媽改長頭髮、字卡往下、藥櫃也畫成像素圖），每一步都由作者試玩確認後才繼續。

## 3. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 劇本檢查 | 新增 12 項（物品／旗標／數值對得上、出口與出現位置存在、每個區域走得到）；用故意寫錯 12 處的測試區域確認全部抓得到 | 通過 |
| 單元測試 | GameState 與 variants 的邏輯 | 12/12 |
| **自動遊玩測試**（Lv4-7） | headless 載入真正的 `Main.tscn`，用互動鍵與按選項跑三輪：A 不拿錄音筆、B 拿錄音筆、C 回標題再玩一輪 | **24/24** |
| 測試的有效性 | 故意把診療椅的條件改錯 → 遊玩測試 4 項失敗、劇本檢查也抓到 | 兩道檢查都有效 |

## 4. 兩個 MCP 的特性（Lv4 新發現）

| MCP | 觀察 |
|---|---|
| godot-mcp-toolkit | `editor_save_scene` 帶 `file_path` 可以另存場景，**做新區域最快**；`duplicate` 不保存子節點；`input_simulate` 的 `action` 不會移動按鈕焦點，測鍵盤選項要用 `key`；瞬移主角後要等物理更新 |
| pixelorama | 小道具一個畫布、`draw_pixels` 一次送完最單純；大圖改用 **`import_image`**：只吃 RGB／RGBA（調色盤 PNG 會被拒絕），而且**會把相近的顏色合併**，匯入後一定要比對 |

## 5. 專案變大之後，AI 的品質

- **規模**：腳本 9 個、區域 3 個、互動點 14 個。主要的錯誤（診療椅的 variant）不是寫錯程式，而是**兩個功能組合時的邊界情況**（自動旗標 × 只觸發一次 × variants）。
- **抓到它的是「照作者設計的流程實際走一遍」**（先坐 → 拿錄音筆 → 再坐），單元測試原本沒有這個情況。修好後把它加進單元測試和遊玩測試。
- **自動遊玩測試的價值**：三輪 24 項只要幾十秒，之後 Lv5 加東西時可以重複執行，確認 Lv4 的行為沒有被破壞。

## 6. Lv4 結論

1. **資料驅動的格式撐得住**：三個區域、物品、條件、多出口都只靠 JSON 描述，程式不用為每個區域寫特例。
2. **MCP 做場景、測試靠腳本**：建區域與調畫面用 Toolkit 最快；完整的遊玩流程用 headless 測試比 MCP 一步步操作穩定得多。
3. **「另存再修改」是做新區域的好方法**，但要注意複製節點的陷阱。
4. **給 Lv5 的建議**：剩下的 4 個區域照「另存 → 修改 → 資料 → 遊玩測試」的流程做；數值、Bad End、結局條件加進遊玩測試（最佳／一般／最差路線）。

---
---

# Lv5：其餘區域、Bad End 與結局

- 日期：2026-10-05～10-06
- MCP：**godot-mcp-toolkit**（4 個新區域場景、執行與截圖驗證）；本級沒有用到 pixelorama（像素人物與場景物件移到 Lv6）
- 成果：停車場 → 街道 → 診所 →〔搜捕隊〕→〔手術台〕→ 設施走廊 → 廢墟與避難所 → 舊家 →〔營火〕→ 牆前 → 結局，**7 個區域＋3 段過場**從頭玩到尾；3 個 Bad End 可以「從這裡重試」（回到檢查點、數值還原）；結局依記憶／人性解鎖，不夠的選項顯示灰色「……（你想不起來）」。
- 狀態：**Lv5 完成**（完成標準 6/6）。自動測試 Lv4 24/24、Lv5 29/29；劇本檢查通過；作者在瀏覽器試玩確認（`index.pck` 約 47.9MB）。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| Lv5-0 | 拆成 Lv5／Lv6、範圍與格式 | — | 寫文件 |
| Lv5-1 | 檢查點、Bad End 重試、數值選項與鎖定、F3 數值 | `execute_code`（設定數值、跳到場景）、`input_simulate`、`runtime_screenshot` | `main.gd`、`game_state.gd`；劇本檢查加「窮舉路線」 |
| Lv5-2 | 設施走廊 | `editor_save_scene` 另存診所 → `node_manage`、`scene_delete_node`、`node_set_property`（批次） | `lab.json`、區域選項支援 `item` |
| Lv5-2-1 | 診所字卡掛到柱子上（作者回饋） | `scene_create_node`、`node_set_property` | — |
| Lv5-3 | 廢墟與避難所 | 同 Lv5-2 | `ruins.json` |
| Lv5-4 | 舊家 | 同上；互動點子節點用 `scene_create_node` 重建（避開 duplicate 的陷阱） | `home.json`（女兒用 variants 依筆記本換文字） |
| Lv5-5 | 牆前與結局 | 同上；`execute_code` 設定數值後重新產生選項，截圖三種解鎖情況 | `wall.json`、`story.json`（刪暫時的場景 17）；最後的亮度微調**直接改 `.tscn`**（原因見下方 #6） |
| Lv5-6 | 測試、匯出、紀錄 | `lsp_project_diagnostics` | headless 遊玩測試與匯出（專案副本，MCP 沒有匯出工具） |

## 2. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 結局 A 需要記憶 6，但 Lv5-1 時最多只到 5；BE2、BE3 走不到 | 劇本檢查的**窮舉路線** | 預期中的缺口，當成待辦清單：每補一個區域重跑，Lv5-3 起全部通過（最後上限記憶 9、人性 9） |
| 2 | 暫存區被系統清空，Lv4 的遊玩測試腳本不見 | 要執行時找不到 | 依對話紀錄重寫；作者決定測試放進專案的 `tests/`，加 `run_tests.sh` 自動建立副本 |
| 3 | 診所的柱子被窗光與手電筒照得太亮 | 截圖 | 改成暗的舊灰泥色 |
| 4 | 舊家的窗戶與女孩被對話框擋住 | 截圖 | 往上移到對話框上方 |
| 5 | 牆前沒有出口，劇本檢查報錯 | 劇本檢查 | 規則放寬：一定能選（沒有 `require`）、會離開區域的選項也算出口（「永遠遊走」） |
| 6 | **另存後編輯器仍在編輯原檔**：牆前的修改被存進 `Home.tscn` | 存檔回傳的路徑是 `Home.tscn` | 另存成 `Wall.tscn` 後用 git 還原 `Home.tscn`；寫進 `CLAUDE.md` 的規則 |
| 7 | 另存的 `Wall.tscn` 分頁停在舊內容，`editor_refresh` 也不會重新載入 | `scene_get_tree` 的根節點還叫 Home | 不在那個分頁存檔；亮度微調直接改 `.tscn`，請作者關掉分頁重開 |
| 8 | 牆面色塊被燈照成幾乎全白 | 截圖 | 調暗色塊與燈光 |
| 9 | 測試時出現 `set_can_move` on Nil | 遊戲 log | **Claude 測試步驟的錯**：在 `_start_game` 淡出還沒結束時就切換區域；分開執行即正常，玩家不會遇到 |

作者回饋：場景物件（燈、殘骸、車體等色塊）改在 Lv6 畫成像素圖；診所字卡不要漂浮。

## 3. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 劇本檢查 | 格式＋**窮舉所有路線**：6 個結局都走得到、數值上限（寬鬆估計）達到結局門檻、鎖住的選項門檻達得到 | 通過（9 個場景、7 個區域） |
| Lv4 遊玩測試 | 停車場～診所三輪（改成繼承共用的 `play_base.gd`） | 24/24 |
| **Lv5 遊玩測試** | 最佳路線（記憶 9、人性 8）→ A；一般路線（記憶 3、人性 −2，A 鎖住）→ B；最差路線（初始值，只剩 C）→ C；BE1／BE2／BE3 重試回到檢查點、數值與物品還原、事件人物重新出現；Bad End 回標題後重設 | **29/29**（全部約 40 秒） |
| lsp | 全專案（含測試） | 12 個檔案 0 錯誤 |
| Web 匯出 | `.pck` 內有 `story.json` 與 7 個區域資料；沒有外掛、測試、劇本檢查工具 | 通過 |

## 4. MCP 的特性（Lv5 新發現）

| 觀察 | 說明 |
|---|---|
| 另存不會切換編輯中的場景 | `editor_save_scene` 帶 `file_path` 後，接下來不帶路徑的存檔仍寫回**原檔**。Lv4 沒出事是因為另存後剛好先 `scene_open` 了新檔 |
| 編輯器不會重新載入已開的分頁 | 檔案在外部被改（或在另存前就開過），分頁會停在舊內容，`editor_refresh` 無效；`scene_get_tree` 的 `source` 和根節點名稱可以拿來確認 |
| runtime 連線仍要輪詢 | `game_start` 後常見 `GAME_NOT_RUNNING`，登錄檔其實已寫好；`runtime_poll` 後再等 3～5 秒最穩 |
| `execute_code` 很適合測資料驅動的遊戲 | 直接設定數值（`Dictionary.merge`）再重新產生選項，一次截完三種解鎖情況，不用真的玩三輪 |
| 過場的選項沒有鍵盤焦點 | 區域裡的選項會自動聚焦（可用 Enter），過場（搜捕隊、手術台、營火）只能用滑鼠點；測試時用 `click` 座標 |

## 5. Lv5 結論

1. **資料格式撐到最後**：7 個區域、3 段過場、6 個結局、檢查點都只靠 JSON 描述；Lv5 的程式改動集中在 Lv5-1，之後 4 個區域幾乎只寫資料與排場景。
2. **窮舉路線是好用的「待辦清單」**：還沒做的區域會讓結局走不到、門檻達不到，每補一塊就少一項錯誤，最後全綠。
3. **遊玩測試從 Lv4 延續下來最有價值**：共用操作抽成 `play_base.gd` 後，Lv5 的 29 項一次就通過；之後 Lv6 調整數值平衡時可以直接重跑。
4. **MCP 的編輯器狀態要自己確認**：另存、外部修改都可能讓「編輯器裡的場景」和「磁碟上的檔案」不一致，存檔前先看 `scene_get_tree`。
5. **給 Lv6 的建議**：過場選項的鍵盤焦點、像素人物與場景物件（取代色塊）、衝動機制（甲）、數值平衡（目前最佳路線記憶 9／人性 8，結局 A 門檻記憶 6、人性 3，可以再收緊）。

---
---

# Lv6：衝動機制、像素人物與場景物件、鍵盤操作、平衡

- 日期：2026-10-06
- MCP：**godot-mcp-toolkit**（節點、shader 疊層、`sound_generate`、換色塊、執行與截圖驗證）＋ **pixelorama**（6 組人物、18 張場景物件）
- 成果：所有選項只用鍵盤就能選；靠近「還沒發生的事件」時畫面泛紅、心跳加快、手電筒閃爍；6 組人物畫成像素圖（原圖有的照原圖）；6 個區域的色塊換成像素物件（燈、殘骸、車、路牌、柱子、圍籬、窗戶、門等）。
- 狀態：**Lv6 完成**（完成標準 6/6）。自動測試 Lv4 24/24、Lv5 29/29、Lv6 24/24；劇本檢查通過；lsp 14 個檔案 0 錯誤；作者完整試玩一輪確認平衡不用調整；Web 版 `index.pck` 約 47.9MB。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| Lv6-0 | 範圍、`impulse` 格式、人物規格、物件清單 | — | 寫文件 |
| Lv6-1 | 所有選項自動聚焦、鎖住的不能聚焦 | `input_simulate`（`key`：方向鍵、Enter）、`runtime_screenshot` | `main.gd`；`test_lv6.gd` 改用真正的按鍵 |
| Lv6-2 | 衝動機制（甲） | `scene_create_node`（ImpulseOverlay＋Heartbeat）、`node_set_property`（ShaderMaterial）、**`sound_generate`**（暫用心跳聲）、`execute_code`（瞬移量距離）、`runtime_screenshot` | shader、`impulse_fx.gd`、`main.gd`、劇本檢查認得 `impulse` |
| Lv6-3 | 婦人（定規格） | pixelorama `create_canvas`、`draw_pixels`、`clear_cel`、`save_project`、`export_image`；Toolkit 換 `Figure` | 造型用 Python 格線設計；`.import` 改無損 |
| Lv6-4 | 其餘 5 組人物 | pixelorama `import_image`、`draw_pixels`（補像素）；Toolkit `node_set_property`（`region_rect` 讓女兒只露出上半身） | 同上 |
| Lv6-5 | 6 個區域的場景物件（牆前保留色塊、改英文字） | pixelorama `import_image`、`draw_pixels`、**`draw_rect`（半透明玻璃）**、`rename_canvas`、`switch_canvas`；Toolkit `scene_delete_node`、`scene_create_node`、`node_manage`（`duplicate` 燈光、`reorder` 前後順序）、`node_set_property` | Python 設計（共用 `pix.py`：外框、半透明、字型）、ImageMagick 逐像素比對 |
| Lv6-6 | 平衡 | — | 作者試玩一輪，數值不變 |
| Lv6-7 | 測試、匯出、紀錄 | `lsp_project_diagnostics` | headless 遊玩測試與匯出（專案副本，MCP 沒有匯出工具） |

## 2. 作者回饋與調整

Lv6 幾乎每一步都是「Claude 做第一版 → 作者看截圖 → 改一輪」，主觀的地方都由作者決定：

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 婦人 | 「是參照原本場景圖片的人物塑造的嗎」 | 第一版只照劇本文字設計 → 照 scene_02 重畫；之後立下規則：**原圖有的照原圖畫，沒有的才自己設計**（存進記憶） |
| 婦人的嘴 | 尖叫的嘴型很怪 | 改回閉著的一格（手舉起來保留） |
| 警衛 | 要拿槍 | 加步槍與槍管下的手電筒 |
| 女兒 | 全身站在窗前很怪 | `region_rect` 只顯示上半身＋窗台擋住切口 |
| 感染者群 | 應該是一般人大小 | 照主角比例重畫（舊版另存 `horde_small`） |
| 出口 | 「做個門把才有門的感覺，用喇叭鎖」、不用 EXIT | 坡道 → 喇叭鎖鐵門；EXIT 版另存備用；之後換色成木門、做成破損版、舊家的鑲板門 |
| 燈管 | 頻率再慢一點 | 熄滅機率 0.03 → 0.01 |
| 車體 | 放大 1.3 倍 | 座標乘 1.3 重畫（不用非整數縮放，像素大小一致） |
| 尋人啟事的桿子 | 畫風一致 | 和路牌同畫風的水泥電線桿 |
| 背景已有字的兩個色塊 | 保留，改成英文 | `Daddy, I know it's you.`、`I'm still here.` |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 選項剛出現時按空白鍵會**直接選到第一個**（自動聚焦的副作用） | MCP 截圖時狀態不對 | 選項出現後 0.3 秒內不接受選擇；加進測試 |
| 2 | 遊戲嵌在編輯器裡，編輯器不在前景時截圖是**舊畫面** | 截圖裡主角位置和讀到的座標不一致 | 先送一個無作用的 `execute_code`、等 0.5 秒再截（寫進 `CLAUDE.md`） |
| 3 | 新 PNG 預設**有損壓縮**，像素顏色會跑掉 | 遊戲截圖顏色和設計不同 | `.import` 改 `compress/mode=0` |
| 4 | Pixelorama `import_image` **會掉像素**（每張 3～49 格；稀疏細線的圍籬掉 471 格） | 每張匯出後都逐像素比對 | 用 `draw_pixels` 一次補回；比對改用 txt 逐格比（`compare -metric AE` 的數字不是格數） |
| 5 | `import_image` 會把**半透明像素變成不透明**（窗戶玻璃變實心） | 逐像素比對差 4540 格、並排看圖 | 匯入後用 `draw_rect`／`draw_pixels` 以 `#RRGGBBAA` 重畫玻璃 |
| 6 | 燈管被場景的暗色蓋成灰色，看不出是亮的 | 截圖 | `node_manage` 複製紅色警示燈，改成淡藍色、偶爾熄滅（文字「光線閃爍」） |
| 7 | 第一版預覽：感染者像墓碑、背像石頭、破窗像星空、鐵絲網太密看不到妻子 | 給作者看之前先看預覽 | 各自改一輪才交給作者 |
| 8 | 連續兩次在長串工具操作後**用英文回報** | 作者提醒 | 寫進記憶：工具之間的進度短句也用繁體中文 |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 劇本檢查 | 格式、窮舉路線、`impulse` 欄位（故意寫錯 2 種都抓到） | 通過 |
| Lv4／Lv5 遊玩測試 | 改用真正的按鍵選選項後照常通過 | 24/24、29/29 |
| **Lv6 遊玩測試** | 選項聚焦與方向鍵、Enter 只開始打回應、空白鍵一次只做一件事、0.3 秒內不誤選、鎖住的選項不能聚焦、結局用 Enter 回標題、標題按一次空白鍵不跳過開場；衝動強度隨距離變化、選項出現時最強、選完淡出、手電筒還原、人走後不再觸發 | **24/24** |
| 像素圖 | 每張設計圖與匯出圖逐格比對 | 6 組人物＋18 張物件全部 0 差異 |
| lsp | 全專案 | 14 個檔案 0 錯誤 |
| Web 匯出 | `.pck` 有劇本、7 個區域資料、人物與物件圖、shader、心跳聲；沒有外掛、測試、`art/` 原始檔、劇本檢查工具 | 通過 |

## 5. MCP 的特性（Lv6 新發現）

| 觀察 | 說明 |
|---|---|
| Pixelorama 的 `import_image` 不是無損的 | 大張、稀疏、半透明的圖都會出錯；`draw_pixels` 才是精確的。最穩的做法是「匯入 → 比對 → 補差異」 |
| `draw_pixels` 一次可以送很多格 | 圍籬一次補 471 格沒有問題 |
| Toolkit `sound_generate` 夠當暫用音效 | 心跳聲直接在專案裡產生，作者之後再換 |
| `node_manage` 的 `duplicate` 適合複製燈光 | 沒有子節點的節點可以安全複製（GradientTexture 與腳本都會帶過去） |
| `reorder` 控制畫的前後 | 妻子在圍籬後、海報在電線桿前、窗戶在女兒前，都靠節點順序 |
| runtime 偶爾要重開 | 一次 `GAME_NOT_RUNNING` 輪詢無效，`game_stop`＋`game_start` 後正常 |

## 6. Lv6 結論

1. **「AI 先做、人來挑」是畫素材最有效的節奏**：每一區先給預覽或截圖，作者一句話（「用喇叭鎖」「放大 1.3 倍」「畫風一致」）就能精準改；造型的好壞仍然只有人能判斷。
2. **參考原圖要明確寫成規則**：第一個人物沒看原圖，作者指出後寫進規格與記憶，之後 5 組人物、6 區物件都先找原圖。
3. **工具會出錯，所以每一步都要能驗證**：Pixelorama 的匯入會掉像素、會吃掉透明度，靠逐像素比對全部抓出來；如果只看截圖，很多錯不會被發現。
4. **測試讓「改體驗」也能放心**：鍵盤、衝動機制、0.3 秒防誤選都寫成測試，之後換素材、調參數都可以重跑。
5. **作者的評價**：以第一版來說很好；下一版想做會動的像素、音效、更多場景與互動方式（記在 `docs/開發路線圖.md` 第 6 節）。

---
---

# 整體總結：階段 1 到 Lv6

從 Kivy 版的選項式遊戲，到 Godot 網頁版的橫向捲軸冒險（7 個區域、3 段過場、6 個結局、衝動機制、像素人物與物件），全程用 Claude Code ＋ 兩個 MCP（godot-mcp-toolkit、pixelorama）完成。

## 1. 每一級做了什麼

| 級 | 內容 | 主要的 MCP 用法 |
|---|---|---|
| 階段 1 | 視覺小說版：標題、打字機、選項、BGM 交叉淡入、結局 | Toolkit 建整個 UI、截圖與模擬點擊驗證 |
| Lv1 | 停車場可以走動（替代美術） | 建區域場景、`input_simulate` 走路 |
| Lv2 | 景深分層與光影 | Parallax2D、CanvasModulate、PointLight2D；執行中改數值再截圖給作者選 |
| Lv3 | 畫主角（20 格動畫） | 第一次兩個 MCP 配合：Pixelorama 畫 → spritesheet → Toolkit 切成 SpriteFrames |
| Lv4 | 多區域、物品與旗標、劇本 v1.5 | 另存區域再修改；headless 遊玩測試開始 |
| Lv5 | 其餘區域、Bad End、結局依數值 | 資料驅動，4 個區域幾乎只寫 JSON 與排場景 |
| Lv6 | 鍵盤、衝動機制、像素人物與物件 | Pixelorama 量產素材、Toolkit 換色塊與 shader |

## 2. AI 與 MCP 幫最多的地方

| 地方 | 為什麼 |
|---|---|
| **自己執行、自己看、自己修** | `game_start`＋`execute_code`＋`input_simulate`＋`runtime_screenshot`＋`debugger_get_log` 讓 Claude 能像玩家一樣操作並檢查畫面，很多問題在作者看到之前就修好了 |
| **建場景與節點** | 7 個區域、所有色塊換成 Sprite、燈光、shader 疊層，全部用 Toolkit 完成，很少手改 `.tscn` |
| **精確的像素繪圖** | 造型用程式設計，Pixelorama 照格畫，逐像素比對保證「設計＝成品」；改一個嘴巴只要 3 格 |
| **資料驅動的格式＋檢查工具** | 劇本、區域、條件、結局都在 JSON；劇本檢查窮舉所有路線，任何改動都能馬上知道結局還走不走得到 |
| **自動遊玩測試** | 77 項測試（Lv4 24、Lv5 29、Lv6 24）用真正的按鍵玩三條路線、三個 Bad End、鍵盤與衝動機制，約 40 秒跑完 |
| **把經驗寫成規則** | 每個踩過的坑（另存的陷阱、截圖舊畫面、有損匯入、掉像素、半透明）都寫進 `CLAUDE.md`，之後不再犯 |

## 3. 仍然需要人的地方

| 地方 | 例子 |
|---|---|
| **好不好看、好不好玩** | 背景太黑、婦人沒照原圖、女兒全身站在窗前很怪、感染者太小、出口要有門把、燈管閃太快——全部是作者看出來的 |
| **聽聲音** | BGM 換曲、心跳聲、音效好不好聽，Claude 聽不到 |
| **劇本** | Claude 可以起草，但定稿一定是作者 |
| **方向與取捨** | 改走可移動的新路線、Lv5 拆成 Lv5／Lv6、背景已有字的色塊要保留、這一版先到這裡 |
| **環境與安全** | 安裝 MCP 與外掛、匯出模板、在真正的瀏覽器試玩、關掉沒有驗證機制的 Pixelorama 連線 |
| **提醒 AI 的習慣** | 回答語言、參考原圖——作者提醒一次後寫進記憶 |

## 4. 給下一版的建議

1. **素材流程已經成熟**：Python 設計 → 預覽給作者 → Pixelorama 畫 → 逐像素比對 → Toolkit 換上 → 截圖確認。會動的像素可以沿用 Lv3 的「複製相近的格＋只送差異」。
2. **音效需要作者準備或挑選**：`sound_generate` 只適合暫用；腳步、環境音、互動音請作者決定風格。
3. **新的互動方式先寫進資料格式**：照 Lv4～Lv6 的做法擴充 JSON 欄位，同時讓劇本檢查和遊玩測試認得它。
4. **網頁版的大小**：`index.pck` 約 48MB（音樂占大部分），公開發布前再處理。

---
---

# A＋ A1：分層背景

- 日期：2026-10-08～2026-10-13
- MCP：**godot-mcp-toolkit**（建節點、排版、匯入、執行與截圖驗證）＋ **pixelorama**（74 張像素素材）
- 成果：7 個區域都從「一張插畫＋色塊」變成五層：遠景 0.3、中景 0.7、遊戲層 1.0（含像素地面）、近景（依前後排序）、前景 1.3。停車場遠景的重複拼接接縫修掉；燈管加上遊戲層的吊架；街道、診所、設施走廊、廢墟、舊家各有一個**放在路中間、不能穿過的障礙物**；牆前的灰色色塊換成灰泥牆面。
- 狀態：**A1 完成**。測試 98 項通過（劇本檢查＋Lv4 24、Lv5 29、Lv6 24、A1.5 21）；Web 版 `index.pck` 48.0MB（A1 全部素材只多約 0.1MB）；作者在編輯器試玩確認。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| A1-0 | 讀現況、規劃五層 | `game_start`、`execute_code`（讀各層位置）、`runtime_screenshot` | 寫規劃 |
| A1-1 停車場 | 中景柱、天花板條、遠處的車、前景柱、地面、血泊、燈管吊架、近景 4 種 | pixelorama `import_image`、`draw_pixels`、`save_project`、`export_image`；Toolkit `scene_delete_node`、`scene_create_node`、`node_set_property`（`batch`）、`node_manage`（`reorder`）、`editor_refresh` | Python 設計圖＋ImageMagick 合成預覽與逐像素比對；`.import` 改無損 |
| A1-2 街道 | 店面×2、電線桿、公車亭、停著的車、地面、近景、前景；燒毀的車放到路中間 | 同上＋Toolkit `scene_create_node`（`StaticBody2D` 阻擋）、`input_simulate`（實測擋住的位置） | 屬性清單用 Python 產生 JSON 再一次送出（避免手打錯） |
| A1-3～A1-6 | 診所、設施走廊、廢墟、舊家 | 同上；pixelorama `draw_rect`（補整排掉的像素） | 同上 |
| A1-7 牆前 | 灰泥牆面取代色塊（英文字保留 Label）、極簡的中景與前景 | 同上 | 同上 |
| 收尾 | 測試、匯出、紀錄 | — | headless 測試與匯出（專案副本） |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 前景柱 | 用 B（像素剪影＋邊緣細節） | 「2D 與 2.5D 素材需求本來就不一樣，視情況調整」寫進記憶，Lv6 的畫面決定在 A＋ 只當參考 |
| 燈管 | 換素材後像飄在天上 | 遊戲層短梁＋吊鏈（中景的梁移動速度不同，不能掛在中景） |
| 人物移動 | 想要像《小朋友齊打交 2》那樣上下左右走 | 插入 A1.5（見下一節），排在其他 6 區之前，避免地面與近景重做 |
| 燒毀的車 | 看 A／B 截圖後選 B（放到路中間） | 加 `Block`（StaticBody2D），從車前或車後繞過去都能調查 |
| 障礙物 | 診所、設施走廊、廢墟、舊家都要 | 擔架床、翻倒的實驗推車、拒馬、倒下的衣櫃 |
| 流程 | 「素材製作完成後就直接放到場景上」 | 只在設計圖與最後成果兩處請作者看（寫進記憶）；A1-4 起「現況＋規劃＋設計圖」一次給 |
| 牆前 | 同意把色塊換成灰泥牆面 | 英文字仍用 Label，保持清楚 |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 停車場遠景用**重複拼接**，走到出口有接縫、翻倒的車出現兩次 | A1-0 截圖 | 改等比例蓋滿、寬 1500（其他區早就是） |
| 2 | 設計圖預覽每一區第一版都有問題：中景太亮搶戲、店面像紙盒、牆板擋掉背景、倒塌的樓像完整方塊、斷牆變鋸齒、牆面像告示板 | 給作者看之前先疊在實際截圖上看 | 調暗、透空（觀察窗、破洞）、改不規則輪廓後才交給作者 |
| 3 | 預覽合成時 `-resize` 沒用括號，套用到整張圖 | 預覽尺寸變成 2304 | 每個疊圖都加括號 |
| 4 | Pixelorama `import_image` 每一區都會掉像素（停車場 4 格 → 牆前 167 格，舊家沙發整排 102 格） | 每張都逐像素比對 | `patch.py` 算出差異，`draw_pixels`／`draw_rect` 補回，全部 0 差異 |
| 5 | 前景剪影可能擋住主角或互動物件 | 擺放前用「前景 x − 1.3 × 鏡頭位置」算每個互動點 | 每一區都先算再放，實際截圖確認 |
| 6 | 暫存區被系統清空，繪圖工具不見 | A1-6 開始時找不到檔案 | 工具改放專案的 `art/tools/`（`.gdignore`，不匯出） |
| 7 | runtime 連線時好時壞 | `GAME_NOT_RUNNING` | 「停止重開」或「等 5 秒再輪詢兩次」，都記進路線圖 |
| 8 | 作者自己按 F5 試玩時，Claude 的指令送進同一個遊戲 | `game_start` 回報已經在執行 | 先停止再重開，並請作者試玩時先說一聲 |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 像素圖 | 74 張設計圖與匯出圖逐格比對 | 全部 0 差異（補回共 651 格） |
| 視差 | 讀各層畫面位置，對照鏡頭位移 | 0.3／0.7／1.0／1.3 正確 |
| 阻擋 | `input_simulate` 按住方向鍵，讀主角停下的位置 | 車 738、擔架床 873、推車 868、拒馬 1123、衣櫃 793，都等於物件邊緣減去腳寬的一半 |
| 遊玩測試 | 換完 7 區畫面後全部重跑 | 98 項通過 |
| FPS | 每一區 | 60（編輯器內） |
| Web 匯出 | `.pck` 有 67 張圖層素材、道具、影子、劇本與 7 個區域資料；沒有外掛、測試、`art/` | 通過 |

## 5. MCP 的特性（A1 新發現）

| 觀察 | 說明 |
|---|---|
| `node_set_property` 的 `batch` 很適合大量排版 | 一區 20～30 個 Sprite 的貼圖、位置、縮放、翻轉一次送出；用 Python 產生 JSON 可以避免手打錯 |
| `NewResource` 可以直接建碰撞形狀 | 阻擋範圍、觸發範圍都不用另外建 `.tres` |
| `TextureRect` 的 `stretch_mode = 1` 加 `scale 2` 就是可拼接的像素地面 | 天花板管線條也一樣 |
| Pixelorama 的錯誤有規律 | 常是某一欄或某一列整條跑掉；`draw_rect` 一次補整排最快 |
| 截圖的顏色要讀數值判斷 | 圖片看起來偏亮，實際像素值很暗；用 `magick` 讀像素才知道 |

## 6. A1 結論

1. **「疊在實際截圖上預覽」比單看素材有用**：每一區第一版的問題都是放進畫面才看得出來（太亮、太方、擋背景），所以先合成預覽、自己修一輪再給作者。
2. **前景要先算再放**：前景移動得比主角快，擺錯位置會剛好擋住互動物件；用公式算每個互動點的螢幕位置，比放完再截圖找問題快。
3. **流程可以越來越短**：從「規劃 → 確認 → 設計 → 確認 → 製作 → 確認」縮成「規劃＋設計 → 確認 → 製作並放進場景 → 確認」，一區的往返從 4 次變 2 次。
4. **背景插畫仍是最大的落差**：7 張遠景都還是原本的第一人稱插畫（翻倒的車、拿筆記本的手、牆上的大字），要等作者用生圖 AI 產生 P1～P7 才會和側面視角一致。

---

# A＋ A1.5：上下左右移動（縱深帶）

- 日期：2026-10-08
- MCP：**godot-mcp-toolkit**（`input_map`、場景排序與觸發範圍、執行驗證）＋ **pixelorama**（影子）
- 成果：主角可以在縱深帶（腳的 y 650～735）上下左右走，上下 0.6 倍速；腳下有影子；人物、互動物件、近景依腳的位置前後遮擋；互動提示浮在頭上；互動要走到物件前面才觸發；婦人、科學家、警衛站到路中間。
- 狀態：**A1.5 完成**，作者試玩確認手感。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| A1.5-0 | 縱深帶範圍、要不要深度縮放 | `execute_code`（直接改主角的 y 與縮放）、`runtime_screenshot` | — |
| A1.5-1 | 上下移動、影子、頭上的提示 | **`input_map_action`／`input_map_event`**（新增 `move_up`／`move_down`，寫入實體按鍵）、pixelorama `create_canvas`＋`draw_pixels`（半透明影子）、`node_set_property`（提示標籤改成不錨定） | `player.gd`、`area.gd`、`main.gd`；影子由程式加到 7 個場景共用的 Player |
| A1.5-2＋3 | y 排序、腳底判定、27 個互動點的觸發範圍、人物站到路中間 | `node_set_property`（`y_sort_enabled`、`z_index`、`NewResource` 形狀）× 7 個場景 | 腳底判定在 `player.gd`；`spawns` 支援 `[x, y]` |
| A1.5-4 | 測試 | `lsp_project_diagnostics` | 新增 `tests/test_a15.gd` 21 項 |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 深度縮放 | 不縮放 | 0.92 倍會讓像素粗細不均；規則「像素圖只用整數倍放大」寫進 `CLAUDE.md` |
| 提示位置 | 浮在主角頭上 | 原本固定在畫面下方，往外側走會擋路 |
| 觸發範圍 | 「還沒靠近物品就有提示」 | 主角判定改成腳底 24×12；互動點寬度和物件差不多，只涵蓋物件前方的地面；人物事件涵蓋整個縱深帶，避免從外側繞過劇情 |
| 婦人 | 應該站在路中間 | y 692；之後科學家、警衛也移過去，妻子、女兒、感染者群照劇情留在原位 |
| 速度 | 「上下左右速率很好」 | 不變 |

## 3. 自動驗證（`tests/test_a15.gd`，21 項）

移動到縱深帶邊緣停住、上下速度比例 0.6、影子畫在角色下面；離物件 100 沒有提示、60 有提示、提示在頭上、站在外側不觸發、站到前面可以調查、從最外側走向婦人照樣觸發；區域／互動點／近景都依 y 排序、前景在最前面、婦人在路中間；`place_player(x, y)` 的 y 與邊界；`spawns` 寫 `[x, y]` 通過、故意寫錯兩種都報錯。

## 4. A1.5 結論

1. **玩法的改動要在畫素材之前決定**：上下移動會改變地面高度與近景規則，所以插在停車場之後、其他 6 區之前，其餘區域一次就做對。
2. **「截圖 A／B 給作者選」對手感一樣有效**：縱深帶範圍、要不要縮放、車子放哪裡，都是先在遊戲裡暫時改、截圖給作者看再決定，不用先寫程式。
3. **改判定方式要 7 區一起改**：主角判定改成腳底後，其他區的互動點不跟著改就會碰不到，所以 A1.5-2 和 A1.5-3 合併做，每一區改完都跑全部測試。

---

# A＋ A2：光影與空氣感

- 日期：2026-10-13
- MCP：**godot-mcp-toolkit**（建節點、材質與 shader 參數、執行時調整強度、截圖驗證）；A2 沒有用到 pixelorama（粒子用 2×2 方塊、霧與光束用 shader，都不需要貼圖）
- 成果：7 區的主要燈光都有陰影，主角與 6 個人物有法線貼圖；每一區至少一種空氣感（停車場灰塵＋霧、街道火星＋霧、診所灰塵＋光束、走廊火花＋霧、廢墟灰燼＋霧、舊家光束、牆前光束）；人物事件時鏡頭推近、撲上去與槍聲時震動、衝動強度高時晃動。
- 狀態：**A2 完成**。測試 98 項通過；Web 版 `index.pck` 48.05MB（A2 只多約 0.05MB）；作者在瀏覽器測試完成。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| A2-0 | 7 區截圖、規劃每區的效果與效能風險 | `game_start`、`execute_code`（換區域、瞬移）、`runtime_screenshot` | — |
| A2-1 | 停車場陰影＋主角法線貼圖，匯出網頁版試效能；之後套到 7 區與 6 個人物 | `scene_create_node`（`LightOccluder2D`）、`node_set_property`（`NewResource` 建 `OccluderPolygon2D`、燈光的 `shadow_*`／`height`）、`editor_save_scene` | 遮光多邊形用 `art/tools/occluder_poly.py` 由貼圖算出（凸包，或歪斜的柱子用 `span` 逐列取左右邊）；法線貼圖用 `normal_map.py` 產生；網頁版匯出（專案副本 headless，MCP 沒有匯出工具） |
| A2-2 粒子 | 灰塵、火星、灰燼、診所灰塵、走廊火花 | `scene_create_node`（`CPUParticles2D`）、`node_set_property`（`NewResource` 建 `Gradient`、`CanvasItemMaterial`）；`execute_code` 在遊戲中直接改數量、大小拍 A／B | 比較圖用 ImageMagick 合成 |
| A2-3 霧與光束 | 霧 shader、光束 shader | `node_set_property`（`NewResource` 建 `ShaderMaterial`、`material:shader_parameter/…` 設參數）、`execute_code` 呼叫 `set_shader_parameter` 拍 A／B | shader、noise 貼圖、霧的共用材質 `.tres` 用檔案寫入（內容是程式碼／資源檔） |
| A2-4 鏡頭 | 推近、震動、晃動 | `scene_create_node`（`unique_name`）、`node_set_script`（回傳 `@export` 清單）、`script_check`、`input_simulate`（實際選「撲上去」測震動）、`execute_code`（讀 `zoom`／`offset`、暫時隱藏對話框重拍） | `scripts/camera_fx.gd`、`main.gd` 的掛勾；資料加 `"camera": "shake"` |
| A2-5 | 測試、匯出、紀錄 | — | headless 測試與匯出（專案副本） |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 網頁版效能 | 陰影＋法線貼圖在瀏覽器流暢 | 法線貼圖不縮小範圍，套到所有人物 |
| 出口門 | 被自己的遮光體壓暗，可以接受 | 其他區的門不加遮光體；可以看穿的圍籬也不加 |
| 粒子 | 選 B，「A 的顆粒太小」 | 大小 2～4、數量多（灰塵 150、火星 45、灰燼 140） |
| 霧與光束 | 選 A，「B 有點太多」 | 霧 0.3、光束 0.35；霧也加到街道、廢墟、走廊 |
| 鏡頭推近 | 第一次比較圖「文字擋住人物，看不出差別」 | 暫時隱藏對話框重拍；選 B（1.12），「壓迫感好一點」，震動、晃動一起用 B |
| 進度紀錄 | 「A＋ 的進度沒有做紀錄」 | 每一步都在路線圖加一列（寫進記憶） |
| 語言 | 報告變成英文時提醒「台灣繁體中文回答」 | 記憶補上：系統提醒之後的短句與長報告特別容易切回英文 |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 主角自己的遮光體讓主角變暗 | A2-1 截圖 | 拿掉主角的遮光體；物件的遮光體一律放在 Sprite 底下、不放在燈光裡 |
| 2 | 手電筒 `height` 0 時法線貼圖照不亮正面 | 截圖人物整個變暗 | 手電筒 80、區域燈 60；`area.gd` 新增 `flashlight_height` |
| 3 | 燈桿的凸包變成大三角形，影子形狀錯 | 截圖影子和柱子對不上 | `occluder_poly.py` 加 `span` 模式；共線的點去掉，多邊形更小 |
| 4 | 粒子 A 幾乎看不見 | 第一次截圖 | 灰塵被 `CanvasModulate` 壓暗 → 調高數量與不透明度；灰燼改成不受燈光影響 |
| 5 | 火花截圖都剛好拍在兩次噴發之間 | 放大截圖什麼都沒有 | 在遊戲中暫時改成連續噴發確認位置與亮度，場景保留一陣一陣的設定 |
| 6 | 霧第一版像灰色雲塊貼在暗處 | 截圖 | 改成受燈光影響（暗處看不見），透明度分 24 階 |
| 7 | 光束第一版太寬，像一塊方形的光 | 截圖＋差異圖 | 改窄、加長、頂端淡入、條紋加強 |
| 8 | 差異圖整張白色 | 截圖 PNG 有 alpha 通道 | `magick` 比較前先 `-alpha off` |
| 9 | 推近時畫面底部露出灰帶 | 隱藏對話框重拍時看到 | 鏡頭的下緣限制會隨倍率放寬、鏡頭自己會往主角靠，額外往下移是重複計算 → 拿掉 |
| 10 | 震動、晃動貼邊時也會露出灰邊 | 讀 `get_screen_center_position` 算出來 | Camera2D 的 `offset` 不受 `limit` 限制，自己限制在區域內 |
| 11 | 測試步驟：開始遊戲後馬上換區域會當掉；重新進入同一區後節點名稱變成 `@Node2D@8` | `execute_code` 回傳錯誤 | 開始後等 2.5 秒再換區域；重新進入後用 `World.get_child(0)` 找區域 |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 截圖 | 每一項效果在每一區截圖；粒子、霧、光束、推近都做 A／B 比較圖 | 作者依比較圖選擇 |
| 數值 | `execute_code` 讀鏡頭的 `zoom`、`offset`、畫面中心，讀背景圖的位置 | 推近 1.06／1.12 正確、震動中 offset 會動、限制函式擋住往外的位移 |
| 實際操作 | `input_simulate` 在婦人事件選「撲上去」；`leave_area(21)` 進入槍聲 | 鏡頭震動、背景圖震動都正常 |
| 遊玩測試 | 每一步改完都重跑 | 98 項通過 |
| log | 每次截圖後讀 `debugger_get_log` | 沒有錯誤 |
| Web 匯出 | `.pck` 有霧與光束的 shader、noise 貼圖、霧材質、`camera_fx.gd`、劇本與 7 區資料（含 5 個 `"camera": "shake"`）；沒有外掛、測試、`art/`、劇本檢查工具 | 通過 |

## 5. MCP 的特性（A2 新發現）

| 觀察 | 說明 |
|---|---|
| `NewResource` 可以一路建到底 | `OccluderPolygon2D`、`Gradient`、`CanvasItemMaterial`、`ShaderMaterial`（裡面再放 `Resource` 指向 shader）都能直接建，不用另外寫 `.tres` |
| `material:shader_parameter/…` 可以直接設 shader 參數 | 每個場景的強度、大小、顏色都用 batch 一次送出 |
| A／B 不用存兩份場景 | 遊戲執行中用 `execute_code` 改 `amount`、`set_shader_parameter`、`event_zoom`，同一個畫面拍兩張；作者選好再寫回場景或預設值 |
| `node_set_script` 會回傳 `@export` 清單 | 掛上腳本後馬上知道屬性面板會出現哪些可調參數 |
| 動態效果很難用截圖判斷 | 粒子、火花、震動、晃動在靜態截圖裡看不出差別；要靠讀數值（offset、`_shake_left`）或暫時改成連續效果 |
| UI 會擋住要比較的東西 | 對話框蓋住人物時，比較圖沒有意義；拍之前先想作者要看哪裡，必要時暫時隱藏 UI |
| runtime 連線仍然不穩 | `GAME_NOT_RUNNING` 時等 10～15 秒再輪詢；開始遊戲後要等一下才能換區域 |

## 6. A2 結論

1. **效能先試**：A2-1 先在一區做最重的兩項（陰影、法線貼圖）匯出給作者在瀏覽器看，確定流暢後才全部套用，之後的粒子、霧、光束都很輕（`.pck` 只多約 0.05MB）。
2. **A／B 在遊戲裡直接改最快**：同一個執行中的遊戲改參數、拍兩張，不用存兩份場景；作者每一項都很快就能決定（粒子 B、霧與光束 A、鏡頭 B）。
3. **比較圖要讓作者看得到差別**：第一次推近的比較圖被對話框擋住，等於白拍；拍之前先確認要比較的東西在畫面上，動態效果要另外說明或請作者實際試玩。
4. **重拍會抓到自己的錯**：為了讓作者看清楚而重拍，才發現推近時底部露出灰帶，以及震動可能露出區域外。只看數值或只拍一次都抓不到。
5. **背景插畫仍是最大的落差**：舊家的遠景沒有畫屋頂破洞，光束只能假設破洞在畫面外；等作者用生圖 AI 換成側面視角的遠景（P1～P7）後，光束與霧的位置可以再調。

---

# A＋ A3：會動的像素

- 日期：2026-10-13～2026-10-14
- MCP：**pixelorama**（10 套圖共 57 格：匯入每一格、補掉的像素、存 `.pxo`、匯出逐格）＋ **godot-mcp-toolkit**（`spriteframes_from_spritesheet`／`spriteframes_edit` 建動畫、換節點、掛腳本、執行與截圖驗證）
- 成果：火焰（燃燒的車、兩個火桶，火光跟著火焰明暗）、停車場燈管（只有燈管閃）、婦人（尖叫動嘴 → 往遠離主角的方向快跑）、感染者群（啃食循環，站著那隻偶爾轉頭）、女科學家（抱筆記本 → 對話時遞出 → 跑走）、警衛（低姿戒備搜索 → 舉槍瞄準，槍上的手電筒光沿著槍管）、妻子（分麵包循環）、女兒（眨眼、比手勢、轉身淡出）、主角（調查時轉向物件伸手、衝動高時朝那個人前傾）。走廊的火（只畫在遠景插畫裡）不做，主角手勢留到 A5。
- 狀態：**A3 完成**。測試 110 項通過（劇本檢查＋Lv4 26、Lv5 35、Lv6 24、A1.5 25）；Web 版 `index.pck` 48.12MB（A3 只多約 0.07MB）；作者在瀏覽器測試完成。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| A3-0 | 規劃 8 組、截圖動畫對象 | `game_start`、`execute_code`、`runtime_screenshot` | 素材放大排成一張（ImageMagick） |
| 設計（每組） | 依原圖或自己設計，產生每一格 | — | Python 設計腳本（`art/design/a3/*.py`）＋GIF 預覽（ImageMagick）；Pixelorama 沒有「從設計圖產生動畫」的能力 |
| 製作（每組） | 逐格匯入、補像素、存檔、匯出 | pixelorama `import_image`、`add_frame`、`switch_frame`、`duplicate_frame`、`draw_pixels`、`export_animation`、`save_project` | 逐像素比對（`verify.sh`／`patch.py`）；spritesheet 拼接與每格法線（`normal_map.py`） |
| 放進遊戲 | SpriteFrames、換成 AnimatedSprite2D、燈光與腳本 | Toolkit `spriteframes_from_spritesheet`、`spriteframes_edit`、`scene_delete_node`／`scene_create_node`、`node_manage`（`reorder`、`reparent`、`rename`）、`node_set_script`、`node_set_property`、`editor_refresh`、`discover_tools` | `interact_point.gd`、`area.gd`、`main.gd`、`player.gd`、`flicker_light.gd`，新腳本 `idle_variation.gd`、`gun_torch.gd`；`CanvasTexture`（`*_anim_canvas.tres`）與錐形光貼圖用檔案寫入 |
| 驗證 | 每組截圖、讀動畫狀態、測試 | `runtime_screenshot`、`execute_code`（讀 `animation`／`frame`、強制觸發）、`debugger_get_log`、`input_simulate` | 測試新增 Lv4 2 項、Lv5 6 項、A1.5 4 項 |
| A3 收尾 | 測試、匯出、紀錄 | — | headless 測試與匯出（專案副本） |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 範圍與順序 | 走廊的火不做、手勢留到 A5、先做火焰 | 照建議順序：火焰 → 燈管 → 婦人 → 感染者群 → 女科學家 → 警衛 → 妻子、女兒 → 主角 |
| 燈管 | 「整個畫面都在閃爍，燈管的變化不明顯」→「燈管有發亮，場景就不閃爍」 | 熄滅時燈光亮度不變（`dropout_ratio` 1.0），燈管改成不受光，只有燈管本身亮／熄 |
| 婦人 | 「尖叫的話嘴巴是不是要動」「步伐像快走，被驚嚇應該跑很快」 | 嘴巴小張／大張交替（保持小而圓，Lv6 曾嫌張嘴怪）；改成快跑（騰空格、大步伐、手臂彎曲）、12 fps、跑速 1.7 倍；方向改成遠離主角 |
| 警衛 | 「手電筒可以裝在槍上」→「你確定槍上掛著手電筒的行為是這樣嗎」 | 第一版只移槍口 5 欄（槍會折）、光和槍角度對不上；重畫成整把槍以肩膀為支點轉動、光永遠沿著槍管、平常低姿戒備搜索、事件時舉槍瞄準 |
| 主角 | 「手是不是再升高一點」 | 伸手的最後一格從腰下方抬到胸口高度 |
| 暫存區 | 「將怕被刪除的素材從暫存資料夾移出」 | 設計腳本、每格設計圖、GIF、比較圖搬到 `art/design/`（附 README），之後直接寫在那裡 |
| 語言 | 多次提醒「台灣繁體中文回答」 | 記憶補上：成果報告、設計報告、被質疑時最容易切成英文 |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 節點型別的 `@export`（`follow: AnimatedSprite2D`）用 Toolkit 設定後載入是 null | 火光沒有跟著火焰跳，讀屬性是 null | 改成 `NodePath`，`_ready()` 再取節點（寫進 `CLAUDE.md`） |
| 2 | `PackedFloat32Array` 的 export 被 Toolkit 寫成一般陣列，重新存檔後被丟掉，進走廊就當掉 | 遊戲當掉，`Out of bounds get index` | 改成 `PackedVector3Array`（x、y、角度存在一起） |
| 3 | 改了腳本的 `@export` 後，編輯器一直快取舊的屬性清單 | `node_set_script` 回傳的還是舊欄位 | `editor_refresh`、`script_write`、重掛都無效，最後換新檔名 `gun_torch.gd` |
| 4 | 加寬主角 spritesheet（640→960）後，只刷新該檔案沒有重新匯入，新格子在遊戲裡是透明的 | 截圖找不到主角，讀貼圖寬度是 640 | 整個專案重新掃描；**自動測試在副本重新匯入、只看動畫名稱，抓不到** |
| 5 | 光錐放大後頂點落在警衛身上（offset 沒有跟著 `texture_scale` 放大） | 截圖警衛胸口被照亮 | `offset` 乘上 `texture_scale` |
| 6 | 前傾時背對婦人 | 測試結果 `lean_left`（婦人在右邊） | 前傾時轉向衝動最強的那個人 |
| 7 | `var x := impulse_fx.strength_at()` 推斷不了型別，編譯錯誤讓測試卡住 | `script_check` 報錯、測試逾時 | 明寫 `float` |
| 8 | 設計圖第一版的問題：火焰核心太黃、燈管熄滅格被燈照亮看不出來、婦人肩膀凹口與黑點、科學家的書像「E」、女兒的手像兔耳朵、警衛手臂像背帶、主角手臂像棍子 | 給作者看之前先放大檢查 | 每組都自己先修一輪才交給作者 |
| 9 | `add_frame` 不會切到新的格，第一次匯入畫在第 0 格上 | 匯出第 0 格內容錯 | 每格先 `switch_frame` 再匯入 |
| 10 | 動態效果在截圖裡看不出來；編輯器不在前景時遊戲時間走得很慢，隨機事件等不到 | 等 3 秒倒數只少 0.8 秒 | 用 `execute_code` 直接觸發（倒數歸零、強制熄滅），再讀狀態確認 |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 像素圖 | 10 套 57 格設計圖與 Pixelorama 匯出逐格比對 | 全部 0 差異（掉像素的有車 51、燈管 43、火桶 5、感染者每格 8～9，都補回） |
| 法線貼圖 | 每格由 `normal_map.py` 產生；和原本相同的那一格比對 | 婦人、女科學家、妻子的原姿勢格和原本的法線 0 差異 |
| 遊玩測試 | 婦人尖叫 → 往右跑 → 消失；女科學家遞出 → 直接跑；警衛舉槍、光水平照過來；女兒舉手 → 轉身 → 淡出；主角轉向伸手、朝婦人前傾、恢復 | 110 項通過 |
| 實際畫面 | 每組在遊戲中截圖（必要時隱藏對話框、紅色暈影） | 位置、前後順序（圍籬、窗框）、光的方向正確 |
| log | 每次截圖後讀 `debugger_get_log` | 沒有錯誤 |
| Web 匯出 | `.pck` 有 8 個新的 SpriteFrames、主角新增的 4 個動畫、燈管、錐形光、`gun_torch.gd`、`idle_variation.gd`、`"figure": "wave"`；沒有外掛、測試、`art/`、舊的 `gun_light.gd` | 通過 |

## 5. MCP 的特性（A3 新發現）

| 觀察 | 說明 |
|---|---|
| Pixelorama「逐格切換＋匯入」最穩 | 比「複製上一格＋送差異」少很多資料；有幾組完全沒掉像素 |
| `spriteframes_from_spritesheet` 可以直接用 `CanvasTexture` | 每格自動帶法線貼圖，不用另外處理 |
| `spriteframes_edit` 能在既有的 SpriteFrames 加動畫 | 主角的新動作接在原本 20 格後面，不必重建 |
| Toolkit 的型別限制 | 節點參照、`PackedFloat32Array`、`null` 都寫不進去；要選 Toolkit 支援的型別（NodePath、PackedVector2／3Array），或改用預設值相同的寫法 |
| 編輯器快取與匯入 | 改 `@export` 或加寬已匯入的圖之後，要確認編輯器真的更新了（換檔名、整個專案重新掃描、在遊戲裡讀大小） |
| 重開工作階段後工具群組要重新啟用 | `editor_advanced`、`spriteframes` 需要 `discover_tools` |

## 6. A3 結論

1. **作者對「動作合不合理」很敏銳**：警衛的手電筒、婦人的快跑、尖叫要動嘴、燈管閃爍的範圍、手的高度，都是作者看預覽就指出來的。設計動作前先想清楚實際的動作邏輯，比做完再改省事。
2. **動畫要和遊戲邏輯一起設計**：同一組人物需要 `idle`／`event`／`scream`／`run`／`leave` 等狀態，事件開始、選項、結束時自動切換；建好一次之後，後面幾組只要準備同名動畫就能用。
3. **自動測試看不到畫面**：主角新格子透明、光錐位置錯，都是截圖才發現；動畫名稱正確不代表畫面正確，每組都要實際截圖。
4. **Toolkit 寫入的型別與編輯器快取是主要的坑**：這一級 3 個最花時間的問題都來自這裡，已整理進 `CLAUDE.md`。

---

# A＋ A4：聲音

- 日期：2026-10-14
- MCP：**godot-mcp-toolkit**（`audiobus_edit` 建音量分組、`scene_create_node`／`node_set_property` 建位置音效與播放器、`editor_refresh` 重新匯入、`script_check`、執行與讀狀態）。這一級沒有用 Pixelorama；ElevenLabs 沒有用到（免費素材就夠了）。
- 成果：
  - 音量分組 Master／BGM／SFX／Ambient。
  - 7 區環境音（換區域交叉淡化）；腳步聲跟著行走畫格，分水泥、碎玻璃、木頭。
  - 調查、撿起、開門、低吼、尖叫、槍聲、撞鐵絲網、心跳；選項的游標與確認音。
  - 位置音效：車火、火桶、避難所人聲、警報、燈管嗡聲（熄滅時靜音並發出喀喀聲）。
  - 新音樂：標題、避難所、Bad End。
  - 共 43 個音效、3 首音樂，網頁版 `index.pck` 48.1 → 52.3MB。
- 狀態：**A4 完成**。測試 144 項通過（劇本檢查＋Lv4 26、Lv5 35、Lv6 24、A1.5 25、A4 34），作者在瀏覽器試聽確認「大致上沒問題」。

## 1. 各步驟使用的工具

| 步驟 | 內容 | 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| A4-0 | 聲音清單、搜尋關鍵字；作者請 Claude 找候選 | WebFetch（Freesound 搜尋頁，優先 CC0） | Freesound 有頻率限制（429），要一筆一筆查；要登入才能下載，由作者下載 |
| A4-1 | Kenney 素材包 | curl 下載（作者同意） | — |
| A4-1c | 整理候選：切單步、裁切、音量、無縫循環、混音、合成 | — | Python＋ffmpeg（`art/tools/a4_sfx_prep.py`）；試聽網頁 `a4_sfx_page.py`（勾選後複製結果） |
| 放進專案 | 轉 ogg、匯入、單發音效不循環 | `editor_refresh`（整個專案） | ffmpeg 沒有 libvorbis，作者同意安裝 `vorbis-tools`（`oggenc`）；`.import` 的 `loop` 用檔案修改 |
| A4-2 | 音量分組、播放器、位置音效 | `audiobus_edit`、`scene_create_node`、`node_set_property`（`bus`、`stream`、`autoplay`、`max_distance`、NodePath）、`editor_save_scene` | 程式：`sound_lib.gd`（新）、`main.gd`、`player.gd`、`impulse_fx.gd`、`flicker_light.gd`、`area_data.gd`、`validate_story.gd`；資料加聲音欄位 |
| 驗證 | 執行、讀播放狀態 | `game_start`、`execute_code`、`debugger_get_log` | 測試新增 `test_a4.gd`；用匯出的 `.pck` 跑檢查腳本（`--main-pack`） |
| A4-3 | 作者試聽一輪 | — | 依回饋修改後重新匯出 |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 找素材 | 「你可以用 A4-0 幫我找素材嗎」 | 每項列 1～3 個 Freesound 候選網址；說明 Freesound 的用法與搜尋關鍵字；下載 Kenney 素材包 |
| 挑選 | 用試聽網頁勾選（腳步各 3、調查 5 個…）；M1 沒勾、介面音 a／b 都勾 | 問清楚：M1 用 Metris、音樂盒 → 避難所、sad world → 標題、介面音用 a 組 |
| 開門聲、槍聲 | 「在轉場之後才出現，感覺怪怪的」「是否需要加黑屏再轉下個場景」 | 遊戲啟動時預載音效；有聲音的轉場在黑畫面停 0.7 秒，聲音在變暗、黑畫面時響起 |
| 打字聲 | 「和音效重疊，感覺很躁，是否應該去掉」 | 先關掉（`TYPE_SOUND`），A6 的設定可以做開關 |
| 腳步 | 「人停下來後腳步聲還在持續」 | 腳步檔裁到 0.4 秒，停下時 0.08 秒淡出 |
| 劇情音效 | 撲向妻子要尖叫、加入同類要低吼 | `sfx` 可以寫成陣列，同時播放低吼和尖叫 |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | ffmpeg 內建的 vorbis 編碼器只支援立體聲、音質差 | 轉單聲道測試失敗 | 試聽版先用 WAV；正式轉檔改用 `oggenc` |
| 2 | 淡入（5 毫秒）蓋掉腳步聲開頭的衝擊，峰值只有 -15 dB | 逐檔量響度與峰值 | 淡入改成 1 毫秒、往前多留 20 毫秒 |
| 3 | 火的劈啪尖峰讓整體被壓到 -29.6 LUFS | 同上 | 先加壓縮再調音量 |
| 4 | 作者下載的「撿起」其實是小貨車開門聲 | 查 Freesound 頁面 | 提醒作者，改從 Kenney 挑 |
| 5 | `AudioStreamPolyphonic` 在網頁版的 Sample 播放模式不一定支援 | 查文件與討論（沒有明確答案） | 改成 4 個一般播放器輪流用 |
| 6 | 匯出後音效檔名會變（`.import`／`.remap`），查找工具可能找不到 | 擔心網頁版沒聲音 | 用匯出的 `.pck` 跑檢查腳本，確認 `SoundLib` 和預載都找得到 |
| 7 | 預載的聲音如果沒有留住參考，被釋放後再載入又要重新解碼 | 寫程式時想到 | 存在靜態陣列裡 |
| 8 | **測試腳本 Parse Error 時，`run_tests.sh` 仍顯示「全部通過」**（Godot 結束碼是 0） | 新測試有型別錯誤，結果卻是通過 | 看輸出判斷：有 `SCRIPT ERROR` 或沒印出結果都算失敗 |
| 9 | 改了 `flicker_light.gd` 的 export，`node_set_property` 設不進去（編輯器快取舊屬性） | 回傳 readback 是 null | 這次 `editor_refresh` 該腳本就好了（A3 時要換檔名） |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 素材 | 80 個試聽檔的長度、響度、峰值；循環接縫的跳動和一般相鄰取樣比較 | 全部正常（接縫比例 0～1.2） |
| 授權 | 9 個非 CC0 篩選的檔案逐一查頁面 | CC BY 3 個（cosmicembers、pfranzen、Metris），已寫進 `docs/素材來源.md` |
| 匯入 | 單發音效 32 個不循環、循環 12 個；重新匯入後確認匯入結果時間 | 通過 |
| 遊玩測試 | 分組、環境音切換與淡出、腳步次數（走 1 秒 3 步、停下沒有）、地面材質、翻找、撿起、開門、黑畫面停留時間、低吼、尖叫、游標（自動聚焦不出聲）、燈管熄滅靜音、車火、槍聲在黑畫面中、新音樂、資料檢查（包含寫錯的名稱） | 34 項通過 |
| Web 匯出 | `.pck` 有新音效、`sound_lib.gd`、音量分組，沒有測試與外掛；用匯出的 `.pck` 確認查找與預載（45 個） | 通過 |

## 5. MCP 與工具的特性（A4 新發現）

| 觀察 | 說明 |
|---|---|
| `audiobus_edit` 很好用 | 建分組直接寫成 `default_bus_layout.tres`，不用手動編輯 |
| `node_set_property` 可以設 `stream`（Resource）和 `bus` | 位置音效完全用 Toolkit 建立 |
| Claude 聽不到聲音 | 只能驗證「什麼時候播了哪個聲音」：在程式裡加 `sound_log`、`steps_played` 給測試與 `execute_code` 讀；好不好聽、時機自不自然都是作者試聽才發現（轉場後才出聲） |
| 網頁版的聲音和桌面版不同 | 網頁版預設用瀏覽器的 Sample 方式播放：第一次播放要解碼（延遲），部分串流類型不一定支援；在編輯器裡測不出來，要在瀏覽器聽 |
| 外部網站的限制 | Freesound 查太快會 429、下載要登入；Kenney 可以直接下載 |

## 6. A4 結論

1. **素材流程分工清楚**：Claude 找候選、整理、做試聽網頁，作者聽和挑。試聽網頁可以勾選、複製結果，比用文字一個一個說快很多。
2. **聲音資料化**：和 A2 的 `camera` 一樣，用資料的 `sfx`／`ambience`／`floor` 指定聲音，劇本檢查會確認檔案存在，之後調整不用改程式。
3. **聲音的時機要和畫面一起設計**：作者最在意的是「什麼時候響」（轉場後才出聲、停下還有腳步、打字和音效重疊），比音量平衡更重要。
4. **測試工具本身也要驗證**：`run_tests.sh` 把腳本錯誤當成通過，這個問題從以前就存在，這次才被發現。

---

# A＋ A5：新的互動方式

- 日期：2026-10-14～2026-10-16
- MCP：**godot-mcp-toolkit**（`input_map_action`／`input_map_event` 加 G 鍵、`spriteframes_edit` 加手勢動畫、`scene_create_node`／`node_set_property`／`node_manage` 建閃回畫面、白光、抵抗量表、掩護與通風管，`node_set_script` 掛互動點腳本，`editor_refresh`、`script_check`、執行、截圖、讀狀態）＋ **pixelorama**（手勢 10 格、箱子、通風管）
- 成果：四個互動都做（作者決定：先做手勢、記憶閃回，效果好再加壓抑衝動、躲藏）
  - **手勢**：G 鍵比出劇本裡教女兒的「我——在——這——裡」（手按胸口 → 手掌朝前 → 指向地面點兩下），7 個人物／地點有反應文字，沒有對象時第一次有獨白；不加數值。
  - **記憶閃回**：調查醒來的地方、診療椅（有錄音筆）、實驗紀錄、蠟筆字時，白光一閃切到原插畫（scene_19／05／12／10），褪色、雜訊、暗角約 2.2 秒，可跳過；閃回音由 Claude 合成。
  - **壓抑衝動**：婦人、女科學家、警衛、妻子的事件先抵抗衝動（量表），成功時「撲上去」類選項消失，失敗時自動撲上去（妻子＝Bad End「噬語」）。正式版是連打，**目前是作者要求的按住測試版**（`RESIST_HOLD`）。
  - **躲藏**：設施走廊的警衛原地轉身，站在光照到的地面會被發現 → 被發現版的警衛事件；推車、箱子是掩護，通風管是避開警衛的捷徑。
- 狀態：**A5 完成**（作者在瀏覽器試玩：「整體都很流暢」）。測試 215 項通過（劇本檢查＋Lv4 26、Lv5 35、Lv6 24、A1.5 25、A4 35、A5 70）；Web 版 52.3MB。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| A5-0／A5-1 | 四個候選比較、每個互動的設計稿與文字草稿 | — | 設計稿寫在 `docs/A5_*設計.md`；示意圖、預覽用 Python／ImageMagick（手勢 GIF、閃回 A／B 比較、抵抗量表示意、走廊配置圖、箱子與通風管） |
| 手勢 | 動畫 10 格、G 鍵、動畫 | pixelorama `create_canvas`、`add_frame`、`switch_frame`、`import_image`、`save_project`、`export_animation`；Toolkit `input_map_action`、`input_map_event`、`spriteframes_edit` | 動畫接到 `player.png` 後面與法線貼圖（ImageMagick、`normal_map.py`）；程式 `player.gd`、`main.gd` |
| 記憶閃回 | shader、閃回畫面、白光、閃回音 | Toolkit `scene_create_node`、`node_set_property`（ShaderMaterial）、`node_manage`（reorder、reparent） | `shaders/flashback.gdshader`；閃回音用 ffmpeg 從現有音樂合成；Freesound 候選用 WebFetch 找 |
| 壓抑衝動 | 對話框裡的量表 | Toolkit `scene_create_node`、`node_set_property`、`node_manage` | 量表配色在 `_setup_style()`；`impulse_fx.gd` 加心跳訊號 |
| 躲藏 | 箱子、通風管、掩護與通風管的互動點 | pixelorama 同上；Toolkit `scene_create_node`、`node_set_script`、`node_set_property`、`editor_save_scene` | 新腳本 `guard_patrol.gd`（Main 依資料在執行時建立） |
| 驗證 | 截圖、讀狀態 | `game_start`、`execute_code`、`input_simulate`、`runtime_screenshot`（`force_foreground_game`）、`debugger_get_log` | 測試 `tests/test_a5.gd`（70 項）；用匯出的 `.pck` 確認新圖與資料 |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 範圍 | 先做手勢、記憶閃回；之後「我還是想加壓抑衝動和躲藏，讓作品互動更多」 | 四個都做，一次做一個（設計 → 定稿 → 製作 → 試玩） |
| 手勢 | 「手往前下方指地面時，可以多點兩下嗎」 | 加第 4 格「往下點」，3、4 交替兩次；數值用方案 A（不加），B 當備案 |
| 記憶閃回 | 效果用 A、B 備案；scene_19（也是結局 B 的圖）繼續用；閃回音「你先產生，免費素材也幫我整理」 | Claude 合成 3 個候選＋整理 Freesound 候選，作者選合成的 a |
| 壓抑衝動 | 連打空白鍵、女兒不抵抗（她會直接跑掉）；「連打的指數先設低一點」；「先改成按住空白鍵進行測試版，正式版再改回來」 | 連打次數調低（6／8／8／10）；加開關 `RESIST_HOLD`，按住秒數 1.5／2／2／2.5，連打的程式與資料保留 |
| 躲藏 | 四項都做 A（警衛原地轉身、變暗半透明、被發現進事件、通風管是捷徑），B 當升級方案；被發現要不要「抓回去」→ 比較後維持現在的方式 | 抓回去與「被發現後拿掉躲進通風管」記為升級方案 |
| MCP | 「再檢查一次 MCP」 | 對話開始時 Godot 編輯器沒開；開了之後兩個 MCP 都實際呼叫一次確認 |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 手勢設計第一版手臂太細（像棍子）、「在」的手擋住臉 | 給作者看之前放大檢查 | 手臂加粗到 4px、手移到下巴前方 |
| 2 | `spriteframes_edit` 的 `add_animation` 帶入的畫格被忽略，動畫是空的 | 讀 `.tres` 確認 | 再用 `add_frame` 加畫格（寫進 `CLAUDE.md`） |
| 3 | 閃回的雜訊有斜向規則紋路 | MCP 截圖放大 | `fract(sin())` 在 Compatibility 精度不夠，換 hash12（寫進 `CLAUDE.md`） |
| 4 | 手勢提示只設錨點，跑到左上角、蓋在閃回與對話框上 | 截圖 | 錨點＋位移一起設；閃回、對話框打開時隱藏 |
| 5 | 白光放在閃回畫面底下，閃回畫面隱藏時白光也看不見 | 寫流程時想到 | 搬到 UI 層、排在閃回畫面後面 |
| 6 | 連打時空白鍵會直接按到剛出現的選項、或跳過撲上去的回應 | 設計時想到 | 判定後鎖按鍵 0.9 秒；按住版要放開才出選項 |
| 7 | 抵抗插進事件後，舊測試直接選「撲上去」會選錯 | 測試失敗 | 共用 `choose()` 遇到抵抗時依選項判定成敗、編號往前移；`read()` 等按鍵鎖解除 |
| 8 | 燈管測試偶爾失敗（遊戲剛開始時燈管自己熄滅過，喀喀聲在冷卻） | 全部測試時偶發 | 測試先把冷卻歸零 |
| 9 | 閃回素材預覽刪除指令用了變數路徑，被安全檢查擋下 | 工具拒絕 | 改用 `"${D:?}"` 寫法 |
| 10 | 躲藏的光錐幾何判定行不通（手電筒在胸口高度往下照，主角要貼到腳邊才會被照到） | MCP 讀手電筒的位置與角度後計算 | 改成「面向主角、在光照到的地面範圍內」 |
| 11 | 判定範圍比畫面上看得到的光大，看不到光的地方也會被發現 | MCP 截圖對照 | 範圍改成約 266 px，箱子、通風管往警衛那邊移 |
| 12 | 變數名 `hidden` 和 CanvasItem 內建的訊號同名 | `script_check` 編譯錯誤 | 改名 `in_cover` |
| 13 | 離開走廊後 `_process` 還在讀已釋放的巡視節點 | 測試輸出大量錯誤 | 先檢查再用、離開區域時清空 |
| 14 | 劇本檢查不知道「被發現」旗標是程式自動設定的 | 劇本檢查報錯 | 自動旗標（spotted／gesture／flashback）列入「有地方設定」 |
| 15 | 匯出時測試副本的 `build/web` 不見了（暫存區被清過） | 匯出失敗 | 匯出前先建立資料夾 |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 像素圖 | 手勢 10 格、箱子、通風管逐像素比對 | 全部一次就 0 差異；主角原本 30 格與法線 0 差異 |
| 遊玩測試 | 手勢（動畫、不能移動、反應一次、獨白、對話中無效、數值不變）；閃回（約 3 秒、跳過、一輪一次、診療椅條件）；抵抗（按住／連打成功、時限失敗、鎖按鍵、妻子 BE 與重試）；躲藏（轉身節奏、被發現、掩護、移動出來、通風管、警衛事件結束、到出口）；劇本檢查的錯誤資料 | A5 70 項，全部 215 項通過；按住和連打兩種模式都跑過 |
| 實際畫面 | 手勢、婦人的反應、閃回畫面與雜訊、抵抗量表、箱子後面躲著、通風管、警衛轉身 | 截圖確認 |
| log | 每次截圖後讀 `debugger_get_log` | 沒有錯誤 |
| Web 匯出 | `.pck` 有手勢動畫（`player.png` 1280 寬）、閃回 shader 與插畫、抵抗與躲藏的資料、新腳本 | 通過 |

## 5. MCP 的特性（A5 新發現）

| 觀察 | 說明 |
|---|---|
| `input_map_event` 用 `keycode` 寫入時會存成實體按鍵 | 和專案其他按鍵的格式一致 |
| `spriteframes_edit` 的 `add_animation` 不吃 `frames` | 要分兩步：先建動畫，再 `add_frame` |
| `runtime_screenshot` 的 `force_foreground_game` | 遊戲嵌在編輯器裡時不能真的拿到前景，但這樣截圖會拿到最新的畫面（不用另外送空指令） |
| MCP 連線取決於編輯器 | 對話開始時編輯器沒開，Toolkit 的工具就不見了；開了之後要重新載入工具 |
| 判定邏輯要靠 MCP 實測 | 光錐的位置、角度、看得到光的範圍，都是讀遊戲裡的實際數值、截圖對照後才定案；只看程式推不出來 |

## 6. A5 結論

1. **一次做一個互動、每個都先定稿**，作者可以在每一步調整（點兩下、連打改按住、次數調低），不用整個重做。
2. **資料化讓互動可以重複使用**：`gesture`、`flashback`、`resist`、`hide`／`patrol`、區域 `hint` 都寫在資料裡，劇本檢查會檢查格式；之後新增人物或區域不用改程式。
3. **玩法要在實際畫面上驗證**：躲藏最初的幾何判定在紙上合理，實測才發現幾乎不會發生；判定範圍也要和「玩家看得到的光」一致才公平。
4. **新互動會影響舊流程**：抵抗衝動插進人物事件後，舊測試、連打的按鍵、選項的編號都要一起調整；測試的共用操作要跟著更新。

---

# A＋ A6：收尾與發布

- 日期：2026-10-16
- MCP：**godot-mcp-toolkit**（`scene_create_node`／`node_set_property`／`node_manage` 建標題選單、設定面板、製作群面板，`editor_save_scene`、`editor_refresh`、`script_check`、`lsp_project_diagnostics`、執行、`input_simulate`、截圖）
- 成果：
  - **設定畫面**：標題的「點擊開始」改成選單（開始遊戲／設定／製作群）；設定面板可以調音樂、音效、環境音（A4 的音量分組）與打字聲開關，存在 `user://settings.cfg`（網頁版存在瀏覽器裡）。
  - **製作群**：CC BY 三位作者、感謝名單、字型、工具，最後是 Godot Engine 的 MIT 授權全文與第三方元件清單（引擎提供）。
  - **網頁版瘦身**：沒用到的 8 首 BGM 不匯出、字型只留用到的字，`index.pck` 52.3 → **31.3MB**，上傳用的 zip 39.2MB。
  - **打包**：`build/shiyuzhe_web_itch.zip`，上傳步驟與公開前確認更新在 `docs/itch.io上傳步驟.md`；上傳由作者自己做。
- 作者決定不在 A6 做的：壓抑衝動改回連打（維持按住的測試版）、A5 的升級方案、BGM 再壓縮或縮短循環。
- 狀態：**A6 完成**（作者確認）。測試 240 項通過（劇本檢查＋Lv4 26、Lv5 35、Lv6 24、A1.5 25、A4 35、A5 70、A6 25）；`lsp_project_diagnostics` 24 個腳本 0 錯誤。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| A6-0 | 收尾清單、瘦身分析 | — | Python 分析測試副本 `.godot/imported` 的大小、找出沒用到的 BGM |
| A6-1 設定畫面 | 選單、設定面板（21 個節點） | `scene_create_node`、`node_set_property`（錨點、位移、字級、顏色）、`editor_save_scene` | 樣式（StyleBox、按鈕顏色、▶ 標示）與行為寫在 `main.gd`；設定模組 `scripts/game_settings.gd`；示意圖用 ImageMagick |
| A6-2 製作群 | 製作群面板 | 同上 | 內容放 `data/credits.json`；授權全文用 `Engine.get_license_text()` |
| A6-4 瘦身 | 排除 BGM、精簡字型 | `editor_refresh` | `export_presets.cfg` 直接編輯（Toolkit 沒有匯出設定的工具）；字型用 fonttools（`art/tools/font_subset.py`，作者同意在 `~/Tools/fonttools-venv` 安裝） |
| A6-5 打包 | 最後檢查、匯出、zip | `lsp_project_diagnostics` | 匯出在測試副本上；zip 照 cross-platform-archive-agent 技能的規則排除系統檔 |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 瘦身 | 做 ①（沒用到的 BGM 不匯出）＋③（字型精簡），不壓縮音樂 | 52.3 → 31.3MB，音質不變 |
| 範圍 | 升級方案先不做；順序：設定 → 製作群 → 瘦身 → 打包 → 紀錄 | 壓抑衝動改回連打不在清單裡，維持按住版並在公開前確認列出 |
| 設定 | 版面可以、音量預設 100%、只放標題 | 照做 |
| 製作群 | 作者名稱、「開發協助：Claude」先不加；感謝名單保留 | 照做，內容放資料檔，之後補名字只改資料 |
| MCP | 「再檢查一次 MCP」 | 編輯器開啟後兩個 MCP 都實際呼叫一次確認 |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 截圖時按 ←，把作者電腦上的音樂設定存成 90% | 讀設定檔 | 改回 100% |
| 2 | 測試會讀到作者自己的設定（測試副本和編輯器共用使用者資料夾） | 從問題 1 想到 | 測試改用 `user://settings_test.cfg`，每次從預設值開始 |
| 3 | 設定面板後面透出標題的字、字級不一致、選單在亮色牆上不好讀 | MCP 截圖 | 打開面板時隱藏標題、統一 22、加陰影 |
| 4 | 打字聲開關被加了兩個 ▶ | 寫程式時發現 | 開關的 ▶ 只加在那一列的名稱 |
| 5 | `event.pressed` 在 `InputEvent` 上不能用、迴圈變數和外層變數同名 | `script_check` | 改用 `is_pressed()`、改名 |
| 6 | Godot 要求發布的遊戲附上引擎授權聲明（之前沒注意到） | 起草製作群時 | 製作群最後接引擎提供的授權全文與第三方元件清單 |
| 7 | 排除 BGM 後，之後劇本換回某首音樂時網頁版會沒有檔案 | 設計瘦身時想到 | 劇本檢查確認用到的音樂沒被排除（故意排除 bgm_01 測過） |
| 8 | 字型精簡後，新增文字忘了重新產生會變方塊字 | 設計瘦身時想到 | 劇本檢查確認資料裡的字都在字型裡（故意加「龘」測過） |
| 9 | 全形空白「　」被精簡工具濾掉 | 問題 8 的檢查第一次就抓到 | Python 的 `isprintable()` 會濾掉全形空白，改成只排除控制字元 |
| 10 | runtime 連線常常要輪詢兩、三次 | `GAME_NOT_RUNNING` | 照 `CLAUDE.md` 的經驗：`game_start` 後等 5 秒再呼叫 |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 遊玩測試 | 標題選單（焦點、▶、游標聲、第一次按鍵解鎖聲音）、設定（音量變化套到分組、0% 靜音、打字聲開關、存檔與重新讀取、Esc）、製作群（CC BY、授權全文、捲動、Esc）、開始遊戲 | A6 25 項，全部 240 項通過 |
| 劇本檢查 | 用到的 BGM 沒被排除、資料裡的字都在字型裡 | 兩項都用故意寫錯的資料測過 |
| 編譯 | `lsp_project_diagnostics` | 24 個腳本 0 錯誤 |
| 實際畫面 | 標題選單、設定面板、製作群（前段與授權全文）、精簡字型後的中文 | MCP 截圖確認 |
| Web 匯出 | `.pck` 有 `game_settings.gd`、`data/credits.json`，沒有排除的 8 首 BGM 和完整字型 | 通過 |

## 5. MCP 的特性（A6 新發現）

| 觀察 | 說明 |
|---|---|
| Toolkit 適合建 UI 的節點樹 | 21 個節點的設定面板全部用 `scene_create_node`＋批次 `node_set_property` 建好，存檔一次就正確 |
| 錨點的警告 | `anchor_top` 設 0.79 時 Toolkit 警告「可能不會保存」，實際存檔有保存；以存檔後的 `.tscn` 為準 |
| Toolkit 沒有匯出設定的工具 | `export_presets.cfg` 只能直接編輯；所以加了劇本檢查當保險 |
| `lsp_project_diagnostics` 可以當發布前的總檢查 | 測試只會載入用到的腳本，LSP 會檢查專案裡每一個腳本 |

## 6. A6 結論

1. **瘦身先找「沒用到的東西」**：一半的節省來自沒用到的 BGM，不影響品質；壓縮音質是最後的手段。
2. **每一個讓檔案變少的做法都要配一道檢查**：排除清單、精簡字型都可能在之後出錯，劇本檢查讓錯誤在發布前就被抓到。
3. **MCP 操作會改到使用者的真實環境**：截圖時的一個按鍵就改了作者的設定，測試也會讀到作者的設定；測試和驗證要和使用者的資料分開。

---

# A＋總結（A1～A6）

## 1. 做了什麼

| 級 | 內容 | 測試（累計） | 網頁版 `.pck` |
|---|---|---|---|
| A1 | 7 區五層分層背景（遠景、中景、遊戲層、近景、前景）、像素地面、路中間的障礙物 | 98 | 48.0MB |
| A1.5 | 上下左右移動（縱深帶）、影子、前後遮擋 | 98 | — |
| A2 | 陰影、法線貼圖、粒子、霧與光束、鏡頭推近／震動／晃動 | 98 | 48.05MB |
| A3 | 會動的像素：火焰、燈管、婦人、感染者群、女科學家、警衛（槍上手電筒）、妻子、女兒、主角新動作 | 110 | 48.12MB |
| A4 | 聲音：音量分組、環境音、腳步、互動與事件音、位置音效、新 BGM | 144 | 52.3MB |
| A5 | 新互動：手勢、記憶閃回、壓抑衝動、躲藏 | 215 | 52.3MB |
| A6 | 設定、製作群、瘦身、打包 | 240 | **31.3MB** |

## 2. MCP 的使用

| MCP | 主要用途 | 心得 |
|---|---|---|
| **godot-mcp-toolkit** | 建場景與 UI 節點、設定屬性與資源、音量分組、按鍵、SpriteFrames、執行遊戲、模擬輸入、讀狀態、截圖、log、LSP | 幾乎所有場景修改都能用它完成；要注意的坑都整理在 `CLAUDE.md`（Control 版面要先建再設、`duplicate` 不存子節點、節點型別的 export 要用 NodePath、`PackedFloat32Array` 會掉、改 export 後的屬性快取、`add_animation` 不吃 frames、加寬圖片要整個專案重新掃描、runtime 連線要等幾秒） |
| **pixelorama** | A1 的 74 張分層素材、A3 的 57 格動畫、A5 的手勢與躲藏素材 | 「每格先切換再匯入整格」最穩；匯入偶爾掉像素，所以一律逐像素比對；A5 起幾乎都一次 0 差異 |
| 沒用到的 | ElevenLabs（免費素材就夠了） | 聲音由作者在 Freesound 下載、Claude 整理與合成 |

## 3. 工作方式的心得

1. **一次一步、每步先定稿**：設計圖或示意圖 → 作者確認 → 製作 → 截圖 → 作者試玩。作者在每一步都能調整（燈管只閃燈管、婦人要快跑、手電筒裝在槍上、指地面點兩下、連打改按住…），不用大改。
2. **資料化**：鏡頭、聲音、手勢、閃回、抵抗、躲藏、製作群都寫在資料裡，劇本檢查會檢查格式與檔案；之後調整不用改程式。
3. **自動測試＋實際畫面兩者都要**：測試抓流程與時機（240 項），截圖抓畫面（透明的新格子、光錐位置、字型方塊、雜訊紋路）；兩者各自都抓到對方看不到的問題。
4. **Claude 看不到、聽不到的部分**：好不好看、好不好聽、手感，全部由作者在瀏覽器判斷；Claude 負責把可以量化的部分（時機、音量、接縫、像素、大小）先驗證好。
5. **語言**：作者多次提醒要用繁體中文回報，工具之間的短句也一樣（記憶檔已記錄）。

## 4. 留給之後的

- **壓抑衝動**：目前是按住的測試版（`RESIST_HOLD = true`），正式版改回連打只要改一行。
- **升級方案**：警衛巡邏走路、主角蹲下、被發現抓回去、手勢加數值、閃回舊底片效果、更多物品閃回、A1 的 7 張新遠景與 Bad End 圖。
- **製作群**：作者名稱之後補在 `data/credits.json`。
- **下一步**：照作者決定的順序進入 **真的 2.5D**（`docs/2.5D方案.md`，另開新專案，從 B0 技術驗證開始），之後是 HD-2D。

---

# 2.5D B0：技術驗證（2026-10-20）

- 目標：在新專案 `失語者_2.5D` 確認「3D 場景＋像素人物＋側面透視鏡頭」在網頁版（Compatibility）做不做得下去。
- MCP：**godot-mcp-toolkit**（`3d_tools` 群組建灰盒、`scene_create_node`／`node_set_property` 建主角與景深平面、執行、`input_simulate`、截圖、`execute_code` 讀投影大小）、**pixelorama**（主角正面／背面）；**Blender MCP** 已安裝設定（B2 才正式用）；**Playwright** 開網頁版量 FPS。
- 成果（檔案都在 `scenes/b0/`、`scripts/b0/`、`shaders/b0_*`、`art/design/b0/`，A＋ 的程式不動）：
  - **灰盒停車場**：地面、牆、柱子（含縱深帶裡能繞前繞後的一根、前景一根）、車、聚光燈陰影、燈管、紅燈；比例 1 公尺＝主角貼圖 32px。
  - **縱深帶**：兩種做法實測（A 接受縮放 ±9%、B 縮小縱深帶 ±1%），作者看完歧路旅人的做法比較後**選 A**。
  - **景深與霧**：自己寫的景深 shader（焦點跟著主角，強度接近歧路旅人）、A2 的霧改成 3D 半透明平面；網頁版開著也是 FPS 90～100。
  - **主角正面／背面**：走路 6 格＋待機 4 格，照原圖 scene_18、scene_20 畫，四個方向自動切換。
  - **人物受光**：作者選「受光＋調亮環境光」，環境光 0.35 → 1.2。
- 狀態：B0 收尾完成，等作者確認是否進 B1。全部 240 項測試通過（B0 沒有新增自動測試，驗證靠 MCP 截圖與讀值）。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| 準備 | Blender、Blender MCP | — | Blender 由作者用 brew 安裝；附加元件用 `uvx mcp-for-blender install-addon`，`claude mcp add`（user 範圍、關遙測）；Claude Desktop 設定檔直接編輯（先備份） |
| B0-1 灰盒 | 場景、主角、鏡頭、兩種縱深帶 | `scene_create`、`3d_create_primitive`／`3d_create_light`／`3d_create_camera`／`3d_setup_environment`、`scene_create_node`（`NewResource` 建碰撞形狀）、`node_set_property`（batch）、`node_set_script`、`execute_code`（`unproject_position` 量人物在畫面上的高度） | 主角與鏡頭邏輯寫在 `b0_player.gd`／`b0_test.gd`；3D 用的 SpriteFrames 用 sed 從 2D 版複製（指向 PNG）；比較圖用 ImageMagick |
| B0-1 網頁版 | 匯出、量 FPS | — | 在拿掉外掛的副本上把主場景換成 B0 再匯出（專案設定不動）；Playwright 用真的鍵盤輸入走動、讀畫面上的 FPS |
| B0-2 景深與霧 | 兩個 shader、全螢幕平面 | `scene_create_node`（QuadMesh＋ShaderMaterial 一次建立）、`node_set_property`（`material_override:shader_parameter/…`、NoiseTexture2D＋FastNoiseLite 巢狀 `NewResource`） | shader 用一般檔案編輯；Toolkit 不能把屬性設成空值，牆面改回素面是給一個新的材質 |
| B0-3 主角前後 | 設計、繪製、接進遊戲 | pixelorama `create_canvas`、`add_frame`×19、`switch_frame`＋`import_image`×20、`add_animation_tag`、`save_project`、`export_animation`；Toolkit `editor_refresh`、`input_simulate`（action）讀動畫名稱 | 設計腳本 `player_fb.py`（共用 `pix.py`）；`.import` 改無損；`player_frames_3d.tres` 直接加動畫（比 `spriteframes_edit` 逐格加快） |
| B0-4 收尾 | 環境光 | `execute_code` 在執行中試三種亮度、`node_set_property` 寫進場景 | — |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 景深與霧 | 拆到 B0-2 | B0-1 只做灰盒、主角、鏡頭、效能、縱深截圖 |
| 主角模型 | 「2.5D 的話主角模型要改嗎」 | 建議沿用像素圖（方案的做法、HD-2D 也是），改 3D 模型等於全部人物重做 |
| 縱深帶 | 問歧路旅人的做法後選 A | 歧路旅人＝接受縮放＋強景深遮掉缺點＋多方向走路圖；景深焦點在主角上，所以主角自己的縮放遮不掉 |
| 主角前後 | 補正面、背面走路，再補待機 | 第一版太方正挺直，改成駝背版；待機照側面的喘氣節奏 |
| 人物受光 | 「人物的圖示中有受光嗎」→ 選受光＋調亮環境光 | 試 0.35／0.8／1.2，採用 1.2 |
| 景深強度 | 先照目前，有問題再調 | 不改 |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 主角在 3D 是白色方塊 | 截圖 | 2D 的 SpriteFrames 指向法線貼圖用的 CanvasTexture，3D 不支援；另做 `player_frames_3d.tres` 指向 PNG |
| 2 | Godot 自動把主角貼圖改成 VRAM 有損壓縮＋mipmap | `git status` 看到 `.import` 被改 | 改回無損、`detect_3d/compress_to=0`；比較圖重拍、網頁版重新匯出 |
| 3 | ~~聚光燈往上照~~（誤判） | 讀 `.tscn` 的變換矩陣 | 當時以為 `3d_create_light` 的 rotation 正負號相反，改用 `rotation_degrees` 重設；B1-1 在遊戲裡讀燈的方向，才發現角度本來就是對的，是我讀錯矩陣，重設沒有改到東西 |
| 4 | 柱子上有陰影條紋 | 截圖 | `shadow_bias` 0.08、`shadow_normal_bias` 2 |
| 5 | 畫面上方露出黑色、主角位置比 2D 版高 | 截圖 | 牆和柱子加高；鏡頭距離與注視高度改成每種做法各一組，讓縱深帶中間的主角是 96px、腳在 y 690 |
| 6 | 模糊的背景暈到主角頭上 | 截圖 | 取樣規則改成「比較遠的取樣點只用兩者中比較小的模糊程度」 |
| 7 | 霧被景深蓋掉的風險 | 設計時想到（畫面拷貝只有不透明物件） | 景深平面 `render_priority` −100，霧畫在之後 |
| 8 | 灰盒沒有紋路看不出模糊、霧在雜訊牆上看不出來 | 比較圖 | 地面加雜訊紋路、牆面維持素面、霧 0.3 → 0.4 |
| 9 | 起點在前景柱子後面 | 網頁版截圖 | 起點 x 5 → 8 |
| 10 | 模擬的 KeyboardEvent 收不到 | 網頁版截圖沒變 | 改用 Playwright 真的鍵盤輸入 |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 遊玩測試 | A＋ 的全部測試（確認 B0 的新檔沒有影響） | 240 項通過（每一步都跑） |
| 量測 | `unproject_position` 算主角頭腳在畫面上的位置；`input_simulate` 走動後讀座標、動畫名稱 | 速度、縱深速度、鏡頭邊界、四方向切換都符合 |
| 像素 | 20 格主角正面／背面逐像素比對 | 全部 0 差異 |
| 網頁版 | Chrome（ANGLE Metal、M2 Pro）走動、切換做法、開關陰影、景深、霧 | FPS 90～100（瀏覽器上限 100），draw calls 13～24 |

## 5. MCP 的特性（B0 新發現）

| 觀察 | 說明 |
|---|---|
| Toolkit 的 3D 工具夠建灰盒 | 方塊、燈、鏡頭、環境一次一個節點；材質只能設顏色、粗糙度，貼圖要再用 `node_set_property` |
| ~~`3d_create_light` 的旋轉正負號相反~~ | B1-1 更正：角度是對的；`.tscn` 的矩陣不好直接看，要在遊戲裡讀 `-global_transform.basis.z` 確認方向 |
| Toolkit 不能把屬性設成空值 | 要拿掉貼圖只能換一個新材質，或直接改 `.tscn` |
| runtime 連線這次很不穩 | `GAME_NOT_RUNNING` 有時連續好幾次，隔十幾秒自己恢復；遊戲的 log 裡看不到指令，問題在 MCP 伺服器端 |
| Pixelorama 小圖逐格 `import_image` 很穩 | 32×48、20 格都沒掉像素（以前掉像素的是大圖、稀疏線條、半透明） |
| `execute_code` 很適合量 3D | 綁定鏡頭當 `self` 呼叫 `unproject_position`，直接得到人物在畫面上的像素高度 |

## 6. B0 結論

1. **網頁版 3D 做得下去**：灰盒＋陰影＋4 盞燈＋景深＋霧，Chrome 上都跑滿 100 fps；之後要注意的是燈和霧的數量、真的模型與貼圖進來之後的效能（B2 再量）。
2. **像素人物在 3D 裡可以用**：要注意貼圖的匯入設定（3D 偵測會自動改成有損）、不能用 CanvasTexture、受光後偏暗（環境光調亮）。
3. **縮放是最大的取捨**：選 A 之後主角在縱深帶前後會差 ±9%，像素粗細不均要靠景深、光暈等整體氛圍來接受，主角自己無法被景深遮住。
4. **建議進 B1**：把區域系統改成 3D、接回劇本，先讓灰盒版的 7 區從頭玩到結局。

---

# 2.5D B1：區域系統改成 3D（2026-10-20～21）

- 目標：把 7 個可走動區域換成 3D 灰盒場景，接回原本的劇本與 Main，讓遊戲從標題一路玩到結局；2D 版保留，用專案設定 `game/areas_3d` 切換。
- MCP：**godot-mcp-toolkit**（範本與繼承場景、3D 燈、掛腳本、改名、存檔、執行、`execute_code` 讀值與瞬移、`input_simulate`、截圖、`script_check`）；**Playwright** 開網頁版量 FPS。Pixelorama、Blender MCP 這一級沒用到。
- 成果：
  - **3D 基礎元件**（B1-1）：`area_3d.gd`、`player_3d.gd`、`interact_point_3d.gd`，介面和 2D 版相同；區域資料維持 2D 的像素座標，在 3D 換算（64 像素＝1 公尺、縱深帶 650～735 ↔ z −1.5～1.5）；範本 `scenes/areas3d/AreaBase3D.tscn`。
  - **接上 Main**（B1-2）：Main 不再直接讀主角座標，改用區域的函式；鏡頭效果、衝動機制的手電筒支援 3D；有 3D 版的區域用 3D、沒有的照舊用 2D（2D／3D 可以混著玩）。
  - **轉換工具**（B1-3、B1-4）：`art/tools/convert_area_3d.py` 讀 2D 區域場景，一次產生 3D 場景的互動點、人物、道具、近景、位置音效、牆上的字、區域燈，再用 Toolkit 調整；重跑時只重新產生互動點與近景，手動加的東西保留。
  - **7 區都是 3D**：警衛巡視（槍上手電筒改成聚光燈）、躲藏、通風管、窗外的女兒、婦人逃跑都照 2D 的規則運作。
  - **測試與收尾**（B1-5）：同一套遊玩測試在 2D、3D 各跑一次並全部通過；劇本檢查也比對 3D 場景的互動點；網頁版 `build/web_b1/`。
- 作者的決定：2D 保留＋開關、互動點用轉換工具產生初稿＋Toolkit 調整、資料維持像素座標、人物先能用（B4 精修）；景深選 A（清楚範圍 1 → 2 公尺，B＝整條走道固定清楚當備案）；B1 維持灰盒，B2 再做模型。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| B1-1 基礎元件 | 範本、測試場景、人物 3D 版 | `scene_create`、`scene_create_node`、`3d_create_camera`、`3d_setup_environment`、`node_set_script`、`scene_create_inherited`、`execute_code`（`unproject_position` 量大小、讀互動點偵測）、`input_simulate` | 三個 3D 腳本用一般檔案編輯；6 個 `*_frames_3d.tres` 用 sed 從 2D 版複製（指向 PNG） |
| B1-2 接上 Main | 開關、鏡頭效果、提示位置 | `project_set_setting`（`game/areas_3d`）、`scene_create_inherited`（停車場）、`3d_create_light`、`script_check` | `main.gd`、`camera_fx.gd`、`impulse_fx.gd`、`area.gd` 的修改用一般檔案編輯 |
| B1-3 停車場 | 互動點、婦人、出口 | `scene_close`＋`scene_open`（讓編輯器讀到新檔）、`3d_create_primitive`（出口的樓梯間）、`node_set_property`（燈的位置、景深範圍 `material_override:shader_parameter/focus_range`）、`scene_create_node`（`AudioListener3D`） | 轉換工具是 Python 直接寫 `.tscn`：Toolkit 一次只能建一個節點、設一個屬性，37 個互動點連同子節點有幾百次呼叫；工具產生後再用 Toolkit 檢查與調整 |
| B1-4 其餘 6 區 | 6 個場景、特殊機制 | `execute_code` 呼叫 `enter_area` 直接跳到各區、瞬移主角、讀巡視狀態；`input_simulate` 一路走出口玩到結局 | 待機變化、槍上手電筒、燈光閃爍的 3D 版腳本用一般檔案編輯（內容和 2D 版相同，只換節點型別） |
| B1-5 測試與收尾 | 3D 測試、劇本檢查、網頁版 | `node_manage`（rename 停車場的燈 → `LampLight`）、`node_set_script`、`node_set_property`（batch，閃爍參數與 NodePath） | 測試與 `run_tests.sh` 用一般檔案編輯；匯出在拿掉外掛的副本上做；Playwright 用真的鍵盤輸入 |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 規劃（B1-0） | 2D 保留＋開關、轉換工具＋Toolkit、資料維持像素、人物先能用 | 照這四點分成 B1-1～B1-5 |
| 場景單薄 | 「之前有背景圖襯托，現在的場景素材好像不太夠」 | 說明 B1 是灰盒（2D 的遠景插畫、中景、霧、灰塵都還沒搬）；作者決定維持灰盒、B2 再做模型 |
| 景深 | 「沒有在聚光燈中的素材會變模糊，這樣是正常的嗎」、「歧路旅人也是一樣的做法嗎」 | 說明是景深不是聚光燈，焦點對主角、前後 1 公尺清楚；歧路旅人是整個舞台清楚、只糊前景與遠景。作者選 A：清楚範圍放寬到 2 公尺，B（走道固定清楚）當備案 |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 人物在燈下過曝 | B1-1 截圖 | 主角身上的光 1.6 → 0.6 |
| 2 | `script_check` 報 `main.gd`「無法推斷型別」 | B1-2 `script_check` | 原因是離線檢查讀不到 autoload 的型別；實際能跑，仍改成明確型別 |
| 3 | 轉換後編輯器的分頁還是舊內容 | `scene_get_tree` 看到 Points 是空的 | `scene_close` 再 `scene_open`；不在舊分頁存檔，避免蓋掉新檔 |
| 4 | 位置音效聽不到（燈管嗡聲） | 設計時想到：鏡頭離場景 14 公尺 | 範本主角加 `AudioListener3D`，以主角為聽者（和 2D 版的鏡頭在主角身上一樣） |
| 5 | 出口的門孤零零立在空中、聚光燈和燈具對不上、紅燈卡在樓梯間上緣 | 截圖 | Toolkit 加樓梯間灰盒、燈移到燈具下方與門上方 |
| 6 | 轉換工具的 `id=` 讀到 `uid=`、`pixel_size` 四捨五入成 0.0312、跨行的文字只讀到第一行 | 執行錯誤、檢查產生的 `.tscn` | 屬性名稱前面要是非文字字元、數字留 6 位、跨行字串接著讀 |
| 7 | 燒毀的車沒有 3D 版的 SpriteFrames | 工具的警告 | 它本來就指向 PNG，可以沿用；工具改成檢查有沒有 CanvasTexture，並一起修匯入設定 |
| 8 | 區域燈在後面的物件上照出亮斑（牆前、街道）、車火離車子很遠 | 截圖 | 燈改放縱深帶中間；跟著互動點的燈放在那個點前面 |
| 9 | 妻子和圍欄同一個深度，前後順序靠運氣 | 截圖 | 同一個點底下的圖照 2D 的順序往前錯開 0.01 公尺 |
| 10 | `guard_patrol.gd` 改成 2D／3D 共用後 `length` 無法推斷型別 | `script_check`（背景測試也全部報錯） | 明確型別 |
| 11 | 3D 的 `place_player` 只給 x 時把主角放回縱深帶中間 | 3D 測試失敗 1 項 | 和 2D 一樣保留原本的前後位置 |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 遊玩測試 | 7 個測試在 2D、3D 各跑一次（`run_tests.sh` 預設兩種都跑，`AREAS_3D=0／1` 只跑一種）；`play_base.gd` 加上不分 2D／3D 的查詢（主角的像素座標、放主角、燈的亮度、音效範圍） | 2D 240 項、3D 239 項全部通過（3D 的「y 排序」「前景層」兩項合成「近景在走道前面」一項） |
| 劇本檢查 | 2D 與 3D 場景的 `point_id` 都和區域資料比對 | 通過；在副本裡故意改錯一個 3D 互動點，會報兩個錯 |
| MCP 遊玩 | 從標題一路走出口：停車場 → 街道 → 診所 → 過場 6、7 → 設施走廊（通風管）→ 廢墟 → 舊家 → 過場 15 → 牆前 → 結局 C | 全部 3D、log 無錯誤 |
| 網頁版 | Chrome（ANGLE Metal、M2 Pro）的 3D 停車場、街道 | 站著與走路都是 100 FPS（瀏覽器上限），最慢一格 15 ms；console 沒有錯誤；`index.pck` 32.9MB（A＋ 31.3MB） |

## 5. MCP 的特性（B1 新發現）

| 觀察 | 說明 |
|---|---|
| 大量節點用「工具產生＋Toolkit 調整」 | Toolkit 適合檢查、改幾個屬性、加幾個節點；幾百個節點用 Python 直接寫 `.tscn` 快很多，產生後再用 Toolkit 開、看、改 |
| 編輯器不會自己重新載入已開啟的場景 | 外部改了 `.tscn` 之後，`editor_refresh` 不會更新已開的分頁；要 `scene_close`（`cleanup` 群組）再 `scene_open` |
| `execute_code` 呼叫 Main 的函式很好用 | `enter_area` 直接跳到任何區域、`place_player` 瞬移，不用每次從頭玩 |
| 背景跑 headless 測試時 runtime 常斷 | 測試的副本沒有外掛，但 `GAME_NOT_RUNNING` 還是常出現；等測試結束、先呼叫一次 `debugger_get_log`，再呼叫 runtime 工具就連上了 |
| `node_set_property` 的 batch 可以設 NodePath | 燈的閃爍要連到另一個節點（燈管的圖、嗡聲），一次設完 |
| 執行前連 `script_check` 才抓得到型別錯誤 | 遊戲 log 不會顯示編譯錯誤；背景測試也只會看到一堆 SCRIPT ERROR |

## 6. B1 結論

1. **7 區都是 3D、可以玩到結局**：劇本、數值、旗標、事件完全沒改，只換了區域場景；2D 版保留，用 `game/areas_3d` 切換。
2. **轉換工具很划算**：37 個互動點連同人物、道具、近景一次產生，之後 B2 換成真的模型時，互動點也不用重做。
3. **網頁版的效能還很寬鬆**：灰盒＋多盞燈＋景深在 Chrome 上跑滿 100 FPS；B2 放進真的模型與貼圖後要再量。
4. **還沒做的**（照作者決定留給之後）：遠景插畫、中景與前景的圖、霧、粒子（灰塵、火星、灰燼）、中景的位置音效（警報、火桶）；人物精修留給 B4。
5. **建議進 B2**：用 Blender MCP 做第一個區域（停車場）的模型，取代灰盒。

---

# 2.5D B2：停車場樣板（2026-10-21）

- 目標：用 Blender MCP 做出完整的 3D 停車場（模型、貼圖、燈管、紅燈、陰影），練習三個 MCP 的配合，並把做法整理成 B3 其餘 6 區的樣板。
- MCP：**Blender MCP**（建模、材質、UV、匯出、預覽）、**Pixelorama**（13 張像素貼圖的原始檔與匯出）、**godot-mcp-toolkit**（鏡頭比較、包裝場景、擺放模型、燈光、執行、截圖、讀值）；**Playwright** 量網頁版 FPS。
- 成果：
  - **鏡頭 B**（作者在 B2-1 從三種做法中選）：天花板真實 3 m，鏡頭在天花板下、距離 7.2 m、高 2.2 m、往下 5°，主角約 214 px；寫進 `area_3d.gd` 的預設值，7 區都換。
  - **12 個低多邊形模型**：結構（地面、後牆、天花板、大樑、管線、停車格線、車擋）、柱子、翻倒的車與廢車、燈具（亮的與壞的）、紅色警示燈、出口樓梯間、門、血跡、照片、地面殘骸；`assets/models/parking/*.gltf`，原始檔 `art/models/parking/parking.blend`。
  - **13 張像素貼圖**（32 px＝1 m）：`art/design/b2/textures.py` 設計 → Pixelorama 存 `.pxo`、匯出 PNG（`assets/textures/parking/`）→ Blender 接材質、程式算 UV。
  - **燈光**：環境光 1.2 → 0.5（青綠），燈管聚光燈有陰影、熄滅時燈管換暗材質，x 17 的壞燈閃冷光，出口紅燈。
  - 樣板流程文件 `docs/2.5D_區域樣板流程.md`；網頁版 `build/web_b2/`。
- 作者的決定：低多邊形＋像素貼圖、可調查的小道具也建模、天花板真實 3 m＋降低鏡頭（選 B）、停車格＋第二排柱子、全部 Blender MCP 自建；「2.5D 版和原本的版本不一樣，做新的素材沒問題」。

## 1. 各步驟使用的工具

| 步驟 | 內容 | MCP 工具 | 繞過 MCP 的部分（原因） |
|---|---|---|---|
| B2-0 規劃 | 物件清單、配置 | — | 只讀檔；`AskUserQuestion` 問四個決定 |
| B2-1 鏡頭比較與配置圖 | 3 m 天花板的灰盒、三種鏡頭 | Toolkit `scene_create_inherited`、`3d_create_primitive`×25、`node_set_property`、執行中 `execute_code` 改鏡頭參數＋`unproject_position` 量大小、`runtime_screenshot` | 配置圖用 ImageMagick MVG 畫（`layout.py`） |
| B2-2 建模 | 12 個模型、鏡頭 B 預覽 | Blender `execute_blender_code`（bmesh 建模、合併、glTF 匯出）、`look`（camera／angles、rendered／material） | — |
| B2-3 貼圖 | 13 張貼圖、材質、UV | Pixelorama `import_image`×13、`save_project`、`export_image`、`draw_pixels`（補像素）；Blender 接 Image Texture、bmesh 算 UV | 設計用 Python 腳本；逐像素比對用 ImageMagick |
| B2-4 放進 Godot | 匯入、擺放、鏡頭 B | Toolkit `editor_refresh`（指定檔案）、`scene_create_inherited`×12（包裝場景）、`scene_instantiate`（batch）、`scene_delete_node`、`node_set_property`、`execute_code`（讀貼圖像素、燈管材質） | `.import` 用 sed 改；`area_3d.gd`、`flicker_light_3d.gd` 用一般檔案編輯 |
| B2-5 燈光 | 環境光、壞燈 | Toolkit 執行中試數值、`node_set_property`（`NewResource` Environment）、`scene_create_node`＋`node_set_script` | — |
| B2-6 收尾 | 測試、網頁版、文件 | — | 副本上匯出；Playwright 真的鍵盤 |

## 2. 作者回饋與調整

| 項目 | 作者的回饋 | 調整 |
|---|---|---|
| 天花板 | 選「真實 3 m＋降低鏡頭」 | 說明主角 96 px 時畫面約涵蓋 12 m 高，3 m 只佔 1/4；拍 A 平視／B 拉近／C 切掉前段天花板三種，作者選 B |
| 素材 | 「2.5D 版和原本的版本不一樣，所以做新的素材沒問題」 | 人物照新大小重畫留給 B4；記進方案與記憶 |
| 提示文字 | 「邊走邊看到提示文字的話字會模糊」 | 3D 投影位置是小數＋Main 用上一格的鏡頭：位置取整數、投影前先更新鏡頭 |
| 其他場景 | 問其他場景的 3D 素材是不是 B3 做 | 是；B2-6 的樣板流程文件就是給 B3 用 |

## 3. Claude 自己發現並修好的問題

| # | 問題 | 怎麼發現 | 解法 |
|---|---|---|---|
| 1 | 清空 Blender 場景用了 `read_factory_settings`，MCP 連線斷掉 | 指令沒有回應 | 請作者重新 Start MCP Server；之後只刪物件、網格、材質（記進 CLAUDE.md） |
| 2 | 前景柱子 x 32.5 擋住出口門 | Blender 預覽 | 前景柱子改到 x 12.5、19.5、28.5（離互動點 2 m 以上） |
| 3 | 柱子的「B2」太小，看起來像「B:2」 | 貼圖預覽 | 改成 2×2 像素一格 |
| 4 | Pixelorama 匯入出口牌時白色線段多延伸 13 格 | 逐像素比對 | `draw_pixels` 補回 |
| 5 | `verify.sh` 回報 3115 格不同 | 和 PNG 比對結果不一致 | 色碼大小寫不同造成誤報，改成 PNG 對 PNG 比 |
| 6 | Blender 執行中自己重開成預設場景 | 找不到物件 | 從 `parking.blend` 用 `libraries.load` 搬回；覆蓋存檔前先 `libraries.remove` |
| 7 | 紅色警示燈擋住出口牌 | Blender 近看 | 警示燈改放 2.78 m |
| 8 | `.glb` 匯入後貼圖被抽成 31 份複本、會被改成有損 | 看匯入產生的檔案 | 改匯出 `.gltf`，貼圖指向 `assets/textures/parking/` |
| 9 | Toolkit 的 `scene_instantiate` 不能放 `.gltf` | 錯誤訊息 | 用 `scene_create_inherited` 做包裝 `.tscn` |
| 10 | 新加的 `off_mesh` 屬性設不進去 | `node_set_property` 讀回是 null | 指定腳本 `editor_refresh` 後再設 |
| 11 | 燈管只有 1～2 px，看不出來 | 遊戲截圖放大 | Blender 加粗、發光加倍 |

## 4. 自動驗證

| 層級 | 內容 | 結果 |
|---|---|---|
| 遊玩測試 | 2D、3D 各跑一次 | 2D 240 項、3D 239 項全部通過（B2-4、B2-5 各跑一次） |
| 像素 | 13 張貼圖設計圖 vs Pixelorama 匯出；遊戲裡讀地面貼圖一個像素 | 全部 0 差異；(64,75,77) 和原圖相同 |
| MCP 讀值 | 燈管材質、熄滅時換材質與嗡聲靜音、提示文字位置是整數 | 全部符合 |
| 網頁版 | Chrome（ANGLE Metal、M2 Pro）走過燈下、壞燈 | 100 FPS；第一次走到燈下卡一次約 1 秒，來回第二次不會（shader 第一次編譯）；`index.pck` 33.0 MB（B1 32.9）；console 無錯誤 |

## 5. MCP 的特性（B2 新發現）

| 觀察 | 說明 |
|---|---|
| Blender MCP 適合用程式建模 | `execute_blender_code` 跑 bmesh，做低多邊形很快；`look` 的 camera 模式可以直接用和遊戲相同的鏡頭預覽 |
| Blender MCP 的連線比較脆弱 | 重設 Blender、程式裡刪節點都斷過線；Blender 還自己重開過一次。步驟要切小、隨時存檔 |
| 三個 MCP 的資料流 | Python 設計 → Pixelorama（原始檔＋匯出）→ Blender（材質、UV、匯出 `.gltf`）→ Toolkit（包裝場景、擺放、燈光），每一段都用檔案交接 |
| Toolkit 處理 3D 模型的限制 | 只能放 `.tscn`；位置要帶型別、旋轉用弧度；匯入要指定檔案刷新 |
| runtime 連線 | 測試或匯出剛跑完時常 `GAME_NOT_RUNNING`，呼叫一次 `debugger_get_log` 後再試通常就好 |

## 6. B2 結論

1. **三個 MCP 可以完整做出一個 3D 區域**：建模、貼圖、組場景、燈光、驗證都在 MCP 裡完成，只有設計與比對用 Python／ImageMagick。
2. **鏡頭 B 讓 2.5D 有室內感**，但人物在畫面上變大一倍，原本的像素圖顆粒變粗，B4 要照新大小重畫。
3. **網頁版效能還很寬鬆**：模型＋貼圖＋3 盞燈＋陰影＋景深仍是 100 FPS；要注意第一次編譯 shader 的卡頓（B5 可以預熱）。
4. **待處理**：前景的地上小物（2D 像素圖）調暗後變成黑色剪影；其他 6 區還是灰盒。
5. **建議進 B3**：照 `docs/2.5D_區域樣板流程.md` 一區一區做，依遊戲順序從街道開始。
