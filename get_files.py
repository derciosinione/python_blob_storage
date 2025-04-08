from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

# Storage account info
account_url = "https://storagetaskfy.blob.core.windows.net"
account_name = "storagetaskfy"
container_name = "taskfy-blob-container"

# Your storage account key (ensure you protect it in production)
account_key = "Y7SNjTbPrqIE++F/pFMdvX6HfzwnRw9q6HJFz7oo00468Bu+azQOnZdv70kaLBBcVxYYv1FjaJSK+AStGbEDmQ=="

# Construct the connection string
connection_string = (
    f"DefaultEndpointsProtocol=https;"
    f"AccountName={account_name};"
    f"AccountKey={account_key};"
    "EndpointSuffix=core.windows.net"
)

# Create the BlobServiceClient using the connection string
blob_service_client = BlobServiceClient.from_connection_string(connection_string)


def list_images_with_sas():
    # Get a client for your container
    container_client = blob_service_client.get_container_client(container_name)

    print("Listing images and their SAS URLs:")

    for blob in container_client.list_blobs():
        # Generate SAS token for each blob
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob.name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),  # Grant read permission
            expiry=datetime.utcnow() + timedelta(hours=1)  # Set token expiration time
        )

        # Construct the full URL using the SAS token
        blob_url = f"{account_url}/{container_name}/{blob.name}?{sas_token}"

        print(f"Image: {blob.name}")
        print(f"SAS URL: {blob_url}\n")


if __name__ == '__main__':
    list_images_with_sas()
