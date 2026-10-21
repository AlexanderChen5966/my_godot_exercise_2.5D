# 像素素材的設計檔（A＋）

暫存區會被系統清空，所以 A1～A3 的設計腳本、設計圖與給作者看的比較圖都放在這裡（`art/` 有 `.gdignore`，不會被匯入或匯出）。

| 資料夾 | 內容 |
|---|---|
| `a1_home/`、`a1_wall/` | A1 舊家、牆前的設計腳本（`*_a1.py`）、每個素材的設計圖（`.txt`，ImageMagick 像素清單，逐像素比對用）、修改前後的預覽 |
| `a2/` | 遮光多邊形產生腳本 `gen_occ.py`、A2 各項 A／B 比較圖（粒子、霧與光束、鏡頭、法線貼圖） |
| `b0/` | 2.5D B0 的比較圖（縱深兩種做法、人物受光、景深與霧、網頁版）；主角正面／背面設計腳本 `player_fb.py`（輸出到 `player_fb/`：每一格的 `.txt`、PNG、GIF 預覽、Pixelorama 逐格匯出 `export/` 與 spritesheet `sheet/`） |
| `b1/` | 2.5D B1 的截圖（3D 主角與互動點、接上 Main、停車場、景深比較、其餘 6 區、網頁版） |
| `b2/` | 2.5D B2 的停車場樣板：鏡頭比較 `b2-1_鏡頭比較.png`、配置圖與配色 `b2-1_配置圖.png`（由 `layout.py` 產生：`python3 art/design/b2/layout.py 輸出.png`） |
| `a3/` | 火焰 `fire.py`、燈管 `lamp.py`、婦人 `woman.py` 的設計腳本與每一格的設計圖、GIF 動態預覽、遊戲中的截圖 |

- 設計腳本的用法：`python3 腳本.py 輸出資料夾`，會輸出每一格的 `.txt`；`magick x.txt PNG32:x.png` 轉成 PNG 匯入 Pixelorama。
- Pixelorama 的原始檔（`.pxo`）在 `art/props/`、`art/layers/`、`art/characters/`；共用工具在 `art/tools/`。
- 驗證：`zsh art/tools/verify.sh 設計.txt 匯出.png`（0 格不同才算完成）。
