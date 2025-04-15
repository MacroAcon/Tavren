from fastapi import FastAPI, APIRouter
import uvicorn

# Define a simple router
router = APIRouter()

# Create a simple endpoint
@router.get("/")
def read_root():
    return {"message": "Hello World"}

# Create the FastAPI app
app = FastAPI()

# Include the router in the app
app.include_router(router)

# Run the app directly
if __name__ == "__main__":
    print("Starting test server. If this runs without errors, APIRouter is working correctly.")
    print("Visit http://127.0.0.1:8000/ in your browser to see the result.")
    uvicorn.run(app, host="127.0.0.1", port=8000) 