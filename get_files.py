from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

import json
import subprocess

def get_storage_account_keys(resource_group, storage_account_name):
    cmd = [
        "az", "storage", "account", "keys", "list",
        "--resource-group", resource_group,
        "--account-name", storage_account_name,
        "--output", "json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    keys = json.loads(result.stdout)
    return keys[0]["value"]

resource_group = "Taskify"
storage_account_name = "storagetaskfy"
account_key = get_storage_account_keys(resource_group, storage_account_name)
print("Account Key:", account_key)

account_url = "https://storagetaskfy.blob.core.windows.net"
container_name = "taskfy-blob-container"

# Construct the connection string
connection_string = (
    f"DefaultEndpointsProtocol=https;"
    f"AccountName={storage_account_name};"
    f"AccountKey={account_key};"
    "EndpointSuffix=core.windows.net"
)

blob_service_client = BlobServiceClient.from_connection_string(connection_string)

def list_images_with_sas():
    container_client = blob_service_client.get_container_client(container_name)

    print("Listing images and their SAS URLs:")

    for blob in container_client.list_blobs():
        sas_token = generate_blob_sas(
            account_name=storage_account_name,
            container_name=container_name,
            blob_name=blob.name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),  # Grant read permission
            expiry=datetime.utcnow() + timedelta(hours=1)  # Set token expiration time
        )

        blob_url = f"{account_url}/{container_name}/{blob.name}?{sas_token}"

        print(f"Image: {blob.name}")
        print(f"SAS URL: {blob_url}\n")


if __name__ == '__main__':
    list_images_with_sas()
