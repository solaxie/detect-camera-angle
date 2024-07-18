# 使用最新版本的Pytorch作為基礎映像
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# 設置工作目錄
WORKDIR /app

# 安裝 git 並克隆項目
RUN apt-get update && \
    apt-get install -y git && \
    git clone --recurse-submodules --depth 1 https://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@github.com/solaxie/omo-project.git && \
    pip install --no-cache-dir -e ./omo-project/LightGlue && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /root/.cache /app/omo-project/.git

# 聲明預設掛載點，以供存放log/video/config.txt
VOLUME /app/

# 設置容器的默認命令
CMD ["python3", "detect_camera_angle.py"]