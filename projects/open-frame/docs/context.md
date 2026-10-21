我的升降桌下面有放一臺我 Jarvis 專用的 Mac mini，原本是放在我的 5080 電腦的頭上面，等於說它不會直接放在地板上。我現在的問題是我的 HDMI 線，今天 Mac mini 的 HDMI 線不夠長，導致我升降桌如果升起來的話，它的長度不夠讓我放到地上，所以它必須一定要放在一個離地有一段距離的東西上面。

之前是放在 5080 的電腦的，但是 5080 電腦現在已經放到倉庫裡面去了，所以我必須拿一個東西墊。我本來是拿一個紙箱墊，但是我後來想說我可以把我的 Xbox S 放在它的下面，這樣子我以後也可以接 Xbox 來用電腦玩，就是電腦螢幕就可以接 Xbox 來玩，然後我也可以切換回去用這個。反正等於說我就可以把它墊在，把這個 Mac mini 墊在 Xbox 的上面。

但是我想要做一個架子，一個外殼的架子，這個架子是可以很簡單的幫我抽取這個 Xbox S。也就是說呢，我甚至可以把 Xbox 輕易地從裡面拿走，像一個架子一樣從上面拿走，但是我的這個 Mac mini 依然是放在這個架子的頭頂上面。

所以現在是呢，我想要要麼是自己設計、自己建模畫一個架子，然後這個架子要是組裝起來的，因為我覺得我的 Bambu Lab 的 A1 mini 的空間不夠一體成型的，沒有辦法一體成型的印出這個東西。所以如果我們自己做的話呢，一定是要用切的，先畫好外形，然後切，然後拼裝起來。

那另一種做法呢，是我們直接找關鍵字，先上社群去看看有沒有網友已經分享過類似的外形，然後我們再來調整它的尺寸，然後再來切。你覺得怎麼做呢？我們今天這一篇就是來討論這個專案。

__

gpt回了一些沒用的建議...

＿＿＿

聽起來你找過社群以後沒有找到適合的架子可以拆解，那跟我想像差不多啦，所以或許勢必還是要我們自己來做，然後自己做拼接。我的想法是我剛剛去量了這個長寬，長我們以這個 Xbox S 的底座為基礎，我抓大概 20 公分以內綽綽有餘。寬的話寬度我們選比較寬，寬度更大的 Mac mini 本身，16 公分綽綽有餘。你看我畫的設計圖，我覺得應該是這樣子，我們只需要想好 layer N 跟 top 跟 base 就好了。我們只要能夠做到 layer 和 layer 之間可以有那種插銷或是拔介面，或是像樂高一樣那樣子都可以，我們只是舉例啦。所以我們只需要印好 top、layer N 跟 base 就 OK，然後 layer N 我可以自己再複製 N 個對吧。然後也許 layer N 之間就像我們說它們之間就是用那個樂高之類或是某個巧妙的設計可以讓它們之間做拼接，然後 layer 之間可以是做鏤空的，不用就是完全像我這樣實體，但是你大概懂我意思嗎？

＿＿＿

對，我完全懂你的意思，而且我覺得你現在這個想法 **比一開始更清楚、也更適合 A1 mini**。

你現在其實已經把整個系統抽象成 3 種零件了：

1. **base**
2. **layer N**
3. **top**

然後靠 **layer N 重複堆疊** 去決定高度。  
這個方向我覺得是對的，而且是最適合做成「可調高度、可拆裝、可反覆改版」的設計。

---

## 一、先講結論：你的模組化思路是成立的

你現在的概念，本質上就是：

- **Base**：最底部，負責站穩、定位、承重
- **Layer N**：標準中間層，每多加一層就多一段高度
- **Top**：最上面平台，放 Mac mini
- **中間留空**：讓 Xbox Series S 可以被包在中間，但前後或至少前方保持開放，方便抽取與散熱

這樣的好處很大：

- 高度可以調整
- 不用一次印超大件
- 搬家或修改容易
- 如果之後不用 Xbox，仍然能把它當作一般設備架
- 如果第一版高度不對，只要增減 layer N，不用整個重做

所以答案是：**對，layer N 就是可以複製 N 個。**

---

## 二、但有一個關鍵現實：你畫的 20 cm base / top，A1 mini 不能單片印

這點要先抓出來，不然你後面一畫完才發現不能印。

你剛剛說大概：

