import requests
import string
import random
import sys

BASE_URL = "http://localhost:8000/api/v1"

def gen_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def run_tests():
    username = f"testuser_{gen_random_string()}"
    email = f"{username}@example.com"
    password = "password123"

    print(f"--- Registering user: {username} ---")
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    
    if reg_res.status_code != 200:
        print("Registration failed:", reg_res.text)
        sys.exit(1)
        
    print("Registration successful.")

    print("\n--- Testing Login ---")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    
    if login_res.status_code != 200:
        print("Login failed:", login_res.text)
        sys.exit(1)
        
    data = login_res.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    
    print(f"Obtained Access Token: {access_token[:10]}...")
    print(f"Obtained Refresh Token: {refresh_token[:10]}...")
    
    if not access_token or not refresh_token:
        print("Tokens missing from login response.")
        sys.exit(1)

    print("\n--- Testing /me endpoint ---")
    me_res = requests.get(f"{BASE_URL}/auth/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    
    if me_res.status_code != 200:
        print("/me failed:", me_res.text)
        sys.exit(1)
        
    print("User profile retrieved successfully:", me_res.json()["username"])

    print("\n--- Testing Refresh Flow ---")
    refresh_res = requests.post(f"{BASE_URL}/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    if refresh_res.status_code != 200:
        print("Refresh failed:", refresh_res.text)
        sys.exit(1)
        
    new_data = refresh_res.json()
    new_access_token = new_data.get("access_token")
    new_refresh_token = new_data.get("refresh_token")
    
    print("Refresh successful.")
    print(f"New Access Token: {new_access_token[:10]}...")
    print(f"New Refresh Token: {new_refresh_token[:10]}...")
    
    if new_refresh_token == refresh_token:
        print("Refresh token was not rotated!")
        sys.exit(1)

    print("\n--- Testing Reuse Detection (Security Measure) ---")
    reuse_res = requests.post(f"{BASE_URL}/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    if reuse_res.status_code == 403:
        print("Reuse detected successfully. 403 Forbidden returned.")
    else:
        print("Reuse detection failed. Expected 403, got:", reuse_res.status_code, reuse_res.text)
        sys.exit(1)
        
    print("\n--- Testing if valid session was revoked after reuse ---")
    # Using the new refresh token should now fail because all sessions were revoked
    verify_revoke_res = requests.post(f"{BASE_URL}/auth/refresh", json={
        "refresh_token": new_refresh_token
    })
    
    if verify_revoke_res.status_code == 401:
        print("New refresh token correctly revoked! User must re-login.")
    else:
        print("Failed: New refresh token should be invalid after family revocation. Got:", verify_revoke_res.status_code)
        sys.exit(1)
        
    print("\n--- All Tests Passed Successfully! ---")

if __name__ == "__main__":
    run_tests()
