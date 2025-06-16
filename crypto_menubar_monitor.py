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
            self.crypto_data[current_pair] = {
                'price': float(data['lastPrice']),
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
                if self.get_current_crypto_price():
                    # 直接在背景執行緒中更新顯示（rumps 是執行緒安全的）
                    self.update_display()
                else:
                    print("⚠️ 更新失敗，將在下次間隔後重試")
                
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
    
    def manual_refresh(self, sender):
        """手動重新整理"""
        print("🔄 手動重新整理價格...")
        refresh_thread = threading.Thread(target=self.initial_update, daemon=True)
        refresh_thread.start()
    
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