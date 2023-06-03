from django.core.files.storage import default_storage


def create_bucket():
    if not default_storage.bucket.creation_date:
        default_storage.bucket.create()
