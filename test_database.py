import unittest
import sys
import sqlalchemy
from sqlalchemy import text
from database import engine, get_transactions_table, get_pending_transactions
import config

class TestDatabaseConnection(unittest.TestCase):
    
    def test_database_connection(self):
        """測試能否成功連接到數據庫"""
        try:
            # 嘗試連接到資料庫
            with engine.connect() as connection:
                # 執行簡單查詢確認連接正常
                result = connection.execute(text("SELECT 1"))
                self.assertEqual(result.scalar(), 1)
                print("✅ 資料庫連接成功！")
        except Exception as e:
            self.fail(f"❌ 資料庫連接失敗: {e}")
    
    def test_transactions_table_exists(self):
        """測試交易表是否存在"""
        try:
            # 獲取交易表
            table = get_transactions_table()
            self.assertIsNotNone(table)
            print(f"✅ 交易表 '{config.DB_TABLE}' 存在！")
            
            # 列出表的列名
            columns = [col.name for col in table.c]
            print(f"表結構: {columns}")
        except Exception as e:
            self.fail(f"❌ 無法獲取交易表: {e}")
    
    def test_get_pending_transactions(self):
        """測試獲取未處理交易功能"""
        try:
            # 獲取未處理的交易
            pending_txs = get_pending_transactions()
            # 確認返回值是列表
            self.assertIsInstance(pending_txs, list)
            print(f"✅ 成功獲取未處理交易，共 {len(pending_txs)} 筆")
        except Exception as e:
            self.fail(f"❌ 獲取未處理交易失敗: {e}")

def main():
    """主測試入口"""
    print("🧪 開始測試數據庫連接...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    print("測試完成！")

if __name__ == "__main__":
    main() 