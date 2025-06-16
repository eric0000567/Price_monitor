#!/bin/bash

# 賽博龐克加密貨幣選單欄監控器啟動腳本
# 解決跨桌面空間顯示問題的終極方案

echo "🚀 正在啟動賽博龐克加密貨幣選單欄監控器..."
echo "💡 這個版本使用 macOS 原生選單欄，可以在所有桌面空間顯示！"

# 檢查是否已安裝 rumps
if ! python3 -c "import rumps" 2>/dev/null; then
    echo "❌ 需要安裝 rumps 套件"
    echo "🔧 正在安裝 rumps..."
    pip3 install rumps
    
    if [ $? -ne 0 ]; then
        echo "❌ 安裝 rumps 失敗，請手動執行："
        echo "pip3 install rumps"
        exit 1
    fi
    echo "✅ rumps 安裝成功"
fi

# 檢查是否已安裝 requests
if ! python3 -c "import requests" 2>/dev/null; then
    echo "❌ 需要安裝 requests 套件"
    echo "🔧 正在安裝 requests..."
    pip3 install requests
    
    if [ $? -ne 0 ]; then
        echo "❌ 安裝 requests 失敗，請手動執行："
        echo "pip3 install requests"
        exit 1
    fi
    echo "✅ requests 安裝成功"
fi

echo ""
echo "🌟 選單欄監控器優勢："
echo "✅ 在所有桌面空間都能看到"
echo "✅ 不會被 Control+↑ 隱藏"
echo "✅ 原生 macOS 體驗"
echo "✅ 點擊選單欄圖示查看詳細資訊"
echo ""

echo "🚀 啟動模式選擇："
echo "1. 前景執行（預設）- 可在終端看到訊息"
echo "2. 背景執行 - 關閉終端也會繼續運行"
echo ""

read -p "請選擇啟動模式 [1/2，直接按 Enter 選擇前景]: " mode

if [ "$mode" = "2" ]; then
    echo "🌙 正在背景啟動選單欄監控器..."
    echo "💡 要停止程式，請從選單欄點擊退出，或執行："
    echo "   pkill -f crypto_menubar_monitor"
    
    # 背景執行，輸出到日誌檔案
    nohup python3 crypto_menubar_monitor.py > crypto_monitor.log 2>&1 &
    PID=$!
    echo "✅ 監控器已在背景啟動 (PID: $PID)"
    echo "📄 日誌檔案：crypto_monitor.log"
else
    echo "🖥️ 正在前景啟動選單欄監控器..."
    echo "💡 按 Ctrl+C 或從選單欄點擊退出來停止程式"
    
    # 前景執行
    python3 crypto_menubar_monitor.py
    echo "🛑 加密貨幣選單欄監控器已停止"
fi 