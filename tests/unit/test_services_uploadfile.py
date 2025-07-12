import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from fastapi import UploadFile
from src.services.upload_file import UploadFileService


@pytest.fixture
def service():
    return UploadFileService(
        cloud_name="dummy", api_key="dummy_key", api_secret="dummy_secret"
    )


@pytest.fixture
def mock_upload_file():
    return UploadFile(filename="avatar.png", file=BytesIO(b"mock image"))


@patch("src.services.upload_file.cloudinary.uploader.upload")
@patch("src.services.upload_file.cloudinary.CloudinaryImage")
def test_upload_file_success(
    mock_cloudinary_image, mock_uploader, service, mock_upload_file
):
    # Mock upload result
    mock_uploader.return_value = {"version": "123456"}

    # Mock CloudinaryImage().build_url()
    mock_url_builder = MagicMock()
    mock_url_builder.build_url.return_value = "http://mocked.cloudinary.url/avatar.png"
    mock_cloudinary_image.return_value = mock_url_builder

    result = service.upload_file(mock_upload_file, username="testuser")

    assert result == "http://mocked.cloudinary.url/avatar.png"
    mock_uploader.assert_called_once()
    mock_url_builder.build_url.assert_called_once_with(
        width=250, height=250, crop="fill", version="123456"
    )
