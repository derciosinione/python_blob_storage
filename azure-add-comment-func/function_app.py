from asyncio import exceptions
import azure.functions as func
import logging
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError
import os
import uuid
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("DATABASE_NAME")
COSMOS_CONTAINER = "ProjectComments"

headers = { "Access-Control-Allow-Origin": "*" }

def json_response(status: int, success: bool, message: str, data: dict = None) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps({
            "success": success,
            "message": message,
            "data": data or {}
        }),
        status_code=status,
        mimetype="application/json",
        headers=headers
    )

@app.route(route="project/{projectId}/comment", methods=["POST"])
def add_project_comment(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        project_id = req.route_params.get("projectId")
        description = body.get("description")
        username = body.get("username")

        if not project_id or not description or not username:
            return json_response(400, False, "Parâmetros project, username e description são obrigatórios.")

        client = CosmosClient(COSMOS_URL, credential=COSMOS_KEY)

        db = client.create_database_if_not_exists(id=COSMOS_DATABASE)

        container = db.create_container_if_not_exists(
            id=COSMOS_CONTAINER,
            partition_key=PartitionKey(path="/project_id")
        )

        id = str(uuid.uuid4())
        
        data = {
            "id": id,
            "project_id": project_id,
            "username": username,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
        }

        container.create_item(body=data)

        return  func.HttpResponse(
                body=json.dumps(data or {}),
                status_code=201,
                mimetype="application/json",
                headers=headers
            )

    except CosmosHttpResponseError as ce:
        logging.error(f"Erro Cosmos: {ce.message}")
        return json_response(500, False, f"Erro ao comunicar com a base de dados. \n  {ce}")
    except Exception as e:
        logging.error(f"Erro ao criar tarefa: {e}")
        return json_response(500, False, f"Erro interno ao criar tarefa. \n {e}")