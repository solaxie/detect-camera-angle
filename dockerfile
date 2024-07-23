# 使用最新版本的Pytorch作為基礎映像
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# 設置工作目錄
WORKDIR /app/

# 安裝 git 並克隆項目
RUN apt-get update && \
    apt-get install -y git libgl1-mesa-glx libglib2.0-0 wget && \
    git clone --recurse-submodules --depth 1 https://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@github.com/solaxie/omo-project.git . && \
    pip install --no-cache-dir -e ./LightGlue && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /root/.cache /app/omo-project.git && \
    mkdir -p /root/.cache/torch/hub/checkpoints && \
    wget -O /root/.cache/torch/hub/checkpoints/superpoint_v1.pth https://github.com/cvg/LightGlue/releases/download/v0.1_arxiv/superpoint_v1.pth && \
    wget -O /root/.cache/torch/hub/checkpoints/superpoint_lightglue_v0-1_arxiv.pth https://github.com/cvg/LightGlue/releases/download/v0.1_arxiv/superpoint_lightglue.pth

# 聲明預設掛載點，以供存放frame/log/video/config
VOLUME /mnt/video
VOLUME /mnt/config
VOLUME /mnt/log
VOLUME /mnt/frame
VOLUME /mnt/compare_matchpoint

# 設置容器的默認命令
CMD ["python", "camera_angle_detection.py"]