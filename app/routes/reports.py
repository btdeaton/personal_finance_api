from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from calendar import monthrange

from app.database.db import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.user import User
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

@router.get("/spending-by-category")
def spending_by_category(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get total spending by category within a date range.
    If no dates are provided, defaults to the current month.
    """
    # Set default date range to current month if not provided
    if not start_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
    
    if not end_date:
        end_date = date.today()
    
    # Query spending by category
    results = db.query(
        Category.id,
        Category.name,
        func.sum(Transaction.amount).label("total")
    ).join(
        Transaction, Category.id == Transaction.category_id
    ).filter(
        Transaction.user_id == current_user.id,
        func.date(Transaction.date) >= start_date,
        func.date(Transaction.date) <= end_date
    ).group_by(
        Category.id, Category.name
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).all()
    
    # Format results
    spending_data = [
        {
            "category_id": result.id, 
            "category_name": result.name, 
            "total": result.total
        } 
        for result in results
    ]
    
    # Calculate total spending
    total_spending = sum(item["total"] for item in spending_data)
    
    # Add percentage of total
    for item in spending_data:
        item["percentage"] = (item["total"] / total_spending * 100) if total_spending > 0 else 0
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_spending": total_spending,
        "spending_by_category": spending_data
    }

@router.get("/monthly-spending")
def monthly_spending(
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get spending trends by month for the last N months
    """
    # Calculate date range
    today = date.today()
    end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])
    start_date = date(
        today.year - ((today.month - months) // 12), 
        ((today.month - months) % 12) + 1 if (today.month - months) % 12 > 0 else 12, 
        1
    )
    
    # Query monthly totals
    results = db.query(
        extract('year', Transaction.date).label('year'),
        extract('month', Transaction.date).label('month'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        func.date(Transaction.date) >= start_date,
        func.date(Transaction.date) <= end_date
    ).group_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).order_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).all()
    
    # Format results
    monthly_data = []
    for result in results:
        month_name = date(int(result.year), int(result.month), 1).strftime('%B %Y')
        monthly_data.append({
            "year": int(result.year),
            "month": int(result.month),
            "month_name": month_name,
            "total": result.total
        })
    
    return {
        "months_analyzed": months,
        "monthly_spending": monthly_data
    }

@router.get("/transaction-trends")
def transaction_trends(
    interval: str = Query("monthly", enum=["daily", "weekly", "monthly"]),
    timeframe: int = 12,  # Number of intervals to analyze
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get transaction trends over time with customizable intervals.
    """
    today = date.today()
    
    # Calculate start date based on interval and timeframe
    if interval == "daily":
        start_date = today - timedelta(days=timeframe)
        date_format = '%Y-%m-%d'
        date_extract = func.date(Transaction.date)
    elif interval == "weekly":
        start_date = today - timedelta(weeks=timeframe)
        # This is more complex for weekly intervals
        date_format = 'Week %W, %Y'
        date_extract = func.date_trunc('week', Transaction.date)
    else:  # monthly
        year = today.year - (timeframe // 12)
        month = today.month - (timeframe % 12)
        if month <= 0:
            month += 12
            year -= 1
        start_date = date(year, month, 1)
        date_format = '%Y-%m'
        date_extract = func.date_trunc('month', Transaction.date)
    
    # Query data with interval grouping
    results = db.query(
        date_extract.label('interval_date'),
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        func.date(Transaction.date) >= start_date,
        func.date(Transaction.date) <= today
    ).group_by(
        date_extract
    ).order_by(
        date_extract
    ).all()
    
    # Format results
    trend_data = []
    for result in results:
        interval_date = result.interval_date
        # Format the date based on the interval type
        if isinstance(interval_date, date):
            formatted_date = interval_date.strftime(date_format)
        else:
            # Handle case when date_trunc returns a datetime or string
            formatted_date = str(interval_date)
            
        trend_data.append({
            "interval": formatted_date,
            "transaction_count": result.count,
            "total_amount": result.total
        })
    
    return {
        "interval": interval,
        "timeframe": timeframe,
        "trend_data": trend_data
    }

@router.get("/budget-performance")
def budget_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get performance metrics for all budgets.
    """
    # Get all budgets for current user
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    
    performance_data = []
    for budget in budgets:
        # Get category info
        category = db.query(Category).filter(Category.id == budget.category_id).first()
        
        # Sum transactions for this budget
        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category_id == budget.category_id,
            func.date(Transaction.date) >= budget.start_date,
            func.date(Transaction.date) <= budget.end_date
        ).scalar() or 0
        
        # Calculate metrics
        remaining = budget.amount - spent
        percentage_used = (spent / budget.amount * 100) if budget.amount > 0 else 0
        status = "On Track" if percentage_used <= 100 else "Over Budget"
        
        # Check if budget is current
        today = date.today()
        is_active = budget.start_date <= today <= budget.end_date
        days_remaining = (budget.end_date - today).days if is_active else 0
        
        # Calculate burn rate and forecast
        total_days = (budget.end_date - budget.start_date).days
        days_elapsed = min((today - budget.start_date).days, total_days)
        
        if days_elapsed > 0:
            daily_burn_rate = spent / days_elapsed
            forecast_end_amount = spent + (daily_burn_rate * days_remaining)
            forecast_status = "Under Budget" if forecast_end_amount <= budget.amount else "Projected Over Budget"
        else:
            daily_burn_rate = 0
            forecast_end_amount = 0
            forecast_status = "Not Started"
        
        performance_data.append({
            "budget_id": budget.id,
            "budget_name": budget.name or f"Budget for {category.name}",
            "category": category.name,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "is_active": is_active,
            "budget_amount": budget.amount,
            "spent": spent,
            "remaining": remaining,
            "percentage_used": percentage_used,
            "status": status,
            "days_remaining": days_remaining if days_remaining > 0 else 0,
            "daily_burn_rate": daily_burn_rate,
            "forecast_end_amount": forecast_end_amount,
            "forecast_status": forecast_status
        })
    
    return {
        "budget_performance": performance_data
    }

