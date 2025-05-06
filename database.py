from sqlalchemy import create_engine, MetaData, Table, select, update, and_, not_, func, or_
import config
import logging

# 設置日誌
logger = logging.getLogger("BscScanFetcher.Database")

# 創建資料庫引擎
engine = create_engine(config.DATABASE_URL)
metadata = MetaData()

# 獲取已存在的交易表
def get_transactions_table():
    """獲取已存在的交易表"""
    return Table(config.DB_TABLE, metadata, autoload_with=engine)

# 更新交易狀態
def update_transaction_status(tx_hash, status):
    """
    更新交易狀態
    
    參數:
        tx_hash (str): 交易哈希
        status (str): 交易狀態
    
    返回:
        bool: 更新成功返回 True，否則返回 False
    """
    try:
        table = get_transactions_table()
        
        # 準備更新數據
        update_data = {}
        
        # 根據 BscScan 上的交易狀態更新 Status 欄位
        from datetime import datetime
        if status == 'success':
            update_data['Status'] = 2  # 將成功狀態設為整數 2
            update_data['UpdateTime'] = datetime.now()
        # pending 狀態不更新資料庫，保持為 null
        
        # 如果沒有要更新的數據，則返回 False
        if not update_data:
            logger.warning(f"沒有需要更新的數據 - TxHash: {tx_hash}")
            return False
        
        # 執行更新
        stmt = update(table).where(table.c.TxHash == tx_hash).values(**update_data)
        with engine.connect() as conn:
            result = conn.execute(stmt)
            conn.commit()
            
            # 只有在成功更新時才顯示 TransactionID
            if result.rowcount > 0:
                select_stmt = select(table).where(table.c.TxHash == tx_hash)
                updated_record = conn.execute(select_stmt).fetchone()
                if updated_record:
                    print(f"成功更新交易 - TransactionID: {updated_record.TransactionID}, BscScan狀態: 成功 (2)")
                    logger.info(f"已將 TransactionID: {updated_record.TransactionID} 的 Status 設為 {update_data.get('Status')}，更新時間: {update_data.get('UpdateTime', datetime.now())}")
            
        return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新交易狀態時發生錯誤: {e}")
        return False

# 獲取所有未處理的交易
def get_pending_transactions():
    """
    獲取所有 Status 為 null 的交易，排除 Internal Transfer
    
    返回:
        list: 未處理的交易列表
    """
    try:
        table = get_transactions_table()
        
        # 查詢條件：Status 為 null，且 TxHash 不以 'Internal Transfer' 開頭
        stmt = select(table).where(
            and_(
                table.c.Status == None,
                not_(func.lower(table.c.TxHash).like('internal transfer%'))
            )
        )
        
        with engine.connect() as conn:
            result = conn.execute(stmt)
            pending_txs = [dict(row._mapping) for row in result.fetchall()]
            
            # 顯示待處理的交易資訊
            if pending_txs:
                print("\n=== 待處理的交易列表 ===")
                for i, tx in enumerate(pending_txs, 1):
                    print(f"{i}. TransactionID: {tx.get('TransactionID')}, 交易哈希: {tx.get('TxHash')}, 當前狀態: 未處理 (null)")
                print(f"\n總計: {len(pending_txs)} 筆待處理交易需要查詢 BscScan 狀態")
                print("=" * 40 + "\n")
            else:
                print("未找到需要查詢的交易記錄")
            
            return pending_txs
    except Exception as e:
        logger.error(f"獲取未處理交易時發生錯誤: {e}")
        return []
