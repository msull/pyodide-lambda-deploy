import logging
import mimetypes
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi import Response
from mangum import Mangum
from simplesingletable import DynamoDbMemory
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi.middleware.gzip import GZipMiddleware

logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response


app.add_middleware(LoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)


_MEMORY = None


def _get_memory() -> DynamoDbMemory:
    global _MEMORY
    if _MEMORY is None:
        _MEMORY = DynamoDbMemory(
            logger=logger, table_name=os.environ["DYNAMODB_TABLE"], track_stats=True
        )
    return _MEMORY


@app.get("/api/ping")
def api_ping():
    return "pong"


@app.get("/flet/{name:path}", response_class=Response)
@app.get("/flet", response_class=Response)
def read_flet_file(name: str = "index.html"):
    try:
        # Define the base directory
        base_dir = Path("flet_app").resolve()
        # Resolve the target file path within the base directory
        file_path = (base_dir / name).resolve()

        # Ensure the file path is within the base directory
        if not file_path.is_file() or base_dir not in file_path.parents:
            raise FileNotFoundError

        # Detect MIME type based on file extension
        media_type, _ = mimetypes.guess_type(str(file_path))
        media_type = media_type or "application/octet-stream"

        # Read and serve the file contents in binary mode
        with open(file_path, "rb") as f:
            content = f.read()

        return Response(content=content, media_type=media_type)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{name} not found in flet_app")


@app.get("/pyodide", response_class=Response)
def read_index():
    try:
        with open("pyodide_example.html", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="pyodide_example.html not found")


@app.get("/pyodide2", response_class=Response)
def read_index():
    try:
        with open("pyodide_example2.html", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="pyodide_example2.html not found")


@app.get("/streamlit", response_class=Response)
def read_index():
    try:
        with open("streamlit_index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="streamlit_index.html not found")


@app.get("/streamlit_app.py", response_class=Response)
def read_streamlit_app():
    try:
        with open("streamlit_app.py", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/plain")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="streamlit_app.py not found")


_SVG_FAVICON = """
<svg width="100" height="100" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" fill="none">
  <!-- Background Circle -->
  <circle cx="24" cy="24" r="22" fill="#4A90E2" stroke="#2C3E50" stroke-width="2"/>

  <!-- Outer Dots Representing Statelessness and Decentralization -->
  <circle cx="8" cy="8" r="2" fill="#ECF0F1"/>
  <circle cx="40" cy="8" r="2" fill="#ECF0F1"/>
  <circle cx="8" cy="40" r="2" fill="#ECF0F1"/>
  <circle cx="40" cy="40" r="2" fill="#ECF0F1"/>

  <!-- Center Icon Representing Code Execution and Interactivity -->
  <path d="M24 15 L30 24 L24 33 L18 24 Z" fill="#ECF0F1"/>
  <circle cx="24" cy="24" r="3" fill="#4A90E2" stroke="#ECF0F1" stroke-width="1.5"/>

  <!-- Subtle Waves Representing Web Interaction -->
  <path d="M18 12 C20 14, 28 14, 30 12" stroke="#ECF0F1" stroke-width="1.2" stroke-linecap="round"/>
  <path d="M18 36 C20 34, 28 34, 30 36" stroke="#ECF0F1" stroke-width="1.2" stroke-linecap="round"/>
</svg>
""".strip()


@app.get("/favicon.ico")
def get_favicon():
    return Response(content=_SVG_FAVICON, media_type="image/svg+xml")


# AWS Lambda handler
handler = Mangum(app)
