import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from services.s3_service import upload_file_to_s3, delete_file_from_s3

def test_upload_file_to_s3_success(mocker):
    # Мокаем s3_client
    mock_s3_client = mocker.patch("services.s3_service.s3_client")
    mock_file = MagicMock()

    # Мокаем CDN_URL и S3_PUBLIC_URL
    mocker.patch("services.s3_service.CDN_URL", None)
    mocker.patch("services.s3_service.S3_PUBLIC_URL", "http://localhost:9000/hobbyhold")

    result = upload_file_to_s3(mock_file, "test_image.jpg", "image/jpeg")

    mock_s3_client.upload_fileobj.assert_called_once()
    assert result == "http://localhost:9000/hobbyhold/test_image.jpg"

def test_upload_file_to_s3_with_cdn(mocker):
    mock_s3_client = mocker.patch("services.s3_service.s3_client")
    mock_file = MagicMock()

    mocker.patch("services.s3_service.CDN_URL", "https://cdn.example.com")

    result = upload_file_to_s3(mock_file, "test_image.jpg")

    mock_s3_client.upload_fileobj.assert_called_once()
    assert result == "https://cdn.example.com/test_image.jpg"

def test_upload_file_to_s3_client_error(mocker):
    mock_s3_client = mocker.patch("services.s3_service.s3_client")
    mock_s3_client.upload_fileobj.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Error"}}, "Upload"
    )
    mock_file = MagicMock()

    with pytest.raises(ClientError):
        upload_file_to_s3(mock_file, "test_image.jpg")

def test_delete_file_from_s3_success(mocker):
    mock_s3_client = mocker.patch("services.s3_service.s3_client")

    delete_file_from_s3("test_image.jpg")

    mock_s3_client.delete_object.assert_called_once_with(Bucket=mocker.ANY, Key="test_image.jpg")

def test_delete_file_from_s3_client_error(mocker):
    mock_s3_client = mocker.patch("services.s3_service.s3_client")
    mock_s3_client.delete_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "Delete"
    )

    # Должно пройти без исключений, так как ошибка логируется и подавляется
    delete_file_from_s3("test_image.jpg")
    mock_s3_client.delete_object.assert_called_once()

def test_init_s3_bucket_success_exists(mocker):
    mock_s3_client = mocker.patch("services.s3_service.s3_client")
    
    # Бакет существует
    from services.s3_service import init_s3_bucket
    init_s3_bucket()
    
    mock_s3_client.head_bucket.assert_called_once()
    mock_s3_client.create_bucket.assert_not_called()
    mock_s3_client.put_bucket_policy.assert_called_once()

def test_init_s3_bucket_creates_bucket(mocker):
    mock_s3_client = mocker.patch("services.s3_service.s3_client")
    mock_s3_client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
    )
    
    from services.s3_service import init_s3_bucket
    init_s3_bucket()
    
    mock_s3_client.head_bucket.assert_called_once()
    mock_s3_client.create_bucket.assert_called_once()
    mock_s3_client.put_bucket_policy.assert_called_once()

