import pytest
from unittest.mock import MagicMock, patch
from services.video_service import process_video_hls
from pathlib import Path

def test_process_video_hls_success(mocker):
    # Мокаем файловую систему
    mocker.patch("pathlib.Path.mkdir")
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.unlink")
    mocker.patch("shutil.rmtree")
    
    # Имитируем, что ffmpeg сгенерировал два файла: master.m3u8 и segment.ts
    mock_master_path = MagicMock(spec=Path)
    mock_master_path.name = "master.m3u8"
    mock_master_path.suffix = ".m3u8"
    
    mock_segment_path = MagicMock(spec=Path)
    mock_segment_path.name = "segment.ts"
    mock_segment_path.suffix = ".ts"
    
    mocker.patch("pathlib.Path.glob", return_value=[mock_master_path, mock_segment_path])
    
    # Мокаем встроенную функцию open
    mocker.patch("builtins.open", mocker.mock_open())
    
    # Мокаем subprocess
    mock_subprocess = mocker.patch("services.video_service.subprocess.run")
    
    # Мокаем S3 upload
    mock_upload = mocker.patch("services.video_service.upload_file_to_s3", return_value="http://s3/master.m3u8")
    
    # Мокаем БД
    mock_db = MagicMock()
    mock_hobby = MagicMock()
    mock_db.query().get.return_value = mock_hobby
    mocker.patch("services.video_service.SessionLocal", return_value=mock_db)

    # Вызываем функцию напрямую (не через .delay())
    process_video_hls(1, "test_video.mp4")
    
    # Проверки
    mock_subprocess.assert_called_once()
    assert mock_upload.call_count == 2
    mock_db.commit.assert_called_once()
    assert mock_hobby.video_path == "http://s3/master.m3u8"
    mock_db.close.assert_called_once()

def test_process_video_hls_subprocess_error(mocker):
    mocker.patch("pathlib.Path.mkdir")
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.unlink")
    mocker.patch("shutil.rmtree")
    
    mock_subprocess = mocker.patch("services.video_service.subprocess.run")
    import subprocess
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "ffmpeg")
    
    # При ошибке транскодирования исключение перехватывается, логируется, 
    # и должны быть вызваны функции очистки
    mock_rmtree = mocker.patch("shutil.rmtree")
    mock_unlink = mocker.patch("pathlib.Path.unlink")
    
    # Вызываем функцию
    process_video_hls(1, "test_video.mp4")
    
    # Проверки очистки
    mock_rmtree.assert_called_once()
    mock_unlink.assert_called_once()
