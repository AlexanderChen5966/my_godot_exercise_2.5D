# 失語者 2.5D — Godot 專案（由 A＋ 完成版複製，2026-10-19）

> **這是 2.5D 版的專案**（`失語者_2.5D`，`project.godot` 的名稱是「失語者_2.5D」）。A＋ 的完成版在旁邊的 `失語者_Godot`，**不要去改它**。
> 2.5D 的方案在 `docs/2.5D方案.md`，分步指令在 `PROMPTS.md` 的「2.5D B0 分步指令」；一次只做一步，B0-0 只規劃、不改檔案。
> 下面的內容是從 A＋ 專案複製過來的，2.5D 做到哪裡再逐步改寫；與 2.5D 方案衝突時（例如「A＋ 完成前不要做 3D」）以 2.5D 方案為準。
> 不要同時開著兩個專案的 Godot 編輯器：godot-mcp-toolkit 可能會連到另一個專案。
> **2.5D 進度**：B0 技術驗證完成（2026-10-20，經過見 `MCP實驗紀錄.md` 的「2.5D B0」、決定見 `docs/2.5D方案.md` 的「B0 的決定」）：縱深帶採用接受縮放（3 公尺）、主角有正面／背面走路與待機、人物受光＋環境光 1.2、景深與霧用 shader 模擬。**B1 完成（2026-10-21）**：7 區都有 3D 灰盒場景（`scenes/areas3d/*3D.tscn`，範本 `AreaBase3D.tscn`，由 `art/tools/convert_area_3d.py` 從 2D 場景產生再用 Toolkit 調整），專案設定 `game/areas_3d` 切換 2D／3D（2D 保留）；**`run_tests.sh` 預設 2D、3D 各跑一次**（`AREAS_3D=0／1` 只跑一種），劇本檢查也比對 3D 場景；網頁版在副本上匯出到 `build/web_b1/`。經過見 `MCP實驗紀錄.md` 的「2.5D B1」。**B2 完成（2026-10-21）**：停車場是樣板（Blender 模型＋Pixelorama 像素貼圖＋燈光，鏡頭 B），做法整理在 `docs/2.5D_區域樣板流程.md`，經過見 `MCP實驗紀錄.md` 的「2.5D B2」，網頁版 `build/web_b2/`。**B3 進行中（2026-10-27 起）**：決定見 `docs/2.5D方案.md` 的「B3 的決定」，分步指令在 `PROMPTS.md` 的「2.5D B3 分步指令」（每區 a 配置圖 → b 建模＋貼圖 → c 放進 Godot＋燈光＋驗證）。
> **2.5D 的坑（B0-1）**：①像素圖用在 3D 時，Godot 會自動把 `.import` 改成 VRAM 壓縮＋mipmap（`detect_3d`），要改回 `compress/mode=0`、`mipmaps/generate=false`，並把 `detect_3d/compress_to=0`；②2D 的 SpriteFrames 若指向 CanvasTexture（法線貼圖用，例如 `player_canvas.tres`），在 3D 會是白色方塊，3D 要另做指向 PNG 的版本（`player_frames_3d.tres`）；③`3d_create_light` 的 rotation 是對的（B0 時誤判成正負號相反，B1-1 在遊戲裡讀燈的方向確認）；`.tscn` 的 Transform3D 矩陣不好直接看方向，要確認時在遊戲裡讀 `-global_transform.basis.z`。B0 的檔案在 `scenes/b0/`、`scripts/b0/`，網頁版在副本上把主場景換成 B0 後匯出到 `build/web_b0/`。④**Blender MCP 清空場景不要用 `bpy.ops.wm.read_factory_settings`**（B2-2）：它會連 MCP 附加元件一起重設、連線斷掉，要請作者在 Blender 側邊欄重新 Start MCP Server；改成逐一刪除物件、網格、材質。B2 的模型原始檔在 `art/models/parking/parking.blend`，匯出成 `assets/models/parking/*.gltf`＋`.bin`（**不用 `.glb`**：Godot 會把包在裡面的貼圖抽成多份複本、還被改成有損；貼圖：B3 起通用的在 `assets/textures/common/`、各區專屬的在 `assets/textures/<區域>/`，匯出用 `export_keep_originals=True` 讓 `.gltf` 指向原檔；`.import` 要無損、不產生 mipmap、關閉 3D 偵測）。每個物件原點在自己的底部中心，Blender 的 Y＝負的 Godot z；Toolkit 的 `scene_instantiate` 只能放 `.tscn`，所以每個模型有一個 `scene_create_inherited` 做的包裝場景（`assets/models/parking/*.tscn`）。鏡頭 B（B2-4 起）寫在 `area_3d.gd` 的預設值。


這份檔案是給 Claude Code 讀的專案說明。每次開新對話都會自動載入。

## 目前進度（每次開始前先看）

- **階段 1（視覺小說式）已完成**，下方「要做的功能」「完成標準」是階段 1 的內容，保留作為現有系統的說明。
- 之後改走 **Lv1～5 新路線**（橫向捲軸 2.5D、可移動），練習 MCP 與 AI 輔助開發：
  - 路線、原規劃與新路線的對照、已確定的決策：`docs/開發路線圖.md`
  - 每一級的規格、步驟、驗證方式、完成標準：`docs/Lv製作流程.md`
  - 作者貼給你的分步指令：`PROMPTS.md` 的「LvN 分步指令」（每一級開始時補上該級的指令）
