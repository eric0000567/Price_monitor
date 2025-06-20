# 🚀 加密貨幣監控器交易指南 v4.0

## 📋 目錄
1. [快速開始](#快速開始)
2. [警報設定](#警報設定)
3. [交易功能](#交易功能)
4. [輸入格式說明](#輸入格式說明)
5. [macOS 權限設定](#macos-權限設定)
6. [常見問題](#常見問題)
7. [風險管理](#風險管理)

## 🚀 快速開始

### 啟動應用程式
```bash
python3 crypto_menubar_monitor.py
```

啟動後，您會在 macOS 選單欄看到⚡符號，點擊即可使用所有功能。

## 🚨 警報設定

### 警報設定方式
1. 點擊選單欄中的 "🚨 警報設定"
2. 系統會彈出兩個對話框分別設定高價和低價警報
3. 輸入您希望的警報閾值（單位：USDT）
4. 設定完成後會**自動儲存到 `config.json` 文件**

### 警報設定特點
- ✅ **永久保存**：所有警報設定會儲存到 `config.json`，重啟程式後依然有效
- 🔄 **即時生效**：設定完成後立即開始監控
- 📱 **系統通知**：達到閾值時會發送 macOS 系統通知
- ⏰ **冷卻機制**：避免重複通知，預設冷卻時間 5 分鐘
- 🎯 **智能重置**：價格回到安全範圍後自動重置警報狀態

### 警報設定例子
- **當前價格**：$45,000
- **高價警報**：$50,000（漲到此價格時通知）
- **低價警報**：$40,000（跌到此價格時通知）

## 💰 交易功能

### 現貨交易
#### 市價交易
- **🟢 市價買入**：以當前市價立即買入
- **🔴 市價賣出**：以當前市價立即賣出

#### 限價交易
- **🎯 限價買入**：設定買入價格，等待價格到達時執行
- **🎯 限價賣出**：設定賣出價格，等待價格到達時執行

### 合約交易
- **📈 做多**：看漲時開多單，價格上漲獲利
- **📉 做空**：看跌時開空單，價格下跌獲利
- **🔄 平倉**：關閉所有持倉

### 帳戶功能
- **💼 帳戶餘額**：查看現貨和合約餘額
- **📊 持倉資訊**：查看當前合約持倉和盈虧
- **📋 訂單紀錄**：查看最近的交易記錄

## 📝 輸入格式說明

### 對話框輸入方式
程式使用 macOS 原生對話框，確保良好的輸入體驗：

1. **對話框會自動獲得焦點**
2. **直接在文字框中輸入數字**
3. **按確認或 Enter 鍵提交**

### 數量輸入範例
```
輸入: 10
意思: 10 USDT
```

### 價格輸入範例（限價訂單）
```
輸入: 45000
意思: $45,000 USDT
```

### 槓桿輸入範例（合約交易）
```
輸入: 5
意思: 5倍槓桿
```

## 🔐 macOS 權限設定

### 必要權限
1. **輔助功能權限**
   - 系統偏好設定 > 安全性與隱私 > 隱私權 > 輔助功能
   - 添加終端機或 Python 應用程式

2. **通知權限**
   - 系統偏好設定 > 通知
   - 確保允許來自 Python 或終端機的通知

### 權限設定步驟
1. 第一次運行時，系統可能會要求權限
2. 點擊「系統偏好設定」
3. 勾選相關應用程式的權限選項
4. 重新啟動程式

## ❓ 常見問題

### Q: 對話框無法輸入內容怎麼辦？
A: 程式已使用 macOS 原生對話框解決此問題。如果仍有問題：
- 確保應用程式有輔助功能權限
- 重新啟動程式
- 檢查是否有其他應用程式干擾

### Q: 警報設定會丟失嗎？
A: 不會！所有警報設定都會自動儲存到 `config.json` 文件中，重啟程式後會自動載入。

### Q: 交易失敗怎麼辦？
A: 常見原因和解決方案：
- **API 錯誤**：檢查 API 密鑰是否正確
- **餘額不足**：確保帳戶有足夠餘額
- **數量格式錯誤**：確保輸入純數字，不含符號

### Q: 如何切換測試網和主網？
A: 在 `config.json` 中修改：
```json
{
  "binance_api": {
    "testnet": false  // false=主網, true=測試網
  }
}
```

## ⚠️ 風險管理

### 基本原則
1. **小額測試**：先用小額測試功能
2. **設定止損**：控制潛在損失
3. **分散投資**：不要把所有資金投入單一交易
4. **了解槓桿風險**：合約交易風險較高

### 建議設定
- **止損百分比**：5-10%
- **止盈百分比**：10-20%
- **槓桿倍數**：新手建議 1-3 倍

### 警報最佳實踐
- 設定合理的警報範圍（不要太接近當前價格）
- 定期檢查和調整警報閾值
- 結合技術分析設定警報點位

## 🔧 技術支援

### 檔案結構
```
Monitor_price/
├── crypto_menubar_monitor.py  # 主程式
├── config.json               # 配置文件（包含警報設定）
├── requirements.txt          # 依賴套件
└── TRADING_GUIDE.md         # 本指南
```

### 重要配置文件
- **`config.json`**：包含所有設定，包括警報閾值
- **`.env`**：API 密鑰（可選，優先於 config.json）

### 記錄檔案
所有操作都會在終端機顯示詳細記錄，便於除錯。

---

**⚠️ 免責聲明**：加密貨幣交易具有高風險，可能導致資金損失。請僅使用您能承受損失的資金進行交易，並在使用前充分了解相關風險。本軟體僅供學習和參考使用。 