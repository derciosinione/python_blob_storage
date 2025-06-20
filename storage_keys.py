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