- **暫不支援手機**：Lv1 起可走動區域只做鍵盤操作，不要自行加觸控。按鍵衝突（`interact` 與 `ui_accept`）已在 Lv6-1 處理：所有選項自動聚焦第一個能選的選項（鎖住的不能聚焦），一次按鍵只處理一件事（`tests/test_lv6.gd` 檢查）。
- **Lv1（停車場可走動）、Lv2（景深分層與光影）已完成（2026-10-02）；Lv3（Pixelorama MCP 畫主角）已完成（2026-10-05）**：32×48、放大 2 倍，左右各一套共 20 格（待機 4 fps、行走 8 fps），原始檔 `art/player.pxo`，遊戲用 `assets/sprites/player.png`＋`player_frames.tres`。經過與觀察見 `MCP實驗紀錄.md` 的「Lv3」。**劇本 v1.5 已定稿（2026-10-05）**：`docs/story_v1.5_outline.md`、`docs/story_v1.5_draft.md`，素材需求 `docs/asset_requests.md`。**Lv4（多區域、物品與旗標）已完成（2026-10-05）**：停車場（v1.5）→ 街道 → 診所，格式與步驟見 `docs/Lv製作流程.md` 的「Lv4」，經過見 `MCP實驗紀錄.md` 的「Lv4」。**Lv5（其餘區域、Bad End 與結局）已完成（2026-10-06）**：7 個區域＋3 段過場、6 個結局、Bad End 重試，規格見 `docs/Lv製作流程.md` 的「Lv5」，經過見 `MCP實驗紀錄.md` 的「Lv5」。**Lv6（鍵盤操作、衝動機制、像素人物與場景物件、平衡）已完成（2026-10-06）**：規格見 `docs/Lv製作流程.md` 的「Lv6」，經過與從階段 1 到 Lv6 的整體總結見 `MCP實驗紀錄.md`。**下一版的想法**（會動的像素、音效、場景、互動方式）記在 `docs/開發路線圖.md` 第 6 節。
- **下一版（2026-10-08 作者決定）：先做 A＋（深化 2.5D，延續本專案、維持網頁版），之後再決定 HD-2D**。**2026-10-14 作者決定順序：A＋ 做完 → 真的 2.5D（3D 場景、側面固定鏡頭；A＋ 其實是「2D 強化版」）→ HD-2D**；A＋ 完成前不要做 3D 的東西。2.5D 的決定：複製新專案、3D 模型先用 Blender MCP 實驗建模（Godot 基本形狀能沿用的先沿用，最後才用免費素材包），Blender MCP 從 2.5D 起使用。方案見 `docs/2.5D方案.md`（網頁版做不到的效果：A shader 模擬 → B 預先算圖 → D 桌面版 → C 換網頁引擎；等級 B0～B5）。**A1（7 區分層背景）、A1.5（上下左右移動）已完成（2026-10-13）**，經過見 `MCP實驗紀錄.md` 的「A＋ A1」「A＋ A1.5」。**A2（光影與空氣感）已完成（2026-10-13）**，經過見 `MCP實驗紀錄.md` 的「A＋ A2」：A2-1 陰影、法線貼圖完成（7 區都有陰影，主角與 6 個人物有法線貼圖），A2-2 粒子、A2-3 霧與光束、A2-4 鏡頭完成（霧與光束的 shader 在 `shaders/`，霧的共用材質 `assets/fx/fog_material.tres`；鏡頭的推近、震動、晃動在 `scripts/camera_fx.gd`〔Main 的 `CameraFx`〕，資料用 `"camera": "shake"` 指定震動）。**A3（會動的像素）已完成（2026-10-14）**，經過見 `MCP實驗紀錄.md` 的「A＋ A3」：火焰（車、火桶）、停車場燈管、婦人（尖叫＋逃跑）、感染者群（啃食＋轉頭）、女科學家（抱筆記本 → 遞出 → 跑走）、警衛（低姿搜索 → 舉槍瞄準，槍上手電筒 `scripts/gun_torch.gd`）、妻子（分麵包）、女兒（眨眼、比手勢、轉身淡出；選項用 `"figure": "wave"` 指定人物動畫）、主角新動作（調查伸手、朝人前傾）完成，8 組全部完成。**A4（聲音）已完成（2026-10-14）**，經過見 `MCP實驗紀錄.md` 的「A＋ A4」。**A5（新的互動方式）已完成（2026-10-16）**，經過見 `MCP實驗紀錄.md` 的「A＋ A5」：作者選先做手勢、記憶閃回（效果好再加壓抑衝動、躲藏）。**手勢**（設計與定稿文字 `docs/A5_手勢設計.md`）：G 鍵比出「我——在——這——裡」（`player.gd` 的 `play_gesture()`，動畫 `gesture_right`／`left`，原始檔 `art/player_gesture.pxo`），互動點的 `gesture`（`text`、`range` 預設 360、`effects`）在比完後顯示反應、每人一輪一次、設定旗標「區域.互動點.gesture」；沒有對象時一輪第一次顯示 `story.json` 的 `gesture_alone`；數值用方案 A（不加）。**記憶閃回**（`docs/A5_記憶閃回設計.md`）：互動點或 variant 的 `"flashback": "scene_xx.webp"`，調查時白光一閃 → 原插畫（`shaders/flashback.gdshader`，效果 A；B 的參數寫在 shader 註解）約 2.2 秒 → 回到區域顯示文字，按互動鍵跳過、一輪一次；Main 的 UILayer 有 `Flashback`、`Flash`；閃回音 `assets/sfx/flashback.ogg`（暫用 Claude 合成的候選 a）。**shader 的亂數不要用 `fract(sin(...))`**（Compatibility 精度下會有規則紋路），用 hash12。**壓抑衝動**（`docs/A5_壓抑衝動設計.md`）：互動點的 `resist: {presses, time, fail}`，事件文字後抵抗（狀態 `RESIST`，對話框的 `Resist` 量表）；**目前是測試版：`main.gd` 的 `RESIST_HOLD = true`＝按住空白鍵（依 `hold` 秒數），正式版要改回 `false`＝連打（依 `presses`）**（作者 2026-10-16），成功隱藏 fail 選項、失敗自動選 fail；判定後鎖按鍵 0.9 秒（`_input_locked_until`）；婦人、女科學家、警衛、妻子有，女兒沒有。**躲藏**（`docs/A5_躲藏設計.md`，作者 2026-10-16 定稿，四項都做 A、B 是升級方案）：設施走廊的警衛依互動點的 `patrol` 由 Main 建立 `scripts/guard_patrol.gd`（原地轉身、主角在光照到的地面範圍內 0.4 秒 → 被發現 → 警衛事件換成 `lab.guard.spotted` 的 variant 文字）；新互動點類型 `hide`（掩護按 E 躲起來，`player.gd` 的 `in_cover` 變暗半透明、一移動就出來；有 `to_x` 的是通風管：`text` → 黑畫面 → 到 `to_x` 顯示 `after_text`，`done` 的事件一起結束）；區域 `hint` 走過 `after_x` 時畫面下方提示一次。**A6（收尾與發布）已完成（2026-10-16），A＋ 全部完成**，經過見 `MCP實驗紀錄.md` 的「A＋ A6」與「A＋總結」。**下一步：照作者的順序進入 2.5D（`docs/2.5D方案.md`，另開新專案；`PROMPTS.md` 有 B0 分步指令），作者指示後才開始**。A6 的內容（分步指令在 `PROMPTS.md`；作者決定順序：1 設定畫面 → 2 製作群 → 4 瘦身〔沒用到的 BGM 不匯出＋字型只留用到的字〕→ 5 測試匯出打包 → 6 紀錄；壓抑衝動改回連打不在清單裡，先維持按住版）。**A6-1 設定畫面已完成**：標題選單 `TitleMenu`、設定面板 `SettingsPanel`，設定存在 `user://settings.cfg`（`scripts/game_settings.gd`），打字聲改讀設定；**測試用 `user://settings_test.cfg`**（`play_base.gd` 設定，避免讀到作者的設定）。**A6-2 製作群已完成**：內容在 `data/credits.json`（作者名稱、開發協助先不加），Godot 的授權全文與第三方元件清單由引擎提供，面板 `CreditsPanel`。**A6-4 瘦身已完成**（`index.pck` 52.3 → 31.3MB）：沒用到的 8 首 BGM 在 Web 的 exclude_filter（劇本檢查確認用到的沒被排除）；字型只留用到的字（`art/tools/font_subset.py`，完整版在 `art/fonts/`，**改了任何文字後要執行 `~/Tools/fonttools-venv/bin/python art/tools/font_subset.py`**，劇本檢查會抓缺字）。A6-5 打包：`build/shiyuzhe_web_itch.zip`（39.2MB），上傳步驟與公開前確認在 `docs/itch.io上傳步驟.md`。A4 的內容：A4-1 素材（`assets/sfx/` 43 個、`bgm_bad`／`bgm_shelter`／`bgm_title`，來源在 `docs/素材來源.md`，整理工具 `art/tools/a4_sfx_prep.py`）、A4-2 程式、A4-3 作者試聽後修改（有聲音的轉場在黑畫面停 0.7 秒、遊戲啟動時預載音效〔網頁版第一次播放會延遲〕、打字聲關閉 `TYPE_SOUND`、腳步停下淡出；`sfx` 可寫成陣列同時播放）。聲音用資料指定：區域 `ambience`（環境音）、`floor`（concrete／glass／wood 腳步）；互動點、選項、場景的 `sfx`（例如 `"growl"` 會從 `growl_1`、`growl_2` 隨機挑，`scripts/sound_lib.gd`）、`done_sfx`（人物消失時）；互動點沒寫 sfx 時調查＝翻找、item＝撿起；出口在通過時播 sfx。音量分組 Master／BGM／SFX／Ambient（`default_bus_layout.tres`）；位置音效是區域場景裡的 `AudioStreamPlayer2D`（bus Ambient）；人物的 `idle`／`event`／`scream`／`run` 動畫由 `interact_point.gd` 依事件開始、結束自動切換；設計檔在 `art/design/a3/`，待機偶爾換動作用 `scripts/idle_variation.gd`；每一步記在 `docs/開發路線圖.md` 的「進度紀錄」，分步指令在 `PROMPTS.md`。
  - A＋ 的等級 A1～A6、素材分工、驗證與完成標準：`docs/A+方案.md`；外部 AI 素材的提示詞與檔名：`docs/A+素材提示詞.md`；分步指令：`PROMPTS.md` 的「A1 分步指令」（之後每一級開始時補上）。
  - 聲音素材**免費素材為主、AI 補缺**（作者 2026-10-08）：專案沒有商業用途，非商業授權也可以用，以找到適合的聲音為最優先。作者下載候選、Claude 整理（轉檔、裁切、音量、循環），作者挑選後才放進 `assets/`；每個外部素材記錄在 `docs/素材來源.md`。
  - 找不到合適的聲音時，才用 **ElevenLabs MCP**（或 Suno）補：**每次呼叫會消耗點數，只在作者同意的範圍內呼叫**。
  - **不要做 HD-2D 的任何東西**（3D、Forward+、Blender MCP），除非作者決定開始；方案見 `docs/HD-2D方案.md`（桌面版優先、另開專案）。