- 長：**20 cm**
- 寬：**16 cm**

而 **A1 mini 的列印範圍是 180 × 180 mm**。  
所以：

- **16 cm 寬沒問題**
- **20 cm 長超過 18 cm，不能整片一次印**

也就是說：

### 這代表兩種做法：

#### 做法 A：把 base / top 也切件
例如切成：
- 左半 + 右半
- 或 前半 + 後半

然後用：
- 榫接
- 卡扣
- 螺絲
- 插銷

拼回一整片。

#### 做法 B：把整體長度壓到 17.8～17.9 cm 以內
這樣 base / top 才能單片列印。  
但你現在是以 Xbox 底座抓 20 cm，我覺得 **不太建議硬縮**，因為可能會讓抽取手感變差，也讓穩定性下降。

**所以我比較建議：base 和 top 也做成分件式。**

---

## 三、我建議你不要把 layer N 做成「整圈實體框」，而是做成「骨架模組」

你有說可以鏤空，我很贊成。

因為這個架子其實不需要實心牆，它更像是一個 **開放式骨架 tower**。

我建議每個 layer N 可以長這樣：

### 方案 1：四柱框架型（最穩）
每一層 layer N 由這些構成：

- 左前柱
- 右前柱
- 左後柱
- 右後柱
- 上方橫樑／側樑做連接

也就是一個像小桌框的結構。

**優點**
- 最穩
- 受力直覺
- 好堆疊
- Mac mini 重量可以直接沿四角往下傳到底座

**缺點**
- 零件數稍多

---

### 方案 2：門字型框架（你圖上比較像這個）
每個 layer N 由兩個「ㄇ字型 / U 字型」側框組成，再靠前後連接件固定。

例如：

- 左側一個 U frame
- 右側一個 U frame
- 中間用插接橫桿連起來

**優點**
- 很符合你畫的概念
- 看起來更簡潔
- 比較有「疊 layer」的感覺

**缺點**
- 如果沒有背面補強，左右可能容易扭

---

### 方案 3：四角柱 + 輕量化橫梁（我最推薦）
這是我目前最看好的：

- 每個 layer N 不是整個一圈牆
- 而是 **四個角柱 + 四邊的細橫梁**
- 中間完全留空
- 前面甚至可以不做橫梁，方便抽 Xbox

這樣會有幾個好處：

- **散熱最好**
- **最省料**
- **印得快**
- **看起來更乾淨**
- Xbox 可直接從前面抽出

如果怕晃，可以只在**背面**做一條橫向補強，甚至做 X 型薄拉桿。  

---

## 四、我會怎麼定義這三種零件

下面這個會比較接近工程規格。

## 1. Base
功能：
- 提供最大接地面積
- 承接全部重量
- 提供第一層的定位孔 / 插槽

建議：
- 不要只是平板
- 最好有 **向外微微擴張的底腳** 或至少四角加寬
- 因為你的整體會變成細高型結構，地毯上更需要穩

### Base 建議設計
- 分成兩半列印
- 中間用：
  - 榫槽
  - M3 螺絲
  - 或燕尾滑入
  去組裝
- 上方做四個定位孔，給第一層 layer N 插入

---

## 2. Layer N
功能：
- 提供高度
- 承重
- 模組化堆疊

這是整個設計最關鍵的件。

### 我建議 Layer N 要有這幾個特性：

#### a. 上下對稱
這樣同一件可以一直疊，不分正反，超方便。

#### b. 上面是公頭、下面是母孔
或反過來也行，但要統一。

例如：
- 下方：插孔
- 上方：插柱 / 卡榫

這樣 layer N 可以一層接一層。

#### c. 每層高度固定
例如每層 **50 mm / 60 mm / 70 mm** 其中一種。

如果你 Xbox 高度約 27.5 cm，而 Mac mini 厚度加安全間隙再算上去，  
那你可以用：

- 4 層 × 60 mm = 240 mm
- 5 層 × 60 mm = 300 mm

這樣就可以選擇 4 層或 5 層看實際需要。

我會傾向先做 **60 mm 一層**，很好算，也不會太矮。

---

## 3. Top
功能：
- 放 Mac mini
- 防止滑動
- 保持通風
- 對接最上層 layer N

### Top 建議設計
不是做一塊實心板，而是：

- 外框 + 中間鏤空
- 或者薄板 + 開孔
- 四角做止滑定位邊

