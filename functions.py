import uuid

import os
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

# Storage account info
account_url = "https://storagetaskfy.blob.core.windows.net"
account_name = "storagetaskfy"
container_name = "taskfy-blob-container"

default_credential = DefaultAzureCredential()

blob_service_client = BlobServiceClient(account_url, credential=default_credential)

def create_container():
    name = str(uuid.uuid4())
    container_client = blob_service_client.create_container(name)
    return container_client

def list_containers():
    print("Listing containers:")
    containers = blob_service_client.list_containers()
    for container in containers:
        print(f" - {container['name']}")


