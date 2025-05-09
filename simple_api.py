from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API is working!"}

if __name__ == "__main__":
    print("Starting minimal API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)