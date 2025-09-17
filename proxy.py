# proxy.py
from fastapi import FastAPI, Request, Response
import httpx
import subprocess, time, os

app = FastAPI(title="Cloud Run Proxy", version="1.0.0")

CLOUD_RUN_URL = os.getenv(
    "CLOUD_RUN_URL",
    "https://fastapi-mlbi-pipeline-32684464346.asia-southeast2.run.app",
)

# --- simple in-memory token cache ---
_TOKEN = {"value": None, "exp": 0}
def get_identity_token() -> str:
    now = int(time.time())
    # refresh 5 minutes before expiry
    if _TOKEN["value"] and _TOKEN["exp"] - now > 300:
        return _TOKEN["value"]
    # gcloud token usually valid ~3600s
    token = subprocess.check_output(
        ["gcloud", "auth", "print-identity-token"]
    ).decode().strip()
    _TOKEN["value"] = token
    _TOKEN["exp"] = now + 3600
    return token

@app.get("/", include_in_schema=False)
def root():
    # biar nggak 404 waktu buka 127.0.0.1:8000/
    return {"ok": True, "hint": "Use /proxy/<path> to hit Cloud Run. Try /proxy/docs or your API path."}

@app.api_route("/proxy/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"])
async def proxy(request: Request, path: str):
    token = get_identity_token()

    # build target url
    url = f"{CLOUD_RUN_URL.rstrip('/')}/{path}"

    # copy headers (kecuali hop-by-hop)
    headers = dict(request.headers)
    headers["Authorization"] = f"Bearer {token}"
    headers.pop("host", None)
    headers.pop("content-length", None)

    # body & query
    body = await request.body()
    query = str(request.url.query)

    # forward
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.request(
            method=request.method,
            url=url if not query else f"{url}?{query}",
            headers=headers,
            content=body,
        )

    # pass-through response (status, headers, body)
    excluded = {"content-encoding", "transfer-encoding", "connection"}
    response_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded]
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(response_headers),
        media_type=resp.headers.get("content-type"),
    )
