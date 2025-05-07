# BscScanFetcher

這個工具用於從 BscScan API 獲取交易狀態，並更新資料庫中的交易記錄。

## 功能

- 從 BscScan API 獲取交易狀態
- 更新資料庫中的交易記錄狀態
- 處理所有待處理的交易
- 記錄詳細的操作日誌

## 安裝

### 直接安裝

1. 克隆此專案存儲庫
2. 安裝依賴項：

```bash
pip install -r requirements.txt
```

### 使用 Docker

本專案提供了 Docker 支援，可以使用以下方式運行：

1. 確保已安裝 [Docker](https://www.docker.com/get-started) 和 [Docker Compose](https://docs.docker.com/compose/install/)
2. 複製 `config.py.example` 為 `config.py` 並配置
3. 使用 Docker Compose 啟動服務：

```bash
# 建立並啟動容器
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

或者使用 Docker 命令：

```bash
# 建立映像檔
docker build -t bscscan-fetcher .

# 運行容器
docker run -d --name bscscan-fetcher \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.py:/app/config.py \
  bscscan-fetcher
```

## 配置

1. 複製 `config.py.example` 為 `config.py`
2. 編輯 `config.py` 文件，設置您的 BscScan API 金鑰和資料庫連接信息

## 使用方法

### 直接運行

執行主程序以更新交易狀態：

```bash
python main.py
```

程式會自動每5分鐘執行一次檢查，直到被手動中斷（Ctrl+C）。

## 主要欄位說明

關注的主要資料庫欄位：

- `TxHash`：交易哈希
- `Status`：在 BscScan 上的交易狀態（NULL: 未檢查/未成功，2: 成功）
- `UpdateTime`：交易狀態更新時間

## 程式邏輯

1. 程式啟動時會查詢資料庫中 `Status` 為 NULL 的交易記錄（排除 Internal Transfer 開頭的記錄）
2. 對每筆交易記錄，使用 BscScan API 檢查交易狀態（僅需一次API呼叫）
3. 根據 BscScan 上的狀態進行更新：
   - 成功：將 `Status` 更新為整數 2
   - 其他狀態：不更新資料庫，保持 `Status` 為 NULL
4. 同時更新 `UpdateTime` 為當前時間（僅當狀態更新為成功時）
5. 程式會顯示處理進度和結果，並將詳細日誌記錄到 `logs` 目錄下，格式為 `bscscan_YYYY-MM-DD.log`

## 特殊處理

1. **內部轉帳過濾**：查詢時會自動排除 TxHash 以 "Internal Transfer" 開頭的交易記錄
2. **狀態避免重複更新**：如果交易已經是整數 2 (成功) 狀態且 BscScan 上也是 'success'，則不會再次更新
3. **API呼叫優化**：每筆交易僅呼叫一次API，專注於檢查是否成功
4. **錯誤處理**：如果在查詢過程中發生錯誤，程式會記錄錯誤並繼續處理下一筆交易
5. **日誌按天儲存**：日誌檔案按天分別儲存，方便查詢特定日期的操作記錄

## 運行結果

程式執行時會顯示：
1. 找到多少筆待處理的交易
2. 每筆交易的處理狀態
3. 成功更新、無變化和失敗的交易數量
4. 每次執行後會顯示等待5分鐘的提示，然後自動進行下一次檢查 