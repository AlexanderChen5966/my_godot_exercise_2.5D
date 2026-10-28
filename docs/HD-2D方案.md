# 失語者 HD-2D 方案：3D 場景＋像素角色（桌面版優先）

| 項目 | 內容 |
|---|---|
| 建立日期 | 2026-10-08 |
| 狀態 | **尚未開始**。作者決定先完成 A＋（`docs/A+方案.md`），之後再決定要不要做 HD-2D |
| 平台 | **桌面版優先**（作者 2026-10-08 決定）：Mac，之後可加 Windows。網頁版的可能做法見第 7 節 |
| 目的 | 練習專案：可以使用新的 MCP（Blender MCP），練習 Godot 3D |

---

## 1. HD-2D 是什麼

參考《歧路旅人》：**低多邊形的 3D 場景＋像素角色（2D 圖片立在 3D 空間裡）＋強烈的後處理**。讓它看起來像「微縮模型」的關鍵效果：

| 效果 | Godot 的做法 |
|---|---|
| 景深模糊（移軸、微縮感） | `CameraAttributesPractical` 的遠近模糊 |
| 光暈 | `WorldEnvironment` 的 Glow |
| 體積霧、光束 | `WorldEnvironment` 的 Volumetric Fog＋燈光的 volumetric 強度 |
| 柔和的陰影與環境光遮蔽 | 方向光陰影、SSAO |
| 像素感 | 角色是像素圖、3D 物件用像素貼圖，全部 Nearest 濾鏡 |
| 鏡頭 | 俯角約 30～45 度、窄視角（FOV 約 20～35），讓畫面接近等角視圖 |

### 為什麼桌面版優先

Godot 的網頁版只能用 Compatibility 渲染器，**不支援景深模糊、體積霧、SSAO**（只有光暈和烘焙光照可以用）。這些正是 HD-2D 的招牌，所以先用桌面版的 **Forward+** 做出完整效果，網頁版之後再評估（第 7 節）。

---

## 2. 專案策略：另開一個專案

- **複製一份專案**（例如 `失語者_HD2D`），渲染器改成 Forward+。**原本的網頁版（A＋）不動**。
- 可以直接沿用的（Lv4～Lv6 資料驅動設計的成果）：
  - `data/story.json`、`data/areas/*.json`（劇本、區域、條件、結局）
  - `GameState`（旗標、物品、數值、檢查點）
  - `main.gd` 的 UI 部分（對話框、打字機、選項、標題、結局）：UI 在 CanvasLayer 上，疊在 3D 畫面上方照樣能用
  - 劇本檢查工具、大部分遊玩測試
  - 全部的像素角色與物件圖（A3 的動畫也能用）
- 要改寫的：區域系統（2D → 3D）。

| 2D（現在） | 3D（HD-2D） |
|---|---|
| `Node2D` 區域根節點 | `Node3D` |
| `CharacterBody2D` 主角 | `CharacterBody3D`，主要沿 X 軸走 |
| `AnimatedSprite2D` | `AnimatedSprite3D`（billboard、Nearest、`pixel_size` 調整大小、**開啟陰影投射**） |
| `Area2D` 互動點 | `Area3D` |
| `Camera2D` 跟隨 | `Camera3D` 跟隨＋俯角，邊界限制 |
| `Parallax2D` 分層 | 真正的 3D 深度（物件放在不同的 Z） |
| `PointLight2D`、`CanvasModulate` | `OmniLight3D`／`SpotLight3D`、`WorldEnvironment` 的環境光 |
| 區域資料的 `x` 座標 | 換算成 3D 的 X（必要時新增 `z`） |

---

## 3. 要準備的東西

| 項目 | 內容 | 誰做 |
|---|---|---|
| Godot | 同一個版本，新專案用 Forward+；Mac 的 Metal 支援 | 作者 |
| **Blender**（免費） | 3D 建模 | 作者安裝 |
| **Blender MCP**（新 MCP） | `ahujasid/blender-mcp`：MCP 伺服器＋Blender 外掛，讓 Claude 在 Blender 建模、上材質、匯出 | 作者安裝，Claude 協助設定 |
| 3D 素材包（選做） | Kenney 等 CC0 的低多邊形套件，H1 先拼場景，不用一開始就建模 | 作者下載 |
| 像素貼圖 | Pixelorama 畫 32×32 或 64×64 的牆、地板、金屬、木頭 | Claude（Pixelorama MCP） |
| 角色方向 | 第一版**主要左右走、只能小幅前後移動**，沿用現有 20 格；要自由移動時再補畫面向鏡頭／背對鏡頭的畫格（主角約再 20 格） | H1-0 決定 |
| 3D 基本概念 | 方向光、點光源、聚光燈、WorldEnvironment、鏡頭參數 | Claude 邊做邊解釋 |

> Godot MCP Toolkit 有 3D 的工具群組（外掛裡有 `3d_commands`、`spatial_commands`、`navigation_commands`），建 3D 場景、放燈光、調環境都能透過 MCP 完成。

### 三個 MCP 的分工

| MCP | 負責 |
|---|---|
| Blender MCP | 建模（燒毀的車、柱子、櫃子、牆面模組）、UV、匯出 glTF（`.glb`） |
| Pixelorama MCP | 像素貼圖、角色動畫 |
| godot-mcp-toolkit | 匯入模型、排場景、燈光、環境、後處理、執行與截圖驗證 |

---

## 4. 等級

