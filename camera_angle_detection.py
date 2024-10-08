import cv2
import torch
import logging
from pathlib import Path
from datetime import date, timedelta
from lightglue import LightGlue, SuperPoint
from lightglue.utils import load_image, rbd
from lightglue import viz2d
from send_email import send_email

# 關閉 pytorch gradient calculation 功能
torch.set_grad_enabled(False)

def setup_logging(log_path):
    """
    設置日誌系統的配置。
    :param log_path: 存放日誌文件的目錄路徑
    注意：這個函數沒有返回值，它的作用是配置全局的日誌系統
    配置完成後，可以在程序的任何地方使用 logging.info(), logging.warning() 等函數記錄日誌
    """
    # 獲取當前日期並格式化為 'YYYYMMDD' 形式
    today = date.today().strftime("%Y%m%d")
    
    # 構建日誌文件的完整路徑
    # 格式：/path/to/logs/camera_angle_detection_run_log-YYYYMMDD.txt
    log_file = f"{log_path}/camera_angle_detection_run_log-{today}.txt"
    
    # 配置日誌系統的基本設置
    logging.basicConfig(
        # 指定日誌文件的路徑
        filename=log_file,
        
        # 設置日誌級別為 INFO
        # 這意味着 INFO 級別及以上的日誌都會被記錄（INFO、WARNING、ERROR、CRITICAL）
        level=logging.INFO,
        
        # 設置日誌消息的格式
        # %(asctime)s: 時間戳
        # %(levelname)s: 日誌級別（如 INFO, WARNING 等）
        # %(message)s: 實際的日誌消息
        format='%(asctime)s - %(levelname)s - %(message)s',
        
        # 設置時間戳的格式
        # 這裡設置為 '年-月-日 時:分:秒'
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def setup_device():
    """
    設置執行PyTorch設備
    如果有CUDA GPU 可用,則使用CUDA GPU,否則使用CPU
    :return: PyTorch設備對象
    """
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def setup_extractor_and_matcher(device):
    """
    設置特徵提取器和特徵匹配器
    :param device: PyTorch設備對象
    :return: 特徵提取器和特徵匹配器
    """
    extractor = SuperPoint(max_num_keypoints=2048).eval().to(device)  # 初始化 SuperPoint 模型作為特徵提取器 / 設置最大關鍵點數量為 2048 / 將模型設置為評估模式 / 將模型移動到指定的設備（CPU 或 GPU
    matcher = LightGlue(features="superpoint").eval().to(device)  # 初始化 LightGlue 模型作為特徵匹配器 / 指定使用 SuperPoint 風格的特徵 / 將模型設置為評估模式 / 將模型移動到指定的設備（CPU 或 GPU）
    return extractor, matcher

def get_date_paths(video_path, frame_path):
    """
    獲取今日和昨日的日期路徑
    :param video_path: 影片記錄的根路徑
    :param frame_path: 存放 frame 根目錄路徑
    :return: 今日和昨日的 video 及 frame 目錄路徑
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%Y%m%d")
    yesterday_str = yesterday.strftime("%Y%m%d")
    today_video_dir = video_path / today_str
    today_frame_dir = frame_path / today_str
    yesterday_video_dir = video_path / yesterday_str
    yesterday_frame_dir = frame_path / yesterday_str
    return today_video_dir, today_frame_dir, yesterday_video_dir, yesterday_frame_dir

def process_directory(today_video_dir, today_frame_dir):
    """
    處理指定目錄中的影片和圖片
    1. 批次讀取 .mkv 檔案並保存第一幀為 .jpg
    2. 將 .jpg 存到對應日期的專用目錄
    3. 列出目錄中的所有 .jpg 檔案並存入 log
    :param today_video_dir: 要處理的影片目錄路徑
    :param today_frame_dir: 存放影片第一幀 .jpg 的目錄路徑
    """
    try:
        # 建立 today_frame_dir 目錄
        today_frame_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"建立目錄: {today_frame_dir}")
        # 批次讀取 today_video_dir 全部 .mkv 然後抓取第一幀另存到 today_frame_dir 並存為 .jpg
        for mkv_file in today_video_dir.glob("*-11.mkv"):
            try:
                jpg_file = today_frame_dir / mkv_file.with_suffix('.jpg').name
                video = cv2.VideoCapture(str(mkv_file))
                if not video.isOpened():
                    logging.error(f"錯誤：無法打開影片 {mkv_file}")
                    continue
                ret, frame = video.read()
                if ret:
                    cv2.imwrite(str(jpg_file), frame)
                    logging.info(f"成功：已將 {mkv_file} 的第一幀保存為 {jpg_file}")
                else:
                    logging.error(f"錯誤：無法讀取 {mkv_file} 的第一幀")
                video.release()
            except Exception as e:
                logging.error(f"處理影片 {mkv_file} 時發生錯誤: {str(e)}")

        logging.info(f"\n目錄 {today_frame_dir} 中的 .jpg 檔案：")
        for jpg_file in today_frame_dir.glob("*.jpg"):
            try:
                relative_path = jpg_file.relative_to(today_frame_dir)
                logging.info(f"檔名: {jpg_file.name}")
                logging.info(f"路徑: {relative_path}")
                logging.info("-" * 50)
            except Exception as e:
                logging.error(f"處理 .jpg 檔案 {jpg_file} 時發生錯誤: {str(e)}")

    except Exception as e:
        logging.error(f"處理目錄 {today_video_dir} 時發生錯誤: {str(e)}")

def read_config(config_path):
    """
    讀取並處理 config 的文字
    忽略'#'開頭的註解
    忽略空白字元/換行字元
    偵測'='為分割字元，左邊為key，右邊為value
    :param config_path: config 的路徑
    :return: 配置字典
    """
    config = {}
    with open(config_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

def compare_images(image0, image1, threshold_percentage, extractor, matcher, device):
    """
    比較兩張圖片，提取特徵點，進行匹配，並計算位移。

    參數:
    :param image0: torch.Tensor, 第一張圖片（參考圖）
    :param image1: torch.Tensor, 第二張圖片（比較圖）
    :param threshold_percentage: float, 位移閾值百分比，用於判斷顯著位移
    :param extractor: SuperPoint, 特徵提取器模型
    :param matcher: LightGlue, 特徵匹配器模型
    :param device: torch.device, 計算設備（CPU 或 GPU）

    返回:
    :return: tuple, 包含以下元素：
        - displacements: torch.Tensor, 匹配點之間的位移向量
        - vector_exceed_threshold_indices: torch.Tensor, 超過閾值的位移索引
        - matches01: dict, 匹配結果
        - m_kpts0, m_kpts1: torch.Tensor, 匹配的關鍵點
        - kpts0, kpts1: torch.Tensor, 原始關鍵點
    
    注意：
    1. rbd() 函數用於移除特徵和匹配結果中的批次維度。這是因為 SuperPoint 和 LightGlue 可能以批次形式處理數據，即使我們只處理單個圖像對。
    2. 位移計算使用了向量範數，這意味著它考慮了 x 和 y 方向的總體位移。
    3. 閾值比較是基於圖像尺寸的相對位移，這使得比較對圖像大小不敏感。
    4. 此函數假設輸入圖像已經被正確預處理並加載到指定的設備上。
    """
    # 提取特徵點
    feats0 = extractor.extract(image0.to(device))  # 從第一張圖提取特徵
    feats1 = extractor.extract(image1.to(device))  # 從第二張圖提取特徵

    # 進行特徵匹配
    matches01 = matcher({"image0": feats0, "image1": feats1})

    # 移除特徵和匹配結果的批次維度
    feats0, feats1, matches01 = [rbd(x) for x in [feats0, feats1, matches01]]

    # 提取關鍵點和匹配信息
    kpts0, kpts1 = feats0["keypoints"], feats1["keypoints"]  # 所有關鍵點
    matches = matches01["matches"]  # 匹配的索引
    m_kpts0 = kpts0[matches[..., 0]]  # 第一張圖中匹配的關鍵點
    m_kpts1 = kpts1[matches[..., 1]]  # 第二張圖中匹配的關鍵點

    # 計算匹配點之間的位移
    displacements = m_kpts1 - m_kpts0

    # 獲取圖像尺寸
    height, width = image0.shape[-2:]
    image_dimensions = torch.tensor([width, height], device=displacements.device, dtype=torch.float32)

    # 計算位移的相對大小（相對於圖像尺寸）
    vector_displacements = torch.linalg.vector_norm(displacements, dim=1) / torch.linalg.vector_norm(image_dimensions)

    # 找出超過閾值的位移
    vector_exceed_threshold_indices = torch.nonzero(vector_displacements > threshold_percentage).squeeze()

    return displacements, vector_exceed_threshold_indices, matches01, m_kpts0, m_kpts1, kpts0, kpts1

def main():
    """
    主函數,執行整個程式
    """
    # 設置在 Docker 外部檔案的存取目錄路徑
    config_path = Path("/mnt/config")
    video_path = Path("/mnt/video")
    log_path = Path("/mnt/log")
    frame_path = Path("/mnt/frame")
    compare_matchpoint_path = Path("/mnt/compare_matchpoint")

    # 設置 logging 紀錄相關執行結果
    setup_logging(log_path)

    # 獲取今日和昨日的日期路徑
    today_video_dir, today_frame_dir, yesterday_video_dir, yesterday_frame_dir = get_date_paths(video_path, frame_path)

    # 處理今日的監視器影片目錄
    if today_video_dir.exists():
        logging.info(f"\n處理目錄: {today_video_dir}")
        process_directory(today_video_dir, today_frame_dir)
    else:
        logging.error(f"錯誤：目錄 {today_video_dir} 不存在")

    # 讀取 config 檔案
    config = read_config(config_path / 'config.txt')
    threshold_percentage = float(config['threshold_percentage'])
    sender = config['sender']
    receivers = config['receivers'].split(',')
    subject = config['subject']
    body = config['body']
    attachment= config['attachment']

    # 設置用來執行 PyTorch 設備
    device = setup_device()

    # 設置特徵提取器和特徵匹配器
    extractor, matcher = setup_extractor_and_matcher(device)

    # 獲取昨天和今天的 frame 目錄中的所有 .jpg 檔案
    yesterday_files = list(yesterday_frame_dir.glob("*.jpg"))
    today_files = list(today_frame_dir.glob("*.jpg"))

    # 找出兩個 frame 目錄中檔名相同的 .jpg 檔案
    common_files = set(file.name for file in yesterday_files) & set(file.name for file in today_files)

    for file_name in common_files:
        yesterday_file = yesterday_frame_dir / file_name
        today_file = today_frame_dir / file_name

        # 載入圖片
        image0 = load_image(yesterday_file)
        image1 = load_image(today_file)

        # 比較圖片
        displacements, vector_exceed_threshold_indices, matches01, m_kpts0, m_kpts1, kpts0, kpts1 = compare_images(
            image0, image1, threshold_percentage, extractor, matcher, device
        )

        """
        # 檢測是否有移動或變形
        if vector_exceed_threshold_indices.numel() > 0:
            print(f"Alert: 今日監視器畫面{file_name} 有明顯的移動或變形! 閥值: {threshold_percentage * 100:.1f}%")
            vector_exceed_threshold_displacements = displacements[vector_exceed_threshold_indices]
            print(f"監視器畫面 {file_name} 矢量位移超過閾值 {threshold_percentage * 100:.1f}% 的 displacements 有:")
            print(vector_exceed_threshold_displacements)
        else:
            print(f"Info: {file_name} 無明顯的移動或變形. 閥值: {threshold_percentage * 100:.1f}%")
        """

        # 檢測是否有移動或變形
        if vector_exceed_threshold_indices.numel() > 0:
            logging.warning(f"Alert: 今日監視器畫面{file_name} 有明顯的移動或變形! 閥值: {threshold_percentage * 100:.1f}%")
            vector_exceed_threshold_displacements = displacements[vector_exceed_threshold_indices]
            logging.info(f"監視器畫面 {file_name} 矢量位移超過閾值 {threshold_percentage * 100:.1f}% 的 displacements 有:")
            logging.info(f"{vector_exceed_threshold_displacements}")
        else:
            logging.info(f"Info: {file_name} 無明顯的移動或變形. 閥值: {threshold_percentage * 100:.1f}%")

        # 繪製兩張圖匹配點,如果位移沒超出閾值則為綠色,超出閾值則為紅色
        axes = viz2d.plot_images([image0, image1])
        viz2d.plot_matches(m_kpts0, m_kpts1, color="lime", lw=0.2)
        if vector_exceed_threshold_indices.numel() > 0:
            exceed_kpts0 = m_kpts0[vector_exceed_threshold_indices]
            exceed_kpts1 = m_kpts1[vector_exceed_threshold_indices]
            viz2d.plot_matches(exceed_kpts0, exceed_kpts1, color="red", lw=0.2)
            viz2d.add_text(0, f'Stop after {matches01["stop"]} layers', fs=20)
            # 儲存兩張圖匹配點的圖片
            compare_today = date.today()
            viz2d.save_plot((compare_matchpoint_path) / f'comparison_matchpoint_{compare_today}_{file_name}')
        # 將匹配點的圖片上傳附件並寄出email
        #if vector_exceed_threshold_indices.numel() > 0:
            send_email(subject=f'{subject}:{file_name}', body=(body), attachment=(compare_matchpoint_path), file_name=f'{file_name}')

        """
        # 繪製兩張圖的特徵點
        kpc0, kpc1 = viz2d.cm_prune(matches01["prune0"]), viz2d.cm_prune(matches01["prune1"])
        viz2d.plot_images([image0, image1])
        viz2d.plot_keypoints([kpts0, kpts1], colors=[kpc0, kpc1], ps=10)
        # 儲存兩張圖特徵點的圖片
        viz2d.save_plot(video_path / f'comparison_featurepoint_{file_name}')
        """

if __name__ == "__main__":
    main()