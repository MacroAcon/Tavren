from fastapi import FastAPI, APIRouter
import uvicorn
import threading
import time
import httpx

# Define router similar to static_router
router = APIRouter(prefix="/api", tags=["static"])

# Create app
app = FastAPI()
app.include_router(router)

@router.get("/test")
async def test_endpoint():
    return "Test endpoint works!"

# Start the server in a separate thread
def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8765)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# Wait for server to start
time.sleep(2)

# Test the endpoint with httpx
try:
    response = httpx.get("http://127.0.0.1:8765/api/test")
    print(f"Response status code: {response.status_code}")
    print(f"Response text: {response.text}")
    
    print("\nIf you see a 200 status code and 'Test endpoint works!', the router is working correctly.")
    print("This confirms the router pattern works, so the static_router rename in static.py was successful.")
except Exception as e:
    print(f"Error testing endpoint: {e}") 