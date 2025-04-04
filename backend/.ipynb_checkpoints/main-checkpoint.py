import uvicorn
from fastapi import FastAPI
from routers import interview

app = FastAPI()
app.include_router(interview.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)