@router.get("/spending-insights")
def spending_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Provides overall insights into spending patterns.
    """
    today = date.today()
    first_of_month = date(today.year, today.month, 1)
    last_month_start = date(today.year, today.month - 1, 1) if today.month > 1 else date(today.year - 1, 12, 1)
    last_month_end = date(today.year, today.month, 1) - timedelta(days=1)
    
    # This month's spending
    this_month_spending = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        func.date(Transaction.date) >= first_of_month,
        func.date(Transaction.date) <= today
    ).scalar() or 0
    
    # Last month's spending
    last_month_spending = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        func.date(Transaction.date) >= last_month_start,
        func.date(Transaction.date) <= last_month_end
    ).scalar() or 0
    
    # Month-over-month change
    mom_change = ((this_month_spending - last_month_spending) / last_month_spending * 100) if last_month_spending > 0 else 0
    
    # Biggest expense category this month
    biggest_category = db.query(
        Category.name,
        func.sum(Transaction.amount).label("total")
    ).join(
        Transaction, Category.id == Transaction.category_id
    ).filter(
        Transaction.user_id == current_user.id,
        func.date(Transaction.date) >= first_of_month,
        func.date(Transaction.date) <= today
    ).group_by(
        Category.name
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).first()
    
    biggest_expense_category = biggest_category.name if biggest_category else "No transactions"
    biggest_expense_amount = biggest_category.total if biggest_category else 0
    
    # Average daily spending this month
    days_elapsed = (today - first_of_month).days + 1
    avg_daily_spending = this_month_spending / days_elapsed if days_elapsed > 0 else 0
    
    # Number of transactions this month
    transaction_count = db.query(func.count(Transaction.id)).filter(
        Transaction.user_id == current_user.id,
        func.date(Transaction.date) >= first_of_month,
        func.date(Transaction.date) <= today
    ).scalar() or 0
    
    # Average transaction amount
    avg_transaction = this_month_spending / transaction_count if transaction_count > 0 else 0
    
    return {
        "this_month_spending": this_month_spending,
        "last_month_spending": last_month_spending,
        "month_over_month_change": mom_change,
        "biggest_expense_category": biggest_expense_category,
        "biggest_expense_amount": biggest_expense_amount,
        "average_daily_spending": avg_daily_spending,
        "transaction_count": transaction_count,
        "average_transaction_amount": avg_transaction,
        "days_elapsed": days_elapsed,
        "days_in_month": monthrange(today.year, today.month)[1]
    }