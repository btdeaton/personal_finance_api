# Personal Finance API

A comprehensive RESTful API for personal finance management built with FastAPI and SQLAlchemy.

## Features

- **User Authentication:** Secure JWT-based authentication system
- **Transaction Management:** Create, read, update, and delete financial transactions
- **Categories:** Organize transactions with customizable categories
- **Budget Tracking:** Set and monitor spending limits for different categories
- **Financial Analytics:** Generate insightful reports on spending patterns
- **Enhanced Validation:** Robust input validation for data integrity
- **Error Handling:** Comprehensive error handling with detailed messages
- **Rate Limiting:** Protection against excessive API usage
- **Performance Monitoring:** Response time tracking for performance optimization

## Tech Stack

- **FastAPI:** Modern, high-performance web framework
- **SQLAlchemy:** SQL toolkit and Object-Relational Mapping
- **Pydantic:** Data validation and settings management
- **SQLite:** Lightweight database engine
- **JWT:** JSON Web Tokens for secure authentication
- **Uvicorn:** ASGI server for serving the application

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/personal-finance-api.git
cd personal-finance-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python run.py
```

The API will be available at http://localhost:8000/docs for interactive documentation.

## API Documentation

### Authentication Endpoints

- `POST /token`: Login and receive an access token
- `GET /users/me`: Get current user information

### User Endpoints

- `POST /users/`: Create a new user
- `GET /users/{user_id}`: Get user details

### Category Endpoints

- `GET /categories/`: List all categories
- `POST /categories/`: Create a new category
- `GET /categories/{category_id}`: Get category details
- `PUT /categories/{category_id}`: Update a category
- `DELETE /categories/{category_id}`: Delete a category

### Transaction Endpoints

- `GET /transactions/`: List all transactions
- `POST /transactions/`: Create a new transaction
- `GET /transactions/{transaction_id}`: Get transaction details
- `PUT /transactions/{transaction_id}`: Update a transaction
- `DELETE /transactions/{transaction_id}`: Delete a transaction

### Budget Endpoints

- `GET /budgets/`: List all budgets
- `POST /budgets/`: Create a new budget
- `GET /budgets/{budget_id}`: Get budget details
- `PUT /budgets/{budget_id}`: Update a budget
- `DELETE /budgets/{budget_id}`: Delete a budget
- `GET /budgets/status`: Get status of all budgets

### Reporting Endpoints

- `GET /reports/spending-by-category`: Analyze spending by category
- `GET /reports/monthly-spending`: Track spending trends by month
- `GET /reports/transaction-trends`: Analyze transaction patterns
- `GET /reports/budget-performance`: Evaluate budget compliance
- `GET /reports/spending-insights`: Get insights into spending patterns

## Project Structure

```
personal_finance_api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── transaction.py
│   │   ├── category.py
│   │   └── budget.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── transactions.py
│   │   ├── categories.py
│   │   ├── budgets.py
│   │   └── reports.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── utils/
│       ├── __init__.py
│       ├── auth.py
│       ├── db_utils.py
│       ├── error_handlers.py
│       ├── logger.py
│       └── rate_limiter.py
├── logs/
├── run.py
└── requirements.txt
```

## Security Features

- Password hashing for user security
- JWT authentication with token expiration
- Rate limiting to prevent abuse
- Input validation to prevent injection attacks
- Role-based access control (users can only access their own data)

## Development

### Testing

To run tests:
```bash
pytest
```

### Adding New Features

1. Create models in the `app/models` directory
2. Define schemas in `app/schemas/schemas.py`
3. Implement routes in the `app/routes` directory
4. Include your router in `app/main.py`

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
