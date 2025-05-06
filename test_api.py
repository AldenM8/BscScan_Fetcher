import sys
import json
from bscscan_api import BscScanAPI
import config
import datetime

def test_api_connection(tx_hash):
    """測試 API 連接
    
    參數:
        tx_hash (str): 交易哈希，必須提供
    """
    if not tx_hash:
        print("❌ 錯誤：必須提供交易哈希！")
        return False
    
    try:
        api = BscScanAPI()
        print(f"🔄 使用交易哈希 {tx_hash} 測試 API 連接...")
        
        params = {
            'module': 'transaction',
            'action': 'getstatus',
            'txhash': tx_hash
        }
        response = api._make_request(params)

        # 移除直接打印 status 的語句，避免顯示 None
        # 只在有狀態值時才打印
        status = response.get('result', {}).get('status')
        if status:
            print(f"  交易狀態碼: {status}")
        
        if response.get('status') == '1':
            print("✅ API 連接成功！")
            return True
        else:
            print(f"❌ API 連接失敗: {response.get('message', '未知錯誤')}")
            return False
    except Exception as e:
        print(f"❌ API 連接出錯: {e}")
        return False

def test_transaction_status(tx_hash):
    """測試獲取交易狀態"""
    try:
        api = BscScanAPI()
        print(f"🔍 正在獲取交易 {tx_hash} 的狀態...")
        
        # 獲取基本交易信息
        tx_info = api.get_transaction_info(tx_hash)
        
        # 獲取更詳細的交易數據
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionByHash',
            'txhash': tx_hash
        }
        tx_details = api._make_request(params)
        
        # 打印交易基本信息
        print("\n📋 交易基本信息:")
        print(f"  交易哈希: {tx_hash}")
        print(f"  交易狀態: {tx_info.get('status', '未知')}")
        
        if 'block_number' in tx_info:
            print(f"  區塊號碼: {tx_info.get('block_number')}")
        
        if 'timestamp' in tx_info:
            # 將時間戳轉換為可讀日期時間
            tx_time = datetime.datetime.fromtimestamp(tx_info.get('timestamp'))
            print(f"  交易時間: {tx_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 如果有詳細數據，打印更多信息
        if tx_details.get('status') == '1' and tx_details.get('result'):
            tx_data = tx_details.get('result')
            print("\n💰 交易詳細信息:")
            print(f"  發送地址: {tx_data.get('from', '未知')}")
            print(f"  接收地址: {tx_data.get('to', '未知')}")
            
            # 轉換 wei 到 BNB (1 BNB = 10^18 wei)
            if tx_data.get('value'):
                wei_value = int(tx_data.get('value'), 16)
                bnb_value = wei_value / 10**18
                print(f"  交易金額: {bnb_value} BNB")
            
            print(f"  Gas 限制: {int(tx_data.get('gas', '0'), 16)}")
            print(f"  Gas 價格: {int(tx_data.get('gasPrice', '0'), 16) / 10**9} Gwei")
            
            # 打印原始數據供參考
            print("\n🔧 完整交易數據:")
            print(json.dumps(tx_info, indent=2))
            print("\n原始交易詳情:")
            print(json.dumps(tx_details.get('result', {}), indent=2, default=str))
        
        return True
    except Exception as e:
        print(f"❌ 獲取交易狀態出錯: {e}")
        return False

def main():
    """主測試入口"""
    print("🧪 開始測試 BscScan API...")
    
    # 檢查是否提供了交易哈希
    tx_hash = None
    if len(sys.argv) > 1:
        tx_hash = sys.argv[1]
        print(f"使用提供的交易哈希: {tx_hash}")
    else:
        print("❌ 錯誤：請提供交易哈希作為參數！")
        print("例如: python test_api.py 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
        sys.exit(1)
    
    # 測試 API 連接
    if not test_api_connection(tx_hash):
        print("API 連接測試失敗，請檢查您的 API 密鑰和網絡連接。")
        sys.exit(1)
    
    # 測試獲取交易狀態
    test_transaction_status(tx_hash)
    
    print("測試完成！")

if __name__ == "__main__":
    main() 