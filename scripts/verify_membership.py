import requests
import uuid

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ORG_ID = "PASTE_YOUR_ORG_ID_HERE"
TOKEN = "PASTE_YOUR_TOKEN_HERE"

def verify_membership():
    if ORG_ID == "PASTE_YOUR_ORG_ID_HERE" or TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print("Please set ORG_ID and TOKEN in the script.")
        return

    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # 1. List users before creation
    print(f"Listing users for organization {ORG_ID}...")
    response = requests.get(f"{BASE_URL}/organizations/{ORG_ID}/users", headers=headers)
    if response.status_code != 200:
        print(f"Error listing users: {response.text}")
        return
    
    initial_count = len(response.json())
    print(f"Initial user count: {initial_count}")

    # 2. Create a new user
    new_user_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": new_user_email,
        "first_name": "Test",
        "last_name": "User",
        "send_activation_email": False
    }
    
    print(f"Creating user {new_user_email}...")
    response = requests.post(f"{BASE_URL}/organizations/{ORG_ID}/users", headers=headers, json=payload)
    if response.status_code != 201:
        print(f"Error creating user: {response.text}")
        return
    
    print("User created successfully.")

    # 3. List users after creation
    print("Listing users again...")
    response = requests.get(f"{BASE_URL}/organizations/{ORG_ID}/users", headers=headers)
    if response.status_code != 200:
        print(f"Error listing users: {response.text}")
        return
    
    users = response.json()
    new_count = len(users)
    print(f"New user count: {new_count}")

    # 4. Final check
    found = any(u['email'] == new_user_email for u in users)
    if found and new_count == initial_count + 1:
        print("SUCCESS: User was created and is correctly linked to the organization.")
    else:
        print("FAILURE: User not found in organization list or count hasn't increased correctly.")

if __name__ == "__main__":
    verify_membership()
