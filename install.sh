#!/bin/bash

echo "🚀 安裝加密貨幣監控應用程式..."

# 檢查Python是否安裝
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，請先安裝Python3"
    echo "可以通過Homebrew安裝: brew install python3"
    exit 1
fi

# 檢查pip是否安裝
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到pip3，請先安裝pip3"
    exit 1
fi

echo "📦 安裝Python依賴套件..."
pip3 install -r requirements.txt

echo "✅ 安裝完成！"
echo ""
echo "🎯 使用方法:"
echo "1. 執行應用程式: python3 crypto_monitor.py"
echo "2. 或使用執行腳本: ./run.sh"
echo ""
echo "💡 提示:"
echo "- 應用程式將在Mac選單列顯示比特幣價格"
echo "- 點擊選單列圖示可查看所有監控的加密貨幣"
echo "- 可以新增或移除要監控的加密貨幣"
echo "- 預設每60秒更新一次價格"

# 讓腳本可執行
chmod +x run.sh 