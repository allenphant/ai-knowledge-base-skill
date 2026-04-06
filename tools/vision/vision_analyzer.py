import cv2
import os
import sys
from yt_dlp import YoutubeDL

def download_video(url, output_dir="temp_video"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    ydl_opts = {
        'format': 'best', # 改為自動選擇最佳可用格式
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

def extract_frames(video_path, output_dir="frames", interval_seconds=2):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    interval_frames = int(fps * interval_seconds)
    
    count = 0
    saved_count = 0
    success, image = vidcap.read()
    
    while success:
        if count % interval_frames == 0:
            frame_path = os.path.join(output_dir, f"frame_{saved_count:03d}.jpg")
            cv2.imwrite(frame_path, image)
            saved_count += 1
        success, image = vidcap.read()
        count += 1
    
    vidcap.release()
    return saved_count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vision_analyzer.py [URL]")
        sys.exit(1)
    
    target_url = sys.argv[1]
    print(f"[*] 正在分析影片: {target_url}")
    
    try:
        video_file = download_video(target_url)
        print(f"[+] 下載完成: {video_file}")
        
        num_frames = extract_frames(video_file)
        print(f"[+] 抽幀完成: 共提取 {num_frames} 張關鍵幀於 'frames/' 目錄。")
        
        print("\n[!] 提示: 你現在可以將 'frames/' 資料夾中的圖片傳送給我進行視覺歸納。")
    except Exception as e:
        print(f"[!] 發生錯誤: {str(e)}")
