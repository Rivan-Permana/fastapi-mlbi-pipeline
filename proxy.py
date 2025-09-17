from fastapi import FastAPI, Request
import requests
import subprocess

app = FastAPI()

CLOUD_RUN_URL = "https://fastapi-mlbi-pipeline-32684464346.asia-southeast2.run.app"

def get_identity_token() -> str:
    token = subprocess.check_output(
        ["gcloud", "auth", "print-identity-token"]
    ).decode().strip()
    return token

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    token = get_identity_token()

    body = await request.body()
    headers = {key: value for key, value in request.headers.items()}
    headers["Authorization"] = f"Bearer {token}"

    resp = requests.request(
        method=request.method,
        url=f"{CLOUD_RUN_URL}/{path}",
        headers=headers,
        data=body,
        params=request.query_params,
    )

    return {
        "status_code": resp.status_code,
        "content": resp.json()
        if "application/json" in resp.headers.get("content-type", "")
        else resp.text,
    }
