import requests
import uuid

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
# Replace with a valid token if testing against a protected endpoint
TOKEN = "YOUR_TOKEN_HERE" 

def verify_fix(org_id):
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN != "YOUR_TOKEN_HERE" else {}
    url = f"{BASE_URL}/organizations/{org_id}/users?skip=0&limit=20"
    
    print(f"Requesting: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        users = data if isinstance(data, list) else data.get("data", [])
        print(f"Total users returned: {len(users)}")
        
        for user in users:
            print(f"- {user.get('email')} (ID: {user.get('id')})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # The organization ID provided by the user
    ORG_ID = "5b4a4c8a-a23e-45ff-b2c7-cb20316d7891"
    verify_fix(ORG_ID)
