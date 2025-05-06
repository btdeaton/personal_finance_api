from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.user import User
from app.schemas.schemas import UserCreate, User as UserSchema
from app.utils.auth import get_password_hash, get_current_active_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, password=hashed_password)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
     # Add default categories
    default_categories = [
        {"name": "Food", "description": "Groceries and dining out"},
        {"name": "Transportation", "description": "Gas, public transit, and car maintenance"},
        {"name": "Entertainment", "description": "Movies, games, and fun activities"},
        {"name": "Housing", "description": "Rent, mortgage, and home maintenance"},
        {"name": "Utilities", "description": "Electricity, water, internet, and phone"},
    ]
    
    for category_data in default_categories:
        db_category = Category(
            name=category_data["name"],
            description=category_data["description"],
            user_id=db_user.id
        )
        db.add(db_category)

    db.commit()

    return db_user

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/{user_id}", response_model=UserSchema)
def read_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only admin users would be able to view other users
    # For now, users can only view themselves
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user")
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user