因為 Mac mini 不需要完全被托住，只要：
- 有足夠支撐
- 不滑走
- 下方能通風
就可以了。

如果你怕 Mac mini 位移，可以加：
- 四個小凸點
- 或低矮圍邊（例如 3–5 mm）

這樣既不難拿起來，也能定位。

---

## 五、拼接機構怎麼做？我建議先別用太複雜的「樂高式」

你有提到樂高式，我懂你的意思，但我會建議：

**第一版不要追求太花俏。**
先做「穩、準、可重複裝拆」比較重要。

### 我建議的拼接優先順序：

#### 第一名：插柱 + 定位孔 + 螺絲鎖定
最務實。

- 每層四角有對位柱
- 下一層對應有孔
- 插進去後可選擇用 M3 螺絲或熱熔銅螺母固定

**優點**
- 精準
- 穩
- 不容易鬆
- 很適合承重

---

#### 第二名：燕尾滑槽
如果你想要有點「抽換感」。

例如：
- layer N 的柱子和 base / top 用燕尾導軌滑入
- 裝配有儀式感
- 不容易左右跑掉

**缺點**
- 公差要求更高
- 第一次就做好比較難

---

#### 第三名：純卡扣 / 彈片扣
我反而不建議第一版就用這個。

因為：
- 3D 列印卡扣久了會疲勞
- PETG 比較韌，但精度與手感還是要反覆試
- 承重件若只靠卡扣，我不太放心

---

## 六、我覺得最適合你的 v0.1 結構是這個

### v0.1 推薦架構：
- **Base：左右兩片**
- **Layer N：單一標準件，可重複列印**
- **Top：左右兩片**
- **四角插柱定位**
- **必要時用 M3 螺絲補鎖**
- **前方開放**
- **背面一條補強樑**
- **側面開放式骨架**
- **Top 為托盤式，不做實心厚板**

這樣的結果會是：

- Xbox 直接從前面抽出
- Mac mini 固定在上面
- 整體看起來像小型開放設備塔
- 之後若 HDMI 長度稍有變化，只要減少一層 layer N 即可

---

## 七、尺寸上我建議這樣抓，不要只抓剛剛好

你現在量的是概念尺寸，我建議設計尺寸要再留鬆量。

### 內部淨空建議
以 Xbox Series S 為主體：

- **內長**：至少比 Xbox 實際佔地多 **10–15 mm**
- **內寬**：至少多 **10–15 mm**
- **內高**：至少多 **15–25 mm**

理由：
- 取出比較順
- 線材不會卡
- 散熱比較安心
- 真正列印尺寸會有誤差

### 外部尺寸
你現在想的：
- 約 **200 mm 長**
- 約 **160 mm 寬**

這個方向我覺得合理。  
但因為要分件列印，我甚至會考慮把 base 做到 **200 × 170 mm 左右**，只要不太突出，其實底盤大一點是好事，穩定性更高。

---

## 八、我會怎麼開始建模

如果今天是我陪你真的開始做，我會這樣排順序：

### Step 1：先確定「內部淨空盒」
先不要畫漂亮外殼，先畫一個 invisible box：

- Xbox 所需淨空盒
- Mac mini 所需上方托盤面積
- 預計總高度

也就是先決定：
- 內長
- 內寬
- 每層高度
- 要幾層

---

### Step 2：設計 Layer N 標準件
先把最重要的 layer N 做出來。

你真正的產品核心不是 base，也不是 top，  
而是 **中間那個可重複的標準層**。

只要 layer N 成功：
- Base 很容易接
- Top 很容易接
- 高度也自然能擴充

---

### Step 3：做 base / top 的拼接
因為這兩個超過 A1 mini 長度，要切件。

這裡就順便把：
- 定位榫
- 接縫補強
- 螺絲孔
一起設計好。

---

### Step 4：只印半套樣件測試
例如先印：
- 1 個 layer N
- 1/2 base
- 1/2 top
- 1 個角接頭

做 dry fit，確認：
- 公差
- 插拔鬆緊
- 承重
- 抽取手感

不要一開始就整套印滿。

---

## 九、我對你這個設計的最終判斷

我覺得這個專案現在已經成熟到可以正式進入 CAD 了。  
而且你這次的抽象化很好，因為你不是在想「做一個一次性架子」，你是在想：

> 做一個可重複、可堆疊、可調高度的模組系統。

