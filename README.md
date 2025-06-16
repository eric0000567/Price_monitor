# ⚡ 加密貨幣選單欄監控器 v3.2

一個專為 macOS 設計的加密貨幣價格監控應用程式，使用原生選單欄顯示於系統導覽列。    
讓你上班也能第一時間獲取幣安最新價格。

## ✨ 核心特色

- 🌐 **跨桌面空間顯示**: 在所有 macOS 桌面空間都能看到價格
- 🎯 **節省網路資源**: 只獲取當前選擇的加密貨幣價格
- 🎨 **三種顯示模式**: 僅符號 | 簡潔模式 | 完整模式
- 🔄 **即時價格更新**: 使用幣安 API，30 秒自動更新
- 📊 **詳細資訊面板**: 完整的價格、漲跌、成交量資訊
- 🪙 **智能符號支援**: 自動識別新加密貨幣並生成符號
- ⚙️ **配置檔案驅動**: 透過 JSON 檔案完全自訂

## 🖥️ 系統需求

- **macOS**: 10.12 或更新版本
- **Python**: 3.7 或更新版本
- **網路連線**: 用於獲取幣安 API 資料

## 🚀 快速安裝

### 1. 安裝依賴套件

```bash
pip install rumps requests
```

### 2. 設定執行權限

```bash
chmod +x run_menubar.sh
```

### 3. 啟動監控器

```bash
./run_menubar.sh
```

啟動時會詢問您要前景執行還是背景執行：
- **前景執行**: 可在終端看到運行訊息，關閉終端會停止程式
- **背景執行**: 關閉終端後程式繼續運行

## 📊 支援的加密貨幣

程式透過 `config.json` 檔案支援任何幣安交易所的交易對：

### 預設支援
- ₿ **Bitcoin** (BTCUSDT)
- Ξ **Ethereum** (ETHUSDT) 
- ₳ **Cardano** (ADAUSDT)
- ◎ **Solana** (SOLUSDT)
- Ð **Dogecoin** (DOGEUSDT)
- ✕ **Ripple** (XRPUSDT)
- ⚡ **TRON** (TRXUSDT)
- Ł **Litecoin** (LTCUSDT)
- ₿ **Bitcoin Cash** (BCHUSDT)
- ✪ **Stellar** (XLMUSDT)
- ⬢ **Chainlink** (LINKUSDT)

### 擴展支援
程式內建 20+ 種常見加密貨幣符號，包括：
- ⬡ Binance Coin (BNB)
- ● Polkadot (DOT)
- 🦄 Uniswap (UNI)
- ▲ Avalanche (AVAX)
- 🐕 Shiba Inu (SHIB)
- 等等...

對於新的加密貨幣，程式會自動生成符號。

## ⚙️ 配置檔案

編輯 `config.json` 來自訂監控的加密貨幣：

```json
{
    "trading_pairs": [
        "ETHUSDT",
        "BTCUSDT", 
        "ADAUSDT",
        "SOLUSDT",
        "DOGEUSDT",
        "XRPUSDT",
        "TRXUSDT",
        "LTCUSDT",
        "BCHUSDT",
        "XLMUSDT",
        "LINKUSDT"
    ],
    "update_interval": 30,
    "display_currency": "USDT",
    "show_percentage_change": true,
    "notification_enabled": true,
    "price_alert_enabled": false,
    "alert_thresholds": {
        "ETHUSDT": {
            "high": 2585,
            "low": 2515
        }
    }
}
```

### 配置說明
- **trading_pairs**: 要監控的交易對列表（必須是幣安支援的）
- **update_interval**: 價格更新間隔（秒）
- **其他欄位**: 保留用於未來功能擴展

## 🎨 使用指南

### 顯示模式切換

**🔺 僅符號模式**
- 選單欄只顯示貨幣符號：`₿`
- 節省最多空間

**🔸 簡潔模式**（預設）
- 選單欄顯示符號 + 完整價格：`₿ $67,234.56`
- 平衡空間和資訊量

**🔹 完整模式**
- 選單欄顯示符號 + 價格 + 漲跌：`₿ $67,234.56 +2.34%`
- 顯示最完整資訊

### 查看詳細資訊

點擊選單欄圖示，查看：
- 📊 簡潔資訊摘要
- 📈 詳細資訊子選單
  - 💰 現價
  - 📊 24h 變化
  - ⬆️ 24h 最高
  - ⬇️ 24h 最低  
  - 📈 成交量
  - 🔄 更新時間

### 切換加密貨幣

1. 點擊選單欄圖示
2. 選擇「💰 選擇加密貨幣」
3. 點擊想要監控的貨幣
4. 程式會立即切換並更新價格

