import azure.functions as func
import logging
import os
import json
from azure.storage.blob import (
    BlobServiceClient, generate_blob_sas, BlobSasPermissions
)
from datetime import datetime, timedelta

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Variáveis de ambiente
account_name       = os.getenv("STORAGE_ACCOUNT_NAME")
account_key        = os.getenv("STORAGE_ACCOUNT_KEY")
container_name     = os.getenv("STORAGE_CONTAINER_NAME")
account_url        = os.getenv("STORAGE_ACCOUNT_URL")
connection_string  = os.getenv("AzureWebJobsStorage")
project_prefix     = os.getenv("FUNCTION_PROJECT_PREFIX") 
headers = { "Access-Control-Allow-Origin": "*" }


# Gerar SAS token para leitura
def generate_read_sas(blob_name: str, hours: int = 1) -> str:
    token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=hours),
        content_disposition="inline"
    )
    return f"{account_url}{container_name}/{blob_name}?{token}"


def json_response(status: int, success: bool, message: str, data: dict = None) -> func.HttpResponse:        
    payload = {
        "success": success,
        "message": message,
        "data": data or {}
    }
    return func.HttpResponse(
        body=json.dumps(payload),
        status_code=status,
        mimetype="application/json",
        headers=headers
    )

@app.route(route="document/project/{project_id}/", methods=["GET"])
def get_files_by_project(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Pedido recebido para obter ficheiros por project_id.")

    try:
        project_id = req.route_params.get("project_id")
        if not project_id:
            logging.error("ID do projeto não fornecido na rota.")
            return json_response(400, False, "ID do projeto não fornecido na rota.")
        
        if not all([account_name, account_key, container_name, account_url, connection_string, project_prefix]):
            logging.error("Erro de configuração: variáveis de ambiente em falta.")
            return json_response(500, False, "Erro de configuração: variável de ambiente em falta.")

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        if not container_client.exists():
            logging.error(f"O container '{container_name}' não existe.")
            return json_response(404, False, f"O container '{container_name}' não existe.")

        project_root = f"{project_prefix}{project_id}"
        blobs = container_client.list_blobs(name_starts_with=project_root)
        blob_urls = []

        for blob in blobs:
            blob_name = blob.name
            clean_name = blob_name.replace(f"{project_root}/", "")
            blob_urls.append({
                "id": clean_name,
                "name": clean_name,
                "uploadedAt": blob.creation_time.isoformat() if blob.creation_time else None,
                "lastModified": blob.last_modified.isoformat() if blob.last_modified else None,
                "size": blob.size,
                "url": generate_read_sas(blob_name),
            })

        return func.HttpResponse(
            json.dumps({"id": project_id, "files": blob_urls}, indent=2),
            status_code=200,
            mimetype="application/json",
            headers=headers
        )

    except Exception as e:
        logging.error(f"Erro ao listar blobs: {e}")
        return json_response(500, False, "Erro interno ao buscar ficheiros.")
       
