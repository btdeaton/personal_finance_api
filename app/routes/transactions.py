from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user import User
from app.schemas.schemas import TransactionCreate, Transaction as TransactionSchema
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)

@router.post("/", response_model=TransactionSchema)
def create_transaction(
    transaction: TransactionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify the category exists and belongs to the user
    category = db.query(Category).filter(
        Category.id == transaction.category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db_transaction = Transaction(
        amount=transaction.amount,
        description=transaction.description,
        category_id=transaction.category_id,
        date=transaction.date,
        user_id=current_user.id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/", response_model=List[TransactionSchema])
def read_transactions(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only return transactions belonging to the current user
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return transactions

@router.get("/{transaction_id}", response_model=TransactionSchema)
def read_transaction(
    transaction_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id  # Only allow access to own transactions
    ).first()
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction