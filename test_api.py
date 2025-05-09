import requests
import json

# Configuration
API_URL = "http://localhost:8000"
# Replace with a valid token from your localStorage
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtZUBtZS5jb20iLCJleHAiOjE3NDY3Mjk2NTJ9.kJ2eeJhSLVY56A24MF70ccC5Er-vRrNbjOaibzJmuxI"  # Get this from localStorage in your browser

def test_categories():
    """Test GET /categories/ endpoint"""
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }
    response = requests.get(f"{API_URL}/categories/", headers=headers)
    print(f"Categories Status: {response.status_code}")
    print(f"Categories Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_create_transaction(category_id):
    """Test POST /transactions/ endpoint"""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "amount": 10.99,
        "description": "Test transaction from Python",
        "category_id": category_id,
        "date": "2025-05-08T12:00:00.000Z"
    }
    response = requests.post(
        f"{API_URL}/transactions/", 
        headers=headers,
        json=data
    )
    print(f"Transaction Create Status: {response.status_code}")
    try:
        print(f"Transaction Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Transaction Response Text: {response.text}")
    return response

if __name__ == "__main__":
    print("=== Testing API Endpoints ===")
    try:
        # Test categories first
        categories = test_categories()
        if categories and len(categories) > 0:
            # Use the first category ID to create a transaction
            category_id = categories[0]["id"]
            print(f"\nUsing category_id: {category_id}")
            
            # Test creating a transaction
            test_create_transaction(category_id)
        else:
            print("No categories found to use for transaction test")
    except Exception as e:
        print(f"Error: {str(e)}")