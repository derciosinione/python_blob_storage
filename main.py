from typing import List, Dict
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

from azure.core.exceptions import ResourceNotFoundError

import os
import uuid
from azure.core.exceptions import ResourceExistsError

from storage_keys import get_storage_account_keys

resource_group = "Taskify"
storage_account_name = "storagetaskfy"
account_key = get_storage_account_keys(resource_group, storage_account_name)

account_url = "https://storagetaskfy.blob.core.windows.net"
container_name = "taskfy-blob-container"

connection_string = (
    f"DefaultEndpointsProtocol=https;"
    f"AccountName={storage_account_name};"
    f"AccountKey={account_key};"
    "EndpointSuffix=core.windows.net"
)

blob_service_client = BlobServiceClient.from_connection_string(connection_string)

def create_container():
    return blob_service_client.create_container(container_name)


def generate_read_sas(blob_name: str, hours: int = 1) -> str:
    token = generate_blob_sas(
        account_name=storage_account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=hours)
    )
    return f"{account_url}/{container_name}/{blob_name}?{token}"


def get_or_create_container():
    client = blob_service_client.get_container_client(container_name)
    if not client.exists():
        client = create_container()
    return client


def blob_exists(blob_name: str) -> bool:
    """
    Retorna True se o blob existir, False caso contrário.
    """
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    try:
        return blob_client.exists()
    except ResourceNotFoundError:
        # em algumas versões do SDK ou em caso de permissão negação, capturamos o erro
        return False


def list_images_with_sas():
    container_client = get_or_create_container()
    
    print("Listing images and their SAS URLs: \n")
    
    for blob in container_client.list_blobs():
        sas_token = generate_read_sas(blob.name, 1)

        blob_url = f"{account_url}/{container_name}/{blob.name}?{sas_token}"

        # print(f"Image: {blob.name}")
        print(f"SAS URL: {blob_url}\n")


def get_blob_url(blob_name: str) -> str:
    """
    Retorna a URL completa do blob, incluindo o SAS token.
    """
    _ = get_or_create_container()
    
    if not blob_exists(blob_name):
        raise ResourceNotFoundError(f"Blob '{blob_name}' não encontrado no container '{container_name}'.")
    
    sas_token = generate_read_sas(blob_name, 1)
    return f"{account_url}/{container_name}/{blob_name}?{sas_token}"


def get_blob_url(blob_names: List[str]) -> Dict[str, str]:
    container_client = get_or_create_container()
    sas_urls: Dict[str, str] = {}

    for name in blob_names:
        blob_client = container_client.get_blob_client(name)
        
        # opcional: checar existência
        if not blob_client.exists():
            sas_urls[name] = None
            continue

        sas_token = generate_read_sas(name, 1)
        sas_urls[name] = f"{account_url}/{container_name}/{name}?{sas_token}"
    
    return sas_urls




def upload_document_unique(file_path: str, prefix: str = None, overwrite: bool = False) -> str:
    """
    Faz upload de um arquivo local para o container, gerando um nome de blob único.
    
    :param file_path: caminho completo para o arquivo local.
    :param prefix: prefixo opcional (ex: "docs/" ou "images/") para organizar dentro do container.
    :param overwrite: se True, sobrescreve o blob existente; se False, gera erro se já existir.
    :return: o nome do blob criado.
    """
    # Extrai extensão do arquivo, ex: ".pdf", ".png"
    _, ext = os.path.splitext(file_path)
    
    unique_id = uuid.uuid4().hex
    
    blob_name = f"{unique_id}{ext}"
    if prefix:
        # garante que o prefixo termine com "/"
        prefix = prefix.rstrip("/") + "/"
        blob_name = f"{prefix}{blob_name}"

    container_client = get_or_create_container()

    blob_client = container_client.get_blob_client(blob_name)

    with open(file_path, "rb") as data:
        try:
            blob_client.upload_blob(data, overwrite=overwrite)
            print(f"✔ Upload concluído como '{blob_name}'")
            return blob_name
        except ResourceExistsError:
            print(f"❌ Blob '{blob_name}' já existe. Tente novamente ou habilite overwrite=True.")
            return None
        except Exception as e:
            print(f"❌ Erro ao fazer upload de '{file_path}': {e}")
            return None
            

if __name__ == "__main__":
    
    # # Exemplo de uso:
    # to_check = "Dashboard.pdf"
    # if blob_exists(to_check):
    #     print(f"O blob '{to_check}' existe!")
    # else:
    #     print(f"O blob '{to_check}' NÃO foi encontrado.")
        
    # list_images_with_sas()
    
    # path_name = "docs/pedidosss.pdf"
    # nome_blob2 = upload_document_unique(path_name, overwrite=True)
    
    blob_names = [
        "Dashboard.pdf",
        "PedidosdeCompensasao.pdf",
        "pedidosss.pdf"
    ]
    
    urls = get_blob_url(blob_names)
    
    urls = get_blob_url(blob_names)
    print("URLs dos blobs:")
    for name, url in urls.items():
        print(f" - {name}: {url or 'NÃO ENCONTRADO'}")
    