這樣未來甚至不只是 Xbox + Mac mini：

- 可以換別的主機
- 可以換 NAS
- 可以換 mini PC
- 可以多一層放 dock / hub / 路由器

所以這個方向非常值得做。

## 十、我現在最建議你做的定稿方向

如果要我幫你拍板，我會選：

- **骨架式**
- **前方開放**
- **Layer N 為標準重複件**
- **Base / Top 分件列印**
- **上下插柱定位**
- **必要時 M3 螺絲補強**
- **每層高度 60 mm 左右先試**
- **PETG 優先**

---

如果你要的話，我下一步可以直接幫你做兩件事其中之一：

### A. 幫你把這個變成「可直接建模的規格書」
我會整理成像這樣：
- overall dimensions
- layer N dimensions
- connector logic
- tolerance recommendations
- print orientation
- assembly order

你拿去給 CAD / OpenSCAD / Fusion 直接做。

### B. 我直接幫你先出一版「v0.1 結構藍圖」
我會用文字幫你定義：
- base 怎麼切
- layer N 長什麼樣
- top 怎麼接
- 每個接頭應該在哪裡
- 哪些地方鏤空
- 哪些地方要補強

如果你願意，我建議我們下一則就直接進 **B：v0.1 結構藍圖**，這樣就不是抽象討論，而是可以開始畫了。

＿＿＿

可以，18公分可以，你看我這張圖。其實甚至17.5公分都可以，就是再更小都可以，只是我是想要讓它縫隙稍微大一點，我手伸進去拿的時候比較不用這樣子閃閃啊，或是就是注意，我想要就是快速地拿，所以才會抓20公分這麼充裕，就像你畫圖一樣。但是18公分夠，所以等於說我們的底座還是可以一體成型的話，甚至我們可以抓17.5公分來做都其實放得進去。然後那再來就是每個layer之間，就是base跟layer跟top之間的那個橋接孔，我們是自己畫、自己設計，還是說我們直接用Bambu Lab自己的，它好像就有所謂的那個切片的功能來切就可以了，我記得他們好像也有切。或者是我們也可以找社群裡面有沒有人有做類似的東西，他們也有設計好一個很漂亮的這個插銷或是這個拼接之間的這種設計，我們直接拿來抄襲沿用就好，你覺得呢？

＿＿＿

對！看你這張新的尺規照片，我同意我們可以把 17.5 × 17.5 cm 當作第一版底座的設計目標，不必為了原本預估的 20 cm 特地把底座切成兩片。

這其實讓整個專案簡化很多：Base、Layer N、Top 都有機會各自一體列印，只有組裝時才需要連接。

而且我查到了你記得的功能！Bambu Studio 確實內建切割及連接件功能，甚至還支援燕尾榫（Dovetail）與卡扣（Snap Connector）。&#x20;

