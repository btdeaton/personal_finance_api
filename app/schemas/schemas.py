from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

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

# Transaction schemas - NOW AFTER CATEGORY SCHEMAS
class TransactionBase(BaseModel):
    amount: float
    description: str
    category_id: int
    date: Optional[datetime] = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# This now works because Category is defined above
class TransactionWithCategory(TransactionBase):
    id: int
    user_id: int
    category: Category

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Budget schemas
class BudgetBase(BaseModel):
    amount: float
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