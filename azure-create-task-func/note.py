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
  
allowed_ext = [
    '.jpg', 
    '.jpeg',
    '.png', 
    '.pdf', 
    '.txt', 
    '.docx'
]


def validate_file_extensions(files, allowed_extensions: list) -> str:
    for file in files:
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in allowed_extensions:
            return f"Extensão '{ext}' não permitida. Esperadas: {', '.join(allowed_extensions)}"
    return None 


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

@app.route(route="document/project/{id}/upload/", methods=["POST"])
def upload_file(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Recebido pedido para upload de ficheiro.")
    
    try:
        
        project_id = req.route_params.get("id")
        
        if not project_id:
            logging.error("ID do projeto não fornecido na rota.")
            return json_response(400, False, "ID do projeto não fornecido na rota.")
        
        prefix = project_id
        
         # Validação de variáveis de ambiente
        if not all([account_name, account_key, container_name, account_url, connection_string]):
            logging.error("Erro de configuração: variáveis de ambiente em falta.")
            return json_response(500, False, "Erro de configuração: variável de ambiente em falta.")

        files  = req.files.getlist("files")
        
        if not files:
            logging.error("Nenhum ficheiro enviado no corpo da requisição.")
            return json_response(400, False, "Nenhum ficheiro enviado no corpo da requisição.")
        
        file_validation_message = validate_file_extensions(files, allowed_ext)
        
        if file_validation_message:
            logging.error(file_validation_message)
            return json_response(400, False, file_validation_message)
            
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        container_client = blob_service_client.get_container_client(container_name)

        if not container_client.exists():
            container_client.create_container()
        

        results = []
        
        for file in files:
                        
            file_name, ext = os.path.splitext(file.filename)
                     
            if ext.lower() not in allowed_ext:
                logging.error(f"Extensão '{ext}' não permitida.")
                return json_response(400, False, f"Extensão '{ext}' não permitida.")

            # Gerar nome único
            # unique_id = uuid.uuid4().hex
            # blob_name = f"{unique_id}{ext}"
        
            blob_name : str = file_name
            
            if prefix:
                prefix = prefix.rstrip("/") + "/"
                blob_name = f"{project_prefix}{prefix}{blob_name}"
                blob_name = blob_name.replace(" ", "_").replace(":", "_").replace("\\", "_")                

            content_type = file.content_type or "application/octet-stream"
            content_settings = ContentSettings(content_type=content_type)
            
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            
            blob_client.upload_blob(file.stream, overwrite=True, content_settings=content_settings)

            blob_url = generate_read_sas(blob_name, hours=1)
            
            results.append({
                "blob_name": blob_name,
                "url": blob_url,
                "content_type": content_type
            })
        
            logging.info(f"Ficheiro {blob_name} enviado com sucesso para o Azure Blob Storage.")
            logging.info(f"URL do ficheiro: {blob_url}")
        
        
        return json_response(200, True, "Upload concluído com sucesso.", {"files": results})

    except Exception as e:
        logging.error(f"Erro durante o upload: {e}")
        return json_response(500, False, "Erro interno ao enviar o ficheiro.")
