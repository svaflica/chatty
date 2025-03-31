import io
import hashlib
import base64

from minio import Minio

from config import settings


class MinioClient:
    def __init__(self, url, access_key, secret_key, bucket):
        self.client = Minio(
            url,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )
        self.bucket = bucket

        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            pass

    def put_object(self, file: bytes):
        img_recovered = base64.b64decode(file)

        value_as_a_stream = io.BytesIO(img_recovered)
        filename = hashlib.sha1(img_recovered).hexdigest()
        self.client.put_object(self.bucket, filename, value_as_a_stream, length=len(img_recovered))
        return filename

    def get_object(self, filename):
        obj = self.client.get_object(self.bucket, filename)
        if not obj.data:
            raise Exception('Couldn\'t find file in s3')
        return base64.b64encode(obj.data).decode('utf-8')


def get_minio_client():
    minio_client = MinioClient(
        settings.MINIO_URL,
        settings.AWS_ACCESS_KEY,
        settings.AWS_SECRET_KEY,
        settings.FILE_BUCKET_NAME,
    )
    yield minio_client
