# 使用最新版本的Alpine作為基礎映像
FROM alpine:latest

# 設置工作目錄
WORKDIR /app

# 更新APK相關套件並安裝必要的依賴，最後清除所有緩存
RUN apk update && apk upgrade && \
    apk add --no-cache python3 py3-pip git && \
    rm -rf /var/cache/apk/* && \
    rm -rf /root/.cache

# 下載LightGlue源碼
RUN git git clone --quiet https://github.com/solaxie/omo-project.git

# 安裝Python依賴，並且不保留緩存
RUN pip3 install --no-cache-dir -e ./omo-project/LightGlue

# 聲明1個預設掛載點，以供存放log/video/config.txt
VOLUME /app

# 複製detect_camera_angle.py和send_email.py到工作目錄
# COPY detect_camera_angle.py send_email.py /app/LightGlue/

# 設置容器的默認命令
CMD ["python3", "detect_camera_angle.py"]