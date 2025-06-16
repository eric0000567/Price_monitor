#!/usr/bin/env python3
"""
簡化版跨Spaces設定工具
為加密貨幣監控器提供清晰的手動設定指導
"""

import subprocess
import time
import os

def check_crypto_monitor_running():
    """檢查加密貨幣監控器是否運行"""
    try:
        result = subprocess.run([
            'pgrep', '-f', 'crypto_floating_window.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            pid = result.stdout.strip()
            print(f"✅ 加密貨幣監控器正在運行 (PID: {pid})")
            return True
        else:
            print("❌ 加密貨幣監控器未運行")
            return False
    except Exception as e:
        print(f"❌ 檢查程序狀態失敗: {e}")
        return False

def show_setup_instructions():
    """顯示設定說明"""
    print("\n" + "="*60)
    print("🌐 讓監控器在所有桌面空間中顯示")
    print("="*60)
    
    print("\n🎯 方法一：右鍵選單（推薦，3步驟）")
    print("1. 在監控器中按 T 鍵顯示標題欄")
    print("2. 右鍵點擊視窗 → 選擇 '指定給' → '所有桌面'")
    print("3. 按 T 鍵隱藏標題欄，恢復賽博龐克風格")
    print("4. 完成！現在左滑右滑都能看到視窗")
    
    print("\n🎮 方法二：Mission Control")
    print("1. 在監控器中按 T 鍵顯示標題欄")
    print("2. 按 Control + ↑ 鍵進入 Mission Control")
    print("3. 找到加密貨幣監控器視窗")
    print("4. 拖拽視窗到螢幕頂部的 '所有桌面' 區域")
    print("5. 按 T 鍵隱藏標題欄，恢復風格")
    
    print("\n⚙️ 方法三：系統偏好設定")
    print("1. 打開 系統偏好設定 → Mission Control")
    print("2. 取消勾選 '根據最近的使用情況自動重新排列Spaces'")
    print("3. 這樣可以讓視窗行為更穩定")
    
    print("\n🧪 測試方法：")
    print("• 使用 Control + ← 或 Control + → 切換桌面")
    print("• 或用三指左滑右滑切換桌面")
    print("• 確認監控器視窗在每個桌面都可見")
    
    print("\n💡 小提示：")
    print("• 無邊框視窗（overrideredirect）在Mission Control中會消失")
    print("• 必須先按 T 鍵顯示標題欄才能設定跨桌面")
    print("• 設定完成後，視窗會自動在所有桌面顯示")
    print("• 這個設定會記住，下次啟動時仍然有效")
    print("• 可以隨時按 T 鍵切換標題欄顯示/隱藏")
    
    print("="*60)

def open_mission_control():
    """開啟Mission Control幫助用戶設定"""
    try:
        print("\n🎮 正在開啟Mission Control...")
        print("請在Mission Control中將監控器視窗拖拽到 '所有桌面' 區域")
        
        # 使用AppleScript開啟Mission Control
        applescript = '''
        tell application "System Events"
            key code 126 using {control down}
        end tell
        '''
        
        result = subprocess.run([
            'osascript', '-e', applescript
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✅ Mission Control已開啟")
            print("💡 請將監控器視窗拖拽到頂部的 '所有桌面' 區域")
            return True
        else:
            print(f"❌ 開啟Mission Control失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 開啟Mission Control時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🌐 加密貨幣監控器跨Spaces設定工具")
    print("讓監控器在所有桌面空間中顯示")
    print("-" * 50)
    
    # 檢查監控器是否運行
    if not check_crypto_monitor_running():
        print("\n❌ 請先啟動加密貨幣監控器：")
        print("   python crypto_floating_window.py")
        print("\n然後再運行此設定工具")
        return
    
    # 顯示設定說明
    show_setup_instructions()
    
    # 詢問是否要開啟Mission Control
    print("\n❓ 是否要開啟Mission Control進行設定？")
    choice = input("輸入 'y' 開啟，或按Enter跳過: ").lower().strip()
    
    if choice == 'y':
        open_mission_control()
        print("\n⏳ 請在Mission Control中完成設定...")
        print("設定完成後按Enter繼續...")
        input()
    
    print("\n🧪 現在可以測試跨桌面功能：")
    print("• 使用 Control + ← → 切換桌面")
    print("• 或用三指左滑右滑")
    print("• 確認監控器在每個桌面都可見")
    
    print("\n✅ 設定完成！")
    print("💡 如果還有問題，可以在監控器中按 'S' 鍵查看更多選項")

if __name__ == "__main__":
    main() 
    