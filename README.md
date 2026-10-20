# layerdock

A modular, 3D-printable device stand built with stackable layers, an open frame, and interchangeable top and base plates.

模組化 3D 列印設備架：**Base + Layer × N + Top**，用獨立列印的方形插銷接合。
第一個用途：Mac mini（M4）放頂部，Xbox Series S 直立放在架子裡，**從前方直接抽出**，抽走後 Mac mini 依然由架子承重。

![組裝圖](docs/images/assembly.png)

綠色線框是 Xbox Series S（直立），紅色線框是 Mac mini。

## 設計重點

| 項目 | 決定 | 原因 |
| --- | --- | --- |
| 印表機 | Bambu Lab A1 mini，180 × 180 mm | 每個零件外形 **170 × 175 mm**，全部單件列印、不需支撐 |
| Layer | 四角柱 + 左右側樑 + 後樑，**前方全開、中間完全鏤空** | Xbox 空間內沒有任何橫板；每層一模一樣，印幾個疊幾層 |
| 接合 | Base / Layer / Top 共用同一種 **8.4 mm 方孔**，配 **8 × 8 × 30 mm 方插銷** | 插銷壞了只要重印插銷；重量由柱子端面直接傳遞，插銷只負責對位 |
| Xbox 方向 | 直立，**電源鍵那面（63.5 mm 窄面）朝前**，圓形風扇面朝側邊 | 見下方說明 |
| 層高 | 60 mm × 5 層 = 300 mm；Xbox 上方淨高 312 mm | Xbox 275 mm + 10 mm 餘裕；要更高就多疊一層 |
| 材料 | PETG 優先 | 韌性好，插銷不易斷 |

### 為什麼 Xbox 要轉 90°

Xbox Series S 直立時是 63.5（寬）× 151（深）× 275（高）mm。如果像現在一樣把 151 mm 的風扇面朝前，架子要在 180 mm 的列印平台內同時塞下 151 mm 的 Xbox、兩側伸手的空隙和兩根柱子，數學上不夠。
把 Xbox 轉 90°，讓 63.5 mm 的窄面朝前（也就是微軟官方直立擺法，電源鍵朝前），柱子之間 134 mm 的開口兩側各留 **35 mm** 給手指，抽取非常輕鬆；Xbox 的接線面朝後，後方有 **24 mm** 的插頭空間。Xbox 前緣會比架子突出 6 mm，好抓。

### 各零件

![零件圖（列印方向）](docs/images/parts.png)

| 零件 | 檔案 | 數量 | 列印方向 | 說明 |
| --- | --- | --- | --- | --- |
| Base | `stl/base.stl` | 1 | 如檔案（平放） | 5 mm 底板 + 四角 12 mm 高凸台（方孔朝上）。底板上有兩條 3 mm 導引肋把 Xbox 扶正，後方一條止擋肋讓 Xbox 每次都停在插頭空間之前 |
| Layer | `stl/layer.stl` | 5 | 如檔案（橫樑朝下） | 18 × 18 mm 四角柱 60 mm 高，上下都有方孔；左右 8 mm 側樑、後方 6 mm 後樑，前方全開 |
| Top | `stl/top.stl` | 1 | 如檔案（平放） | 4 mm 托盤 + 3 mm 圍邊 + 四個 Mac mini 定位擋塊 + 通風槽（M4 Mac mini 從底部進氣）。四角凸台朝上，方孔從底部進入 |
| Pin | `stl/pin.stl` | 24 | 如檔案（平躺） | 8 × 8 × 30 mm，兩端 1 mm 倒角。每個接面 4 根：(5 層 + 1) × 4 = 24 |
| 公差試件 | `stl/test-coupon.stl` | 1 | 如檔案 | 三個方孔，間隙 0.2 / 0.4 / 0.6 mm，附一根插銷。**先印這個** |

![爆炸圖](docs/images/exploded.png)

## 列印建議（A1 mini，PETG）

- 層高 0.2 mm，4 道外牆，3 層頂底，填充 25% 以上（柱子要承重）。
- 不需要支撐。170 × 175 mm 的件不要開 brim（會超出平台），或在 Bambu Studio 把 brim 設成 2 mm 以內。
- 第一層打開「Elephant foot compensation」（象腳補償），不然插銷平躺那面會變寬。
- 先印 `test-coupon.stl`：插銷能塞進哪個孔、用手拔得出來但不晃，就把那個間隙填進 `socket_clear` 重新輸出。預設 0.4 mm。

## 組裝

1. Base 平放，四個方孔各插一根 Pin（插到底，露出 15 mm）。
2. 把第一個 Layer 的方孔對準 Pin 壓下去，橫樑那面朝上。
3. 在 Layer 上方四個方孔再插 Pin，再疊下一個 Layer，重複到 5 層。
4. Top 的四個方孔從底部對準 Pin 壓下去，凸台朝上。
5. Xbox 直立、電源鍵朝前，從前方沿著 Base 的導引肋推進去，推到碰到後方止擋肋為止。線從後面接。
6. Mac mini 放進 Top 中央的四個擋塊之間。

要拿 Xbox：直接從前面抓住兩側往前抽，架子和 Mac mini 不動。

## 改參數、重新輸出

所有尺寸都在 [`scad/layerdock.scad`](scad/layerdock.scad) 最上面的參數區（Xbox / Mac mini 尺寸、層高、層數、柱子大小、插銷公差……）。

**方法 A：Blender（這台 Mac 已安裝，不需要 OpenSCAD）**

```bash
tools/build.sh
```

`tools/build_stl.py` 會讀 `.scad` 檔的參數區，用 Blender 重建同樣的幾何、輸出 `stl/` 和 `docs/images/`。

**方法 B：OpenSCAD**

```bash
openscad -D 'part="layer"' -D print_orientation=true -o stl/layer.stl scad/layerdock.scad
```

`part` 可以是 `assembly`、`base`、`layer`、`top`、`pin`、`test`。OpenSCAD 的 Customizer 面板也能直接調參數。
程式會在 console 印出內部淨高、插頭空間等檢查結果，不夠會印 WARNING。

## 待確認

- Mac mini 型號：照片量約 12.7 cm，應該是 M4（127 × 127 mm）。若是舊款 197 mm，`mac_w` / `mac_d` 要改，而且 Top 要重新考慮。
- 插銷公差：以 0.4 mm 起試，依試件結果調整。
- 原始需求與討論記錄在 [`docs/context.md`](docs/context.md)，照片在 `docs/reference/`。

## 參考

- [Pillar Modular Shelf System](https://www.printables.com/model/1834191)（Printables）
- [Shelf Riser — Customizable & Modular](https://makerworld.com/en/models/2259682)（MakerWorld）
