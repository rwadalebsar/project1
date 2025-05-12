from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Sample data
class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    completed: bool = False

# In-memory database
items = [
    Item(id=1, name="Learn FastAPI", description="Create a simple API", completed=True),
    Item(id=2, name="Learn React", description="Create a simple frontend", completed=False),
    Item(id=3, name="Connect backend and frontend", description="Make them work together", completed=False),
]

@app.get("/")
def read_root():
    return {"message": "Welcome to the Todo API"}

@app.get("/api/items", response_model=List[Item])
def read_items():
    return items

@app.get("/api/items/{item_id}", response_model=Item)
def read_item(item_id: int):
    for item in items:
        if item.id == item_id:
            return item
    return {"error": "Item not found"}

@app.post("/api/items", response_model=Item)
def create_item(item: Item):
    items.append(item)
    return item

@app.put("/api/items/{item_id}", response_model=Item)
def update_item(item_id: int, updated_item: Item):
    for i, item in enumerate(items):
        if item.id == item_id:
            updated_item.id = item_id  # Ensure ID doesn't change
            items[i] = updated_item
            return updated_item
    return {"error": "Item not found"}

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    for i, item in enumerate(items):
        if item.id == item_id:
            deleted_item = items.pop(i)
            return {"message": f"Item {deleted_item.name} deleted successfully"}
    return {"error": "Item not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
