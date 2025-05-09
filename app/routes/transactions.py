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
    # Log the incoming request data
    logger.info(f"Creating transaction: {transaction.dict()}")
    logger.info(f"User ID: {current_user.id}")
    
    try:
        # Verify the category exists and belongs to the user
        category = db.query(Category).filter(
            Category.id == transaction.category_id,
            Category.user_id == current_user.id
        ).first()
        
        if not category:
            logger.warning(f"Category {transaction.category_id} not found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Category with ID {transaction.category_id} not found or does not belong to you"
            )
        
        # Handle date with timezone awareness
        transaction_date = transaction.date
        if transaction_date is None:
            transaction_date = datetime.now()
        else:
            # Make sure date is naive (no timezone)
            if hasattr(transaction_date, 'tzinfo') and transaction_date.tzinfo is not None:
                # Convert to naive datetime in local timezone
                transaction_date = transaction_date.replace(tzinfo=None)
        
        # Create transaction object
        db_transaction = Transaction(
            amount=transaction.amount,
            description=transaction.description,
            category_id=transaction.category_id,
            date=transaction_date,
            user_id=current_user.id
        )
        
        # Log the transaction object
        logger.info(f"Transaction object created: {db_transaction.__dict__}")
        
        # Add the transaction to the database
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        logger.info(f"Transaction created with ID: {db_transaction.id}")
        return db_transaction
    except HTTPException as e:
        # Re-raise HTTP exceptions
        logger.error(f"HTTP error in create_transaction: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        # Log the full exception with traceback
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Failed to create transaction: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )

@router.get("/", response_model=List[TransactionSchema])
def read_transactions(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
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
        
        # Apply pagination and get results
        transactions = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
        
        # Return the results
        return transactions
    except Exception as e:
        # Log any errors
        logger.error(f"Error retrieving transactions: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transactions: {str(e)}"
        )

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
        # Handle date with timezone awareness (similar to create_transaction)
        transaction_date = transaction_data.date
        if transaction_date is not None and hasattr(transaction_date, 'tzinfo') and transaction_date.tzinfo is not None:
            # Convert to naive datetime in local timezone
            transaction_date = transaction_date.replace(tzinfo=None)
        
        # Update transaction attributes
        db_transaction.amount = transaction_data.amount
        db_transaction.description = transaction_data.description
        db_transaction.category_id = transaction_data.category_id
        if transaction_date:
            db_transaction.date = transaction_date
        
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