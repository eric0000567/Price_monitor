#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time
import json
import os
import sys
import platform
from datetime import datetime
import subprocess

class CryptoFloatingWindow:
    def __init__(self):
        print("🚀 正在初始化賽博龐克加密貨幣監控器...")
        
        # 載入配置
        self.load_config()
        
        # 初始化資料
        self.crypto_data = {}
        self.running = True
        self.current_crypto_index = 0  # 當前顯示的加密貨幣索引
        
        # 賽博龐克配色方案
        self.colors = {
            'bg_primary': '#0a0a0a',      # 深黑背景
            'bg_secondary': '#1a1a2e',    # 深藍背景
            'accent_cyan': '#00ffff',     # 霓虹青色
            'accent_pink': '#ff00ff',     # 霓虹粉色
            'accent_green': '#00ff41',    # 霓虹綠色
            'accent_red': '#ff073a',      # 霓虹紅色
            'text_primary': '#ffffff',    # 主要文字
            'text_secondary': '#888888',  # 次要文字
            'border': '#333333',          # 邊框
            'glow': '#00ffff'            # 發光效果
        }
        
        # 建立懸浮視窗
        self.setup_window()
        
        # 啟動價格更新執行緒
        self.start_price_updates()
        
        print("✅ 賽博龐克監控器已啟動")
        
    def load_config(self):
        """載入配置檔案"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.trading_pairs = config.get('trading_pairs', ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT'])
                    self.update_interval = config.get('update_interval', 30)
                    print(f"📄 已載入配置：監控 {len(self.trading_pairs)} 種交易對")
            else:
                self.trading_pairs = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT']
                self.update_interval = 30
                print("📄 使用預設配置")
        except Exception as e:
            print(f"⚠️ 載入配置時發生錯誤: {e}")
            self.trading_pairs = ['BTCUSDT', 'ETHUSDT']
            self.update_interval = 30
            
        # 建立交易對到顯示名稱的映射
        self.pair_to_name = {
            'BTCUSDT': 'BITCOIN',
            'ETHUSDT': 'ETHEREUM', 
            'ADAUSDT': 'CARDANO',
            'SOLUSDT': 'SOLANA',
            'DOGEUSDT': 'DOGECOIN',
            'BNBUSDT': 'BINANCE',
            'XRPUSDT': 'RIPPLE',
            'DOTUSDT': 'POLKADOT',
            'LINKUSDT': 'CHAINLINK',
            'LTCUSDT': 'LITECOIN',
            'BCHUSDT': 'BITCOIN CASH',
            'UNIUSDT': 'UNISWAP',
            'AVAXUSDT': 'AVALANCHE',
            'MATICUSDT': 'POLYGON'
        }
        
        # 貨幣符號映射
        self.pair_to_symbol = {
            'BTCUSDT': '₿',
            'ETHUSDT': 'Ξ', 
            'ADAUSDT': '₳',
            'SOLUSDT': '◎',
            'DOGEUSDT': 'Ð',
            'BNBUSDT': '⬡',
            'XRPUSDT': '✕',
            'DOTUSDT': '●',
            'LINKUSDT': '⬢',
            'LTCUSDT': 'Ł',
            'BCHUSDT': '₿',
            'UNIUSDT': '🦄',
            'AVAXUSDT': '▲',
            'MATICUSDT': '⬟'
        }
    
    def setup_window(self):
        """設置賽博龐克風格懸浮視窗"""
        print("🔧 正在建立賽博龐克視窗...")
        
        self.root = tk.Tk()
        self.root.title("⚡ CRYPTO MONITOR")
        
        # 檢查作業系統和Python環境
        system = platform.system()
        python_info = "Conda" if "conda" in sys.executable.lower() else "Standard"
        print(f"🖥️ 檢測到作業系統: {system}")
        print(f"🐍 Python環境: {python_info}")
        
        # 基本視窗設定 - 更小更簡約
        self.root.geometry("200x280+100+100")
        self.root.resizable(False, False)
        self.root.configure(bg=self.colors['bg_primary'])
        
        # 移除標題欄，打造無邊框賽博龐克風格
        # 注意：為了能在Mission Control中設定跨Spaces，我們需要保留標題欄
        # 可以通過按 'T' 鍵切換標題欄顯示
        self.show_titlebar = False
        if not self.show_titlebar:
            self.root.overrideredirect(True)
        
        # 強制顯示視窗 - 第一步
        self.root.deiconify()
        self.root.update()
        
        # 針對macOS的特殊處理
        if system == "Darwin":  # macOS
            print("🍎 正在針對macOS優化視窗設定...")
            print("🌐 設定視窗跨越所有Spaces/桌面...")
            
            # 分階段設定，避免macOS的視窗顯示問題
            self.root.lift()
            self.root.focus_force()
            
            # 延遲設定topmost，這是關鍵
            def set_topmost_delayed():
                try:
                    self.root.attributes('-topmost', True)
                    self.root.lift()
                    print("🔧 已設定視窗置頂")
                except Exception as e:
                    print(f"⚠️ 設定置頂失敗: {e}")
            
            # 延遲設定透明度
            def set_alpha_delayed():
                try:
                    self.root.attributes('-alpha', 0.92)
                    print("🔧 已設定視窗透明度")
                except Exception as e:
                    print(f"⚠️ 設定透明度失敗: {e}")
            
            # macOS跨Spaces設定 - 使用AppleScript方法
            def set_spaces_behavior():
                try:
                    # 方法1: 嘗試tkinter的原生方法
                    self.root.wm_attributes('-type', 'utility')
                    self.root.wm_attributes('-modified', False)
                    print("🌐 已設定視窗跨越所有Spaces (方法1)")
                except Exception as e:
                    print(f"⚠️ 方法1失敗: {e}")
                
                # 方法2: 使用AppleScript設定視窗行為
                try:
                    self.set_window_spaces_behavior_applescript()
                except Exception as e:
                    print(f"⚠️ AppleScript方法失敗: {e}")
            
            # 分階段執行
            self.root.after(200, set_topmost_delayed)
            self.root.after(400, set_alpha_delayed)
            self.root.after(600, set_spaces_behavior)
            
            # 最終強制顯示
            self.root.after(1000, self.force_window_visible)
            
        else:
            # 非macOS系統的標準設定
            self.root.attributes('-topmost', True)
            self.root.attributes('-alpha', 0.92)
            self.root.lift()
        
        # 創建賽博龐克界面
        self.create_cyberpunk_interface(system, python_info)
        
        # 綁定事件
        self.bind_drag_events()
        self.bind_keyboard_events()
        
        print(f"✅ 賽博龐克視窗已建立 ({system} + {python_info})")
    
    def create_cyberpunk_interface(self, system, python_info):
        """創建賽博龐克風格界面"""
        # 主容器 - 帶邊框發光效果
        main_frame = tk.Frame(
            self.root, 
            bg=self.colors['bg_primary'],
            highlightbackground=self.colors['accent_cyan'],
            highlightthickness=1
        )
        main_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # 標題欄 - 可拖拽
        self.title_frame = tk.Frame(
            main_frame, 
            bg=self.colors['bg_secondary'], 
            height=25
        )
        self.title_frame.pack(fill='x')
        self.title_frame.pack_propagate(False)
        
        # 標題文字 - 像素風格
        title_label = tk.Label(
            self.title_frame,
            text="⚡ CRYPTO MONITOR ⚡",
            bg=self.colors['bg_secondary'],
            fg=self.colors['accent_cyan'],
            font=('Courier New', 8, 'bold')
        )
        title_label.pack(pady=3)
        
        # 關閉按鈕
        close_btn = tk.Label(
            self.title_frame,
            text="✕",
            bg=self.colors['bg_secondary'],
            fg=self.colors['accent_red'],
            font=('Courier New', 10, 'bold'),
            cursor='hand2'
        )
        close_btn.place(relx=1.0, rely=0.5, anchor='e', x=-8)
        close_btn.bind('<Button-1>', lambda e: self.close_window())
        
        # 主要顯示區域
        display_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        display_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        # 貨幣符號顯示 - 大字體
        self.crypto_symbol_label = tk.Label(
            display_frame,
            text="₿",
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_cyan'],
            font=('Courier New', 32, 'bold')
        )
        self.crypto_symbol_label.pack(pady=(10, 5))
        
        # 貨幣名稱
        self.crypto_name_label = tk.Label(
            display_frame,
            text="BITCOIN",
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            font=('Courier New', 10, 'bold')
        )
        self.crypto_name_label.pack()
        
        # 價格顯示 - 主要數據
        self.price_label = tk.Label(
            display_frame,
            text="$0.00",
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_green'],
            font=('Courier New', 16, 'bold')
        )
        self.price_label.pack(pady=(10, 5))
        
        # 變化百分比
        self.change_label = tk.Label(
            display_frame,
            text="+0.00%",
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_green'],
            font=('Courier New', 12, 'bold')
        )
        self.change_label.pack()
        
        # 狀態指示器
        self.status_label = tk.Label(
            display_frame,
            text="● LOADING",
            bg=self.colors['bg_primary'],
            fg=self.colors['text_secondary'],
            font=('Courier New', 8)
        )
        self.status_label.pack(pady=(10, 5))
        
        # 時間戳
        self.time_label = tk.Label(
            display_frame,
            text="00:00:00",
            bg=self.colors['bg_primary'],
            fg=self.colors['text_secondary'],
            font=('Courier New', 8)
        )
        self.time_label.pack()
        
        # 控制按鈕區域
        control_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        control_frame.pack(fill='x', padx=8, pady=(0, 8))
        
        # 上一個按鈕
        prev_btn = tk.Label(
            control_frame,
            text="◀",
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_pink'],
            font=('Courier New', 12, 'bold'),
            cursor='hand2'
        )
        prev_btn.pack(side='left')
        prev_btn.bind('<Button-1>', lambda e: self.previous_crypto())
        
        # 貨幣計數器
        self.counter_label = tk.Label(
            control_frame,
            text="1/5",
            bg=self.colors['bg_primary'],
            fg=self.colors['text_secondary'],
            font=('Courier New', 8)
        )
        self.counter_label.pack(side='left', padx=(10, 10))
        
        # 下一個按鈕
        next_btn = tk.Label(
            control_frame,
            text="▶",
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_pink'],
            font=('Courier New', 12, 'bold'),
            cursor='hand2'
        )
        next_btn.pack(side='left')
        next_btn.bind('<Button-1>', lambda e: self.next_crypto())
        
        # 重新整理按鈕
        refresh_btn = tk.Label(
            control_frame,
            text="⟲",
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_cyan'],
            font=('Courier New', 12, 'bold'),
            cursor='hand2'
        )
        refresh_btn.pack(side='right')
        refresh_btn.bind('<Button-1>', lambda e: self.manual_refresh())
        
        # 綁定拖拽到標題欄和主符號
        self.bind_drag_to_widget(self.title_frame)
        self.bind_drag_to_widget(title_label)
        self.bind_drag_to_widget(self.crypto_symbol_label)
    
    def bind_keyboard_events(self):
        """綁定鍵盤事件"""
        self.root.bind('<Left>', lambda e: self.previous_crypto())
        self.root.bind('<Right>', lambda e: self.next_crypto())
        self.root.bind('<space>', lambda e: self.manual_refresh())
        self.root.bind('<s>', lambda e: self.toggle_spaces_behavior())
        self.root.bind('<S>', lambda e: self.toggle_spaces_behavior())
        self.root.bind('<t>', lambda e: self.toggle_titlebar())
        self.root.bind('<T>', lambda e: self.toggle_titlebar())
        self.root.bind('<Escape>', lambda e: self.close_window())
        self.root.focus_set()
        
        print("⌨️ 鍵盤控制已啟用:")
        print("   ← → : 切換加密貨幣")
        print("   空白: 重新整理")
        print("   S   : 顯示跨Spaces設定指導")
        print("   T   : 切換標題欄顯示（用於設定跨Spaces）")
        print("   ESC : 關閉程式")
        print()
        print("🌐 重要提醒：要讓視窗在所有桌面顯示，請手動設定：")
        print("   步驟1: 按 T 鍵顯示標題欄")
        print("   步驟2: 右鍵點擊視窗 → 指定給 → 所有桌面")
        print("   步驟3: 按 T 鍵隱藏標題欄，恢復賽博龐克風格")
        print("   或者: Control+↑ 進入Mission Control，拖拽到「所有桌面」")
    
    def next_crypto(self):
        """切換到下一個加密貨幣"""
        if self.trading_pairs:
            self.current_crypto_index = (self.current_crypto_index + 1) % len(self.trading_pairs)
            self.update_current_crypto_display()
            print(f"🔄 切換到: {self.trading_pairs[self.current_crypto_index]}")
    
    def previous_crypto(self):
        """切換到上一個加密貨幣"""
        if self.trading_pairs:
            self.current_crypto_index = (self.current_crypto_index - 1) % len(self.trading_pairs)
            self.update_current_crypto_display()
            print(f"🔄 切換到: {self.trading_pairs[self.current_crypto_index]}")
    
    def update_current_crypto_display(self):
        """更新當前顯示的加密貨幣"""
        if not self.trading_pairs:
            return
            
        current_pair = self.trading_pairs[self.current_crypto_index]
        
        # 更新符號
        symbol = self.pair_to_symbol.get(current_pair, '?')
        self.crypto_symbol_label.config(text=symbol)
        
        # 更新名稱
        name = self.pair_to_name.get(current_pair, current_pair)
        self.crypto_name_label.config(text=name)
        
        # 更新計數器
        counter_text = f"{self.current_crypto_index + 1}/{len(self.trading_pairs)}"
        self.counter_label.config(text=counter_text)
        
        # 如果有價格資料，更新價格顯示
        if current_pair in self.crypto_data:
            self.update_price_display_single(current_pair)
    
    def update_price_display_single(self, pair):
        """更新單個貨幣的價格顯示"""
        try:
            if pair not in self.crypto_data:
                return
                
            data = self.crypto_data[pair]
            price = data['price']
            change_24h = data['change_24h']
            
            # 格式化價格
            if price >= 1:
                price_text = f"${price:,.2f}"
            else:
                price_text = f"${price:.6f}"
            
            # 更新價格
            self.price_label.config(text=price_text)
            
            # 判斷漲跌並設定顏色
            if change_24h >= 0:
                color = self.colors['accent_green']
                change_text = f"+{change_24h:.2f}%"
                status_text = "● BULLISH"
            else:
                color = self.colors['accent_red']
                change_text = f"{change_24h:.2f}%"
                status_text = "● BEARISH"
            
            # 更新變化百分比
            self.change_label.config(text=change_text, fg=color)
            
            # 更新狀態
            self.status_label.config(text=status_text, fg=color)
            
            # 更新時間
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.config(text=current_time)
            
        except Exception as e:
            print(f"❌ 更新價格顯示時發生錯誤: {e}")
    
    def bind_drag_to_widget(self, widget):
        """為組件綁定拖拽功能"""
        def start_drag(event):
            self.drag_start_x = event.x
            self.drag_start_y = event.y
        
        def drag_window(event):
            x = self.root.winfo_pointerx() - self.drag_start_x
            y = self.root.winfo_pointery() - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")
        
        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", drag_window)
    
    def force_window_visible(self):
        """強制視窗可見（macOS專用增強版）"""
        try:
            # 多重強制顯示策略
            self.root.attributes('-topmost', False)
            self.root.update()
            self.root.attributes('-topmost', True)
            self.root.lift()
            self.root.focus_force()
            
            # macOS特定：確保在所有Spaces中可見
            try:
                # 重新設定utility類型以確保跨Spaces行為
                self.root.wm_attributes('-type', 'utility')
                
                # 嘗試使用macOS特定的視窗樣式
                self.root.call('::tk::unsupported::MacWindowStyle', 'style', self.root._w, 'utility', 'none')
                
                print("🌐 已確保視窗在所有Spaces中可見")
            except Exception as e:
                print(f"⚠️ 設定跨Spaces行為時發生錯誤: {e}")
            
            # 更新狀態指示器
            self.status_label.config(text="● ONLINE", fg=self.colors['accent_cyan'])
            
            print("✅ macOS視窗強制顯示完成")
            print("🌐 視窗現在應該在所有Spaces/桌面中可見")
            print("💡 如果仍然看不到，請檢查系統偏好設定 > Mission Control")
            
        except Exception as e:
            print(f"⚠️ 強制顯示視窗時發生錯誤: {e}")
            self.status_label.config(text="● ERROR", fg=self.colors['accent_red'])
    
    def get_crypto_prices(self):
        """從幣安API獲取加密貨幣價格"""
        try:
            print(f"🔄 正在從幣安獲取 {len(self.trading_pairs)} 種交易對的價格...")
            
            # 獲取24小時價格統計
            url = "https://api.binance.com/api/v3/ticker/24hr"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            all_data = response.json()
            
            # 篩選我們需要的交易對
            filtered_data = {}
            for item in all_data:
                if item['symbol'] in self.trading_pairs:
                    filtered_data[item['symbol']] = {
                        'price': float(item['lastPrice']),
                        'change_24h': float(item['priceChangePercent']),
                        'high_24h': float(item['highPrice']),
                        'low_24h': float(item['lowPrice']),
                        'volume': float(item['volume'])
                    }
            
            if not filtered_data:
                print("⚠️ 幣安API回傳空資料")
                return False
                
            self.crypto_data = filtered_data
            print(f"✅ 成功從幣安獲取 {len(filtered_data)} 種交易對的價格")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"🌐 網路錯誤: {e}")
            return False
        except Exception as e:
            print(f"❌ 獲取價格時發生錯誤: {e}")
            return False
    
    def price_update_worker(self):
        """背景執行緒持續更新價格"""
        print("🔄 價格更新執行緒已啟動")
        while self.running:
            try:
                if self.get_crypto_prices():
                    # 使用after方法在主執行緒中更新UI
                    current_pair = self.trading_pairs[self.current_crypto_index] if self.trading_pairs else None
                    if current_pair:
                        self.root.after(0, lambda: self.update_price_display_single(current_pair))
                else:
                    print("⚠️ 更新失敗，將在下次間隔後重試")
                    self.root.after(0, lambda: self.status_label.config(text="● OFFLINE", fg=self.colors['accent_red']))
                
                # 等待指定間隔
                for _ in range(self.update_interval):
                    if not self.running:
                        return
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ 價格更新執行緒發生錯誤: {e}")
                self.root.after(0, lambda: self.status_label.config(text="● ERROR", fg=self.colors['accent_red']))
                for _ in range(30):
                    if not self.running:
                        return
                    time.sleep(1)
        
        print("🛑 價格更新執行緒已停止")
    
    def start_price_updates(self):
        """啟動價格更新執行緒"""
        print("🚀 正在啟動價格更新執行緒...")
        self.update_thread = threading.Thread(target=self.price_update_worker, daemon=True)
        self.update_thread.start()
        
        # 立即執行一次更新
        initial_update_thread = threading.Thread(target=self.initial_update, daemon=True)
        initial_update_thread.start()
    
    def initial_update(self):
        """初始價格更新"""
        if self.get_crypto_prices():
            current_pair = self.trading_pairs[self.current_crypto_index] if self.trading_pairs else None
            if current_pair:
                self.root.after(0, lambda: self.update_price_display_single(current_pair))
                self.root.after(0, self.update_current_crypto_display)
    
    def manual_refresh(self):
        """手動重新整理"""
        print("🔄 手動重新整理價格...")
        self.status_label.config(text="● SYNCING", fg=self.colors['accent_cyan'])
        refresh_thread = threading.Thread(target=self.initial_update, daemon=True)
        refresh_thread.start()
    
    def bind_drag_events(self):
        """綁定拖曳事件（保留以兼容）"""
        pass  # 拖拽功能已在create_cyberpunk_interface中實現
    
    def show_settings(self):
        """顯示設定對話框（賽博龐克風格）"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ SETTINGS")
        settings_window.geometry("250x150")
        settings_window.attributes('-topmost', True)
        settings_window.configure(bg=self.colors['bg_primary'])
        settings_window.overrideredirect(True)
        
        # 主框架
        main_frame = tk.Frame(
            settings_window,
            bg=self.colors['bg_primary'],
            highlightbackground=self.colors['accent_pink'],
            highlightthickness=1
        )
        main_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # 標題
        tk.Label(
            main_frame,
            text="⚙️ SETTINGS",
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_pink'],
            font=('Courier New', 10, 'bold')
        ).pack(pady=10)
        
        # 更新間隔設定
        tk.Label(
            main_frame,
            text="UPDATE INTERVAL (SEC):",
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            font=('Courier New', 8)
        ).pack(pady=5)
        
        interval_var = tk.StringVar(value=str(self.update_interval))
        interval_entry = tk.Entry(
            main_frame,
            textvariable=interval_var,
            width=10,
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Courier New', 10),
            justify='center'
        )
        interval_entry.pack(pady=5)
        
        # 按鈕框架
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        btn_frame.pack(pady=10)
        
        def save_settings():
            try:
                new_interval = int(interval_var.get())
                if new_interval >= 10:
                    self.update_interval = new_interval
                    print(f"⚙️ 更新間隔已設為 {new_interval} 秒")
                    settings_window.destroy()
                else:
                    print("❌ 更新間隔不能少於10秒")
            except ValueError:
                print("❌ 請輸入有效的數字")
        
        # 儲存按鈕
        save_btn = tk.Label(
            btn_frame,
            text="SAVE",
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_green'],
            font=('Courier New', 8, 'bold'),
            cursor='hand2'
        )
        save_btn.pack(side='left', padx=5)
        save_btn.bind('<Button-1>', lambda e: save_settings())
        
        # 取消按鈕
        cancel_btn = tk.Label(
            btn_frame,
            text="CANCEL",
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_red'],
            font=('Courier New', 8, 'bold'),
            cursor='hand2'
        )
        cancel_btn.pack(side='right', padx=5)
        cancel_btn.bind('<Button-1>', lambda e: settings_window.destroy())
    
    def minimize_window(self):
        """最小化視窗"""
        self.root.iconify()
    
    def close_window(self):
        """關閉視窗"""
        print("👋 正在關閉賽博龐克監控器...")
        self.running = False
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
    
    def run(self):
        """執行應用程式"""
        print("🚀 賽博龐克監控器已啟動")
        print("📱 視窗將始終顯示在最前面")
        print(f"🔄 價格將每 {self.update_interval} 秒自動更新")
        print("💡 現在使用幣安API，響應速度更快！")
        print("🎮 控制說明:")
        print("   ← → 方向鍵: 切換加密貨幣")
        print("   空白鍵: 手動重新整理")
        print("   ESC鍵: 關閉程式")
        print("   拖拽: 點擊符號或標題欄移動視窗")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n👋 使用者中斷")
            self.close_window()

    def toggle_spaces_behavior(self):
        """切換跨Spaces行為（新增功能）"""
        try:
            print("🌐 正在設定視窗跨越所有Spaces...")
            self.status_label.config(text="● SETTING", fg=self.colors['accent_cyan'])
            
            # 方法1: 重新設定視窗類型
            self.root.wm_attributes('-type', 'utility')
            self.root.attributes('-topmost', True)
            self.root.lift()
            
            # 方法2: 使用系統命令強制設定
            self.force_spaces_behavior_system_command()
            
            # 方法3: 顯示手動設定指導
            self.show_spaces_setup_guide()
            
            print("🌐 已重新設定跨Spaces行為")
            self.status_label.config(text="● SPACES OK", fg=self.colors['accent_cyan'])
            
            # 3秒後恢復正常狀態顯示
            self.root.after(3000, lambda: self.status_label.config(text="● ONLINE", fg=self.colors['accent_cyan']))
            
        except Exception as e:
            print(f"⚠️ 切換Spaces行為失敗: {e}")
            self.status_label.config(text="● SPACES ERR", fg=self.colors['accent_red'])
    
    def force_spaces_behavior_system_command(self):
        """使用系統命令強制設定跨Spaces行為"""
        try:
            pid = os.getpid()
            
            # 方法1: 使用defaults命令設定應用程式行為
            app_name = f"Python.{pid}"
            
            # 設定應用程式在所有Spaces中可見
            subprocess.run([
                'defaults', 'write', app_name, 
                'NSWindowCollectionBehavior', '-int', '1'
            ], capture_output=True, text=True)
            
            print("🌐 已使用defaults命令設定跨Spaces行為")
            
            # 方法2: 使用AppleScript強制設定視窗屬性
            applescript = f'''
            tell application "System Events"
                set targetApp to first application process whose unix id is {pid}
                tell targetApp
                    set frontmost to true
                    try
                        tell front window
                            -- 強制視窗在所有桌面顯示
                            set properties to {{collection behavior:{{can join all spaces:true, full screen auxiliary:true}}}}
                        end tell
                    on error
                        -- 如果上面失敗，嘗試簡單的方法
                        set frontmost to true
                    end try
                end tell
            end tell
            '''
            
            result = subprocess.run([
                'osascript', '-e', applescript
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("🌐 AppleScript強制設定成功")
            else:
                print(f"⚠️ AppleScript強制設定失敗: {result.stderr}")
            
            # 方法3: 使用更直接的系統命令
            self.set_window_sticky_all_desktops()
            
        except Exception as e:
            print(f"⚠️ 系統命令設定失敗: {e}")
    
    def set_window_sticky_all_desktops(self):
        """設定視窗在所有桌面上顯示（sticky）"""
        try:
            # 獲取視窗ID
            window_id = self.root.winfo_id()
            
            # 使用yabai或其他視窗管理工具（如果有安裝）
            try:
                subprocess.run([
                    'yabai', '-m', 'window', str(window_id), 
                    '--toggle', 'sticky'
                ], capture_output=True, text=True, timeout=3)
                print("🌐 已使用yabai設定sticky視窗")
            except:
                pass
            
            # 嘗試使用Hammerspoon API（如果有安裝）
            try:
                hammerspoon_script = f'''
                hs.window.find({window_id}):setSticky(true)
                '''
                subprocess.run([
                    'hs', '-c', hammerspoon_script
                ], capture_output=True, text=True, timeout=3)
                print("🌐 已使用Hammerspoon設定sticky視窗")
            except:
                pass
                
            print("🌐 已嘗試所有可用的視窗管理方法")
            
        except Exception as e:
            print(f"⚠️ 設定sticky視窗失敗: {e}")
    
    def show_spaces_setup_guide(self):
        """顯示跨Spaces設定指導"""
        try:
            # 創建指導視窗
            guide_window = tk.Toplevel(self.root)
            guide_window.title("🌐 跨Spaces設定指導")
            guide_window.geometry("400x300+200+200")
            guide_window.attributes('-topmost', True)
            guide_window.configure(bg=self.colors['bg_primary'])
            guide_window.overrideredirect(True)
            
            # 主框架
            main_frame = tk.Frame(
                guide_window,
                bg=self.colors['bg_primary'],
                highlightbackground=self.colors['accent_pink'],
                highlightthickness=2
            )
            main_frame.pack(fill='both', expand=True, padx=4, pady=4)
            
            # 標題
            title_label = tk.Label(
                main_frame,
                text="🌐 設定視窗在所有桌面顯示",
                bg=self.colors['bg_primary'],
                fg=self.colors['accent_pink'],
                font=('Courier New', 12, 'bold')
            )
            title_label.pack(pady=10)
            
            # 說明文字
            instructions = [
                "⚠️ 重要：tkinter無邊框視窗需要特殊處理",
                "",
                "📋 推薦方法（3步驟）：",
                "1. 按 T 鍵顯示標題欄",
                "2. 右鍵點擊 → '指定給' → '所有桌面'",
                "3. 按 T 鍵隱藏標題欄，恢復風格",
                "",
                "🎮 或者 Mission Control方法：",
                "1. 按 T 鍵顯示標題欄",
                "2. 按 Control + ↑ 進入Mission Control",
                "3. 拖拽視窗到 '所有桌面' 區域",
                "4. 按 T 鍵隱藏標題欄",
                "",
                "✅ 設定完成後可左滑右滑測試"
            ]
            
            for instruction in instructions:
                color = self.colors['accent_cyan'] if instruction.startswith(('📋', '🎮', '✅')) else self.colors['text_primary']
                label = tk.Label(
                    main_frame,
                    text=instruction,
                    bg=self.colors['bg_primary'],
                    fg=color,
                    font=('Courier New', 9),
                    anchor='w'
                )
                label.pack(fill='x', padx=20, pady=2)
            
            # 按鈕框架
            btn_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
            btn_frame.pack(pady=20)
            
            # 開啟Mission Control按鈕
            mission_btn = tk.Label(
                btn_frame,
                text="開啟 Mission Control",
                bg=self.colors['bg_secondary'],
                fg=self.colors['accent_cyan'],
                font=('Courier New', 10, 'bold'),
                cursor='hand2',
                padx=10,
                pady=5
            )
            mission_btn.pack(side='left', padx=5)
            mission_btn.bind('<Button-1>', lambda e: self.open_mission_control())
            
            # 關閉按鈕
            close_btn = tk.Label(
                btn_frame,
                text="知道了",
                bg=self.colors['bg_secondary'],
                fg=self.colors['accent_green'],
                font=('Courier New', 10, 'bold'),
                cursor='hand2',
                padx=10,
                pady=5
            )
            close_btn.pack(side='right', padx=5)
            close_btn.bind('<Button-1>', lambda e: guide_window.destroy())
            
            # 5秒後自動關閉
            guide_window.after(15000, guide_window.destroy)
            
            print("📋 已顯示跨Spaces設定指導")
            
        except Exception as e:
            print(f"⚠️ 顯示設定指導失敗: {e}")
    
    def open_mission_control(self):
        """開啟Mission Control"""
        try:
            # 使用AppleScript開啟Mission Control
            applescript = '''
            tell application "System Events"
                key code 126 using {control down}
            end tell
            '''
            
            subprocess.run([
                'osascript', '-e', applescript
            ], capture_output=True, text=True, timeout=5)
            
            print("🎮 已開啟Mission Control")
            
        except Exception as e:
            print(f"⚠️ 開啟Mission Control失敗: {e}")
    
    def toggle_titlebar(self):
        """切換標題欄顯示（用於設定跨Spaces）"""
        try:
            self.show_titlebar = not self.show_titlebar
            
            if self.show_titlebar:
                # 顯示標題欄
                self.root.overrideredirect(False)
                self.root.title("⚡ CRYPTO MONITOR - 右鍵設定跨桌面")
                print("🔧 已顯示標題欄，現在可以右鍵設定「指定給所有桌面」")
                self.status_label.config(text="● TITLEBAR ON", fg=self.colors['accent_pink'])
                
                # 3秒後提示
                self.root.after(3000, lambda: print("💡 設定完成後按 T 鍵隱藏標題欄"))
                
            else:
                # 隱藏標題欄
                self.root.overrideredirect(True)
                print("🎨 已隱藏標題欄，恢復賽博龐克風格")
                self.status_label.config(text="● TITLEBAR OFF", fg=self.colors['accent_cyan'])
                
                # 3秒後恢復正常狀態
                self.root.after(3000, lambda: self.status_label.config(text="● ONLINE", fg=self.colors['accent_cyan']))
            
            # 保持置頂
            self.root.lift()
            self.root.attributes('-topmost', True)
            
        except Exception as e:
            print(f"⚠️ 切換標題欄失敗: {e}")
            self.status_label.config(text="● ERROR", fg=self.colors['accent_red'])

    def set_window_spaces_behavior_applescript(self):
        """使用AppleScript設定視窗在所有Spaces中顯示"""
        try:
            # 獲取當前程序的PID
            pid = os.getpid()
            
            # 修復後的AppleScript - 使用正確的語法
            applescript = f'''
            tell application "System Events"
                set targetProcess to first process whose unix id is {pid}
                tell targetProcess
                    set frontmost to true
                end tell
            end tell
            '''
            
            # 執行AppleScript
            result = subprocess.run([
                'osascript', '-e', applescript
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("🌐 AppleScript設定成功")
                
                # 嘗試更直接的方法 - 使用系統API
                self.set_window_collection_behavior_direct()
                
            else:
                print(f"⚠️ AppleScript執行失敗: {result.stderr}")
                
                # 嘗試替代的AppleScript方法
                self.set_window_spaces_behavior_alternative()
                
        except Exception as e:
            print(f"⚠️ AppleScript設定失敗: {e}")
    
    def set_window_collection_behavior_direct(self):
        """直接使用系統命令設定視窗集合行為"""
        try:
            # 方法1: 使用osascript直接設定視窗屬性
            window_id = self.root.winfo_id()
            
            # 使用JXA (JavaScript for Automation) 而不是AppleScript
            jxa_script = f'''
            var app = Application.currentApplication();
            app.includeStandardAdditions = true;
            
            var SystemEvents = Application("System Events");
            var processes = SystemEvents.processes.whose({{unixId: {os.getpid()}}});
            
            if (processes.length > 0) {{
                var process = processes[0];
                process.frontmost = true;
                
                // 嘗試設定視窗為sticky
                try {{
                    var windows = process.windows;
                    if (windows.length > 0) {{
                        // 這裡我們只能設定基本屬性
                        windows[0].properties = {{}};
                    }}
                }} catch (e) {{
                    // 忽略錯誤
                }}
            }}
            '''
            
            result = subprocess.run([
                'osascript', '-l', 'JavaScript', '-e', jxa_script
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("🌐 JXA腳本執行成功")
            
            # 方法2: 使用更底層的方法
            self.use_low_level_window_management()
            
        except Exception as e:
            print(f"⚠️ 直接設定方法失敗: {e}")
    
    def use_low_level_window_management(self):
        """使用底層視窗管理方法"""
        try:
            # 方法1: 嘗試使用CGWindow API
            self.try_cgwindow_api()
            
            # 方法2: 使用Dock註冊方法
            self.register_with_dock()
            
            # 方法3: 創建一個全域熱鍵來切換視窗顯示
            self.setup_global_hotkey()
            
        except Exception as e:
            print(f"⚠️ 底層視窗管理失敗: {e}")
    
    def try_cgwindow_api(self):
        """嘗試使用Core Graphics Window API"""
        try:
            import ctypes
            from ctypes import cdll, c_int, c_void_p
            
            # 載入Core Graphics框架
            cg = cdll.LoadLibrary('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
            
            # 獲取視窗ID
            window_id = self.root.winfo_id()
            
            print(f"🔧 嘗試使用CGWindow API設定視窗 {window_id}")
            
            # 這裡需要更複雜的實作，暫時作為佔位符
            print("🌐 CGWindow API方法需要更深入的實作")
            
        except Exception as e:
            print(f"⚠️ CGWindow API失敗: {e}")
    
    def register_with_dock(self):
        """向Dock註冊應用程式以獲得更好的視窗管理"""
        try:
            # 創建一個臨時的應用程式包結構
            app_name = "CryptoMonitor"
            
            # 使用defaults命令註冊應用程式
            subprocess.run([
                'defaults', 'write', f'com.user.{app_name}',
                'LSUIElement', '-bool', 'false'
            ], capture_output=True)
            
            subprocess.run([
                'defaults', 'write', f'com.user.{app_name}',
                'NSWindowCollectionBehavior', '-int', '1'
            ], capture_output=True)
            
            print("🌐 已向系統註冊應用程式")
            
        except Exception as e:
            print(f"⚠️ Dock註冊失敗: {e}")
    
    def setup_global_hotkey(self):
        """設定全域熱鍵來強制顯示視窗"""
        try:
            # 創建一個AppleScript來設定全域熱鍵
            hotkey_script = f'''
            on run
                tell application "System Events"
                    set targetProcess to first process whose unix id is {os.getpid()}
                    tell targetProcess
                        set frontmost to true
                        set visible to true
                    end tell
                end tell
            end run
            '''
            
            # 將腳本保存到臨時檔案
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.scpt', delete=False) as f:
                f.write(hotkey_script)
                script_path = f.name
            
            # 編譯AppleScript
            subprocess.run([
                'osacompile', '-o', script_path.replace('.scpt', '.app'), script_path
            ], capture_output=True)
            
            print("🌐 已設定全域熱鍵腳本")
            
            # 清理臨時檔案
            os.unlink(script_path)
            
        except Exception as e:
            print(f"⚠️ 全域熱鍵設定失敗: {e}")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("⚡ 賽博龐克加密貨幣監控器 v3.0 ⚡")
        print("🔄 現在使用幣安 (Binance) API")
        print("🎯 像素風格 - 一次顯示一種貨幣")
        print("🎮 支援鍵盤控制和拖拽操作")
        print("=" * 60)
        
        app = CryptoFloatingWindow()
        app.run()
        
    except Exception as e:
        print(f"❌ 應用程式啟動時發生錯誤: {e}")
        print("請確保您已安裝tkinter套件") 