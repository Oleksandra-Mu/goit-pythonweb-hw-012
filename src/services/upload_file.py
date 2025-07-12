import cloudinary
import cloudinary.uploader


class UploadFileService:
    """Service helper to upload user files (e.g., avatars) to Cloudinary.

    The class encapsulates Cloudinary configuration on instantiation and exposes
    a simple `upload_file` static method that returns a ready-to-use CDN URL for
    the stored image.
    """
    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        """Configure Cloudinary credentials for subsequent uploads.

        Args:
            cloud_name: Cloudinary cloud name/identifier.
            api_key: Public API key issued by Cloudinary.
            api_secret: Corresponding API secret.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """Upload a file object to Cloudinary folder `RestApp/` and return its URL.

        Args:
            file: FastAPI `UploadFile` or any file-like object with a `.file` attribute.
            username: The username used to compose the public_id so that each
                user's image is overwritten on subsequent uploads.

        Returns:
            URL (str) pointing to a 250x250 cropped version of the uploaded image.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