| 級 | 內容 | 練習重點 | 新 MCP |
|---|---|---|---|
| **H0** | 複製專案、改 Forward+、確認視覺小說部分與 UI 正常；決定鏡頭角度與角色移動範圍 | 專案遷移 | — |
| **H1** | **只做停車場**：灰色方塊或素材包拼出場景、`AnimatedSprite3D` 主角、傾斜的 Camera3D、燈管與紅燈改成 3D 燈光、互動點改成 `Area3D`；接回原本的流程 | Toolkit 的 3D 工具；2D 區域系統改成 3D | — |
| **H2** | HD-2D 的質感：景深、光暈、體積霧、SSAO、色調；A／B 截圖給作者選 | AI 調整「微縮模型感」這種主觀目標 | — |
| **H3** | 加入 **Blender MCP**：建 2～3 個停車場的模型（柱子、廢車、燈管），配 Pixelorama 畫的像素貼圖 | 第三個 MCP；三個 MCP 的配合 | **Blender MCP** |
| **H4** | 依 H1～H3 的結果決定：把其餘 6 個區域轉成 3D，或停在停車場當作實驗成果 | 量產 | — |
| H5（選做） | 網頁版（第 7 節的做法擇一） | — | 依做法 |

### H1 驗證方式（沿用 Lv1 的思路）

- `input_simulate` 走路、`runtime_get_node_state` 讀主角 3D 座標，確認移動、邊界、鏡頭跟隨。
- 互動點、婦人事件、出口與 2D 版結果相同（可以直接跑既有遊玩測試的停車場部分）。
- 截圖確認像素角色清晰、有影子、不會被 3D 物件錯誤遮擋。

### 完成標準（H1～H3 共通）

- [ ] 停車場的 3D 版可以從標題玩到出口，接回後續流程並玩到結局
- [ ] 劇本檢查與既有遊玩測試照常通過
- [ ] 作者確認 HD-2D 的質感（H2）、模型與貼圖（H3）
- [ ] `MCP實驗紀錄.md` 新增 H0～H3 各一節，記錄三個 MCP 的配合與 Blender MCP 的穩定度

---

## 5. 主要風險

| 風險 | 對策 |
|---|---|
| 3D 美術工作量遠大於 2D | H1 用灰色方塊與素材包；H3 只做 2～3 個模型；H4 再決定要不要量產 |
| 像素角色在 3D 光照下的樣子（太亮、沒影子、邊緣閃爍） | H1 就確認 `AnimatedSprite3D` 的 shaded、alpha cut、陰影設定 |
| 景深太強讓文字或角色看不清楚 | H2 用 A／B 比較，UI 在 CanvasLayer 不受影響 |
| Blender MCP 不穩定 | 先在另一個資料夾試；失敗時改回素材包 |
| 效能（Forward+ 效果全開） | M2 Pro 應該足夠；H2 回報 FPS |

---

## 6. 開始前要決定的事（H0-0）

1. 鏡頭俯角與視角（Claude 會做 2～3 種截圖給作者選）。
2. 角色移動：只左右走（沿用素材），或自由前後移動（補畫畫格）。
3. 3D 場景：先用素材包，或直接用 Blender MCP 建模。
4. 新專案的資料夾名稱與位置。
5. 天空與陽光的做法（作者 2026-10-28：**HD-2D 可以做得更精緻，不必照 2.5D 的做法，有更好的就調整**）。候選與比較見 `docs/2.5D_天空與陽光.md` 的「改成 HD-2D 時」。

---

## 7. 網頁版 HD-2D 的可能做法（之後再評估）

| 做法 | 景深／光暈等效果 | MCP | 代價 |
|---|---|---|---|
| **A. Godot Compatibility**（同一個專案匯出網頁版） | 光暈可以；景深要**自己寫 shader 模擬**（用深度做模糊）；沒有體積霧與 SSAO | 沿用 godot-mcp-toolkit | 最小。質感會比桌面版差 |
| **B. PlayCanvas**（網頁原生引擎，有網頁編輯器） | 引擎提供後處理（景深、光暈等，採用前要再確認版本與效能） | **官方的 PlayCanvas Editor MCP**：建實體、腳本、素材、燈光貼圖，**也能啟動遊戲、截圖、讀 log、送輸入**，和 godot-mcp-toolkit 的使用感最接近 | 遊戲邏輯要用 JavaScript／TypeScript 重寫；免費方案的專案是公開的 |
| **C. Three.js**（程式庫，沒有編輯器） | 搭配後處理程式庫可以做景深、光暈、SSAO | 引擎專用的 MCP 都還很小、很新；實務上是 Claude 直接寫程式，再用瀏覽器自動化（Chrome／Playwright）截圖驗證 | 一切都要寫程式，場景沒有視覺化編輯器 |
| **D. Unity（WebGL）** | URP 的後處理（含景深）可以在 WebGL 使用 | 有 Unity 官方與社群的 MCP | 改用 C#；網頁版檔案大、載入慢 |
| E. Babylon.js | 內建景深、光暈、SSAO、光束後處理 | 沒有找到成熟的 MCP | 和 Three.js 類似，要寫程式 |

**共通**：換引擎時，劇本與區域 JSON、像素圖、Blender 匯出的 `.glb` 模型、Suno／ElevenLabs 的聲音**都能沿用**；要重寫的是遊戲邏輯、檢查工具與測試。

**建議**：先做桌面版（H0～H3）。真的需要網頁版時，先試 A（成本最低）；如果想練新的 MCP，B（PlayCanvas）最值得試。

參考：Godot 4.5 渲染器功能比較 <https://docs.godotengine.org/en/4.5/tutorials/rendering/renderers.html>、PlayCanvas Editor MCP <https://github.com/playcanvas/editor-mcp-server>、Blender MCP <https://github.com/ahujasid/blender-mcp>
