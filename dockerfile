# 使用最新版本的Alpine作為基礎映像
FROM alpine:latest

# 設置工作目錄
WORKDIR /app

# 更新APK相關套件並安裝必要的依賴，最後清除所有緩存
RUN apk update && \
    apk upgrade && \
    apk add --no-cache python3 py3-pip && \
    git clone --depth 1 --quiet https://github.com/solaxie/omo-project.git && \
    pip3 install --no-cache-dir -e ./omo-project/LightGlue && \
    rm -rf /var/cache/apk/* /root/.cache /app/omo-project/.git

# 聲明1個預設掛載點，以供存放log/video/config.txt
VOLUME /app

# 設置容器的默認命令
CMD ["python3", "detect_camera_angle.py"]