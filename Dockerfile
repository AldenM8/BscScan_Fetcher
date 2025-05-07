FROM python:3.10-slim

WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式文件
COPY . .

# 設置時區
ENV TZ=Asia/Taipei
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 創建日誌目錄
RUN mkdir -p logs

# 運行應用程式
CMD ["python", "main.py"] 