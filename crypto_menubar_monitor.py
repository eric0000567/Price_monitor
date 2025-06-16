#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚡ 賽博龐克加密貨幣選單欄監控器 v3.2 ⚡
🔄 使用幣安 (Binance) API - 精簡版
🌐 選單欄應用 - 跨所有桌面空間顯示
🎯 只獲取當前選擇的加密貨幣，節省網路資源
"""

import sys
import json
import time
import threading
import requests
from datetime import datetime

# 檢查並導入 rumps
try:
    import rumps
    RUMPS_AVAILABLE = True
except ImportError:
    RUMPS_AVAILABLE = False
    print("❌ rumps 套件未安裝")
    print("請執行: pip install rumps")

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
    print("⚡ 賽博龐克加密貨幣選單欄監控器 v3.2 ⚡")
    print("🔄 使用幣安 (Binance) API - 精簡版")
    print("🌐 選單欄應用 - 跨所有桌面空間顯示")
    print("🎯 只獲取當前選擇的加密貨幣，節省網路資源")
    print("=" * 60)
    
    if not RUMPS_AVAILABLE:
        print("❌ 需要安裝 rumps 套件")
        print("請執行: pip install rumps")
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