- **一次只做一級**：沒有作者的指示，不要開始下一級，也不要提前做後面等級的功能。
- MCP：**godot-mcp-toolkit**（Godot 編輯器）＋ **pixelorama**（像素繪圖，Lv3 起使用）。
  - pixelorama 註冊在 **user 範圍**（`~/Tools/pixelorama-mcp`），擴充功能用自己從原始碼打包的 `PixMcpBridge.zip`。安裝紀錄與排除問題見 `docs/Lv製作流程.md` 的 Lv3 與 `MCP實驗紀錄.md` 的「Lv3 準備」。
  - 使用時要**同時開著 Godot 編輯器和 Pixelorama**；開始前先呼叫一次 `list_canvases` 確認連線（擴充功能也可用 `curl -s http://127.0.0.1:7373/health` 確認）。
  - Pixelorama 的擴充功能在 `127.0.0.1:7373` **沒有驗證機制**，不畫圖時請作者關掉 Pixelorama。
- 劇本 **v1.5 已定稿**：Lv4 寫入停車場、街道、診所的資料，Lv5 寫入其餘部分（作者決定分批，讓遊戲每一步都能玩）。1.0 版劇本備份在 `docs/story_v1.0.json`。`docs/v1.5_劇本調整規劃.md` 是原規劃，內容以新大綱與草稿為準。
- 每一級完成時：在 `MCP實驗紀錄.md` 新增該級的一節，並更新 `docs/開發路線圖.md` 的「進度紀錄」。

