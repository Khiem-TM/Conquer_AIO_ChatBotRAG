"""Compatibility entrypoint.

Keeps a single source-of-truth FastAPI app to avoid route drift/404 between
`app.main` and `app.api.main`.
"""

from app.api.main import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
