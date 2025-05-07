from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.db import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user import User
from app.schemas.schemas import TransactionCreate, Transaction as TransactionSchema
from app.utils.auth import get_current_active_user
from app.utils.logger import get_logger
from app.utils.db_utils import safe_db_transaction

logger = get_logger(__name__)

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)

@router.post("/", response_model=TransactionSchema, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: TransactionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verification code...
    
    db_transaction = Transaction(
        amount=transaction.amount,
        description=transaction.description,
        category_id=transaction.category_id,
        date=transaction.date or datetime.now(),
        user_id=current_user.id
    )
    
    with safe_db_transaction(db) as session:
        session.add(db_transaction)
        session.flush()  # Flush to get the ID
        logger.info(f"Transaction created with ID: {db_transaction.id}")
        return db_transaction

@router.get("/", response_model=List[TransactionSchema])
def read_transactions(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Base query - only return transactions belonging to the current user
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    # Apply category filter if provided
    if category_id is not None:
        # Verify category exists and belongs to user
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == current_user.id
        ).first()
        
        if not category:
            logger.warning(f"Category {category_id} not found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Category with ID {category_id} not found or does not belong to you"
            )
        
        query = query.filter(Transaction.category_id == category_id)
    
    # Apply pagination
    transactions = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
    
    return transactions

@router.get("/{transaction_id}", response_model=TransactionSchema)
def read_transaction(
    transaction_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if transaction is None:
        logger.warning(f"Transaction {transaction_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    return transaction

@router.put("/{transaction_id}", response_model=TransactionSchema)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Find the transaction
    db_transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if db_transaction is None:
        logger.warning(f"Transaction {transaction_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    # Verify the category exists and belongs to the user
    category = db.query(Category).filter(
        Category.id == transaction_data.category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        logger.warning(f"Category {transaction_data.category_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Category with ID {transaction_data.category_id} not found or does not belong to you"
        )
    
    try:
        # Update transaction attributes
        db_transaction.amount = transaction_data.amount
        db_transaction.description = transaction_data.description
        db_transaction.category_id = transaction_data.category_id
        if transaction_data.date:
            db_transaction.date = transaction_data.date
        
        db.commit()
        db.refresh(db_transaction)
        logger.info(f"Transaction {transaction_id} updated")
        return db_transaction
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update transaction {transaction_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transaction: {str(e)}"
        )

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if db_transaction is None:
        logger.warning(f"Transaction {transaction_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    try:
        db.delete(db_transaction)
        db.commit()
        logger.info(f"Transaction {transaction_id} deleted")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete transaction {transaction_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transaction: {str(e)}"
        )