## 目標

把原本 Kivy 版的選項式分歧結局遊戲，在 Godot 重做成**網頁版**：背景圖 + 文字 + 選項 + 背景音樂，點擊推進。
這是一個 **MCP 工作流實驗**：場景與節點盡量用 `godot-mcp-toolkit` MCP 工具建立，並用 MCP 執行遊戲、截圖、模擬輸入、讀 log 來驗證。

## 技術限制（不要違反）

- Godot 4.5 以上，**只用 GDScript**（C# 無法匯出網頁版）。
- 渲染器固定 `gl_compatibility`（網頁需要），已在 `project.godot` 設好。
- 基準解析度 1152×768（3:2，與背景圖相同），stretch 模式 `canvas_items` + `keep`。
- 字型已在專案設定指定為 `res://assets/fonts/NotoSansTC-Regular.ttf`，不需要每個節點個別設定。
- **劇本規則（2026-10-05 作者同意修改）**：Claude 可以**起草**劇本（大綱、文字草稿，寫在 `docs/`），但必須經作者審核**定稿**後，才能寫入 `data/story.json` 與 `data/areas/*.json`。未經作者定稿，不可以改寫劇情。
- 不要手動編輯 `.godot/` 資料夾。
- 不要修改 `addons/godot_mcp_toolkit/`（第三方外掛），也不要手動改 `project.godot` 的 `[editor_plugins]`、`[autoload] MCPRuntimeServer`（外掛自己管理）。
- 子資料夾裡**不可以有 `project.godot`**（例如 `scripts/project.godot`），否則 Godot 會把整個資料夾當成別的專案而略過，導致 `class_name` 找不到。

## 專案結構

```
project.godot          專案設定（解析度、字型、匯入預設值都已設好）
export_presets.cfg     已有一個名為 "Web" 的匯出設定，輸出到 build/web/index.html
data/story.json        劇本資料（見下方格式）
assets/bg/             20 張背景 scene_01.webp ~ scene_20.webp（1152×768）
assets/bgm/            20 首背景音樂 bgm_01.ogg ~ bgm_20.ogg（匯入時已設為循環）
assets/sfx/click.ogg   點擊音效
assets/fonts/          Noto Sans TC
tools/validate_story.gd  劇本檢查工具
tests/                 自動遊玩測試（test_lv4.gd、test_lv5.gd、test_lv6.gd、test_a15.gd、test_a4.gd、test_a5.gd、test_a6.gd，共用操作在 play_base.gd；選選項用方向鍵＋Enter、互動鍵用真正的空白鍵）與執行腳本 run_tests.sh（在拿掉外掛的副本上執行）
addons/godot_mcp_toolkit/  Godot MCP Toolkit 編輯器外掛（v1.0.2，MIT）
.mcp.json              Claude Code 的專案 MCP 設定（由外掛產生，連到 godot-mcp-toolkit）
scenes/Main.tscn       主場景
scripts/story_data.gd  劇本讀取（class_name StoryData）
scripts/main.gd        主畫面邏輯
scripts/game_state.gd  一輪遊戲的全域狀態（class_name GameStateData；autoload 名稱 GameState，Lv4-1 用 autoload_manage 加入）
scripts/area_data.gd   區域資料讀取、互動點的文字／條件／variants、區域資料的檢查
scripts/sound_lib.gd   A4：音效名稱 → 檔案（隨機變化），劇本檢查也用它確認檔案存在
scripts/impulse_fx.gd  衝動機制（Lv6-2）的紅色暈影、心跳、手電筒閃爍；掛在 Main 的 UILayer/ImpulseOverlay，**強度參數都在它的屬性面板**
shaders/impulse_vignette.gdshader  紅色暈影
assets/sfx/heartbeat.wav  暫用心跳聲（Toolkit sound_generate 產生，作者準備好再換）
docs/開發路線圖.md       原規劃（階段 1～4）與新路線（Lv1～5）、決策、進度紀錄
docs/Lv製作流程.md       Lv1～5 的規格、步驟、驗證與完成標準
docs/v1.5_劇本調整規劃.md  劇本 1.5 原規劃（視覺小說格式；方向仍有效，格式改成區域 × 事件）
docs/story_v1.5_outline.md  劇本 v1.5 大綱（定稿：區域、事件、數值、Bad End）
docs/story_v1.5_draft.md    劇本 v1.5 完整文字（定稿，標示原文／改／新）
docs/asset_requests.md      v1.5 素材需求與生成提示詞（作者準備背景、BGM、音效）
docs/story_v1.0.json        1.0 版劇本備份（不放 data/，避免被匯出）
docs/itch.io上傳步驟.md      網頁版打包成 zip、上傳 itch.io 的步驟與公開前確認
docs/A+方案.md             下一版 A＋（A1～A6）的內容、素材分工、驗證與完成標準
docs/A+素材提示詞.md        A＋ 外部素材的提示詞、搜尋關鍵字、檔名與勾選清單
docs/素材來源.md            每個外部素材的來源與授權（放進專案時加一列）
docs/2.5D方案.md           真的 2.5D 方案（A＋ 之後、HD-2D 之前；3D 場景＋側面鏡頭、網頁版、新專案）
docs/2.5D_區域樣板流程.md   B2 整理的一區從灰盒到模型＋貼圖＋燈光的步驟（B3 照做）
docs/2.5D_天空與陽光.md     戶外天空與陽光：業界做法、歧路旅人資料、A／B 比較；決定用像素天空平面（漸層天空當備案）
docs/HD-2D方案.md          HD-2D 方案（之後再決定，桌面版優先、另開專案；作者決定前不要做）
art/player.pxo         主角的 Pixelorama 原始檔（含 .gdignore，不匯出）
art/design/            A＋ 的設計腳本、每一格的設計圖（.txt）、GIF 預覽與 A／B 比較圖（暫存區會被清空，A3 起搬來這裡；說明見 art/design/README.md）
art/tools/             像素素材的共用工具（A1-6 起放這裡，暫存區會被清空）：pix.py 畫布、verify.sh 逐像素比對、patch.py 算出要補的像素、dump_points.py 列出互動點、normal_map.py 由 sprite 產生法線貼圖、occluder_poly.py 由貼圖算出遮光多邊形、convert_area_3d.py 把 2D 區域的互動點、近景與區域燈轉成 3D 區域場景（2.5D B1-3、B1-4；用法寫在檔案開頭）
assets/sprites/        主角 spritesheet 與 SpriteFrames；props/ 道具、characters/ 人物（Lv6，原始檔在 art/characters/*.pxo）
data/areas/parking_lot.json  停車場區域資料（Lv4-3 起為 v1.5 格式，文字直接寫在資料裡）
data/areas/street.json  街道區域資料（Lv4-4）
data/areas/clinic.json  診所區域資料（Lv4-5：錄音筆、診療椅的 variants）
data/areas/lab.json     設施走廊區域資料（Lv5-2：女科學家給筆記本、警衛 → BE2）
data/areas/ruins.json   廢墟與避難所區域資料（Lv5-3：同類、妻子 → BE3）
data/areas/home.json    舊家區域資料（Lv5-4：牆上的蠟筆字、女兒的房間、窗外的女兒〔有無筆記本用 variants 換文字〕）
data/areas/wall.json    牆前區域資料（Lv5-5：最後的動作，結局 A／B 依數值解鎖；沒有出口，用一定能選的「永遠遊走」離開）
scenes/areas/          可走動區域的場景：ParkingLot.tscn、Street.tscn、Clinic.tscn、Lab.tscn、Ruins.tscn、Home.tscn、Wall.tscn（之後的都由前一個區域另存後用 Toolkit 修改）
MCP實驗紀錄.md           每一級的 MCP 實驗觀察
```

