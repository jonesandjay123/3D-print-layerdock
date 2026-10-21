# layerdock

Jones 的 3D 列印產品 repo。每個產品是 `projects/` 底下一個獨立的子專案，各自有參數化 CAD、STL、Bambu Studio 專案檔、文件與圖片；repo 根目錄的 `tools/` 放所有產品共用的檢查與切片工具。

印表機：Bambu Lab A1 mini（180 × 180 × 180 mm，0.4 mm 噴頭），材料以 PLA 為主。

| 產品 | 用途 | 狀態 |
| --- | --- | --- |
| [LayerDock Open Frame](projects/open-frame/) | Base + Layer × N + Top 的鏤空設備架：Mac mini 放頂部，Xbox Series S 直立放在裡面、從前方抽出 | v0.1.1，已實際列印並組裝成功（2026-10-20） |
| [LayerDock Stackable Bins](projects/stackable-bins/) | 外觀極簡、圓角、可堆疊的隱藏式收納箱 Bin × N + Lid × 1，取代桌上墊高衛生紙盒的空紙箱 | v0.1，設計完成、切片驗證，待實際列印 |

## 目錄

```
projects/<product>/
  README.md        產品說明、設計決定、列印說明
  scad/            OpenSCAD 參數化模型（參數區是尺寸的唯一來源）
  stl/             輸出的 STL（照檔案方向直接印）
  print/           已切好的 Bambu Studio 3MF 專案檔（A1 mini、PLA），直接開啟按 Print
  docs/            圖片、切片報告、設計記錄
  tools/build.sh   用 Blender 重建 STL + 預覽圖，並呼叫共用工具檢查 / 切片
tools/
  check_stl.py     STL 水密、法線、外形尺寸檢查（純 Python）
  slice.py         Bambu Studio CLI 切片乾跑，輸出 docs/print-report.md
```

重建某個產品：

```bash
projects/open-frame/tools/build.sh --slice
projects/stackable-bins/tools/build.sh --slice
```

`build.sh` 會在產品目錄裡執行，`--slice` 需要本機裝有 Bambu Studio；兩個共用工具也可以單獨跑：`tools/check_stl.py --project projects/<product>`、`tools/slice.py --project projects/<product> [--only part]`。
