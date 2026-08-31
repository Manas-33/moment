import os
import shutil
import uuid
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _has_cloudinary_creds() -> bool:
    return all([
        os.getenv('CLOUDINARY_CLOUD_NAME'),
        os.getenv('CLOUDINARY_API_KEY'),
        os.getenv('CLOUDINARY_API_SECRET'),
    ])


def _upload_to_local_media(file_path: str, public_id_prefix: str = 'shorts'):
    """Copy a generated video into Django's MEDIA_ROOT and return a public URL.

    Used when no Cloudinary credentials are configured so the project can run
    fully offline. The returned dict mirrors the Cloudinary shape so callers
    don't have to special-case the local path.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None

    try:
        local_dir = os.path.join(settings.MEDIA_ROOT, 'local')
        os.makedirs(local_dir, exist_ok=True)

        filename = os.path.basename(file_path)
        # Avoid collisions when the same generated filename is uploaded twice.
        unique_name = f"{public_id_prefix}_{uuid.uuid4().hex[:8]}_{filename}"
        dest_path = os.path.join(local_dir, unique_name)
        shutil.copyfile(file_path, dest_path)

        public_id = f"local/{unique_name}"
        url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}{settings.MEDIA_URL}local/{unique_name}"

        print(f"Stored generated video locally: {url}")
        return {'url': url, 'public_id': public_id}
    except Exception as e:
        logger.error(f"Local media upload error: {e}")
        return None


def upload_to_cloudinary(file_path, public_id_prefix='shorts'):
    """Upload a generated video and return a public URL + identifier.

    When Cloudinary creds are present we still use Cloudinary; otherwise the
    file is copied into the local ``media/local/`` directory and a localhost
    URL is returned. This keeps the rest of the pipeline unchanged whether the
    project is running in cloud or local mode.
    """
    if not _has_cloudinary_creds():
        return _upload_to_local_media(file_path, public_id_prefix)

    # Lazy import so the cloudinary package is only required in cloud mode.
    import cloudinary
    import cloudinary.uploader

    print("Uploading video to Cloudinary.")
    try:
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
            secure=True,
        )

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        filename = os.path.basename(file_path)
        public_id = f"{public_id_prefix}/{os.path.splitext(filename)[0]}"

        upload_result = cloudinary.uploader.upload(
            file_path,
            resource_type="video",
            public_id=public_id,
            overwrite=True,
            folder="shorts",
        )
        print("Cloudinary upload complete.")
        return {
            'url': upload_result['secure_url'],
            'public_id': upload_result['public_id'],
        }
    except Exception as e:
        logger.error(f"Cloudinary upload error: {e}; falling back to local storage")
        return _upload_to_local_media(file_path, public_id_prefix)


def update_supabase(username, youtube_url, cloudinary_urls):
    """Mirror processed videos to Supabase when creds are set; no-op otherwise.

    The local-only mode skips this entirely so the project runs without any
    Supabase configuration.
    """
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    if not supabase_url or not supabase_key:
        return None

    try:
        from supabase import create_client

        supabase_table = os.getenv('SUPABASE_TABLE', 'shorts')
        supabase = create_client(supabase_url, supabase_key)

        if isinstance(cloudinary_urls, str):
            cloudinary_urls = [cloudinary_urls]

        data_to_insert = [{
            "username": username,
            "youtube_url": youtube_url,
            "short_url": url,
            "created_at": "now()",
        } for url in cloudinary_urls]

        if data_to_insert:
            response = supabase.table(supabase_table).insert(data_to_insert).execute()
            if response.data:
                return response.data
        return None
    except Exception as e:
        logger.error(f"Supabase update error: {e}")
        return None
