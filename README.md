# ⚡ 加密貨幣選單欄監控器 v4.0 ⚡

🔄 使用幣安 (Binance) API - 精簡版  
🌐 選單欄應用 - 跨所有桌面空間顯示  
🎯 只獲取當前選擇的加密貨幣，節省網路資源  
💰 支援幣安現貨和合約交易功能  

## 🚀 新功能特色

### 💰 幣安交易功能
- **現貨交易**：市價買入/賣出、限價買入/賣出
- **合約交易**：做多/做空、平倉、可設定槓桿倍數
- **止盈止損**：支援設定止盈止損百分比
- **帳戶管理**：查看餘額、持倉、訂單紀錄
- **安全確認**：所有交易都有確認對話框

### 📊 價格監控功能
- 即時價格更新
- 24小時變化趨勢
- 價格警報通知
- 多種顯示模式

## 🛠️ 安裝和設定

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 配置幣安 API

有兩種方式設定 API 密鑰：

#### 方式一：使用環境變數（推薦）

**方法 A：直接設定環境變數**
```bash
# macOS/Linux
export BINANCE_API_KEY="您的幣安API密鑰"
export BINANCE_API_SECRET="您的幣安API密碼"

# Windows
set BINANCE_API_KEY=您的幣安API密鑰
set BINANCE_API_SECRET=您的幣安API密碼
```

**方法 B：使用 .env 文件**
```bash
# 創建 .env 文件
cat > .env << EOF
BINANCE_API_KEY=您的幣安API密鑰
BINANCE_API_SECRET=您的幣安API密碼
EOF

# 記得將 .env 文件加入 .gitignore（如果使用 Git）
echo ".env" >> .gitignore
```

**方法 C：在啟動時設定**
```bash
BINANCE_API_KEY="您的API密鑰" BINANCE_API_SECRET="您的API密碼" python crypto_menubar_monitor.py
```

#### 方式二：直接在配置文件中設定

編輯 `config.json` 文件：

```json
{
    "binance_api": {
        "api_key": "您的幣安API密鑰",
        "api_secret": "您的幣安API密碼",
        "testnet": true,
        "trading_enabled": false
    },
    "trading_settings": {
        "default_quantity_usdt": 10,
        "default_leverage": 1,
        "default_stop_loss_percentage": 5,
        "default_take_profit_percentage": 10,
        "order_confirmation": true
    }
}
```

> 🔒 **安全提醒**：建議使用環境變數方式，避免將 API 密鑰直接寫在配置文件中，特別是當項目需要版本控制時。

### 3. 獲取幣安 API 密鑰

1. 登入 [幣安官網](https://www.binance.com)
2. 前往「API 管理」頁面
3. 創建新的 API 密鑰
4. **重要**：為了安全起見，建議先在測試網測試

#### 測試網設定
- 測試網址：https://testnet.binance.vision/
- 註冊測試帳號並獲取測試 API 密鑰
- 在 config.json 中設定 `"testnet": true`

#### 正式交易設定
- 確保 API 密鑰有交易權限
- 在 config.json 中設定：
  - `"testnet": false`
  - `"trading_enabled": true`

## 🔧 使用說明

### 啟動應用程式

```bash
python crypto_menubar_monitor.py
```

或使用腳本：

```bash
./run_menubar.sh
```

### 💰 交易功能使用

1. **啟用交易功能**
   - 在 config.json 中設定有效的 API 密鑰
   - 設定 `"trading_enabled": true`

2. **現貨交易**
   - 選擇「💰 交易功能」→「📈 現貨交易」
   - 選擇市價或限價買入/賣出
   - 設定交易數量和止盈止損

3. **合約交易**
   - 選擇「💰 交易功能」→「⚡ 合約交易」
   - 選擇做多/做空/平倉
   - 設定槓桿倍數和止盈止損

4. **查看帳戶資訊**
   - 「💼 帳戶餘額」：查看現貨和合約餘額
   - 「📊 持倉資訊」：查看當前合約持倉
   - 「📋 訂單紀錄」：查看最近的交易訂單

### 🚨 價格警報設定

1. 點擊「🚨 警報設定」
2. 設定高價和低價警報閾值
3. 當價格觸及閾值時會收到系統通知

### 🎨 顯示模式

- **簡潔模式**：顯示價格和變化
- **完整模式**：顯示完整資訊
- **僅符號**：只顯示貨幣符號

## ⚠️ 安全注意事項

### 🔒 API 密鑰安全
- **絕對不要**將 API 密鑰分享給他人
- **建議**先在測試網測試所有功能
- **設定** API 密鑰的 IP 白名單限制
- **定期**更換 API 密鑰

### 💸 交易風險管理
- **小額測試**：先用小額資金測試
- **止盈止損**：總是設定止盈止損
- **合約風險**：合約交易風險較高，請謹慎使用
- **確認對話框**：保持開啟訂單確認功能

## 📋 配置選項說明

### binance_api
- `api_key`: 幣安 API 密鑰
- `api_secret`: 幣安 API 密碼
- `testnet`: 是否使用測試網 (true/false)
- `trading_enabled`: 是否啟用交易功能 (true/false)

### trading_settings
- `default_quantity_usdt`: 預設交易金額 (USDT)
- `default_leverage`: 預設槓桿倍數
- `default_stop_loss_percentage`: 預設止損百分比
- `default_take_profit_percentage`: 預設止盈百分比
- `order_confirmation`: 是否顯示訂單確認對話框

## 🐛 常見問題

### Q: 為什麼交易功能顯示為未啟用？
A: 請檢查：
1. API 密鑰是否正確設定
2. `trading_enabled` 是否設為 `true`
3. 網路連接是否正常

### Q: 如何切換到正式交易？
A: 
1. 獲取正式的幣安 API 密鑰
2. 在 config.json 中設定 `"testnet": false`
3. 確保 `"trading_enabled": true`

### Q: 止盈止損功能如何使用？
A: 在下單對話框中：
1. 勾選「啟用止損」或「啟用止盈」
2. 設定百分比（如 5% 表示價格變動 5% 時觸發）
3. 確認下單後會自動設定止盈止損訂單

## 📝 更新日誌

### v4.0
- ✅ 新增幣安現貨交易功能
- ✅ 新增幣安合約交易功能
- ✅ 新增止盈止損設定
- ✅ 新增帳戶餘額查看
- ✅ 新增持倉資訊查看
- ✅ 新增訂單紀錄查看
- ✅ 新增交易確認對話框
- ✅ 支援測試網和正式網切換

### v3.2
- 價格監控和警報功能
- 多種顯示模式
- 支援多種加密貨幣

## 🤝 支援和回饋

如果您遇到任何問題或有功能建議，請在 GitHub 上提交 Issue。

## ⚖️ 免責聲明

此工具僅供教育和研究用途。加密貨幣交易存在風險，請謹慎使用。開發者不對任何交易損失承擔責任。

---

**⚡ 享受您的加密貨幣交易體驗！ ⚡** 