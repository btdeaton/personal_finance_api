from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date
import decimal
from decimal import Decimal

# User schemas
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# Category schemas - MOVED BEFORE TRANSACTION SCHEMAS
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# Transaction schemas with enhanced validation
class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount must be greater than zero")
    description: str = Field(..., min_length=3, max_length=100, description="Description must be between 3 and 100 characters")
    category_id: int = Field(..., gt=0, description="Must reference a valid category")
    date: Optional[datetime] = None

    @field_validator('amount')
    @classmethod
    def amount_precision(cls, v):
        # Ensure amount has at most 2 decimal places
        decimal_val = Decimal(str(v)).quantize(Decimal('0.01'))
        if decimal_val != Decimal(str(v)):
            raise ValueError('Amount must have at most 2 decimal places')
        return float(decimal_val)
    
    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v):
        if v.strip() == "":
            raise ValueError('Description cannot be empty or only whitespace')
        return v
    
    @model_validator(mode='after')
    @classmethod
    def check_future_date(cls, values):
        date_val = values.date
        if date_val and date_val > datetime.now():
            raise ValueError('Transaction date cannot be in the future')
        return values

class TransactionCreate(BaseModel):
    amount: float
    description: str
    category_id: int
    date: Optional[datetime] = None
    
    @field_validator('date')
    @classmethod
    def ensure_date_format(cls, v):
        if v is None:
            return v
        
        # If it's already a datetime object
        if isinstance(v, datetime):
            # Make naive if it has timezone
            if v.tzinfo is not None:
                return v.replace(tzinfo=None)
            return v
        
        # If it's a string, parse it
        try:
            # Parse ISO format string
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            # Convert to naive datetime
            return dt.replace(tzinfo=None)
        except:
            # Alternative parsing for other formats
            try:
                from dateutil import parser
                dt = parser.parse(v)
                return dt.replace(tzinfo=None)
            except:
                raise ValueError("Invalid date format")

class Transaction(TransactionBase):
    id: int
    user_id: int

    model_config = {
        "from_attributes": True
    }

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Budget schemas
class BudgetBase(BaseModel):
    amount: float = Field(..., gt=0)
    category_id: int
    start_date: Optional[date] = None
    end_date: date
    name: Optional[str] = None

class BudgetCreate(BudgetBase):
    pass

class Budget(BudgetBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# Budget status schema for reporting
class BudgetStatus(Budget):
    spent: float
    remaining: float
    percentage_used: float
    category: Category

    class Config:
        from_attributes = True