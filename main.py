import time
import logging
from datetime import datetime
from bscscan_api import BscScanAPI
import database
import os

# 設置日誌
def get_log_filename():
    """獲取當天的日誌檔案名稱，格式為 bscscan_YYYY-MM-DD.log"""
    today = datetime.now().strftime('%Y-%m-%d')
    return f"bscscan_{today}.log"

# 確保日誌目錄存在
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 日誌檔案將以日期命名，同一天的記錄在同一個檔案中
log_file = os.path.join(log_dir, get_log_filename())

logging.basicConfig(
    encoding='utf-8',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BscScanFetcher")

def update_transaction(tx_data):
    """
    更新單筆交易狀態
    
    注意：此函數已不再使用，所有交易處理邏輯已移至 process_pending_transactions 函數中，
    以減少API呼叫次數。保留此函數僅供參考。
    
    參數:
        tx_data (dict): 包含交易資訊的字典
    
    返回:
        bool: 更新成功返回 True，否則返回 False
    """
    try:
        tx_hash = tx_data.get('TxHash')
        transaction_id = tx_data.get('TransactionID')
        current_status = tx_data.get('Status')
        
        if not tx_hash:
            logger.error(f"交易資料缺少 TxHash，TransactionID: {transaction_id}")
            return False
        
        logger.info(f"正在查詢交易 - TransactionID: {transaction_id}, TxHash: {tx_hash}, 當前狀態: {current_status}")
        api = BscScanAPI()
        tx_info = api.get_transaction_info(tx_hash)
        
        if not tx_info:
            logger.error(f"無法獲取交易資訊 - TransactionID: {transaction_id}, TxHash: {tx_hash}")
            return False
        
        bscscan_status = tx_info.get('status')
        logger.info(f"交易狀態 - TransactionID: {transaction_id}, BscScan狀態: {bscscan_status}")
        
        # 如果當前狀態已經是 2 (success)，且 BscScan 狀態也是 success，則不需要更新
        if current_status == 2 and bscscan_status == 'success':
            logger.info(f"交易已經是成功狀態，無需更新 - TransactionID: {transaction_id}")
            return True
        
        # 如果 BscScan 狀態是 pending，則不更新資料庫
        if bscscan_status == 'pending':
            logger.info(f"交易狀態為 pending，不更新資料庫 - TransactionID: {transaction_id}")
            return True
        
        # 更新資料庫
        update_result = database.update_transaction_status(
            tx_hash=tx_hash,
            status=bscscan_status
        )
        
        if update_result:
            logger.info(f"交易資料已成功更新 - TransactionID: {transaction_id}, 新狀態: {bscscan_status}")
        else:
            logger.warning(f"交易資料更新失敗 - TransactionID: {transaction_id}")
            
        return update_result
    except Exception as e:
        logger.error(f"更新交易時發生錯誤: {e}")
        return False

def process_pending_transactions():
    """
    處理所有待處理的交易
    
    返回:
        int: 成功更新的交易數量
    """
    logger.info("開始處理待處理的交易...")
    
    # 獲取所有 Status 為 null 的交易（已排除 Internal Transfer）
    pending_txs = database.get_pending_transactions()
    
    if not pending_txs:
        logger.info("沒有找到需要更新的交易")
        return 0
    
    
    logger.info(f"找到 {len(pending_txs)} 筆待處理的交易需要查詢")
    
    success_count = 0
    error_count = 0
    unchanged_count = 0
    
    # 逐筆處理交易
    for i, tx in enumerate(pending_txs, 1):
        try:
            logger.info(f"處理第 {i}/{len(pending_txs)} 筆交易")
            tx_hash = tx.get('TxHash')
            transaction_id = tx.get('TransactionID')
            
            # 獲取交易狀態（只呼叫一次API）
            api = BscScanAPI()
            tx_info = api.get_transaction_info(tx_hash)
            
            if not tx_info:
                logger.error(f"無法獲取交易資訊 - TransactionID: {transaction_id}, TxHash: {tx_hash}")
                error_count += 1
                continue
            
            bscscan_status = tx_info.get('status')
            logger.info(f"交易狀態 - TransactionID: {transaction_id}, BscScan狀態: {bscscan_status}")
            
            # 如果交易已經是成功狀態，不需要更新
            current_status = tx.get('Status')
            if current_status == 2 and bscscan_status == 'success':
                logger.info(f"交易已經是成功狀態，無需更新 - TransactionID: {transaction_id}")
                unchanged_count += 1
                continue
            
            # 記錄交易狀態
            if bscscan_status == 'success':
                # 更新為成功狀態
                update_result = database.update_transaction_status(tx_hash=tx_hash, status=bscscan_status)
                if update_result:
                    success_count += 1
                    logger.info(f"交易資料已成功更新 - TransactionID: {transaction_id}, 新狀態: {bscscan_status}")
                else:
                    error_count += 1
                    logger.warning(f"交易資料更新失敗 - TransactionID: {transaction_id}")
            else:
                # 其他狀態（包括failed和未知狀態）不更新資料庫
                unchanged_count += 1
                logger.info(f"交易狀態為 {bscscan_status}，不更新資料庫 - TransactionID: {transaction_id}")
                
        except Exception as e:
            logger.error(f"處理交易時發生錯誤: {e}")
            error_count += 1
            
        # 避免 API 限制，添加短暫的延遲
        # BscScan API 限制：每秒最多5次呼叫，每日最多100,000次
        time.sleep(0.2)  # 調整為0.2秒，因為現在每筆交易只呼叫一次API
    
    logger.info(f"處理完成，成功更新為成功狀態: {success_count} 筆，無變化: {unchanged_count} 筆，失敗: {error_count} 筆")
    return success_count

def main():
    """主程序入口"""
    logger.info("=" * 50)
    logger.info("BscScan 交易查詢程序啟動")
    logger.info(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    try:
        # 每5分鐘執行一次
        while True:
            try:
                logger.info("開始執行交易狀態檢查...")
                process_pending_transactions()
                logger.info(f"本次執行完畢，等待5分鐘後再次執行...")
                # 等待5分鐘
                time.sleep(300)
            except Exception as e:
                logger.error(f"程序執行期間發生錯誤: {e}")
                logger.info("5分鐘後重試...")
                time.sleep(300)
    except KeyboardInterrupt:
        # 處理鍵盤中斷 (Ctrl+C)
        logger.info("接收到鍵盤中斷信號，程序結束")
    
    logger.info("程序執行完畢")
    logger.info("=" * 50)

if __name__ == "__main__":
    main() 