from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.database import MongoDB
from app.schemas.user import Address, UserCreate, UserResponse, UserUpdate
from app.services.geocoding import geocode_address

router = APIRouter(prefix="/api/users", tags=["users"])


def user_doc_to_response(doc: dict) -> UserResponse:
    """Convert a MongoDB user document to an API response model.

    :param doc: Raw MongoDB document with ``_id`` as :class:`~bson.ObjectId`.
    :returns: Serialisable user response with string ID and optional coordinates.
    """
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
    """Create a new user and geocode their address.

    Coordinates are resolved via Nominatim and stored alongside the user
    document. If geocoding fails the user is still created with ``null``
    coordinates.

    :param payload: Validated user creation data including address.
    :returns: The created user with generated ID and coordinates.
    :raises HTTPException: 422 if validation fails (handled by FastAPI).
    """
    doc = payload.model_dump(mode="json")
    coords = await geocode_address(payload.address)
    doc["coordinates"] = coords.model_dump() if coords else None
    result = await MongoDB.get_database().users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return user_doc_to_response(doc)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, payload: UserUpdate):
    """Update an existing user's details.

    Only fields included in the request body are modified. Coordinates are
    re-geocoded only when the address actually changes, avoiding unnecessary
    Nominatim calls.

    :param user_id: MongoDB ObjectId as a hex string.
    :param payload: Partial user data — unset fields are left unchanged.
    :returns: The full updated user document.
    :raises HTTPException: 404 if the user does not exist.
    """
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    existing = await MongoDB.get_database().users.find_one({"_id": ObjectId(user_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True, mode="json")
    if not update_data:
        return user_doc_to_response(existing)

    if payload.address is not None:
        existing_address = Address(**existing["address"])
        if payload.address != existing_address:
            coords = await geocode_address(payload.address)
            update_data["coordinates"] = coords.model_dump() if coords else None

    await MongoDB.get_database().users.update_one(
        {"_id": ObjectId(user_id)}, {"$set": update_data}
    )
    updated = await MongoDB.get_database().users.find_one({"_id": ObjectId(user_id)})
    return user_doc_to_response(updated)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Retrieve a single user by ID.

    :param user_id: MongoDB ObjectId as a hex string.
    :returns: The user document with coordinates.
    :raises HTTPException: 404 if the user does not exist.
    """
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    doc = await MongoDB.get_database().users.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return user_doc_to_response(doc)


@router.get("", response_model=list[UserResponse])
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List all users with page-based pagination.

    :param page: 1-indexed page number (default ``1``).
    :param limit: Maximum users per page, capped at 100 (default ``20``).
    :returns: A list of user responses for the requested page.
    """
    skip = (page - 1) * limit
    cursor = MongoDB.get_database().users.find().skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    return [user_doc_to_response(doc) for doc in users]
