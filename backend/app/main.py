from fastapi import FastAPI

app = FastAPI(title="AI Executive Assistant")

@app.get("/")
def root():
    return {"message": "Backend Running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