Lv1 之後會新增（依 `docs/Lv製作流程.md`）：`scenes/areas/`、`scripts/area_data.gd`、`scripts/area.gd`、`scripts/player.gd`、`scripts/interact_point.gd`。

## 劇本格式（data/story.json）

```json
{
  "game_title": "失語者",
  "start_id": 1,
  "title_screen": { "bg": "scene_16.webp", "bgm": "bgm_15.ogg" },
  "scenes": [
	{
	  "id": 1,
	  "title": "停車場甦醒",
	  "text": "場景主文字（一段）",
	  "hint": "請選擇行動：",
	  "extra_hint": "可能是空字串",
	  "bg": "scene_01.webp",        // 位於 res://assets/bg/
	  "bgm": "bgm_01.ogg",          // 位於 res://assets/bgm/
	  "is_ending": false,
	  "choices": [
		{ "text": "按鈕文字", "response": "選了之後顯示的回應", "next_id": 2 }
	  ]
	}
  ]
}
```

- **v1.5（Lv5-1 起）**：`story.json` 只留過場與結局：6 搜捕隊、7 手術台、15 營火、18～20 結局 A／B／C、21～23 Bad End（`ending_type: bad`）；營火（15）之後進入牆前區域（`next_area: wall`），暫時的場景 17 已在 Lv5-5 移除。開始遊戲進入 `start_area`（停車場）。新欄位（`effects`、`require`、`locked_text`、`next_area`、`action`、`ending_label`）見 `docs/Lv製作流程.md` 的 Lv5。1.0 版備份在 `docs/story_v1.0.json`。
- 以下是 1.0 的說明（格式相容，舊欄位都還能用）：共 20 個場景、3 個結局（id 18、19、20，`is_ending: true`）。
- 結局場景只有一個選項「重新開始」，`next_id` 為 1。
- 有些選項的 `next_id` 等於自己的場景 id（例如「停留不動」），代表留在原場景：顯示回應後重新顯示同一場景的選項即可。
  回到同一場景時，**已選過的選項以半透明顯示**（仍可點），換到新場景時重置，讓玩家知道哪些選過了（場景 4 有 3 個留在原地的選項）。

## 要做的功能（階段 1 MVP）

1. **標題畫面**：背景 `title_screen.bg`、大標題 `game_title`、「點擊開始」。
   瀏覽器規定使用者互動後才能播放聲音，所以**第一次點擊之後才開始播放 BGM**。
2. **劇情畫面**：
   - 全螢幕背景（`TextureRect`，`expand_mode = ignore size`，`stretch_mode = keep aspect covered`）。
   - 畫面下方半透明對話框（約占畫面高度 35%），內含場景標題、主文字。
   - 主文字用 `RichTextLabel` 做**打字機效果**（`visible_ratio` 或 `visible_characters` 逐步增加）；打字中點擊 → 直接顯示全部。
   - 文字全部顯示後，顯示 `hint`（若 `extra_hint` 不是空字串也一併顯示，用較淡的顏色）以及選項按鈕（由 `choices` 動態產生，垂直排列）。
3. **選擇流程**：點選項 → 播放 click 音效 → 隱藏選項 → 在對話框顯示 `response`（同樣打字機）→ 顯示「▼ 點擊繼續」→ 點擊後前往 `next_id`。
4. **換場**：背景淡出淡入（約 0.4 秒，可用 `Tween` 或 `ColorRect` 黑幕）。
5. **BGM**：只有當新場景的 `bgm` 和目前播放的不同時才換曲，換曲時舊曲淡出、新曲淡入（約 0.8 秒）。相同曲目時不要重新開始播放。
6. **結局**：`is_ending` 為 true 時，對話框上方顯示「— 結局 —」標記；選「重新開始」回到**標題畫面**（不是直接回場景 1）。
7. 視窗大小改變時版面不跑掉（使用 anchors／Container，不寫死座標）。

## 建議架構

- `scripts/story_data.gd`：`class_name StoryData`，負責讀 JSON、提供 `get_scene(id) -> Dictionary`、`start_id`、`title_screen`。
- `scenes/Main.tscn`（根節點 `Control`，全螢幕）+ `scripts/main.gd`：管理狀態（TITLE / TYPING / CHOOSING / RESPONSE / ENDING）。
- 建議節點樹：

```
Main (Control, full rect)
├── Background (TextureRect)
├── Fade (ColorRect, 黑色, mouse_filter = ignore)
├── TitleLayer (Control)
│   ├── TitleLabel (Label)
│   └── StartLabel (Label)  「點擊開始」
├── StoryLayer (Control)
│   ├── Choices (VBoxContainer)
│   └── DialogPanel (PanelContainer, 半透明)
│       └── VBox (VBoxContainer)
│           ├── EndingTag (Label)  「— 結局 —」
│           ├── SceneTitle (Label)
│           ├── Body (RichTextLabel)
│           ├── Hint (RichTextLabel)  ← extra_hint 要用較淡顏色，所以用 RichTextLabel + BBCode
│           └── Continue (Label)  「▼ 點擊繼續」
├── BgmA (AudioStreamPlayer)
├── BgmB (AudioStreamPlayer)   ← 兩個播放器交替做 crossfade
├── Sfx (AudioStreamPlayer)
├── TypeSfx (AudioStreamPlayer)  ← 打字音效（max_polyphony 4）
└── RotateHint (ColorRect)      ← 直式畫面時顯示「請將裝置橫向持握」（Lv1-0）
```

- `project.godot` 的 `run/main_scene` 要設成 `res://scenes/Main.tscn`。

## 工作方式（MCP 實驗規則）

### MCP：godot-mcp-toolkit（編輯器外掛）

- 使用 **Godot MCP Toolkit**（`addons/godot_mcp_toolkit/` + `.mcp.json` 的 `godot-mcp-toolkit`）。它透過 WebSocket 連到**正在開著的 Godot 編輯器**，所以使用前編輯器必須開啟此專案，外掛為啟用狀態。
- 常駐工具不夠時，用 `discover_tools` 啟用群組（一次只開需要的，約 5 個以內）。本專案常用：`theme`（StyleBox／字型／顏色覆寫）、`runtime_advanced`、`editor_advanced`、`lsp_code_analysis`、`audio`、`cleanup`。
- 原本的 Coding-Solo/godot-mcp（`create_scene`、`add_node`、`run_project`、`get_debug_output`）已由 Toolkit 取代，不要混用：兩者同時改 `.tscn` 會互相覆蓋。

### 建立場景與節點

