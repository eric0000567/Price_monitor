#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚡ 加密貨幣選單欄監控器 v4.0 ⚡
🔄 使用幣安 (Binance) API - 精簡版
🌐 選單欄應用 - 跨所有桌面空間顯示
🎯 只獲取當前選擇的加密貨幣，節省網路資源
💰 支援幣安現貨和合約交易功能
"""

import sys
import json
import time
import threading
import requests
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import hashlib
import hmac
import urllib.parse
import os

# 檢查並導入 dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()  # 載入 .env 文件中的環境變數
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# 檢查並導入 rumps
try:
    import rumps
    RUMPS_AVAILABLE = True
except ImportError:
    RUMPS_AVAILABLE = False
    print("❌ rumps 套件未安裝")
    print("請執行: pip install rumps")

# 檢查並導入 python-binance
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("⚠️ python-binance 套件未安裝")
    print("請執行: pip install python-binance")

class CryptoMenuBarMonitor(rumps.App):
    def __init__(self):
        # 載入配置
        self.load_config()
        
        # 基本設置
        super().__init__(name="CryptoMonitor", title="⚡", quit_button=None)
        
        # 狀態變數
        self.running = True
        self.update_thread = None
        self.current_crypto_index = 0
        self.crypto_data = {}
        self.display_mode = "compact"  # compact, full, symbol_only
        
        # 初始化幣安客戶端
        self.init_binance_client()
        
        # 設定選單
        self.setup_menu()
        
        # 啟動價格更新
        self.start_price_updates()
    
    def load_config(self):
        """載入配置檔案"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.trading_pairs = config.get('trading_pairs', [])
            self.update_interval = config.get('update_interval', 30)
            self.price_alert_enabled = config.get('price_alert_enabled', False)
            self.alert_thresholds = config.get('alert_thresholds', {})
            self.alert_cooldown = config.get('alert_cooldown', 300)  # 5分鐘冷卻時間
            
            # 幣安 API 配置
            self.binance_config = config.get('binance_api', {})
            self.trading_settings = config.get('trading_settings', {})
            
            if not self.trading_pairs:
                print("⚠️ 配置檔案中沒有交易對，請檢查 config.json")
                sys.exit(1)
                
        except FileNotFoundError:
            print("❌ 找不到 config.json 配置檔案")
            print("請建立 config.json 檔案並設定要監控的交易對")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 載入配置檔案時發生錯誤: {e}")
            sys.exit(1)
        
        # 交易對映射 - 涵蓋更多幣種
        self.pair_to_symbol = {
            'BTCUSDT': '₿',
            'ETHUSDT': 'Ξ',
            'ADAUSDT': '₳',
            'SOLUSDT': '◎',
            'DOGEUSDT': 'Ð',
            'XRPUSDT': '✕',
            'TRXUSDT': '⚡',
            'LTCUSDT': 'Ł',
            'BCHUSDT': '₿',
            'XLMUSDT': '✪',
            'LINKUSDT': '⬢'
        }
        
        self.pair_to_name = {
            'BTCUSDT': 'Bitcoin',
            'ETHUSDT': 'Ethereum',
            'ADAUSDT': 'Cardano',
            'SOLUSDT': 'Solana',
            'DOGEUSDT': 'Dogecoin',
            'XRPUSDT': 'Ripple',
            'TRXUSDT': 'TRON',
            'LTCUSDT': 'Litecoin',
            'BCHUSDT': 'Bitcoin Cash',
            'XLMUSDT': 'Stellar',
            'LINKUSDT': 'Chainlink'
        }
        
        print(f"📊 監控 {len(self.trading_pairs)} 種加密貨幣")
        print(f"⏰ 更新間隔：{self.update_interval} 秒")
        if self.price_alert_enabled:
            print(f"🚨 價格警報：已啟用（{len(self.alert_thresholds)} 個交易對有設定閾值）")
        else:
            print("🔕 價格警報：已停用")
        
        # 初始化警報狀態追蹤
        self.last_alert_time = {}  # 記錄上次警報時間，避免重複通知
        self.alert_triggered = {}  # 記錄已觸發的警報狀態
    
    def init_binance_client(self):
        """初始化幣安客戶端"""
        self.binance_client = None
        self.trading_enabled = False
        
        if not BINANCE_AVAILABLE:
            print("⚠️ python-binance 套件未安裝，交易功能將被停用")
            return
        
        # 支援環境變數配置，優先順序：環境變數 > config.json
        api_key = os.environ.get('BINANCE_API_KEY') or self.binance_config.get('api_key', '')
        api_secret = os.environ.get('BINANCE_API_SECRET') or self.binance_config.get('api_secret', '')
        testnet = self.binance_config.get('testnet', True)
        trading_enabled = self.binance_config.get('trading_enabled', False)
        
        # 顯示密鑰來源資訊（不顯示實際密鑰內容）
        if os.environ.get('BINANCE_API_KEY'):
            print("🔑 使用環境變數中的 API 密鑰")
        elif api_key:
            print("🔑 使用配置文件中的 API 密鑰")
        else:
            print("⚠️ 未找到 API 密鑰")
        
        if not api_key or not api_secret:
            print("⚠️ 幣安 API 密鑰未設定，交易功能將被停用")
            print("請在 config.json 中設定 binance_api.api_key 和 binance_api.api_secret")
            return
        
        try:
            self.binance_client = Client(
                api_key=api_key,
                api_secret=api_secret,
                testnet=testnet
            )
            
            # 測試連接
            account_info = self.binance_client.get_account()
            self.trading_enabled = trading_enabled
            
            if testnet:
                print("🧪 幣安測試網連接成功")
            else:
                print("🚀 幣安主網連接成功")
            
            if trading_enabled:
                print("💰 交易功能已啟用")
            else:
                print("🔒 交易功能已停用（請在 config.json 中設定 trading_enabled: true）")
                
        except Exception as e:
            print(f"❌ 幣安 API 連接失敗: {e}")
            print("請檢查 API 密鑰是否正確")
            self.binance_client = None
            self.trading_enabled = False
    
    def get_crypto_symbol(self, trading_pair):
        """動態獲取加密貨幣符號"""
        # 先檢查預設映射
        if trading_pair in self.pair_to_symbol:
            return self.pair_to_symbol[trading_pair]
        
        # 如果沒有映射，從交易對名稱提取基礎貨幣符號
        base_currency = trading_pair.replace('USDT', '').replace('BUSD', '').replace('BTC', '').replace('ETH', '')
        
        # 常見的加密貨幣符號映射
        common_symbols = {
            'BNB': '⬡', 'DOT': '●', 'UNI': '🦄', 'AVAX': '▲', 'MATIC': '⬟',
            'SAND': '🏖️', 'MANA': '🌐', 'FTT': '📈', 'NEAR': '🌙', 'ATOM': '⚛️',
            'LTC': 'Ł', 'BCH': '₿', 'ETC': '💎', 'XLM': '✪', 'VET': '🔗',
            'THETA': 'θ', 'FIL': '📁', 'ICP': '♾️', 'SHIB': '🐕', 'CRO': '👑'
        }
        
        if base_currency in common_symbols:
            return common_symbols[base_currency]
        
        # 如果都沒有，使用前 2-3 個字母作為符號
        if len(base_currency) <= 3:
            return base_currency
        else:
            return base_currency[:3]
    
    def get_crypto_name(self, trading_pair):
        """動態獲取加密貨幣名稱"""
        # 先檢查預設映射
        if trading_pair in self.pair_to_name:
            return self.pair_to_name[trading_pair]
        
        # 如果沒有映射，從交易對名稱提取基礎貨幣名稱
        base_currency = trading_pair.replace('USDT', '').replace('BUSD', '').replace('BTC', '').replace('ETH', '')
        
        # 常見的加密貨幣名稱映射
        common_names = {
            'BNB': 'Binance Coin', 'DOT': 'Polkadot', 'UNI': 'Uniswap', 
            'AVAX': 'Avalanche', 'MATIC': 'Polygon', 'SAND': 'The Sandbox',
            'MANA': 'Decentraland', 'FTT': 'FTX Token', 'NEAR': 'Near Protocol',
            'ATOM': 'Cosmos', 'ETC': 'Ethereum Classic', 'VET': 'VeChain',
            'THETA': 'Theta Network', 'FIL': 'Filecoin', 'ICP': 'Internet Computer',
            'SHIB': 'Shiba Inu', 'CRO': 'Cronos', 'ALGO': 'Algorand',
            'FLOW': 'Flow', 'XTZ': 'Tezos', 'EGLD': 'MultiversX'
        }
        
        if base_currency in common_names:
            return common_names[base_currency]
        
        # 如果都沒有，返回基礎貨幣代碼
        return base_currency
    
    def check_price_alerts(self, trading_pair, current_price):
        """檢查價格警報"""
        if not self.price_alert_enabled:
            print(f"🔕 價格警報已停用")
            return
            
        if trading_pair not in self.alert_thresholds:
            print(f"🔍 {trading_pair} 沒有設定警報閾值")
            return
        
        thresholds = self.alert_thresholds[trading_pair]
        high_threshold = thresholds.get('high')
        low_threshold = thresholds.get('low')
        current_time = time.time()
        
        print(f"🔍 檢查 {trading_pair} 價格警報:")
        print(f"   當前價格: ${current_price:,.2f}")
        if high_threshold:
            print(f"   高價閾值: ${high_threshold:,.2f}")
        if low_threshold:
            print(f"   低價閾值: ${low_threshold:,.2f}")
        
        # 檢查是否在冷卻期內
        last_alert = self.last_alert_time.get(trading_pair, 0)
        cooldown_remaining = self.alert_cooldown - (current_time - last_alert)
        if cooldown_remaining > 0:
            print(f"⏰ 警報冷卻中，剩餘 {cooldown_remaining:.0f} 秒")
            return
        
        symbol = self.get_crypto_symbol(trading_pair)
        name = self.get_crypto_name(trading_pair)
        
        alert_sent = False
        
        # 檢查高價警報
        if high_threshold and current_price >= high_threshold:
            alert_key = f"{trading_pair}_high"
            if not self.alert_triggered.get(alert_key, False):
                self.send_price_alert(
                    f"🚨 {symbol} {name} 高價警報！",
                    f"當前價格 ${current_price:,.2f} 已達到或超過設定的高價閾值 ${high_threshold:,.2f}"
                )
                self.alert_triggered[alert_key] = True
                self.last_alert_time[trading_pair] = current_time
                alert_sent = True
                print(f"🚨 {symbol} 高價警報觸發：${current_price:,.2f} >= ${high_threshold:,.2f}")
            else:
                print(f"⏰ {symbol} 高價警報已觸發過，等待重置")
        else:
            # 重置高價警報狀態（當價格低於高價閾值時）
            high_key = f"{trading_pair}_high"
            if self.alert_triggered.get(high_key, False):
                self.alert_triggered[high_key] = False
                print(f"✅ {symbol} 高價警報狀態已重置 (價格: ${current_price:,.2f} < 閾值: ${high_threshold:,.2f})")
        
        # 檢查低價警報
        if low_threshold and current_price <= low_threshold:
            alert_key = f"{trading_pair}_low"
            if not self.alert_triggered.get(alert_key, False):
                self.send_price_alert(
                    f"🚨 {symbol} {name} 低價警報！",
                    f"當前價格 ${current_price:,.2f} 已達到或低於設定的低價閾值 ${low_threshold:,.2f}"
                )
                self.alert_triggered[alert_key] = True
                self.last_alert_time[trading_pair] = current_time
                alert_sent = True
                print(f"🚨 {symbol} 低價警報觸發：${current_price:,.2f} <= ${low_threshold:,.2f}")
            else:
                print(f"⏰ {symbol} 低價警報已觸發過，等待重置")
        else:
            # 重置低價警報狀態（當價格高於低價閾值時）
            low_key = f"{trading_pair}_low"
            if self.alert_triggered.get(low_key, False):
                self.alert_triggered[low_key] = False
                print(f"✅ {symbol} 低價警報狀態已重置 (價格: ${current_price:,.2f} > 閾值: ${low_threshold:,.2f})")
        
        # 如果沒有發送警報，顯示狀態
        if not alert_sent:
            status = "正常範圍"
            if high_threshold and low_threshold:
                status = f"正常範圍 (${low_threshold:,.2f} - ${high_threshold:,.2f})"
            elif high_threshold:
                status = f"低於高價閾值 (< ${high_threshold:,.2f})"
            elif low_threshold:
                status = f"高於低價閾值 (> ${low_threshold:,.2f})"
            print(f"✓ {symbol} 價格 ${current_price:,.2f} 在{status}")
    
    def send_price_alert(self, title, message):
        """發送 macOS 系統通知"""
        print(f"📢 準備發送通知: {title}")
        print(f"📝 通知內容: {message}")
        
        # 方法 1: 使用 osascript（最可靠）
        try:
            import subprocess
            script = f'''
            display notification "{message}" with title "{title}" subtitle "加密貨幣價格監控器" sound name "Glass"
            '''
            result = subprocess.run([
                'osascript', '-e', script
            ], capture_output=True, text=True, check=True)
            print("✅ osascript 通知發送成功")
            return True
        except Exception as e:
            print(f"⚠️ osascript 通知失敗: {e}")
        
        # 方法 2: 使用 rumps 通知
        try:
            rumps.notification(
                title=title,
                subtitle="加密貨幣價格監控器",
                message=message,
                sound=True
            )
            print("✅ rumps 通知發送成功")
            return True
        except Exception as e:
            print(f"⚠️ rumps 通知失敗: {e}")
        
        # 方法 3: 使用 terminal-notifier（如果安裝了）
        try:
            import subprocess
            subprocess.run([
                'terminal-notifier', 
                '-title', title,
                '-subtitle', '加密貨幣價格監控器',
                '-message', message,
                '-sound', 'Glass'
            ], check=True)
            print("✅ terminal-notifier 通知發送成功")
            return True
        except Exception as e:
            print(f"⚠️ terminal-notifier 通知失敗: {e}")
        
        print("❌ 所有通知方法都失敗了")
        return False

    def setup_menu(self):
        """設定選單欄選單"""
        # 主要顯示區域（會動態更新）
        self.price_menu = rumps.MenuItem("⏳ 載入中...", callback=None)
        self.menu.add(self.price_menu)
        
        # 詳細資訊子選單
        self.detail_submenu = rumps.MenuItem("📈 詳細資訊")
        self.detail_price = rumps.MenuItem("💰 現價：載入中...", callback=None)
        self.detail_change = rumps.MenuItem("📊 24h 變化：載入中...", callback=None)
        self.detail_high = rumps.MenuItem("⬆️ 24h 最高：載入中...", callback=None)
        self.detail_low = rumps.MenuItem("⬇️ 24h 最低：載入中...", callback=None)
        self.detail_volume = rumps.MenuItem("📈 成交量：載入中...", callback=None)
        self.detail_time = rumps.MenuItem("🔄 更新時間：載入中...", callback=None)
        
        self.detail_submenu.add(self.detail_price)
        self.detail_submenu.add(self.detail_change)
        self.detail_submenu.add(self.detail_high)
        self.detail_submenu.add(self.detail_low)
        self.detail_submenu.add(self.detail_volume)
        self.detail_submenu.add(rumps.separator)
        self.detail_submenu.add(self.detail_time)
        self.menu.add(self.detail_submenu)
        
        # 分隔線
        self.menu.add(rumps.separator)
        
        # 顯示模式切換
        self.display_submenu = rumps.MenuItem("🎨 顯示模式")
        self.mode_compact = rumps.MenuItem("🔸 簡潔模式", callback=self.set_compact_mode)
        self.mode_full = rumps.MenuItem("🔹 完整模式", callback=self.set_full_mode)
        self.mode_symbol_only = rumps.MenuItem("🔺 僅符號", callback=self.set_symbol_only_mode)
        self.display_submenu.add(self.mode_compact)
        self.display_submenu.add(self.mode_full)
        self.display_submenu.add(self.mode_symbol_only)
        self.menu.add(self.display_submenu)
        
        # 分隔線
        self.menu.add(rumps.separator)
        
        # 加密貨幣選擇子選單
        self.crypto_submenu = rumps.MenuItem("💰 選擇加密貨幣")
        for i, pair in enumerate(self.trading_pairs):
            name = self.get_crypto_name(pair)
            symbol = self.get_crypto_symbol(pair)
            menu_item = rumps.MenuItem(
                f"{symbol} {name}",
                callback=self.create_crypto_callback(i)
            )
            self.crypto_submenu.add(menu_item)
        self.menu.add(self.crypto_submenu)
        
        # 分隔線
        self.menu.add(rumps.separator)
        
        # 交易功能選單
        if self.trading_enabled and self.binance_client:
            self.trading_submenu = rumps.MenuItem("💰 交易功能")
            
            # 現貨交易
            self.spot_trading_submenu = rumps.MenuItem("📈 現貨交易")
            self.spot_trading_submenu.add(rumps.MenuItem("🟢 市價買入", callback=self.spot_market_buy))
            self.spot_trading_submenu.add(rumps.MenuItem("🔴 市價賣出", callback=self.spot_market_sell))
            self.spot_trading_submenu.add(rumps.MenuItem("🎯 限價買入", callback=self.spot_limit_buy))
            self.spot_trading_submenu.add(rumps.MenuItem("🎯 限價賣出", callback=self.spot_limit_sell))
            self.trading_submenu.add(self.spot_trading_submenu)
            
            # 合約交易
            self.futures_trading_submenu = rumps.MenuItem("⚡ 合約交易")
            self.futures_trading_submenu.add(rumps.MenuItem("📈 做多", callback=self.futures_long))
            self.futures_trading_submenu.add(rumps.MenuItem("📉 做空", callback=self.futures_short))
            self.futures_trading_submenu.add(rumps.MenuItem("🔄 平倉", callback=self.futures_close))
            self.trading_submenu.add(self.futures_trading_submenu)
            
            # 帳戶資訊
            self.trading_submenu.add(rumps.separator)
            self.trading_submenu.add(rumps.MenuItem("💼 帳戶餘額", callback=self.show_account_balance))
            self.trading_submenu.add(rumps.MenuItem("📊 持倉資訊", callback=self.show_positions))
            self.trading_submenu.add(rumps.MenuItem("📋 訂單紀錄", callback=self.show_orders))
            
            self.menu.add(self.trading_submenu)
            self.menu.add(rumps.separator)
        
        # 重新整理按鈕
        self.menu.add(rumps.MenuItem("🔄 重新整理", callback=self.manual_refresh))
        
        # 警報設定按鈕
        if self.price_alert_enabled:
            self.menu.add(rumps.MenuItem("🚨 警報設定", callback=self.show_alert_settings))
            self.menu.add(rumps.MenuItem("🔔 測試通知", callback=self.test_notification))
            self.menu.add(rumps.MenuItem("⚡ 立即檢查警報", callback=self.check_alerts_now))
        
        # 分隔線
        self.menu.add(rumps.separator)
        
        # 退出按鈕
        self.menu.add(rumps.MenuItem("❌ 退出", callback=self.quit_app))
        
        # 設定初始模式狀態
        self.mode_compact.state = True
    
    def create_crypto_callback(self, index):
        """創建加密貨幣切換回調函數"""
        def callback(sender):
            self.current_crypto_index = index
            # 立即更新顯示
            self.manual_refresh(None)
            # 更新選單項目的勾選狀態
            for i, item in enumerate(self.crypto_submenu.keys()):
                self.crypto_submenu[item].state = (i == index)
        return callback
    
    def set_compact_mode(self, sender):
        """設定簡潔模式"""
        self.display_mode = "compact"
        self.update_mode_states("compact")
        self.update_display()
        print("🔸 已切換到簡潔模式")
    
    def set_full_mode(self, sender):
        """設定完整模式"""
        self.display_mode = "full"
        self.update_mode_states("full")
        self.update_display()
        print("🔹 已切換到完整模式")
    
    def set_symbol_only_mode(self, sender):
        """設定僅符號模式"""
        self.display_mode = "symbol_only"
        self.update_mode_states("symbol_only")
        self.update_display()
        print("🔺 已切換到僅符號模式")
    
    def update_mode_states(self, current_mode):
        """更新模式選項的勾選狀態"""
        self.mode_compact.state = (current_mode == "compact")
        self.mode_full.state = (current_mode == "full")
        self.mode_symbol_only.state = (current_mode == "symbol_only")
    
    def get_prices_for_alerts(self):
        """獲取所有有設定警報的交易對價格"""
        if not self.price_alert_enabled or not self.alert_thresholds:
            return True
            
        # 獲取所有有設定警報的交易對
        alert_pairs = list(self.alert_thresholds.keys())
        print(f"🚨 檢查 {len(alert_pairs)} 個設定了警報的交易對: {alert_pairs}")
        
        for pair in alert_pairs:
            try:
                print(f"🔄 正在獲取 {pair} 的價格用於警報檢查...")
                
                url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                current_price = float(data['lastPrice'])
                
                # 檢查價格警報
                self.check_price_alerts(pair, current_price)
                
            except Exception as e:
                print(f"❌ 獲取 {pair} 價格失敗: {e}")
        
        return True

    def get_current_crypto_price(self):
        """只獲取當前選擇的加密貨幣價格 - 節省網路資源"""
        if not self.trading_pairs:
            return False
            
        current_pair = self.trading_pairs[self.current_crypto_index]
        
        try:
            print(f"🔄 正在獲取 {current_pair} 的價格...")
            
            # 只獲取當前選擇的交易對的24小時價格統計
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={current_pair}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 更新當前加密貨幣的資料
            current_price = float(data['lastPrice'])
            self.crypto_data[current_pair] = {
                'price': current_price,
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume': float(data['volume'])
            }
            
            print(f"✅ 成功獲取 {current_pair} 的價格")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"🌐 網路錯誤: {e}")
            return False
        except Exception as e:
            print(f"❌ 獲取價格時發生錯誤: {e}")
            return False
    
    def update_display(self):
        """更新選單欄顯示"""
        current_pair = self.trading_pairs[self.current_crypto_index]
        
        if current_pair not in self.crypto_data:
            self.title = "⚡"
            self.price_menu.title = "⏳ 載入中..."
            return
        
        data = self.crypto_data[current_pair]
        symbol = self.get_crypto_symbol(current_pair)
        name = self.get_crypto_name(current_pair)
        
        # 格式化價格 - 根據顯示模式使用不同格式
        price = data['price']
        
        # 為簡潔模式和完整模式提供更詳細的價格顯示
        if self.display_mode in ["compact", "full"]:
            # 簡潔模式和完整模式：顯示完整數字和小數點
            if price >= 1000:
                price_str = f"${price:,.2f}"  # 如 $67,234.56
            elif price >= 1:
                price_str = f"${price:.2f}"   # 如 $123.45
            elif price >= 0.0001:
                price_str = f"${price:.4f}"   # 如 $0.1234
            else:
                price_str = f"${price:.6f}"   # 如 $0.000123
        else:
            # 僅符號模式：使用簡化格式節省空間
            if price >= 1000000:
                price_str = f"${price/1000000:.1f}M"
            elif price >= 1000:
                price_str = f"${price/1000:.0f}K"
            elif price >= 1:
                price_str = f"${price:.0f}"
            else:
                price_str = f"${price:.4f}"
        
        # 漲跌狀態
        change_24h = data['change_24h']
        if change_24h > 0:
            change_emoji = "🟢"
            change_str = f"+{change_24h:.2f}%"
        elif change_24h < 0:
            change_emoji = "🔴"
            change_str = f"{change_24h:.2f}%"
        else:
            change_emoji = "⚪"
            change_str = "0.00%"
        
        # 根據顯示模式更新選單欄標題
        if self.display_mode == "symbol_only":
            self.title = symbol
        elif self.display_mode == "compact":
            self.title = f"{symbol} {price_str}"
        else:  # full mode
            self.title = f"{symbol} {price_str} {change_str}"
        
        # 更新詳細資訊選單項目 - 使用緊湊的格式避免被截斷
        detail_info = f"📊 {symbol} {name} | 💰 {price_str} | {change_emoji} {change_str} | 🔄 {datetime.now().strftime('%H:%M:%S')}"
        self.price_menu.title = detail_info
        
        # 更新詳細資訊子選單
        current_time = datetime.now().strftime('%H:%M:%S')
        self.detail_price.title = f"💰 現價：{price_str}"
        self.detail_change.title = f"📊 24h 變化：{change_str}"
        self.detail_high.title = f"⬆️ 24h 最高：${data['high_24h']:,.2f}"
        self.detail_low.title = f"⬇️ 24h 最低：${data['low_24h']:,.2f}"
        self.detail_volume.title = f"📈 成交量：{self.format_volume(data['volume'])}"
        self.detail_time.title = f"🔄 更新時間：{current_time}"
    
    def format_volume(self, volume):
        """格式化成交量顯示"""
        if volume >= 1000000000:
            return f"{volume/1000000000:.2f}B"
        elif volume >= 1000000:
            return f"{volume/1000000:.2f}M"
        elif volume >= 1000:
            return f"{volume/1000:.2f}K"
        else:
            return f"{volume:.2f}"
    
    def price_update_worker(self):
        """背景執行緒持續更新價格"""
        print("🔄 價格更新執行緒已啟動")
        while self.running:
            try:
                # 更新當前顯示的加密貨幣價格
                if self.get_current_crypto_price():
                    # 直接在背景執行緒中更新顯示（rumps 是執行緒安全的）
                    self.update_display()
                else:
                    print("⚠️ 顯示價格更新失敗")
                
                # 檢查所有設定了警報的交易對
                self.get_prices_for_alerts()
                
                # 等待指定間隔
                for _ in range(self.update_interval):
                    if not self.running:
                        return
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ 價格更新執行緒發生錯誤: {e}")
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
        if self.get_current_crypto_price():
            self.update_display()
        # 立即檢查警報
        self.get_prices_for_alerts()
    
    def manual_refresh(self, sender):
        """手動重新整理"""
        print("🔄 手動重新整理價格...")
        def refresh_with_alerts():
            self.initial_update()
        refresh_thread = threading.Thread(target=refresh_with_alerts, daemon=True)
        refresh_thread.start()
    
    def show_alert_settings(self, sender):
        """顯示警報設定對話框"""
        current_pair = self.trading_pairs[self.current_crypto_index]
        symbol = self.get_crypto_symbol(current_pair)
        name = self.get_crypto_name(current_pair)
        
        # 獲取當前閾值
        current_thresholds = self.alert_thresholds.get(current_pair, {})
        current_high = current_thresholds.get('high', '')
        current_low = current_thresholds.get('low', '')
        
        # 顯示高價閾值設定對話框
        high_response = rumps.Window(
            title="🚨 設定高價警報",
            message=f"為 {symbol} {name} 設定高價警報閾值：\n（當價格達到或超過此值時發送通知）",
            default_text=str(current_high) if current_high else "",
            ok="設定",
            cancel="跳過",
            dimensions=(350, 120)
        ).run()
        
        # 顯示低價閾值設定對話框
        low_response = rumps.Window(
            title="🚨 設定低價警報", 
            message=f"為 {symbol} {name} 設定低價警報閾值：\n（當價格達到或低於此值時發送通知）",
            default_text=str(current_low) if current_low else "",
            ok="設定",
            cancel="跳過",
            dimensions=(350, 120)
        ).run()
        
        # 處理設定結果
        try:
            if current_pair not in self.alert_thresholds:
                self.alert_thresholds[current_pair] = {}
            
            updated = False
            
            # 處理高價閾值
            if high_response.clicked == 1 and high_response.text.strip():
                try:
                    high_value = float(high_response.text.strip())
                    self.alert_thresholds[current_pair]['high'] = high_value
                    updated = True
                    print(f"🚨 {symbol} 高價警報閾值設定為：${high_value:,.2f}")
                except ValueError:
                    rumps.alert("❌ 錯誤", "高價閾值必須是有效數字")
            
            # 處理低價閾值
            if low_response.clicked == 1 and low_response.text.strip():
                try:
                    low_value = float(low_response.text.strip())
                    self.alert_thresholds[current_pair]['low'] = low_value
                    updated = True
                    print(f"🚨 {symbol} 低價警報閾值設定為：${low_value:,.2f}")
                except ValueError:
                    rumps.alert("❌ 錯誤", "低價閾值必須是有效數字")
            
            if updated:
                # 重置該交易對的警報狀態
                high_key = f"{current_pair}_high"
                low_key = f"{current_pair}_low"
                self.alert_triggered[high_key] = False
                self.alert_triggered[low_key] = False
                
                # 儲存配置到檔案
                self.save_alert_config()
                rumps.alert("✅ 完成", f"{symbol} {name} 的警報設定已更新")
            
        except Exception as e:
            rumps.alert("❌ 錯誤", f"設定警報時發生錯誤: {e}")
    
    def save_alert_config(self):
        """儲存警報配置到檔案"""
        try:
            # 讀取現有配置
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新警報設定
            config['alert_thresholds'] = self.alert_thresholds
            
            # 寫入檔案
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print("📄 警報配置已儲存到 config.json")
            
        except Exception as e:
            print(f"⚠️ 儲存警報配置失敗: {e}")
    
    def test_notification(self, sender):
        """測試通知功能"""
        print("🔔 測試通知功能...")
        success = self.send_price_alert(
            "🔔 測試通知",
            "如果您看到這個通知，表示警報功能正常運作！"
        )
        
        if success:
            rumps.alert("✅ 成功", "通知測試成功！您應該已經收到系統通知。")
        else:
            rumps.alert("❌ 失敗", "通知測試失敗。請檢查系統通知權限設定。")
    
    def check_alerts_now(self, sender):
        """立即檢查所有警報"""
        print("⚡ 立即檢查所有價格警報...")
        self.get_prices_for_alerts()
        rumps.alert("✅ 完成", "已完成立即警報檢查，請查看終端輸出了解詳情。")
    
    # ==================== 交易功能方法 ====================
    
    def show_trading_dialog(self, order_type, side, symbol=None):
        """顯示交易對話框"""
        if symbol is None:
            symbol = self.trading_pairs[self.current_crypto_index]
        
        # 創建主窗口
        root = tk.Tk()
        root.title(f"幣安交易 - {order_type} {side}")
        root.geometry("400x500")
        root.resizable(False, False)
        
        # 使用變數來儲存結果
        result = {'confirmed': False}
        
        # 標題
        title_frame = tk.Frame(root)
        title_frame.pack(pady=10)
        tk.Label(title_frame, text=f"📈 {order_type} {side}", font=("Arial", 16, "bold")).pack()
        tk.Label(title_frame, text=symbol, font=("Arial", 14)).pack()
        
        # 獲取當前價格
        current_price = 0
        if symbol in self.crypto_data:
            current_price = self.crypto_data[symbol]['price']
        
        tk.Label(title_frame, text=f"當前價格: ${current_price:,.6f}", font=("Arial", 12)).pack()
        
        # 交易參數框架
        params_frame = tk.LabelFrame(root, text="交易參數", font=("Arial", 12))
        params_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # 數量/金額
        tk.Label(params_frame, text="數量 (USDT):", font=("Arial", 10)).pack(anchor="w", padx=10, pady=(10,0))
        quantity_var = tk.StringVar(value=str(self.trading_settings.get('default_quantity_usdt', 10)))
        quantity_entry = tk.Entry(params_frame, textvariable=quantity_var, font=("Arial", 10))
        quantity_entry.pack(fill="x", padx=10, pady=(0,10))
        
        # 價格 (限價訂單才顯示)
        price_frame = tk.Frame(params_frame)
        if "限價" in order_type:
            price_frame.pack(fill="x", padx=10, pady=(0,10))
            tk.Label(price_frame, text="限價 (USDT):", font=("Arial", 10)).pack(anchor="w")
            price_var = tk.StringVar(value=str(current_price))
            price_entry = tk.Entry(price_frame, textvariable=price_var, font=("Arial", 10))
            price_entry.pack(fill="x")
        else:
            price_var = None
        
        # 槓桿 (合約交易才顯示)
        leverage_frame = tk.Frame(params_frame)
        if "合約" in order_type:
            leverage_frame.pack(fill="x", padx=10, pady=(0,10))
            tk.Label(leverage_frame, text="槓桿倍數:", font=("Arial", 10)).pack(anchor="w")
            leverage_var = tk.IntVar(value=self.trading_settings.get('default_leverage', 1))
            leverage_scale = tk.Scale(leverage_frame, from_=1, to=20, orient="horizontal", variable=leverage_var)
            leverage_scale.pack(fill="x")
        else:
            leverage_var = None
        
        # 止盈止損設定
        sl_tp_frame = tk.LabelFrame(params_frame, text="止盈止損設定", font=("Arial", 10))
        sl_tp_frame.pack(fill="x", pady=10)
        
        # 止損
        enable_sl_var = tk.BooleanVar()
        sl_frame = tk.Frame(sl_tp_frame)
        sl_frame.pack(fill="x", padx=10, pady=5)
        tk.Checkbutton(sl_frame, text="啟用止損", variable=enable_sl_var, font=("Arial", 9)).pack(anchor="w")
        sl_var = tk.StringVar(value=str(self.trading_settings.get('default_stop_loss_percentage', 5)))
        tk.Label(sl_frame, text="止損百分比 (%):", font=("Arial", 9)).pack(anchor="w")
        sl_entry = tk.Entry(sl_frame, textvariable=sl_var, font=("Arial", 9))
        sl_entry.pack(fill="x")
        
        # 止盈
        enable_tp_var = tk.BooleanVar()
        tp_frame = tk.Frame(sl_tp_frame)
        tp_frame.pack(fill="x", padx=10, pady=5)
        tk.Checkbutton(tp_frame, text="啟用止盈", variable=enable_tp_var, font=("Arial", 9)).pack(anchor="w")
        tp_var = tk.StringVar(value=str(self.trading_settings.get('default_take_profit_percentage', 10)))
        tk.Label(tp_frame, text="止盈百分比 (%):", font=("Arial", 9)).pack(anchor="w")
        tp_entry = tk.Entry(tp_frame, textvariable=tp_var, font=("Arial", 9))
        tp_entry.pack(fill="x")
        
        # 確認按鈕
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)
        
        def confirm_order():
            try:
                # 收集所有參數
                params = {
                    'symbol': symbol,
                    'order_type': order_type,
                    'side': side,
                    'quantity': float(quantity_var.get()),
                    'price': float(price_var.get()) if price_var else None,
                    'leverage': leverage_var.get() if leverage_var else None,
                    'stop_loss': {
                        'enabled': enable_sl_var.get(),
                        'percentage': float(sl_var.get()) if enable_sl_var.get() else None
                    },
                    'take_profit': {
                        'enabled': enable_tp_var.get(),
                        'percentage': float(tp_var.get()) if enable_tp_var.get() else None
                    }
                }
                result['params'] = params
                result['confirmed'] = True
                root.destroy()
            except ValueError as e:
                messagebox.showerror("錯誤", f"參數輸入錯誤: {e}")
        
        def cancel_order():
            result['confirmed'] = False
            root.destroy()
        
        tk.Button(button_frame, text="確認下單", command=confirm_order, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=12).pack(side="left", padx=5)
        tk.Button(button_frame, text="取消", command=cancel_order, bg="#f44336", fg="white", font=("Arial", 12), width=12).pack(side="left", padx=5)
        
        # 顯示對話框
        root.mainloop()
        
        return result
    
    def execute_order(self, params):
        """執行訂單"""
        try:
            symbol = params['symbol']
            order_type = params['order_type']
            side = params['side']
            quantity = params['quantity']
            price = params.get('price')
            leverage = params.get('leverage')
            
            print(f"🔄 正在執行 {order_type} {side} 訂單...")
            print(f"交易對: {symbol}")
            print(f"數量: {quantity} USDT")
            if price:
                print(f"價格: {price}")
            if leverage:
                print(f"槓桿: {leverage}x")
            
            # 根據訂單類型執行不同的交易
            if "現貨" in order_type:
                result = self.execute_spot_order(params)
            elif "合約" in order_type:
                result = self.execute_futures_order(params)
            else:
                raise Exception("未知的訂單類型")
            
            # 設定止盈止損
            if result and (params['stop_loss']['enabled'] or params['take_profit']['enabled']):
                self.set_stop_loss_take_profit(result, params)
            
            return result
            
        except Exception as e:
            print(f"❌ 執行訂單失敗: {e}")
            messagebox.showerror("交易失敗", str(e))
            return None
    
    def execute_spot_order(self, params):
        """執行現貨訂單"""
        symbol = params['symbol']
        side = params['side'].replace('買入', 'BUY').replace('賣出', 'SELL')
        quantity = params['quantity']
        price = params.get('price')
        
        # 計算實際購買的幣種數量
        if side == 'BUY':
            if "市價" in params['order_type']:
                # 市價買入：用 USDT 數量買入
                order = self.binance_client.order_market_buy(
                    symbol=symbol,
                    quoteOrderQty=quantity
                )
            else:
                # 限價買入：計算能買多少幣
                coin_quantity = quantity / price
                order = self.binance_client.order_limit_buy(
                    symbol=symbol,
                    quantity=coin_quantity,
                    price=str(price)
                )
        else:
            # 賣出時需要先獲得持倉數量
            account = self.binance_client.get_account()
            coin_symbol = symbol.replace('USDT', '')
            balance = 0
            
            for asset in account['balances']:
                if asset['asset'] == coin_symbol:
                    balance = float(asset['free'])
                    break
            
            if balance <= 0:
                raise Exception(f"沒有足夠的 {coin_symbol} 餘額")
            
            if "市價" in params['order_type']:
                # 市價賣出：賣出所有餘額
                order = self.binance_client.order_market_sell(
                    symbol=symbol,
                    quantity=balance
                )
            else:
                # 限價賣出
                coin_quantity = min(balance, quantity / price)
                order = self.binance_client.order_limit_sell(
                    symbol=symbol,
                    quantity=coin_quantity,
                    price=str(price)
                )
        
        print(f"✅ 現貨訂單執行成功: {order['orderId']}")
        return order
    
    def execute_futures_order(self, params):
        """執行合約訂單"""
        symbol = params['symbol']
        side = params['side'].replace('做多', 'BUY').replace('做空', 'SELL').replace('平倉', 'CLOSE')
        quantity = params['quantity']
        leverage = params.get('leverage', 1)
        
        # 設定槓桿
        self.binance_client.futures_change_leverage(symbol=symbol, leverage=leverage)
        
        # 計算合約數量
        current_price = self.crypto_data[symbol]['price']
        contract_quantity = quantity / current_price
        
        if side == 'CLOSE':
            # 平倉：獲取當前持倉
            positions = self.binance_client.futures_position_information(symbol=symbol)
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    position_side = 'SELL' if float(pos['positionAmt']) > 0 else 'BUY'
                    order = self.binance_client.futures_create_order(
                        symbol=symbol,
                        side=position_side,
                        type='MARKET',
                        quantity=abs(float(pos['positionAmt']))
                    )
                    print(f"✅ 合約平倉成功: {order['orderId']}")
                    return order
        else:
            # 開倉
            order = self.binance_client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=contract_quantity
            )
            print(f"✅ 合約訂單執行成功: {order['orderId']}")
            return order
        
        return None
    
    def set_stop_loss_take_profit(self, order, params):
        """設定止盈止損"""
        try:
            if "現貨" in params['order_type']:
                # 現貨止盈止損 (OCO 訂單)
                pass  # 需要更複雜的邏輯
            elif "合約" in params['order_type']:
                # 合約止盈止損
                symbol = params['symbol']
                current_price = self.crypto_data[symbol]['price']
                
                if params['stop_loss']['enabled']:
                    sl_percentage = params['stop_loss']['percentage']
                    if 'BUY' in order.get('side', ''):
                        sl_price = current_price * (1 - sl_percentage / 100)
                    else:
                        sl_price = current_price * (1 + sl_percentage / 100)
                    
                    self.binance_client.futures_create_order(
                        symbol=symbol,
                        side='SELL' if 'BUY' in order.get('side', '') else 'BUY',
                        type='STOP_MARKET',
                        stopPrice=sl_price,
                        closePosition=True
                    )
                    print(f"✅ 止損訂單設定成功: {sl_price}")
                
                if params['take_profit']['enabled']:
                    tp_percentage = params['take_profit']['percentage']
                    if 'BUY' in order.get('side', ''):
                        tp_price = current_price * (1 + tp_percentage / 100)
                    else:
                        tp_price = current_price * (1 - tp_percentage / 100)
                    
                    self.binance_client.futures_create_order(
                        symbol=symbol,
                        side='SELL' if 'BUY' in order.get('side', '') else 'BUY',
                        type='TAKE_PROFIT_MARKET',
                        stopPrice=tp_price,
                        closePosition=True
                    )
                    print(f"✅ 止盈訂單設定成功: {tp_price}")
                    
        except Exception as e:
            print(f"⚠️ 設定止盈止損失敗: {e}")
    
    # ==================== 現貨交易方法 ====================
    
    def spot_market_buy(self, sender):
        """現貨市價買入"""
        if not self.trading_enabled:
            rumps.alert("交易功能未啟用", "請先在 config.json 中設定 trading_enabled: true")
            return
        
        result = self.show_trading_dialog("現貨市價", "買入")
        if result['confirmed']:
            if self.trading_settings.get('order_confirmation', True):
                if rumps.alert("確認下單", f"確定要執行現貨市價買入嗎？\n數量: {result['params']['quantity']} USDT", ok="確認", cancel="取消") != 1:
                    return
            self.execute_order(result['params'])
    
    def spot_market_sell(self, sender):
        """現貨市價賣出"""
        if not self.trading_enabled:
            rumps.alert("交易功能未啟用", "請先在 config.json 中設定 trading_enabled: true")
            return
        
        result = self.show_trading_dialog("現貨市價", "賣出")
        if result['confirmed']:
            if self.trading_settings.get('order_confirmation', True):
                if rumps.alert("確認下單", f"確定要執行現貨市價賣出嗎？", ok="確認", cancel="取消") != 1:
                    return
            self.execute_order(result['params'])
    
    def spot_limit_buy(self, sender):
        """現貨限價買入"""
        if not self.trading_enabled:
            rumps.alert("交易功能未啟用", "請先在 config.json 中設定 trading_enabled: true")
            return
        
        result = self.show_trading_dialog("現貨限價", "買入")
        if result['confirmed']:
            if self.trading_settings.get('order_confirmation', True):
                if rumps.alert("確認下單", f"確定要執行現貨限價買入嗎？\n數量: {result['params']['quantity']} USDT\n價格: {result['params']['price']}", ok="確認", cancel="取消") != 1:
                    return
            self.execute_order(result['params'])
    
    def spot_limit_sell(self, sender):
        """現貨限價賣出"""
        if not self.trading_enabled:
            rumps.alert("交易功能未啟用", "請先在 config.json 中設定 trading_enabled: true")
            return
        
        result = self.show_trading_dialog("現貨限價", "賣出")
        if result['confirmed']:
            if self.trading_settings.get('order_confirmation', True):
                if rumps.alert("確認下單", f"確定要執行現貨限價賣出嗎？\n價格: {result['params']['price']}", ok="確認", cancel="取消") != 1:
                    return
            self.execute_order(result['params'])
    
    # ==================== 合約交易方法 ====================
    
    def futures_long(self, sender):
        """合約做多"""
        if not self.trading_enabled:
            rumps.alert("交易功能未啟用", "請先在 config.json 中設定 trading_enabled: true")
            return
        
        result = self.show_trading_dialog("合約交易", "做多")
        if result['confirmed']:
            if self.trading_settings.get('order_confirmation', True):
                if rumps.alert("確認下單", f"確定要執行合約做多嗎？\n數量: {result['params']['quantity']} USDT\n槓桿: {result['params']['leverage']}x", ok="確認", cancel="取消") != 1:
                    return
            self.execute_order(result['params'])
    
    def futures_short(self, sender):
        """合約做空"""
        if not self.trading_enabled:
            rumps.alert("交易功能未啟用", "請先在 config.json 中設定 trading_enabled: true")
            return
        
        result = self.show_trading_dialog("合約交易", "做空")
        if result['confirmed']:
            if self.trading_settings.get('order_confirmation', True):
                if rumps.alert("確認下單", f"確定要執行合約做空嗎？\n數量: {result['params']['quantity']} USDT\n槓桿: {result['params']['leverage']}x", ok="確認", cancel="取消") != 1:
                    return
            self.execute_order(result['params'])
    
    def futures_close(self, sender):
        """合約平倉"""
        if not self.trading_enabled:
            rumps.alert("交易功能未啟用", "請先在 config.json 中設定 trading_enabled: true")
            return
        
        result = self.show_trading_dialog("合約交易", "平倉")
        if result['confirmed']:
            if self.trading_settings.get('order_confirmation', True):
                if rumps.alert("確認平倉", "確定要平倉所有持倉嗎？", ok="確認", cancel="取消") != 1:
                    return
            self.execute_order(result['params'])
    
    # ==================== 帳戶資訊方法 ====================
    
    def show_account_balance(self, sender):
        """顯示帳戶餘額"""
        if not self.binance_client:
            rumps.alert("錯誤", "幣安客戶端未初始化")
            return
        
        try:
            # 現貨餘額
            account = self.binance_client.get_account()
            spot_balances = []
            for asset in account['balances']:
                free = float(asset['free'])
                locked = float(asset['locked'])
                if free > 0 or locked > 0:
                    spot_balances.append(f"{asset['asset']}: {free + locked:.8f} (可用: {free:.8f})")
            
            # 合約餘額
            futures_account = self.binance_client.futures_account()
            futures_balance = float(futures_account['totalWalletBalance'])
            
            balance_info = f"💼 帳戶餘額\n\n📈 現貨餘額:\n" + "\n".join(spot_balances[:10])
            if len(spot_balances) > 10:
                balance_info += f"\n... 還有 {len(spot_balances) - 10} 個幣種"
            
            balance_info += f"\n\n⚡ 合約餘額:\n總餘額: {futures_balance:.2f} USDT"
            
            rumps.alert("帳戶餘額", balance_info)
            
        except Exception as e:
            rumps.alert("錯誤", f"獲取帳戶餘額失敗: {str(e)}")
    
    def show_positions(self, sender):
        """顯示持倉資訊"""
        if not self.binance_client:
            rumps.alert("錯誤", "幣安客戶端未初始化")
            return
        
        try:
            positions = self.binance_client.futures_position_information()
            active_positions = []
            
            for pos in positions:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    unrealized_pnl = float(pos['unrealizedPnl'])
                    mark_price = float(pos['markPrice'])
                    entry_price = float(pos['entryPrice'])
                    
                    direction = "多單" if position_amt > 0 else "空單"
                    pnl_color = "📈" if unrealized_pnl >= 0 else "📉"
                    
                    active_positions.append(
                        f"{pos['symbol']}: {direction}\n"
                        f"  數量: {abs(position_amt):.6f}\n"
                        f"  開倉價: {entry_price:.6f}\n"
                        f"  現價: {mark_price:.6f}\n"
                        f"  {pnl_color} 未實現盈虧: {unrealized_pnl:.2f} USDT"
                    )
            
            if active_positions:
                positions_info = "📊 持倉資訊\n\n" + "\n\n".join(active_positions)
            else:
                positions_info = "📊 持倉資訊\n\n目前沒有持倉"
            
            rumps.alert("持倉資訊", positions_info)
            
        except Exception as e:
            rumps.alert("錯誤", f"獲取持倉資訊失敗: {str(e)}")
    
    def show_orders(self, sender):
        """顯示訂單紀錄"""
        if not self.binance_client:
            rumps.alert("錯誤", "幣安客戶端未初始化")
            return
        
        try:
            symbol = self.trading_pairs[self.current_crypto_index]
            
            # 獲取最近的現貨訂單
            spot_orders = self.binance_client.get_all_orders(symbol=symbol, limit=5)
            
            # 獲取最近的合約訂單
            futures_orders = self.binance_client.futures_get_all_orders(symbol=symbol, limit=5)
            
            orders_info = f"📋 {symbol} 最近訂單\n\n"
            
            if spot_orders:
                orders_info += "📈 現貨訂單:\n"
                for order in spot_orders[-3:]:  # 最近3筆
                    status = "✅" if order['status'] == 'FILLED' else "⏰" if order['status'] == 'NEW' else "❌"
                    orders_info += f"{status} {order['side']} {order['type']} - {order['origQty']} @ {order['price']}\n"
            
            if futures_orders:
                orders_info += "\n⚡ 合約訂單:\n"
                for order in futures_orders[-3:]:  # 最近3筆
                    status = "✅" if order['status'] == 'FILLED' else "⏰" if order['status'] == 'NEW' else "❌"
                    orders_info += f"{status} {order['side']} {order['type']} - {order['origQty']} @ {order['price']}\n"
            
            rumps.alert("訂單紀錄", orders_info)
            
        except Exception as e:
            rumps.alert("錯誤", f"獲取訂單紀錄失敗: {str(e)}")

    def quit_app(self, sender):
        """退出應用程式"""
        print("🛑 正在關閉加密貨幣監控器...")
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)
        rumps.quit_application()

def main():
    """主函數"""
    print("=" * 60)
    print("⚡ 加密貨幣選單欄監控器 v4.0 ⚡")
    print("🔄 使用幣安 (Binance) API - 精簡版")
    print("🌐 選單欄應用 - 跨所有桌面空間顯示")
    print("🎯 只獲取當前選擇的加密貨幣，節省網路資源")
    print("💰 支援幣安現貨和合約交易功能")
    print("=" * 60)
    
    if not RUMPS_AVAILABLE:
        print("❌ 需要安裝 rumps 套件")
        print("請執行: pip install rumps")
        return 1
    
    if not BINANCE_AVAILABLE:
        print("⚠️ 需要安裝 python-binance 套件")
        print("請執行: pip install python-binance")
        return 1
    
    try:
        app = CryptoMenuBarMonitor()
        app.run()
    except Exception as e:
        print(f"❌ 應用程式啟動時發生錯誤: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 