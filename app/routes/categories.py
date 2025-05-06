from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.schemas import CategoryCreate, Category as CategorySchema
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)

@router.post("/", response_model=CategorySchema)
def create_category(
    category: CategoryCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if a category with the same name already exists for this user
    db_category = db.query(Category).filter(
        Category.name == category.name,
        Category.user_id == current_user.id
    ).first()
    
    if db_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    # Create new category
    db_category = Category(
        name=category.name,
        description=category.description,
        user_id=current_user.id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/", response_model=List[CategorySchema])
def read_categories(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only return categories belonging to the current user
    categories = db.query(Category).filter(
        Category.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return categories

@router.get("/{category_id}", response_model=CategorySchema)
def read_category(
    category_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update category attributes
    db_category.name = category.name
    db_category.description = category.description
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(db_category)
    db.commit()
    return {"detail": "Category deleted successfully"}