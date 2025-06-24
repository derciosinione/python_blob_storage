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

@app.route(route="project/{projectId}/comment")
def get_all_project_comments(req: func.HttpRequest) -> func.HttpResponse:
    try:
        project_id = req.route_params.get("projectId")
        if not project_id:
            return json_response(400, False, "O parâmetro projectId é obrigatório.")

        # Connect to Cosmos DB
        client = CosmosClient(COSMOS_URL, credential=COSMOS_KEY)
        db = client.get_database_client(COSMOS_DATABASE)
        container = db.get_container_client(COSMOS_CONTAINER)

        query = "SELECT * FROM c WHERE c.project_id = @project_id"
        parameters = [{"name": "@project_id", "value": project_id}]

        response = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False
        ))
        
        results = []
        
        for item in response:
           results.append({
            "id": item.get("id"),
            "project_id": item.get("project_id"),
            "description": item.get("description"),
            "username": item.get("username"),
            "created_at": item.get("created_at"),
        })

        return func.HttpResponse(
            body=json.dumps({
                "success": True,
                "data": results
            }),
            status_code=200,
            mimetype="application/json",
            headers=headers
        )

    except CosmosHttpResponseError as ce:
        logging.error(f"Erro Cosmos: {ce}")
        return json_response(500, False, "Erro ao comunicar com a base de dados.")
    except Exception as e:
        logging.error(f"Erro ao obter tarefas: {e}")
        return json_response(500, False, "Erro interno ao obter tarefas.")