### 手動重新整理

點擊選單中的「🔄 重新整理」立即更新價格。

## 🔧 進階功能

### 背景執行

使用背景執行模式讓程式持續運行：

```bash
./run_menubar.sh
# 選擇 2（背景執行）
```

停止背景程式：
```bash
pkill -f crypto_menubar_monitor
```

或從選單欄點擊「❌ 退出」

### 新增自訂加密貨幣

1. 編輯 `config.json`
2. 在 `trading_pairs` 中新增幣安支援的交易對
3. 重新啟動程式

範例：新增 Polygon (MATIC)
```json
{
    "trading_pairs": [
        "ETHUSDT",
        "BTCUSDT",
        "MATICUSDT"
    ]
}
```

程式會自動為 MATIC 生成符號 ⬟ 和名稱 Polygon。

### 開機自動啟動

1. 打開「系統偏好設定」→「使用者與群組」
2. 選擇「登入項目」
3. 新增 `run_menubar.sh` 腳本

或使用 LaunchAgent（推薦）：

```bash
# 建立 LaunchAgent 檔案
cp com.crypto.monitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.crypto.monitor.plist
```

## 🎯 優勢特色

### vs 傳統浮動視窗
- ✅ **永不消失**: 不會被 Mission Control 影響
- ✅ **跨空間顯示**: 在所有桌面都能看到
- ✅ **原生體驗**: 完美融入 macOS 選單欄
- ✅ **節省空間**: 不佔用桌面空間

### vs 網頁監控
- ✅ **即時更新**: 自動背景更新，無需手動刷新
- ✅ **離線友好**: 本地快取資料
- ✅ **低資源消耗**: 比瀏覽器分頁更輕量

### vs 手機 App
- ✅ **無需切換**: 始終在視線範圍內
- ✅ **工作流程**: 完美融入桌面工作環境
- ✅ **多螢幕支援**: 在所有螢幕的選單欄都會顯示

## 🛠️ 疑難排解

### 常見問題

**Q: 選單欄沒有顯示圖示**
```bash
# 檢查 rumps 套件
pip show rumps

# 重新安裝
pip install --upgrade rumps
```

**Q: 價格無法更新**
```bash
# 檢查網路連線
curl -s "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"

# 檢查 API 回應
python3 -c "import requests; print(requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT').status_code)"
```

**Q: 程式無法啟動**
```bash
# 檢查 Python 版本
python3 --version

# 檢查配置檔案
cat config.json | python3 -m json.tool
```

**Q: 背景程式如何停止**
```bash
# 方法 1：從選單欄退出
# 點擊選單欄圖示 → ❌ 退出

# 方法 2：命令列停止
pkill -f crypto_menubar_monitor

# 方法 3：查看並停止特定程序
ps aux | grep crypto_menubar_monitor
kill [PID]
```

**Q: 新增的加密貨幣沒有符號**
A: 程式會自動為新貨幣生成符號，通常使用貨幣代碼的前 2-3 個字母。

## 📋 檔案結構

```
Monitor_price/
├── crypto_menubar_monitor.py   # 主程式檔案
├── run_menubar.sh             # 啟動腳本  
├── config.json                # 配置檔案
├── README.md                  # 說明文件
└── 使用指南.md                # 詳細使用指南
```

## 📈 API 資訊

- **資料來源**: 幣安 (Binance) API
- **更新頻率**: 30 秒（可調整）
- **API 端點**: `https://api.binance.com/api/v3/ticker/24hr`
- **限制**: 免費 API，每日有使用限制

## 🔗 相關連結

- [幣安 API 文檔](https://binance-docs.github.io/apidocs/)
- [Rumps 套件文檔](https://github.com/jaredks/rumps)
- [macOS 選單欄應用開發](https://developer.apple.com/design/human-interface-guidelines/macos/menus/menu-bar-menus/)

## 📝 版本資訊

- **當前版本**: v3.2 精簡版
- **發布日期**: 2024
- **主要功能**: 選單欄加密貨幣價格監控
- **支援平台**: macOS 10.12+
- **授權**: MIT License

## 🆘 技術支援

如遇到問題，請檢查：

1. **系統需求**: macOS 版本和 Python 版本
2. **網路連線**: 確保可以存取幣安 API
3. **配置檔案**: `config.json` 格式正確
4. **套件安裝**: rumps 和 requests 套件完整安裝

---

**💡 提示**: 這個應用程式專為 macOS 用戶設計，完美解決了跨桌面空間監控加密貨幣價格的需求。無論您使用多少個桌面空間，價格資訊始終在您的視線範圍內！ 