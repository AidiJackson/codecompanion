# server.py — production entrypoint (expose FastAPI on 5050)
import uvicorn
import os
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    uvicorn.run("api:app", host="0.0.0.0", port=port, log_level="info")