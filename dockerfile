# 使用最新版本的Pytorch作為基礎映像
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# 設置工作目錄
WORKDIR /app

# 安裝 git 並克隆項目
RUN apt-get update && \
    apt-get install -y git libgl1-mesa-glx libglib2.0-0 && \
    git clone --recurse-submodules --depth 1 https://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@github.com/solaxie/omo-project.git . && \
    pip install --no-cache-dir -e ./LightGlue && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /root/.cache /app/omo-project.git

# 聲明預設掛載點，以供存放log/video/config.txt
VOLUME /dect_camera_angle_files

# 設置容器的默認命令
CMD ["python", "detect_camera_angle.py"]