- **優先用 MCP 工具**：`scene_create`、`scene_open`、`scene_create_node`、`node_set_property`、`node_set_script`、`control_set_layout`、`scene_delete_node`、`node_manage`、`editor_save_scene`；主題樣式用 `theme` 群組的 `theme_edit`；專案設定用 `project_set_setting`。
- MCP 做不到的，再直接編輯 `.tscn` 或在腳本 `_ready()` 中設定，並說明原因。
- 透過 MCP 修改場景後要 `editor_save_scene`。若直接改了 `.tscn` 檔案，要提醒使用者在編輯器重新載入，避免編輯器存檔時覆蓋。
- 執行時動態產生的節點（例如選項按鈕）寫在腳本裡。
- **Control 的版面屬性不要在 `scene_create_node` 時一起設定**：建立時帶入的 `position`／`size`，甚至 `offset_*`，位置都可能被重設成 (0, 0)（Lv1-4、Lv1-5 各發生一次）。做法：先建立節點，**再用 `node_set_property` 設定 `offset_left/top/right/bottom`**，存檔後檢查 `.tscn`。
- **`spriteframes_edit` 的 `add_animation` 會忽略帶入的 `frames`**（A5-2）：建好動畫後要再用 `add_frame` 加畫格，存檔後檢查 `.tres`。**`node_manage` 的 `duplicate` 不會把子節點存進 `.tscn`**（Lv4-5）：複製出來的子節點（Shape、Marker）只存在編輯器裡，存檔後就不見了。要複製互動點時改用 `scene_create_node` 重新建立子節點，存檔後檢查 `.tscn`。
- 新的可走動區域：用 `editor_save_scene`（帶 `file_path`）把現有區域**另存**，再用 Toolkit 修改（Lv4-4、Lv4-5 的做法）。**另存後編輯器仍在編輯原檔**（Lv5-5 因此覆蓋過 `Home.tscn`）：另存後要立刻 `scene_open` 新檔，並用 `scene_get_tree` 確認 `source` 是新檔、內容正確，才開始修改與存檔；新檔的分頁若停在舊內容，`editor_refresh` 也不會重新載入，不要在那個分頁存檔。**A1.5 起區域可以上下左右走**（縱深帶 `area.gd` 的 `walk_top`／`walk_bottom`，預設 650～735）：區域根節點、`Points`、`Near` 都開 `y_sort_enabled`，依原點的 y 決定前後，所以互動點、人物、近景物件的**原點要放在腳底／物件底部**（近景 Sprite 用 `offset` 往上移）；`FrontLayer` 設 `z_index = 1` 永遠在最前面。主角的互動判定只有腳底（24×12，`player.gd` 設定）：一般互動點的範圍放在原點往下 0～50（`Shape` 位置 y 25、高 50，寬度和物件差不多），靠近就觸發的人物事件涵蓋整個縱深帶（y 50、高 100），避免從外側繞過劇情。**放在路中間、不能穿過的大物件**（A1-2 街道的燒毀車體）：互動點原點放在物件底部（例如 y 695），加子節點 `Block`（StaticBody2D）＋`Shape`（寬比畫面上的物件窄一點、高約 10，貼在底部），觸發範圍改成涵蓋整個縱深帶，從前面或後面都能調查。不能互動的障礙物（A1-3 診所的擔架床）放在 `Near` 底下：`StaticBody2D`（原點在底部）＋`Sprite`＋`Shape`。
- **新的像素圖匯入後要改成無損**：新 PNG 預設 `compress/mode=1`（有損，會讓像素顏色跑掉），把 `.import` 改成 `compress/mode=0` 再 `editor_refresh`（Lv6-3）。人物用 Sprite2D、名稱 `Figure`（`hide_on_done` 才會隱藏）、`texture_filter = 1`、放大 2 倍、`position.y = -48`（腳踩在地面）。像素圖只用**整數倍**放大（A1.5-0 確認：0.92 這類縮放會讓像素粗細不均，所以縱深不縮放）。Pixelorama 的 `import_image` 偶爾會**掉幾段像素**（Lv6-5），匯出後一律把設計圖和匯出圖都轉成 `magick … txt:-` 逐像素比對，才看得到差在哪幾格（`magick compare -metric AE` 只能看是不是 0，數字不是像素數），有差異就用 `draw_pixels` 補回再存檔、匯出。`import_image` 會把**半透明像素變成不透明**（Lv6-5 舊家的窗戶玻璃），半透明的部分匯入後要用 `draw_rect`／`draw_pixels` 以 `#RRGGBBAA` 重畫。
- **腳本的 `@export` 要指向其他節點時用 `NodePath`**（A3-1）：節點型別的 export（例如 `@export var follow: AnimatedSprite2D`）用 Toolkit 的 `node_set_property` 設定時只會寫入路徑、不會標記成節點參照，載入後是 null；改成 `@export var follow: NodePath`，在 `_ready()` 用 `get_node_or_null` 取得。**數字陣列的 export 不要用 `PackedFloat32Array`**（A3-6）：Toolkit 只能寫成一般陣列，之後重新存檔可能被丟掉；改用 `PackedVector2Array`／`PackedVector3Array`（有型別標記）。**改了腳本的 `@export` 之後編輯器可能一直快取舊的屬性清單**（`editor_refresh`、`script_write`、重新掛腳本都無效），這時換一個新檔名最快。**替換已匯入的圖（例如加寬 spritesheet）後要整個專案 `editor_refresh`（不帶 file_paths），並在遊戲裡讀貼圖大小確認**（A3-8：只刷新該檔案時沒有重新匯入，新格子在遊戲裡是透明的；自動測試在副本重新匯入，抓不到）。動畫用 `AnimatedSprite2D`＋`spriteframes_from_spritesheet`；換掉原本的 Sprite2D 時，子節點（遮光體）用 `node_manage` 的 `reparent` 搬過去。
- 遠景背景（FarLayer/Backdrop）用 `stretch_mode = 6`（等比例蓋滿）、寬約 1500，不要重複拼接（會有接縫）。
- 選項的鍵盤操作要用 `input_simulate` 的 `key` 類型送真正的按鍵（下方向鍵 `keycode 4194322`、Enter `4194309`）；`action` 類型不會移動焦點。用 `execute_code` 瞬移主角後，要等一下物理更新，互動點才會偵測到。
- 模擬移動用 `input_simulate` 的 `action` 類型（會呼叫 `Input.action_press`）。`key` 類型若要觸發動作，必須帶 `physical_keycode`（本專案的按鍵是用實體按鍵綁定）。
- 測試期間如果使用者也在操作遊戲視窗，座標與狀態會被干擾；量測前先確認狀態，結果異常時先懷疑外部輸入。

### 腳本

- **GDScript 檔案**用一般檔案編輯寫入 `scripts/`（也可用 `script_write`／`script_edit`）。
- 寫完用 `script_check` 檢查單一檔案，或 `lsp_project_diagnostics` 檢查整個專案。編譯錯誤**不會**出現在遊戲 log 裡。
- 新增 `class_name` 後若沒被認得，先確認子資料夾沒有多餘的 `project.godot`，再用 `editor_refresh` 或 `Godot --headless --path . --import` 重新掃描。

### 每完成一個步驟

1. `game_start`（`scene_path: "main"`）執行遊戲。若回傳 `runtime_ready: false`，或之後的 runtime 工具回報 `GAME_NOT_RUNNING`（但 log 顯示遊戲有在跑），先呼叫 `game_start`（`if_running: "return"`, `runtime_poll: true`）再重試；有時要**輪詢兩次**才會連上。實測：`game_start` 之後**等約 3～5 秒**（登錄檔更新後）再呼叫 runtime 工具最穩定。
2. `runtime_screenshot` 截圖確認畫面（**一律用 `image_response_mode: "disk"`** 再讀取存下的 PNG；inline 模式圖片超過約 1MB 會失敗，且曾回傳舊畫面）。**遊戲嵌在編輯器的 Game 分頁裡，編輯器不在前景時畫面只在收到指令時重畫**（Lv6-2）：截圖常是「上一個指令剛執行完」的畫面。做法：改完狀態後等一下，先送一個無作用的 `execute_code`（例如讀一個值），等 0.5 秒再截圖，並核對截圖裡主角位置等是否符合；需要互動時用 `input_simulate`（`click` 給座標，或 `click_node` 給節點路徑），再截圖確認結果。座標以 1152×768 為準。
3. `debugger_get_log` 讀錯誤與警告（遊戲剛啟動時 log 可能還沒印完，必要時再讀一次）。
4. 修好之後 `game_stop`。

