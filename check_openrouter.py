import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_key_status():
    # Retrieve key from environment variable
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in environment or .env file.")
        print("Please create a .env file and add: OPENROUTER_API_KEY=your_key_here")
        return

    url = "https://openrouter.ai/api/v1/key"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            # OpenRouter wraps key data in a 'data' object
            data = result.get('data', {})
            
            print("API Key Status: ACTIVE")
            print(f"Key Label: {data.get('label', 'Unnamed')}")
            print(f"Usage: ${data.get('usage', 0):.4f}")
            
            # Optional: Show limit if it exists
            limit = data.get('limit')
            if limit is not None:
                print(f"Limit: ${limit:.2f}")
        elif response.status_code == 401:
            print("API Key Status: INACTIVE (Unauthorized/Invalid Key)")
        else:
            print(f"API Key Status: ERROR (Status Code: {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print(f"Network Error: Could not connect to OpenRouter ({e})")

if __name__ == "__main__":
    check_key_status()