[image](https://www.google.com/s2/favicons?domain=https://newreleases.io\&sz=32)

新發行資訊

+1



不過我研究後的判斷是：

Bambu Studio 的接頭可以用，但如果我們要做你說的 Layer N × N，我更建議借鑑現成接頭結構，再用參數化 CAD 做成自己的標準介面。

理由不是 Bambu Studio 的接頭不好，而是你的需求比較特殊：你想要的是能長期重複使用、自由增減高度、所有層都相容的模組系統。

## 一、Bambu Studio 能做什麼？

[Cut Menu in Studio - Bambu Studio - Bambu Lab Community Forum](https://images.openai.com/static-rsc-4/2l12t-xJs9SjMKt_gQoV4nb67gNXcjkYEbPrgxPegRR5SunSMnYTZpwzGN9vD7riKLPlx9MA2eh0aCg84GvGc1uOQW2LW31S7VMqZXUVrgaU04Bu0MNUrZ1pErSzuKPZdOrWupKgLlzCEQ8jsM7X63kKocZIwtbn9puJH-_jGzY?purpose=inline)

[forum.bambulab.com](https://forum.bambulab.com/t/cut-menu-in-studio/152029?utm_source=chatgpt.com)

Bambu Studio Cut Tool 的接頭設定示意

它基本上可以這樣操作：

1. 載入一個 3D 模型。
2. 使用 Cut（切割） 工具選擇分割面。
3. 選擇 Add Connectors（加入連接件）。
4. 在切面設定插銷、定位柱、卡扣等連接形式。
5. 設定尺寸、公差並執行切割，最後分件列印。

它也能用來處理超過 A1 mini 列印空間的大型模型。

[image](https://www.google.com/s2/favicons?domain=https://forum.bambulab.com\&sz=32)

Bambu Lab Community Forum



但要注意，這是針對「同一個模型被切開的兩個部分」設計的工具，不是一套完整的模組化機械介面設計器。

所以如果你畫好一座 30 cm 高的架子，再用它切成五層，當然可以嘗試。

問題是我們以後若想把同一個 Layer N 複製十次，還希望 Base、Layer N、Top 全部使用完全相同的接頭規格，在 CAD 內直接定義共用介面會更容易維護。

## 二、社群裡我找到兩個值得借鑑的接頭系統

[Modular Furniture Joints by Made By Castelao MakerWorld: Download Free 3D Models](https://images.openai.com/static-rsc-4/K8R61sT2AHzAMmITs3kbHJdWYkRO3SUER-eiMe4VM3r8fmTqXm6EraKKRRtW435WNf8bEQvpct84MfYXm5f63Pbf4vm221aflne9AyK7egMrziNgaHFVCuDIsIkVY8hqDX4n2yxxh5-zXV2Tke2Iymrke7L9Utp8eDU5qMPUWcE?purpose=inline)

[Pillar Modular Shelf System](https://www.printables.com/model/1834191?utm_source=chatgpt.com)

這套最有意思。它的支柱可以上下堆疊，所有零件採用按壓卡合，作者甚至形容像大型樂高，而且不需要螺絲。

[image](https://www.google.com/s2/favicons?domain=https://www.3dgo.app\&sz=32)

3D Printer File



主要使用木板作層板，但它的支柱堆疊介面非常值得我們研究。

[Modular 3D Printable Shelf – Scalable Design by emmemodeling MakerWorld: Download Free 3D Models](https://images.openai.com/static-rsc-4/j7rAKy2oEW-zMLE3saDPZxYFXxhsYYt2sP5Bpl38-fFC5ydm8pACt4oqEUk9YUpa85drDva1LstWsgHq6rFn1TcDbBcqWiPQCJUr_b0-e0ef0fzwjgZ29gZe9bmQJbViTrOEBvGyLGoa0koMGnGWUeCcz3Y0zxJecYbzUY0zCxI?purpose=inline)

[Shelf Riser — Customizable & Modular](https://makerworld.com/en/models/2259682?utm_source=chatgpt.com)

這套更接近參數化 CAD 思路。它使用可設定的公母卡扣，支援修改尺寸、接頭配置與組裝結構。

[image](https://www.google.com/s2/favicons?domain=https://www.3dgo.app\&sz=32)

3D Printer File



值得參考它如何讓所有接頭共用同一套尺寸規格。

第一套採 CC BY-NC-SA 授權；第二套是 MakerWorld Exclusive License。個人改作前可以查看授權，但如果以後打算公開模型或放 GitHub，就應留意原始模型的再利用與分享條件。

## 三、我反而想到一種更適合我們的接法

不一定需要樂高那種公頭、母頭交替的形式。

我們可以做成 母孔＋獨立插銷（Dowel Pin）。

標準接頭概念：所有模組共用同一種孔位

這個設計有個很漂亮的特點：

Layer N 的頂部和底部都可以使用相同孔位。

所以 Base、Layer N、Top 的接合介面完全一致，而插銷可以獨立列印。

如果插銷太鬆、太緊甚至弄壞，我們不用重印整個 Layer N，重新印一顆小插銷就好。

初步可以從 8 mm 方形插銷、8.4 mm 方孔做小樣件測試，然後依實際 PETG 收縮與列印精度調整。這是試驗起點，不是已驗證的最終公差。

不過插銷主要負責對位，真正的重量應由各層支柱的接觸面直接傳遞。高度堆上去以後，還需要背面補強或鎖定結構，避免整座架子左右晃動。

## 四、17.5 cm 的尺寸，我想幫你把兩件事分清楚

目前的尺寸草案

| 部件      | 初步尺寸              | 說明                |
| ------- | ----------------- | ----------------- |
| Base    | 175 × 175 mm      | 單片列印              |
| Layer N | 最大平面 175 × 175 mm | 複製 N 次            |
| Top     | 待確認               | 取決於 Mac mini 實際尺寸 |
| 接合介面    | 四角共用孔位            | 獨立插銷              |

有兩個小地方需要注意。

第一，Xbox Series S 正面寬約 151 mm。如果 175 mm 是整個架子的外寬，扣掉兩側各 8 mm 的支柱之後，內寬只剩 159 mm，左右各約 4 mm 空隙。雖然放得下，但要達到你想要的快速抽取手感，我們需要調整支柱位置，避免前方卡手。

第二，我想修正前面對 Mac mini 型號的假設。Apple 的舊款 Mac mini（例如 2023 款）是 197 × 197 mm，新款 M4 才是 127 × 127 mm。

[image](https://www.google.com/s2/favicons?domain=https://www.apple.com\&sz=32)

Apple (BW)

&#x20;從照片我還不能確定你是哪一款。如果是 197 mm 版本，175 mm 的 Top 可能仍可透過底部支撐區域承托，但需要確認實際落腳位置，不能直接當作完全吻合。



另外，175 mm 正方形在 A1 mini 的 180 mm 平台上只剩很小的邊界，若切片需要 Brim，也得特別檢查。

## 五、我會選的開發方法

我現在的選擇是：

用社群的模組化接頭當參考，用 OpenSCAD 或 Fusion 360 設計共用孔位，再交給 Bambu Studio 切片列印。

而且先不印完整架子。我們可以只建模兩塊小型的接頭測試件，測試插拔手感、鬆緊度和強度。接頭確認後，再把它套用到整個系統。

這樣保留你的三種標準部件設計，也不必投入太多時間重新發明複雜的卡扣。

我現在只想再確認一件事：你這台 Jarvis 專用的 Mac mini，實際上是哪一代、或頂面的邊長是多少公分？

這會決定我們能不能真的把 Base、Layer N、Top 都控制在 175 mm 以內，而且全部單件列印。

＿＿＿

白痴喔！你這樣疊，中間哪有空間放xbox啦！ 我現在因為我差不多在15分鐘就要出門了，我必須要換成用手機來遙控某個agent來幫我往下推，所以我們下一步先來想這個repo可以建立什麼樣的名字。

我會建立一個public的GitHub repo，你幫我想五種版本的適合的名字跟description。等我創好repo以後，我開在repo我可能用opus來幫我畫，你先幫我想名字，我來創。

＿＿＿

哈哈，對，你罵得對 😂 我前面那張圖完全搞錯了！我們的 Layer N 必須是中間完全鏤空的ㄇ字型支架，不能用橫板把 Xbox 的空間擋住。

先不糾結建模，你要出門了，我們先把 GitHub Repo 建起來。

## 五個 GitHub Repo 命名方案

| Repo Name                 | GitHub Description                                                                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1. `layerdock` ⭐          | A modular, 3D-printable device stand built with stackable layers, an open frame, and interchangeable top and base plates. |
| 2. `jarvis-hardware-dock` | A custom 3D-printed hardware dock for Jarvis, designed to hold a Mac mini above a removable Xbox Series S.                |
| 3. `stackframe`           | An open-frame, modular 3D-printed stand with repeatable, interlocking layers and adjustable height.                       |
| 4. `modular-device-stand` | A parametric, 3D-printable stand for stacking electronics using reusable layers and tool-free assembly.                   |
| 5. `printstack`           | A lightweight, customizable stacking system for electronics, designed for compact 3D printers.                            |

## 我最推薦：`layerdock`

我喜歡這個名字，因為它剛好反映你提出的核心架構：

## layerdock

我的首選

Repository name

layerdock

Repository description

A modular, 3D-printable device stand built with stackable layers, an open frame, and interchangeable top and base plates.

&#x20;Copy description

最重要的是，我們以後可以讓 Opus 依照這個架構開發：

`Base + Layer × N + Top`

每個部件都以 Bambu Lab A1 mini 的列印空間為限制，透過標準插接機構組合。Layer 必須保留 Xbox 的完整容納空間，Xbox 可自由取出，而 Mac mini 由架子獨立承重。

這個名字也不會把專案限制在 Xbox 或 Mac mini，未來你想用同一套模組來放 NAS、路由器、其他設備都可以。

我的選擇是 `layerdock`，第二名是 `stackframe`。

你先去建立 Public Repo，等你創好，我們就能讓 Opus 直接開始規劃參數化 CAD 模型和第一版組裝機構。