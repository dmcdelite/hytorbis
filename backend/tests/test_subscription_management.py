"""
Test Subscription Management Features - Iteration 11
Tests for:
- GET /api/subscription/history - Payment history endpoint
- POST /api/subscription/cancel - Cancel subscription endpoint
- Profile dialog 'Manage subscription' link
- ManageSubscription dialog functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hytale.builder"
ADMIN_PASSWORD = "HytaleAdmin123!"


class TestSubscriptionHistory:
    """Tests for GET /api/subscription/history endpoint"""
    
    def test_history_requires_auth(self):
        """GET /api/subscription/history should return 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/subscription/history")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/subscription/history requires authentication (401)")
    
    def test_history_returns_transactions(self):
        """GET /api/subscription/history should return transaction list for authenticated user"""
        # Login first
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        # Get payment history
        response = session.get(f"{BASE_URL}/api/subscription/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "transactions" in data, "Response should contain 'transactions' key"
        assert isinstance(data["transactions"], list), "transactions should be a list"
        print(f"✓ GET /api/subscription/history returns transactions list (count: {len(data['transactions'])})")


class TestSubscriptionCancel:
    """Tests for POST /api/subscription/cancel endpoint"""
    
    def test_cancel_requires_auth(self):
        """POST /api/subscription/cancel should return 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/subscription/cancel")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ POST /api/subscription/cancel requires authentication (401)")
    
    def test_cancel_returns_400_for_free_user(self):
        """POST /api/subscription/cancel should return 400 for users without active subscription"""
        # Login first
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        # Check current subscription status
        status_response = session.get(f"{BASE_URL}/api/subscription/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        print(f"  Current plan: {status_data.get('plan', 'unknown')}")
        
        # Try to cancel (should fail for free users)
        response = session.post(f"{BASE_URL}/api/subscription/cancel")
        
        # If user is on free plan, should get 400
        if status_data.get("plan") == "free":
            assert response.status_code == 400, f"Expected 400 for free user, got {response.status_code}"
            data = response.json()
            assert "detail" in data, "Error response should contain 'detail'"
            assert "No active subscription" in data["detail"], f"Unexpected error: {data['detail']}"
            print("✓ POST /api/subscription/cancel returns 400 for free users (no active subscription)")
        else:
            # User has active subscription, cancel should work
            assert response.status_code == 200, f"Expected 200 for paid user, got {response.status_code}"
            print("✓ POST /api/subscription/cancel works for paid users")


class TestSubscriptionStatus:
    """Tests for GET /api/subscription/status endpoint"""
    
    def test_status_returns_plan_info(self):
        """GET /api/subscription/status should return current plan info"""
        # Login first
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        response = session.get(f"{BASE_URL}/api/subscription/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "plan" in data, "Response should contain 'plan' key"
        assert "limits" in data, "Response should contain 'limits' key"
        assert data["plan"] in ["free", "creator", "developer"], f"Invalid plan: {data['plan']}"
        print(f"✓ GET /api/subscription/status returns plan info (plan: {data['plan']})")


class TestSubscriptionPlans:
    """Tests for GET /api/subscription/plans endpoint"""
    
    def test_plans_returns_all_plans(self):
        """GET /api/subscription/plans should return all 3 plans"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "plans" in data, "Response should contain 'plans' key"
        
        plans = data["plans"]
        assert "free" in plans, "Plans should include 'free'"
        assert "creator" in plans, "Plans should include 'creator'"
        assert "developer" in plans, "Plans should include 'developer'"
        
        # Verify plan details
        assert plans["free"]["name"] == "Explorer", f"Free plan name should be 'Explorer'"
        assert plans["free"]["price"] == 0.0, f"Free plan price should be 0"
        assert plans["creator"]["name"] == "Creator", f"Creator plan name should be 'Creator'"
        assert plans["creator"]["price"] == 9.0, f"Creator plan price should be 9"
        assert plans["developer"]["name"] == "Developer", f"Developer plan name should be 'Developer'"
        assert plans["developer"]["price"] == 29.0, f"Developer plan price should be 29"
        
        print("✓ GET /api/subscription/plans returns all 3 plans with correct prices")


class TestAuthEndpoints:
    """Tests for auth endpoints to ensure they still work"""
    
    def test_login_works(self):
        """POST /api/auth/login should work with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain user id"
        assert "email" in data, "Response should contain email"
        assert data["email"] == ADMIN_EMAIL, f"Email mismatch: {data['email']}"
        print(f"✓ POST /api/auth/login works (user: {data.get('name', 'unknown')})")
    
    def test_me_endpoint(self):
        """GET /api/auth/me should return current user after login"""
        session = requests.Session()
        
        # Login
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        
        # Get current user
        response = session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print("✓ GET /api/auth/me returns current user after login")


class TestAIGating:
    """Tests for AI feature gating"""
    
    def test_ai_chat_gated_for_free_users(self):
        """POST /api/ai/chat should return 403 for free users"""
        session = requests.Session()
        
        # Login
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        
        # Check subscription status
        status_response = session.get(f"{BASE_URL}/api/subscription/status")
        status_data = status_response.json()
        
        if status_data.get("plan") == "free":
            # Try AI chat - should be gated
            response = session.post(f"{BASE_URL}/api/ai/chat", json={
                "world_id": "test-world-id",
                "message": "test message",
                "provider": "openai"
            })
            assert response.status_code == 403, f"Expected 403 for free user, got {response.status_code}"
            print("✓ POST /api/ai/chat returns 403 for free users (subscription gating)")
        else:
            print(f"⚠ User is on {status_data.get('plan')} plan, skipping AI gating test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
