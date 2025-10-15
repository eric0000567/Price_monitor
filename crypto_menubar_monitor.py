#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚡ 加密貨幣選單欄監控器 v4.0 ⚡
🔄 使用幣安 (Binance) API - 精簡版
🌐 選單欄應用 - 跨所有桌面空間顯示
🎯 只獲取當前選擇的加密貨幣，節省網路資源
💰 支援幣安現貨和合約交易功能
📈 新增 K 線圖表功能 - 跟隨滑鼠游標顯示
"""

import sys
import json
import time
import threading
import requests
from datetime import datetime
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
    sys.exit(1)

# 檢查並導入 python-binance
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("⚠️ python-binance 套件未安裝")
    print("請執行: pip install python-binance")

# 檢查並導入圖表相關套件
try:
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    CHART_AVAILABLE = True
except ImportError as e:
    CHART_AVAILABLE = False
    print(f"⚠️ 圖表相關套件未安裝: {e}")
    print("請執行: pip install Pillow")

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
        
        # 價格走勢圖相關變數
        self.chart_visible = False
        self.chart_thread = None
        self.chart_timeframe = "15m"  # 預設時間區間
        self.chart_update_interval = 30  # 更新間隔（秒）
        self.chart_image_path = "/tmp/crypto_chart.png"
        self.preview_process = None  # 預覽程式進程
        
        # 時間區間設定（區間：[幣安K線間隔, K線數量, 顯示名稱, 更新間隔(秒)]）
        self.timeframe_settings = {
            "1m": ["1m", 60, "1分鐘K", 30],       # 1分鐘K線 x 60根
            "5m": ["5m", 60, "5分鐘K", 60],       # 5分鐘K線 x 60根
            "15m": ["15m", 60, "15分鐘K", 120],   # 15分鐘K線 x 60根
            "1h": ["1h", 60, "1小時K", 300],      # 1小時K線 x 60根
            "4h": ["4h", 60, "4小時K", 600],      # 4小時K線 x 60根
            "1d": ["1d", 60, "1天K", 1800]        # 1天K線 x 60根
        }
        
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
        
        # 價格走勢圖功能
        if CHART_AVAILABLE:
            self.menu.add(rumps.separator)
            self.chart_submenu = rumps.MenuItem("📈 走勢圖")
            self.chart_toggle = rumps.MenuItem("👁️ 顯示走勢圖", callback=self.toggle_chart)
            self.chart_submenu.add(self.chart_toggle)
            
            # 時間區間選擇
            self.chart_submenu.add(rumps.separator)
            self.timeframe_submenu = rumps.MenuItem("⏰ 時間區間")
            self.timeframe_1m = rumps.MenuItem("1分鐘K (60根)", callback=lambda s: self.set_chart_timeframe("1m"))
            self.timeframe_5m = rumps.MenuItem("5分鐘K (60根)", callback=lambda s: self.set_chart_timeframe("5m"))
            self.timeframe_15m = rumps.MenuItem("15分鐘K (60根)", callback=lambda s: self.set_chart_timeframe("15m"))
            self.timeframe_1h = rumps.MenuItem("1小時K (60根)", callback=lambda s: self.set_chart_timeframe("1h"))
            self.timeframe_4h = rumps.MenuItem("4小時K (60根)", callback=lambda s: self.set_chart_timeframe("4h"))
            self.timeframe_1d = rumps.MenuItem("1天K (60根)", callback=lambda s: self.set_chart_timeframe("1d"))
            
            self.timeframe_15m.state = True  # 預設選中 15 分鐘
            
            self.timeframe_submenu.add(self.timeframe_1m)
            self.timeframe_submenu.add(self.timeframe_5m)
            self.timeframe_submenu.add(self.timeframe_15m)
            self.timeframe_submenu.add(self.timeframe_1h)
            self.timeframe_submenu.add(self.timeframe_4h)
            self.timeframe_submenu.add(self.timeframe_1d)
            self.chart_submenu.add(self.timeframe_submenu)
            
            self.menu.add(self.chart_submenu)
        else:
            self.menu.add(rumps.separator)
            self.menu.add(rumps.MenuItem("📈 走勢圖 (需要安裝 Pillow)", callback=None))
        
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
        """使用 osascript 顯示警報設定對話框，解決焦點問題"""
        current_pair = self.trading_pairs[self.current_crypto_index]
        symbol = self.get_crypto_symbol(current_pair)
        name = self.get_crypto_name(current_pair)
        
        # 獲取當前價格作為參考
        current_price = 0
        if current_pair in self.crypto_data:
            current_price = self.crypto_data[current_pair]['price']
        
        # 獲取當前閾值
        current_thresholds = self.alert_thresholds.get(current_pair, {})
        current_high = current_thresholds.get('high', '')
        current_low = current_thresholds.get('low', '')
        
        import subprocess
        
        try:
            # 設定高價警報閾值
            high_script = f'''
            set userInput to display dialog "為 {symbol} {name} 設定高價警報閾值
            
當前價格: ${current_price:,.6f}
當價格達到或超過設定值時會發送通知
            
請輸入高價警報閾值 (USDT):" default answer "{current_high}" with title "🚨 高價警報設定" buttons {{"跳過", "設定"}} default button "設定"
            if button returned of userInput is "跳過" then
                return "SKIPPED"
            else
                return text returned of userInput
            end if
            '''
            
            high_result = subprocess.run(['osascript', '-e', high_script], capture_output=True, text=True)
            
            # 設定低價警報閾值
            low_script = f'''
            set userInput to display dialog "為 {symbol} {name} 設定低價警報閾值
            
當前價格: ${current_price:,.6f}
當價格達到或低於設定值時會發送通知
            
請輸入低價警報閾值 (USDT):" default answer "{current_low}" with title "🚨 低價警報設定" buttons {{"跳過", "設定"}} default button "設定"
            if button returned of userInput is "跳過" then
                return "SKIPPED"
            else
                return text returned of userInput
            end if
            '''
            
            low_result = subprocess.run(['osascript', '-e', low_script], capture_output=True, text=True)
            
            # 處理設定結果
            if current_pair not in self.alert_thresholds:
                self.alert_thresholds[current_pair] = {}
            
            updated = False
            
            # 處理高價閾值
            if high_result.returncode == 0 and high_result.stdout.strip() not in ["SKIPPED", ""]:
                try:
                    high_value = float(high_result.stdout.strip().replace(',', '').replace(' ', ''))
                    if high_value > 0:
                        self.alert_thresholds[current_pair]['high'] = high_value
                        updated = True
                        print(f"🚨 {symbol} 高價警報閾值設定為：${high_value:,.2f}")
                except ValueError:
                    subprocess.run(['osascript', '-e', 'display alert "錯誤" message "高價閾值必須是有效數字"'], capture_output=True)
            
            # 處理低價閾值
            if low_result.returncode == 0 and low_result.stdout.strip() not in ["SKIPPED", ""]:
                try:
                    low_value = float(low_result.stdout.strip().replace(',', '').replace(' ', ''))
                    if low_value > 0:
                        self.alert_thresholds[current_pair]['low'] = low_value
                        updated = True
                        print(f"🚨 {symbol} 低價警報閾值設定為：${low_value:,.2f}")
                except ValueError:
                    subprocess.run(['osascript', '-e', 'display alert "錯誤" message "低價閾值必須是有效數字"'], capture_output=True)
            
            if updated:
                # 重置該交易對的警報狀態
                high_key = f"{current_pair}_high"
                low_key = f"{current_pair}_low"
                self.alert_triggered[high_key] = False
                self.alert_triggered[low_key] = False
                
                # 儲存配置到檔案
                self.save_alert_config()
                
                # 顯示成功訊息
                success_script = f'''
                display alert "✅ 警報設定完成" message "{symbol} {name} 的警報設定已更新並儲存到 config.json"
                '''
                subprocess.run(['osascript', '-e', success_script], capture_output=True)
                
                print(f"✅ {symbol} {name} 的警報設定已更新並儲存")
            else:
                print("📋 警報設定未變更")
            
        except Exception as e:
            print(f"❌ 設定警報時發生錯誤: {e}")
            # 備用方案：使用 rumps.alert
            try:
                rumps.alert("❌ 錯誤", f"設定警報時發生錯誤: {e}")
            except:
                pass
    
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
        """使用改進的對話框顯示交易設定，解決焦點問題"""
        if symbol is None:
            symbol = self.trading_pairs[self.current_crypto_index]
        
        print(f"🔄 正在顯示 {order_type} {side} 對話框...")
        
        # 獲取當前價格
        current_price = 0
        if symbol in self.crypto_data:
            current_price = self.crypto_data[symbol]['price']
        
        # 獲取預設值
        default_quantity = self.trading_settings.get('default_quantity_usdt', 10)
        default_leverage = self.trading_settings.get('default_leverage', 1)
        default_sl = self.trading_settings.get('default_stop_loss_percentage', 5)
        default_tp = self.trading_settings.get('default_take_profit_percentage', 10)
        
        # 使用系統對話框解決焦點問題
        import subprocess
        
        try:
            # 構建輸入提示
            params_info = []
            params_info.append(f"交易對: {symbol}")
            params_info.append(f"當前價格: ${current_price:,.6f}")
            params_info.append(f"操作: {order_type} {side}")
            params_info.append("")
            params_info.append("請輸入交易數量 (USDT):")
            
            # 使用 osascript 顯示對話框以獲得更好的焦點控制
            script = f'''
            set userInput to display dialog "{chr(10).join(params_info)}" default answer "{default_quantity}" with title "{order_type} {side}" buttons {{"取消", "繼續"}} default button "繼續"
            if button returned of userInput is "取消" then
                return "CANCELLED"
            else
                return text returned of userInput
            end if
            '''
            
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            
            if result.returncode != 0 or result.stdout.strip() == "CANCELLED":
                print("📋 用戶取消了操作")
                return {'confirmed': False}
            
            quantity_text = result.stdout.strip().replace(',', '').replace(' ', '')
            quantity = float(quantity_text)
            if quantity <= 0:
                raise ValueError("數量必須大於 0")
            quantity = f"{quantity:.8f}".rstrip('0').rstrip('.')
            
            # 如果是限價訂單，獲取價格
            price = None
            if "限價" in order_type:
                script = f'''
                set userInput to display dialog "請輸入限價 (USDT):" default answer "{current_price:.6f}" with title "設定限價" buttons {{"取消", "確認"}} default button "確認"
                if button returned of userInput is "取消" then
                    return "CANCELLED"
                else
                    return text returned of userInput
                end if
                '''
                
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                
                if result.returncode != 0 or result.stdout.strip() == "CANCELLED":
                    return {'confirmed': False}
                
                price_text = result.stdout.strip().replace(',', '').replace(' ', '')
                price = float(price_text)
                if price <= 0:
                    raise ValueError("價格必須大於 0")
                price = f"{price:.8f}".rstrip('0').rstrip('.')
            
            # 如果是合約交易，獲取槓桿
            leverage = None
            if "合約" in order_type:
                script = f'''
                set userInput to display dialog "請輸入槓桿倍數 (1-20):" default answer "{default_leverage}" with title "設定槓桿" buttons {{"取消", "確認"}} default button "確認"
                if button returned of userInput is "取消" then
                    return "CANCELLED"
                else
                    return text returned of userInput
                end if
                '''
                
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                
                if result.returncode != 0 or result.stdout.strip() == "CANCELLED":
                    leverage = default_leverage
                else:
                    leverage = int(float(result.stdout.strip()))
                    if leverage < 1 or leverage > 20:
                        leverage = default_leverage
            
            # 簡化止損止盈設定 - 使用預設值或詢問是否啟用
            sl_enabled = False
            sl_percentage = default_sl
            tp_enabled = False  
            tp_percentage = default_tp
            
            # 組合參數
            params = {
                'symbol': symbol,
                'order_type': order_type,
                'side': side,
                'quantity': quantity,
                'price': price,
                'leverage': leverage,
                'stop_loss': {
                    'enabled': sl_enabled,
                    'percentage': sl_percentage
                },
                'take_profit': {
                    'enabled': tp_enabled,
                    'percentage': tp_percentage
                }
            }
            
            print("✅ 交易參數收集完成")
            return {'confirmed': True, 'params': params}
            
        except Exception as e:
            print(f"❌ 對話框錯誤: {e}")
            # 如果 osascript 失敗，回退到簡單的 rumps.alert
            try:
                simple_result = rumps.Window(
                    title=f"{order_type} {side}",
                    message=f"請輸入數量 (USDT):\n交易對: {symbol}\n當前價格: ${current_price:,.6f}",
                    default_text=str(default_quantity),
                    ok="確認",
                    cancel="取消"
                ).run()
                
                if simple_result.clicked == 1:
                    quantity = f"{float(simple_result.text):.8f}".rstrip('0').rstrip('.')
                    params = {
                        'symbol': symbol,
                        'order_type': order_type,
                        'side': side,
                        'quantity': quantity,
                        'price': f"{current_price:.8f}".rstrip('0').rstrip('.') if "限價" in order_type else None,
                        'leverage': default_leverage if "合約" in order_type else None,
                        'stop_loss': {'enabled': False, 'percentage': default_sl},
                        'take_profit': {'enabled': False, 'percentage': default_tp}
                    }
                    return {'confirmed': True, 'params': params}
                else:
                    return {'confirmed': False}
            except:
                return {'confirmed': False}
    
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
            rumps.alert("交易失敗", str(e))
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
                quantity_float = float(quantity)
                formatted_quantity = f"{quantity_float:.8f}".rstrip('0').rstrip('.')
                
                order = self.binance_client.order_market_buy(
                    symbol=symbol,
                    quoteOrderQty=formatted_quantity
                )
            else:
                # 限價買入：計算能買多少幣
                quantity_float = float(quantity)
                price_float = float(price)
                coin_quantity = quantity_float / price_float
                # 格式化數量以符合 Binance API 要求
                formatted_quantity = f"{coin_quantity:.8f}".rstrip('0').rstrip('.')
                formatted_price = f"{price_float:.8f}".rstrip('0').rstrip('.')
                
                order = self.binance_client.order_limit_buy(
                    symbol=symbol,
                    quantity=formatted_quantity,
                    price=formatted_price
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
                formatted_balance = f"{balance:.8f}".rstrip('0').rstrip('.')
                
                order = self.binance_client.order_market_sell(
                    symbol=symbol,
                    quantity=formatted_balance
                )
            else:
                # 限價賣出
                quantity_float = float(quantity)
                price_float = float(price)
                coin_quantity = min(balance, quantity_float / price_float)
                # 格式化數量以符合 Binance API 要求
                formatted_quantity = f"{coin_quantity:.8f}".rstrip('0').rstrip('.')
                formatted_price = f"{price_float:.8f}".rstrip('0').rstrip('.')
                
                order = self.binance_client.order_limit_sell(
                    symbol=symbol,
                    quantity=formatted_quantity,
                    price=formatted_price
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
        quantity_float = float(quantity)
        contract_quantity = quantity_float / current_price
        # 格式化數量以符合 Binance API 要求
        formatted_contract_quantity = f"{contract_quantity:.8f}".rstrip('0').rstrip('.')
        
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
                quantity=formatted_contract_quantity
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
        print(f"🔄 現貨市價買入被觸發")
        print(f"🔍 trading_enabled: {self.trading_enabled}")
        print(f"🔍 binance_client: {self.binance_client is not None}")
        
        if not self.trading_enabled:
            print("❌ 交易功能未啟用")
            rumps.alert("交易功能未啟用", "請先在 config.json 中設定 trading_enabled: true")
            return
        
        if not self.binance_client:
            print("❌ 幣安客戶端未初始化")
            rumps.alert("連接錯誤", "幣安客戶端未正確初始化")
            return
        
        result = self.show_trading_dialog("現貨市價", "買入")
        if result.get('confirmed'):
            if self.trading_settings.get('order_confirmation', True):
                if rumps.alert("確認下單", f"確定要執行現貨市價買入嗎？\n數量: {result['params']['quantity']} USDT", ok="確認", cancel="取消") != 1:
                    return
            self.execute_order(result['params'])
        else:
            print("📋 用戶取消了操作")
    
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
        print(f"🔄 現貨限價買入被觸發")
        
        if not self.trading_enabled:
            print("❌ 交易功能未啟用")
            rumps.alert("交易功能未啟用", "請先在 config.json 中設定 trading_enabled: true")
            return
        
        if not self.binance_client:
            print("❌ 幣安客戶端未初始化")
            rumps.alert("連接錯誤", "幣安客戶端未正確初始化")
            return
        
        result = self.show_trading_dialog("現貨限價", "買入")
        if result.get('confirmed'):
            if self.trading_settings.get('order_confirmation', True):
                if rumps.alert("確認下單", f"確定要執行現貨限價買入嗎？\n數量: {result['params']['quantity']} USDT\n價格: {result['params']['price']}", ok="確認", cancel="取消") != 1:
                    return
            self.execute_order(result['params'])
        else:
            print("📋 用戶取消了操作")
    
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
        
        # 關閉圖表
        if self.chart_visible:
            self.hide_chart()
        
        # 等待執行緒結束
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)
        if self.chart_thread and self.chart_thread.is_alive():
            self.chart_thread.join(timeout=2)
        
        # 刪除臨時圖片檔案
        try:
            if os.path.exists(self.chart_image_path):
                os.remove(self.chart_image_path)
        except:
            pass
        
        rumps.quit_application()

    # ==================== 價格走勢圖方法 ====================
    
    def toggle_chart(self, sender):
        """切換走勢圖顯示"""
        if not CHART_AVAILABLE:
            rumps.alert("錯誤", "需要安裝 Pillow 套件才能使用走勢圖功能")
            return
        
        if self.chart_visible:
            self.hide_chart()
        else:
            self.show_chart()
    
    def show_chart(self):
        """顯示走勢圖"""
        if self.chart_visible:
            return
        
        try:
            current_pair = self.trading_pairs[self.current_crypto_index]
            timeframe_name = self.timeframe_settings.get(self.chart_timeframe, ["", 0, "未知", 0])[2]
            print(f"📈 正在載入 {current_pair} 的 {timeframe_name} 走勢圖...")
            
            # 更新選單狀態
            self.chart_toggle.title = "🙈 隱藏走勢圖"
            self.chart_visible = True
            
            # 啟動圖表更新執行緒
            self.chart_thread = threading.Thread(target=self.chart_update_worker, daemon=True)
            self.chart_thread.start()
            
        except Exception as e:
            print(f"❌ 顯示走勢圖失敗: {e}")
            rumps.alert("錯誤", f"顯示走勢圖失敗: {str(e)}")
    
    def hide_chart(self):
        """隱藏走勢圖"""
        if not self.chart_visible:
            return
        
        try:
            # 更新選單狀態
            self.chart_toggle.title = "👁️ 顯示走勢圖"
            self.chart_visible = False
            
            # 關閉預覽程式
            if self.preview_process:
                try:
                    self.preview_process.terminate()
                    self.preview_process = None
                except:
                    pass
            
            print("📈 走勢圖已隱藏")
            
        except Exception as e:
            print(f"❌ 隱藏走勢圖失敗: {e}")
    
    def set_chart_timeframe(self, timeframe):
        """設定走勢圖時間區間"""
        self.chart_timeframe = timeframe
        
        # 更新選單狀態
        self.timeframe_1m.state = (timeframe == "1m")
        self.timeframe_5m.state = (timeframe == "5m")
        self.timeframe_15m.state = (timeframe == "15m")
        self.timeframe_1h.state = (timeframe == "1h")
        self.timeframe_4h.state = (timeframe == "4h")
        self.timeframe_1d.state = (timeframe == "1d")
        
        # 獲取時間區間設定
        settings = self.timeframe_settings.get(timeframe, ["", 0, "未知", 0])
        timeframe_name = settings[2]
        
        print(f"⏰ 走勢圖時間區間已設定為: {timeframe_name}")
        
        # 如果走勢圖正在顯示，立即重新繪製
        if self.chart_visible:
            print(f"🔄 將重新從幣安獲取 {timeframe_name} 的K線數據")
    
    def get_kline_data_from_binance(self):
        """從幣安獲取K線數據"""
        try:
            current_pair = self.trading_pairs[self.current_crypto_index]
            settings = self.timeframe_settings.get(self.chart_timeframe, ["1m", 15, "未知", 30])
            interval = settings[0]  # K線間隔
            limit = settings[1]     # K線數量
            
            # 使用幣安公開 API 獲取 K 線數據
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': current_pair,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            klines = response.json()
            
            # 解析 K 線數據（開高低收）
            kline_data = []
            for kline in klines:
                timestamp = datetime.fromtimestamp(kline[0] / 1000).strftime("%H:%M")
                kline_data.append({
                    'timestamp': timestamp,
                    'open': float(kline[1]),    # 開盤價
                    'high': float(kline[2]),    # 最高價
                    'low': float(kline[3]),     # 最低價
                    'close': float(kline[4]),   # 收盤價
                    'volume': float(kline[5])   # 成交量
                })
            
            return kline_data
            
        except Exception as e:
            print(f"❌ 從幣安獲取K線數據失敗: {e}")
            return None
    
    def get_font(self, size=12):
        """獲取中文字體"""
        try:
            # macOS 系統中文字體
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',  # macOS 預設中文字體
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                '/Library/Fonts/Arial Unicode.ttf'
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
        except:
            pass
        return ImageFont.load_default()
    
    def generate_chart_image(self):
        """生成K線圖圖片"""
        try:
            # 從幣安獲取K線數據
            kline_data = self.get_kline_data_from_binance()
            if not kline_data or len(kline_data) < 2:
                print("❌ K線數據不足，無法生成圖表")
                return None
            
            # 圖表尺寸和邊距（縮小尺寸）
            width, height = 800, 400
            margin_left = 60
            margin_right = 20
            margin_top = 40
            margin_bottom = 40
            chart_width = width - margin_left - margin_right
            chart_height = height - margin_top - margin_bottom
            
            # 創建圖片
            img = Image.new('RGB', (width, height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # 獲取字體（縮小字體尺寸）
            title_font = self.get_font(14)
            label_font = self.get_font(10)
            small_font = self.get_font(8)
            
            # 獲取價格範圍
            all_prices = []
            for k in kline_data:
                all_prices.extend([k['high'], k['low']])
            max_price = max(all_prices)
            min_price = min(all_prices)
            price_range = max_price - min_price if max_price != min_price else 1
            
            # 繪製標題（包含時間區間）
            current_pair = self.trading_pairs[self.current_crypto_index]
            timeframe_name = self.timeframe_settings.get(self.chart_timeframe, ["", 0, "未知", 0])[2]
            title = f"{current_pair} K線圖 ({timeframe_name})"
            draw.text((width // 2 - 80, 10), title, fill='white', font=title_font)
            
            # 繪製價格標籤
            draw.text((5, margin_top), f"${max_price:.2f}", fill='#888', font=label_font)
            draw.text((5, height - margin_bottom), f"${min_price:.2f}", fill='#888', font=label_font)
            
            # 繪製參考線
            for i in range(5):
                y = margin_top + (chart_height / 4) * i
                draw.line([(margin_left, y), (width - margin_right, y)], fill='#333', width=1)
            
            # 計算每根K線的寬度
            candle_width = chart_width / len(kline_data)
            candle_body_width = candle_width * 0.6
            
            # 繪製K線
            for i, kline in enumerate(kline_data):
                x = margin_left + i * candle_width + candle_width / 2
                
                # 計算價格對應的Y座標
                def price_to_y(price):
                    return margin_top + chart_height - ((price - min_price) / price_range) * chart_height
                
                open_y = price_to_y(kline['open'])
                close_y = price_to_y(kline['close'])
                high_y = price_to_y(kline['high'])
                low_y = price_to_y(kline['low'])
                
                # 判斷漲跌
                is_rising = kline['close'] >= kline['open']
                color = '#00ff00' if is_rising else '#ff0000'  # 綠色上漲，紅色下跌
                
                # 繪製上影線和下影線
                draw.line([(x, high_y), (x, low_y)], fill=color, width=1)
                
                # 繪製K線實體
                body_top = min(open_y, close_y)
                body_bottom = max(open_y, close_y)
                body_height = body_bottom - body_top if body_bottom > body_top else 1
                
                # 實體矩形
                left = x - candle_body_width / 2
                right = x + candle_body_width / 2
                
                if is_rising:
                    # 上漲：空心（只有邊框）
                    draw.rectangle([left, body_top, right, body_bottom], outline=color, width=1)
                else:
                    # 下跌：實心
                    draw.rectangle([left, body_top, right, body_bottom], fill=color, outline=color)
            
            # 繪製最新價格標記和標籤
            latest = kline_data[-1]
            latest_price = latest['close']
            latest_y = price_to_y(latest_price)
            
            # 繪製價格線（使用短線段模擬虛線效果）
            dash_length = 10
            gap_length = 5
            x = margin_left
            while x < width - margin_right:
                draw.line([(x, latest_y), (min(x + dash_length, width - margin_right), latest_y)], 
                         fill='yellow', width=1)
                x += dash_length + gap_length
            
            # 繪製價格標籤背景
            price_text = f"${latest_price:.2f}"
            draw.rectangle([width - margin_right - 70, latest_y - 10, 
                          width - margin_right, latest_y + 10], 
                         fill='yellow', outline='yellow')
            draw.text((width - margin_right - 65, latest_y - 8), price_text, 
                     fill='black', font=label_font)
            
            # 繪製時間軸
            if len(kline_data) > 0:
                # 顯示幾個時間點（根據K線數量調整顯示數量）
                num_labels = min(8, len(kline_data) // 10 + 1)  # 最多顯示8個時間標籤
                step = max(1, len(kline_data) // num_labels)
                for i in range(0, len(kline_data), step):
                    x = margin_left + i * candle_width + candle_width / 2
                    draw.text((x - 12, height - margin_bottom + 5), 
                             kline_data[i]['timestamp'], fill='#888', font=small_font)
            
            # 保存圖片
            img.save(self.chart_image_path)
            return self.chart_image_path
            
        except Exception as e:
            print(f"❌ 生成走勢圖失敗: {e}")
            return None
    
    
    def show_chart_image(self):
        """使用系統預覽顯示走勢圖"""
        try:
            image_path = self.generate_chart_image()
            if not image_path:
                return
            
            # 使用 macOS 的 open 命令打開圖片（非阻塞，避免 GUI 執行緒問題）
            # 使用 -g 參數讓預覽程式在背景開啟，不搶奪焦點
            if self.preview_process is None:
                # 第一次打開
                self.preview_process = subprocess.Popen(
                    ['open', '-g', image_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # 已經打開了，只需要觸發預覽程式重新載入
                # 使用 touch 命令更新檔案修改時間，讓預覽程式自動重新載入
                subprocess.run(['touch', image_path], check=False)
            
        except Exception as e:
            print(f"❌ 顯示走勢圖失敗: {e}")
    
    def chart_update_worker(self):
        """圖表更新執行緒"""
        try:
            while self.chart_visible and self.running:
                # 獲取當前時間區間的設定
                settings = self.timeframe_settings.get(self.chart_timeframe, ["1m", 15, "未知", 30])
                update_interval = settings[3]  # 更新間隔（秒）
                
                # 從幣安獲取K線數據並生成圖表
                self.show_chart_image()
                
                # 等待更新間隔
                time.sleep(update_interval)
            
        except Exception as e:
            print(f"❌ 圖表更新執行緒錯誤: {e}")

def main():
    """主函數"""
    print("=" * 60)
    print("⚡ 加密貨幣選單欄監控器 v4.2 ⚡")
    print("🔄 使用幣安 (Binance) API - 精簡版")
    print("🌐 選單欄應用 - 跨所有桌面空間顯示")
    print("🎯 只獲取當前選擇的加密貨幣，節省網路資源")
    print("💰 支援幣安現貨和合約交易功能")
    print("📈 價格走勢圖功能 - 每30秒自動更新")
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