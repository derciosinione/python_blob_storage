import azure.functions as func
import logging
import os
import json
import uuid
from datetime import datetime, timedelta
from azure.storage.blob import (
    BlobServiceClient,
    generate_blob_sas,
    BlobSasPermissions,
    ContentSettings
)


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

account_name = os.getenv("STORAGE_ACCOUNT_NAME")
account_key = os.getenv("STORAGE_ACCOUNT_KEY")
container_name = os.getenv("STORAGE_CONTAINER_NAME")
account_url = os.getenv("STORAGE_ACCOUNT_URL")
connection_string = os.getenv("AzureWebJobsStorage")
project_prefix     = os.getenv("FUNCTION_PROJECT_PREFIX") 
headers = { "Access-Control-Allow-Origin": "*" }

def generate_read_sas(blob_name: str,  hours: int = 1) -> str:
    token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=hours),
        content_disposition="inline"  # <- Força visualização inline no browser
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

@app.route(route="upload_file/{id}", methods=["POST"])
def upload_file(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Recebido pedido para upload de ficheiro.")
    
    try:
        
        project_id = req.route_params.get("id")
        
        if not project_id:
            logging.error("ID do projeto não fornecido na rota.")
            return json_response(400, False, "ID do projeto não fornecido na rota.")
        
        
         # Validação de variáveis de ambiente
        if not all([account_name, account_key, container_name, account_url, connection_string]):
            logging.error("Erro de configuração: variáveis de ambiente em falta.")
            return json_response(500, False, "Erro de configuração: variável de ambiente em falta.")

            
        file = req.files.get("file")
        if not file:
            logging.error("Nenhum ficheiro enviado no corpo da requisição.")
            return json_response(400, False, "Nenhum ficheiro enviado no corpo da requisição.")

        _, ext = os.path.splitext(file.filename)
        
        allowed_ext = ['.jpg', '.jpeg', '.png', '.pdf', '.txt', '.docx']
        if ext.lower() not in allowed_ext:
            logging.error(f"Extensão '{ext}' não permitida.")
            return json_response(400, False, f"Extensão '{ext}' não permitida.")

        prefix = project_id

        # Gerar nome único
        unique_id = uuid.uuid4().hex
        blob_name = f"{unique_id}{ext}"
        if prefix:
            prefix = prefix.rstrip("/") + "/"
            blob_name = f"{project_prefix}{prefix}{blob_name}"
        
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        container_client = blob_service_client.get_container_client(container_name)

        if not container_client.exists():
            container_client.create_container()
        
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        content_type = file.content_type or "application/octet-stream"
        content_settings = ContentSettings(content_type=content_type)
        
        blob_client.upload_blob(file.stream, overwrite=True, content_settings=content_settings)

        blob_url = generate_read_sas(blob_name, hours=1)
        
        logging.info(f"Ficheiro {blob_name} enviado com sucesso para o Azure Blob Storage.")
        logging.info(f"URL do ficheiro: {blob_url}")
        
        return json_response(200, True, "Upload concluído com sucesso.", {
                "blob_name": blob_name,
                "url": blob_url,
                "content_type": content_type
            })

    except Exception as e:
        logging.error(f"Erro durante o upload: {e}")
        return json_response(500, False, "Erro interno ao enviar o ficheiro.")
