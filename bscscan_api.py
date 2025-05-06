import requests
import time
from typing import Dict, Any, Optional
import config

class BscScanAPI:
    """BscScan API 客戶端"""
    
    def __init__(self, api_key: str = None):
        """
        初始化 BscScan API 客戶端
        
        參數:
            api_key (str, optional): BscScan API 密鑰。如果未提供，將使用配置中的密鑰。
        """
        self.api_key = api_key or config.BSCSCAN_API_KEY
        self.base_url = config.BSCSCAN_API_URL
        
    def _make_request(self, params: Dict[str, Any]) -> Dict:
        """
        發送請求到 BscScan API
        
        參數:
            params (Dict[str, Any]): API 請求參數
        
        返回:
            Dict: API 響應
        
        異常:
            Exception: 請求失敗時拋出
        """
        # 添加 API 密鑰到請求參數
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API 請求錯誤: {e}")
            raise
    
    def get_transaction_status(self, tx_hash: str) -> Dict:
        """
        獲取交易狀態
        
        參數:
            tx_hash (str): 交易哈希
        
        返回:
            Dict: 包含交易狀態的字典
        """
        params = {
            'module': 'transaction',
            'action': 'gettxreceiptstatus',
            'txhash': tx_hash
        }
        
        return self._make_request(params)
    
    def get_transaction_info(self, tx_hash: str) -> Dict:
        """
        獲取交易詳細信息（僅檢查是否成功）
        
        參數:
            tx_hash (str): 交易哈希
        
        返回:
            Dict: 包含交易詳細信息的字典
        """
        # 只獲取交易收據狀態，減少API呼叫次數
        params = {
            'module': 'transaction',
            'action': 'gettxreceiptstatus',
            'txhash': tx_hash
        }
        
        status_response = self._make_request(params)
        
        # 組合結果
        result = {
            'TxHash': tx_hash,
            'status': 'failed'  # 默認為失敗
        }
        
        # 檢查交易收據狀態
        if status_response.get('status') == '1':
            receipt_status = status_response.get('result', {}).get('status')
            if receipt_status == '1':
                result['status'] = 'success'
        
        return result
    
    def get_block_info(self, block_number: int) -> Optional[Dict]:
        """
        獲取區塊信息
        
        參數:
            block_number (int): 區塊號碼
        
        返回:
            Optional[Dict]: 包含區塊信息的字典，如果失敗則返回 None
        """
        params = {
            'module': 'proxy',
            'action': 'eth_getBlockByNumber',
            'tag': hex(block_number),
            'boolean': 'true'
        }
        
        try:
            response = self._make_request(params)
            if response.get('status') == '1' and response.get('result'):
                block_data = response.get('result')
                return {
                    'timestamp': int(block_data.get('timestamp', '0'), 16)
                }
        except Exception as e:
            print(f"獲取區塊信息時發生錯誤: {e}")
        
        return None 