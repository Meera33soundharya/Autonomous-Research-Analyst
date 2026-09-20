from fastapi import FastAPI

app = FastAPI(
    title="Autonomous Multi-Agent Research Analyst",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Autonomous Research Analyst API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }