# 💰 Mac 加密貨幣價格監控器

一個簡單易用的Mac選單列應用程式，可以即時監控加密貨幣價格並顯示在Mac的選單列中。

## ✨ 功能特色

- 🔄 **即時價格更新**: 自動獲取最新的加密貨幣價格
- 📊 **選單列顯示**: 在Mac選單列顯示主要貨幣（比特幣）價格
- 📈 **漲跌指示**: 使用emoji和顏色顯示價格變化
- 🔧 **可自訂**: 可新增/移除監控的加密貨幣
- ⏰ **更新間隔設定**: 可調整價格更新頻率
- 🔔 **通知功能**: 價格更新時發送系統通知
- 💻 **輕量級**: 使用最少的系統資源

## 📋 系統需求

- macOS 10.10 或更新版本
- Python 3.6 或更新版本
- 網路連線（用於獲取價格資料）

## 🚀 快速開始

### 1. 安裝依賴

```bash
chmod +x install.sh
./install.sh
```

### 2. 執行應用程式

```bash
chmod +x run.sh
./run.sh
```

或直接執行：

```bash
python3 crypto_monitor.py
```

## 🎯 使用方法

### 啟動應用程式
1. 執行應用程式後，您會在Mac選單列看到 "💰 Crypto" 圖示
2. 選單列會顯示比特幣的當前價格，例如：`📈 BTC $45,000`

### 檢視所有價格
1. 點擊選單列的圖示
2. 選單會顯示所有監控中的加密貨幣價格和24小時變化

### 新增加密貨幣
1. 點擊選單中的 "新增貨幣"
2. 輸入加密貨幣的ID（例如：ethereum, cardano）
3. 價格將自動更新並顯示在選單中

### 設定更新間隔
1. 點擊選單中的 "設定更新間隔"
2. 輸入新的更新間隔（秒），最少30秒

## 📊 支援的加密貨幣

本應用程式使用 CoinGecko API，支援所有在 CoinGecko 上列出的加密貨幣。

常見的加密貨幣ID：
- `bitcoin` - 比特幣
- `ethereum` - 以太坊
- `cardano` - 卡達諾
- `solana` - 索拉納
- `dogecoin` - 狗狗幣
- `binancecoin` - 幣安幣
- `ripple` - 瑞波幣
- `polkadot` - 波卡幣

## ⚙️ 配置檔案

應用程式使用 `config.json` 檔案儲存配置：

```json
{
    "cryptocurrencies": ["bitcoin", "ethereum"],
    "update_interval": 60,
    "display_currency": "usd",
    "show_percentage_change": true,
    "notification_enabled": true
}
```

## 🔧 進階功能

### 自動啟動
要讓應用程式在Mac開機時自動啟動：

1. 打開 "系統偏好設定" > "使用者與群組"
2. 選擇您的使用者帳號
3. 點擊 "登入項目" 分頁
4. 點擊 "+" 按鈕，新增本應用程式的腳本

### 建立應用程式包
您可以使用 `py2app` 將Python腳本打包成Mac應用程式：

```bash
pip3 install py2app
python3 setup.py py2app
```

## 🛠️ 疑難排解

### 常見問題

**Q: 應用程式無法啟動**
A: 請確保已安裝所有依賴套件：`pip3 install -r requirements.txt`

**Q: 價格無法更新**
A: 請檢查網路連線，確保可以存取 CoinGecko API

**Q: 選單列沒有顯示圖示**
A: 請確保您的Mac支援選單列應用程式，並檢查Python環境

## 📝 版本資訊

- **版本**: 1.0
- **作者**: AI Assistant
- **資料來源**: CoinGecko API
- **授權**: MIT License

## 🔗 相關連結

- [CoinGecko API](https://www.coingecko.com/en/api)
- [Rumps 文檔](https://github.com/jaredks/rumps)

## 📞 支援

如果您遇到任何問題或有功能建議，請在應用程式中使用 "關於" 選單項目查看詳細資訊。 