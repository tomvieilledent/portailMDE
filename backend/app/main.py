from fastapi import FastAPI

app = FastAPI(title="portailMDE")


@app.get("/health")
def health():
    return {"status": "ok"}
