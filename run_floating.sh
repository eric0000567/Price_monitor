#!/bin/bash

echo "🚀 啟動懸浮視窗加密貨幣監控器..."

# 停止可能運行的舊版本
pkill -f crypto_monitor.py 2>/dev/null
pkill -f crypto_floating_window.py 2>/dev/null

# 檢查依賴是否已安裝
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "❌ tkinter未安裝，請安裝tkinter："
    echo "   brew install python-tk"
    exit 1
fi

if ! python3 -c "import requests" 2>/dev/null; then
    echo "❌ requests未安裝，請先執行: pip3 install requests"
    exit 1
fi

echo "💰 正在啟動懸浮視窗應用程式..."
python3 crypto_floating_window.py 