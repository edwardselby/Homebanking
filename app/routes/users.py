from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.database import db
from app.schemas.user import Address, UserCreate, UserResponse, UserUpdate
from app.services.geocoding import geocode_address

router = APIRouter(prefix="/api/users", tags=["users"])


def user_doc_to_response(doc: dict) -> UserResponse:
    coords = None
    if doc.get("coordinates"):
        coords = doc["coordinates"]
    return UserResponse(
        id=str(doc["_id"]),
        first_name=doc["first_name"],
        last_name=doc["last_name"],
        date_of_birth=doc["date_of_birth"],
        address=doc["address"],
        coordinates=coords,
    )


@router.post("", status_code=201, response_model=UserResponse)
async def create_user(payload: UserCreate):
    doc = payload.model_dump()
    coords = await geocode_address(payload.address)
    doc["coordinates"] = coords.model_dump() if coords else None
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return user_doc_to_response(doc)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, payload: UserUpdate):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    existing = await db.users.find_one({"_id": ObjectId(user_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return user_doc_to_response(existing)

    if payload.address is not None:
        existing_address = Address(**existing["address"])
        if payload.address != existing_address:
            coords = await geocode_address(payload.address)
            update_data["coordinates"] = coords.model_dump() if coords else None

    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    updated = await db.users.find_one({"_id": ObjectId(user_id)})
    return user_doc_to_response(updated)


@router.get("", response_model=list[UserResponse])
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    skip = (page - 1) * limit
    cursor = db.users.find().skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    return [user_doc_to_response(doc) for doc in users]
