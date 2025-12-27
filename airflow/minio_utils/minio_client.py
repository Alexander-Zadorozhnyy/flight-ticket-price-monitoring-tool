import json
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from typing import Any, Optional, Dict, List


class MinIOClient:
    def __init__(
        self, endpoint: str, access_key: str, secret_key: str, secure: bool = False
    ):
        """Initialize MinIO client"""
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def create_bucket(self, bucket_name: str, location: str = "us-east-1") -> bool:
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name, location=location)
                print(f"Bucket '{bucket_name}' created.")
            return True
        except S3Error as e:
            print(f"Error creating bucket: {e}")
            return False

    def upload_dict(
        self,
        bucket_name: str,
        data: dict,
        object_name: str,
        metadata: Optional[Dict] = None,
    ):
        json_data = json.dumps(data).encode("utf-8")
        return self.upload_file(bucket_name, json_data, object_name, metadata)

    def upload_file(
        self,
        bucket_name: str,
        data: bytes,
        object_name: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Upload file to MinIO"""
        try:
            data_length = len(data)
            data_stream = BytesIO(data)

            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=data_stream,
                length=data_length,
                metadata=metadata,
            )
            print(f"Uploaded '{object_name}' to bucket '{bucket_name}'")
            return True
        except S3Error as e:
            print(f"Error uploading: {e}")
            return False

    def read_file_to_memory(self, bucket_name: str, object_name: str):
        """Read file content directly into memory"""
        try:
            response = self.client.get_object(bucket_name, object_name)

            # Read the data
            data = response.read()
            response.close()
            response.release_conn()

            return data
        except S3Error as e:
            print(f"Error reading file: {e}")
            return None

    def list_files(self, bucket_name: str, prefix: str = "") -> List[str]:
        """List files in bucket"""
        try:
            objects = self.client.list_objects(
                bucket_name, prefix=prefix, recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing: {e}")
            return []

    def get_files_by_time(self, bucket_name: str, session_time: str) -> Dict[str, Any]:
        """
        Get all JSON files matching pattern "*{session_time}.json" and load them into memory.

        Args:
            bucket_name: Name of the bucket
            session_time: Time string to match in filenames (e.g., "2024-01-15_10-30")

        Returns:
            Dictionary where keys are filenames and values are parsed JSON content
        """
        try:
            # List all files in the bucket
            all_files = self.list_files(bucket_name)

            # Filter files that match the pattern "*{session_time}.json"
            matching_files = [
                file for file in all_files if file.endswith(f"{session_time}.json")
            ]

            if not matching_files:
                print(f"No files found matching pattern '*{session_time}.json'")
                return {}

            # Load each matching file into memory
            result = {}
            for filename in matching_files:
                try:
                    # Read file content
                    file_data = self.read_file_to_memory(bucket_name, filename)

                    if file_data:
                        # Parse JSON content
                        json_content = json.loads(file_data.decode("utf-8"))
                        result[filename] = json_content

                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON from {filename}: {e}")
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")

            print(f"Loaded {len(result)} files for session time: {session_time}")
            return result

        except Exception as e:
            print(f"Error in get_files_by_time: {e}")
            return {}


# Usage example
if __name__ == "__main__":
    # Initialize client
    minio_client = MinIOClient(
        endpoint="localhost:9000",
        access_key="pBpzPwHAkCciPnZSaud",
        secret_key="8We4NNIWSXjRztRluujpuGJX4KfT7TSZS75b3Yx",
        secure=False,
    )

    # Create bucket
    # minio_client.create_bucket("airline-data-raw")

    # Upload data
    # json_data = json.dumps({"key": "value", "message": "Hello, MinIO!"}).encode("utf-8")
    # minio_client.upload_file("airline-data", json_data, "file.json")

    # # List files
    files = minio_client.list_files("kypibilet-raw-data")
    print(f"Files in bucket: {files}")

    # # # Read file
    # data = minio_client.read_file_to_memory(
    #     "kypibilet-raw-data", "route_2_2025-12-26T20:48:42.498534"
    # )

    # print(f"Read data: {json.loads(data.decode('utf-8'))}" if data else "No data found")

    data = minio_client.get_files_by_time("kypibilet-raw-data", "2025-12-27T14:06:37")
    print(f"{data=}")
