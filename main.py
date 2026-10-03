"""
Root entry point proxy for CareerCatalyst FastAPI application.
Allows running `uvicorn main:app` or `python main.py` directly from project root.
"""
from backend.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
