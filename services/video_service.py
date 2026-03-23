import subprocess
import logging
from core.celery_app import celery_app
from services.s3_service import upload_file_to_s3
from core.config import UPLOAD_DIR
from database import SessionLocal
from models import Hobby

logger = logging.getLogger(__name__)

# HLS Транскодер с поддержкой разных разрешений (1080p, 720p, 480p)
@celery_app.task(name="process_video_hls")
def process_video_hls(hobby_id: int, original_filename: str):
    """
    Транскодирует видео в HLS плейлист (адаптивный битрейт).
    """
    temp_dir = UPLOAD_DIR / f"temp_video_{hobby_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    input_path = UPLOAD_DIR / original_filename

    # Сложная FFmpeg команда для создания мастер-плейлиста с адаптивным битрейтом    # (HLS - 1080, 720, 480)
    # В этом примере мы используем одну из наиболее стабильных схем нарезки
    cmd = [
        "ffmpeg", "-i", str(input_path),
        # Настройки видео потоков
        "-map", "0:v", "-map", "0:a", "-map", "0:v", "-map", "0:a", "-map", "0:v", "-map", "0:a",
        # 1080p
        "-s:v:0", "1920x1080", "-b:v:0", "5000k", "-maxrate:v:0", "5350k", "-bufsize:v:0", "7500k",
        # 720p
        "-s:v:1", "1280x720", "-b:v:1", "2800k", "-maxrate:v:1", "2996k", "-bufsize:v:1", "4200k",
        # 480p
        "-s:v:2", "854x480", "-b:v:2", "1400k", "-maxrate:v:2", "1498k", "-bufsize:v:2", "2100k",
        # Настройки аудио
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        # Настройки HLS (одна из самых современных схем)
        "-f", "hls", "-hls_time", "6", "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(temp_dir / "v%v_%03d.ts"),
        "-master_pl_name", "master.m3u8",
        "-var_stream_map", "v:0,a:0 v:1,a:1 v:2,a:2",
        str(temp_dir / "v%v.m3u8")
    ]

    try:
        logger.info(f"Starting transcoding for Hobby {hobby_id}")
        subprocess.run(cmd, check=True)

        # Теперь загружаем ВСЕ созданные файлы в S3
        master_url = ""
        for file in temp_dir.glob("*"):
            with open(file, "rb") as f:
                # В S3 мы сохраняем их в папку video/hobby_id/...
                s3_path = f"video/{hobby_id}/{file.name}"
                public_url = upload_file_to_s3(f, s3_path, "application/vnd.apple.mpegurl" if file.suffix == ".m3u8" else "video/MP2T")
                if file.name == "master.m3u8":
                    master_url = public_url

        # Обновляем базу данных
        db = SessionLocal()
        try:
            hobby = db.query(Hobby).get(hobby_id)
            if hobby:
                hobby.video_path = master_url
                db.commit()
                logger.info(f"Successfully processed video for Hobby {hobby_id}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error during video processing: {e}")
    finally:
        # Удаляем локальные временные файлы
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if input_path.exists():
            input_path.unlink()