- **自動測試放在專案的 `tests/`**（2026-10-06 作者決定；暫存區會被系統清空，Lv4 的測試因此遺失過一次）：`tests/test_*.gd`（`extends SceneTree`，載入真正的 `Main.tscn` 跑遊玩流程）。Web 匯出已排除 `tests/*`。
  **執行一律用 `zsh tests/run_tests.sh`**（或 `zsh tests/run_tests.sh test_lv4` 只跑一個）：它會自動建立拿掉外掛的副本（`$TMPDIR/shiyuzhe_test_copy`），在副本上跑劇本檢查與所有測試（B1 起 2D、3D 區域各跑一次）。新增測試時繼承 `tests/play_base.gd`（`extends "res://tests/play_base.gd"`，覆寫 `run_tests()`），照 `tests/test_lv5.gd` 的寫法。
  `run_tests.sh` 會把「輸出有 SCRIPT ERROR 或沒印出『共 N 項檢查』」算成失敗（A4-2：測試腳本 Parse Error 時 Godot 結束碼仍是 0，以前會誤判成全部通過）。
  **不要直接對本專案跑 headless**：外掛的 `MCPRuntimeServer` autoload 在 headless 也會啟動，會覆蓋 godot-mcp-toolkit 的 runtime 登錄（`~/Library/Application Support/godot-mcp-toolkit/`），導致正在執行的遊戲之後回報 `GAME_NOT_RUNNING`。
  做法：把專案 rsync 到暫存區（排除 `addons/`、`.mcp.json`、`build/`），刪掉副本 `project.godot` 裡的 `MCPRuntimeServer` autoload 與外掛啟用設定，再對副本執行 `Godot --headless --path <副本> --script <測試腳本>`。
- 劇本檢查也會檢查 `data/areas/*.json`：引用是否存在、`exit_to`、互動點類型、是否有出口、區域 BGM，以及區域場景的 `point_id` 是否與 JSON 一一對應（場景尚未建立時只顯示 ⚠ 提醒）。
- 修改劇本或素材後，執行劇本檢查（同樣會啟動 runtime 外掛，請在**沒有用 MCP 執行遊戲時**跑，或照上面的方式對副本執行）：
  `/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --script res://tools/validate_story.gd`
- 每個步驟結束時，簡短回報：做了什麼、用了哪些 MCP 工具、哪些改用其他方式（與原因）、截圖與 log 是否正常。

### 網頁匯出注意

- **遊戲需要的資料不能少**：Web 設定的 `include_filter` 是 `data/*.json, data/areas/*.json`。之後新增資料資料夾（例如 `data/xxx/`）時要一併加入，匯出後檢查 `.pck` 裡確實有這些檔案。
- Godot 4.3+ 預設的腳本匯出模式（Binary tokens）**不會**排除外掛腳本，匯出前要在 Web 設定的 `exclude_filter` 加上 `addons/*`（外掛會自動移除 `.mcp.json` 與 runtime autoload）。

## 完成標準（Definition of Done）

- [x] 從標題畫面點擊開始，可以一路玩到三個結局中的任一個。
- [x] 每個選項都會先顯示 `response` 再前進。
- [x] 「停留不動」類選項會留在原場景並能再次選擇。
- [x] 相同 BGM 不會重播；不同 BGM 有淡入淡出。
- [x] 結局選「重新開始」回到標題畫面。
- [x] `debugger_get_log` 與 `lsp_project_diagnostics` 沒有錯誤。
- [x] 能用 Web 匯出設定輸出到 `build/web/`，在瀏覽器中可玩，且有聲音。

> 2026-10-02 階段 1 全部完成（使用者已在瀏覽器實測）。實驗過程與觀察見 `MCP實驗紀錄.md`。

## 劇本之後可能再調整（附註）

> 下一版 **1.5** 的劇本調整規劃（分歧、快速結局、隱藏數值）見 `docs/v1.5_劇本調整規劃.md`，2026-10-05 起改寫成可移動版的「區域 × 事件」格式（見 `docs/Lv製作流程.md` 的「劇本 v1.5」一節）。實作前仍以本檔的規則為準。
>
> Lv1 的區域資料以 `from` **引用** `story.json` 的文字；**v1.5（Lv4 起）改成把文字直接寫在區域資料裡**（`title`／`text`，格式見 `docs/Lv製作流程.md` 的 Lv4），`from` 仍然支援。修改 `story.json` 時，若刪除或調換了被引用的場景或選項順序，用 `from` 的區域文字也會跟著變，請一併檢查（劇本檢查工具會檢查引用是否有效）。

劇本（`data/story.json`）之後會依 v1.5 定稿修改，例如處理下面的重複劇情。程式是完全依資料運作的，調整劇本時請注意：

- **程式不需要跟著改**的情況：修改文字、標題、hint、選項文字／response、增減場景或選項、改 `next_id`、改背景／BGM 檔名、改 `title_screen`、改 `start_id`。
- 結局判斷只看 `is_ending: true`；結局的選項不論 `next_id` 是多少，都會回到**標題畫面**。
- `next_id` 等於自己 id 的選項＝留在原地（會變暗）；選項數量不限，但超過約 6 個時對話框上方空間會不夠，需要調整 `Choices` 版面。
- 主文字很長時（超過約 3～4 行），對話框（畫面高度 35%）會不夠放，Body 會出現捲動；需要時再調整版面或字級。
- 新增素材放進 `assets/bg/`、`assets/bgm/`；新的 ogg BGM 會自動循環。**新增音效時要把該檔的匯入設定改成不循環**（專案預設 ogg 都循環，click.ogg 已處理）。
- 改完一定要跑劇本檢查（`tools/validate_story.gd`，注意上面「headless 會覆蓋 runtime 登錄」的說明），再重新匯出 Web 版。
- Claude 可以起草，但**未經作者定稿不可以寫入**；寫入後負責檢查格式、跑驗證與測試。

## 已知劇本問題（階段 1 不處理，僅供參考）

- 場景 1~16 大部分選項都通往同一個下一場景，真正的分歧只在場景 17。
- 場景 5/11、7/12、8/13、10/14 劇情重複。
- 用詞已統一（2026-10-02 作者決定）：主角名稱為「楊尚瑜」；保有意識的感染者稱為「**靜語者**」（不是噬語者），場景 15 已修正。
- 原專案缺 `bgm_13`，已用原專案中的〈Escape Through the Chaos〉代替。
