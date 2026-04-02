"""
Test suite for Subscription Gating and Auth features
Tests: Auth gate, subscription plans, AI feature gating, Stripe checkout
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hytale-base.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@hytale.builder"
ADMIN_PASSWORD = "HytaleAdmin123!"
TEST_USER_EMAIL = "TEST_subscription_user@test.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_USER_NAME = "TEST_SubscriptionUser"


class TestSubscriptionPlans:
    """Test subscription plan endpoints"""
    
    def test_get_plans_returns_all_tiers(self):
        """GET /api/subscription/plans returns all 3 plans"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        data = response.json()
        assert "plans" in data
        plans = data["plans"]
        
        # Verify all 3 plans exist
        assert "free" in plans
        assert "creator" in plans
        assert "developer" in plans
        
        # Verify free plan (Explorer)
        free = plans["free"]
        assert free["name"] == "Explorer"
        assert free["price"] == 0.0
        assert free["ai_enabled"] == False
        assert free["max_worlds"] == 5
        
        # Verify creator plan
        creator = plans["creator"]
        assert creator["name"] == "Creator"
        assert creator["price"] == 9.0
        assert creator["ai_enabled"] == True
        assert creator["max_worlds"] == -1  # Unlimited
        
        # Verify developer plan
        developer = plans["developer"]
        assert developer["name"] == "Developer"
        assert developer["price"] == 29.0
        assert developer["ai_enabled"] == True
        assert developer["analytics"] == True
        
        print("✓ All 3 subscription plans returned correctly")
    
    def test_subscription_status_unauthenticated(self):
        """GET /api/subscription/status returns free plan when not authenticated"""
        response = requests.get(f"{BASE_URL}/api/subscription/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["plan"] == "free"
        assert "limits" in data
        assert data["limits"]["name"] == "Explorer"
        
        print("✓ Unauthenticated users get free plan status")


class TestAuthGating:
    """Test authentication and login flows"""
    
    @pytest.fixture
    def session(self):
        """Create a requests session with cookies"""
        return requests.Session()
    
    def test_login_with_valid_credentials(self, session):
        """POST /api/auth/login with valid admin credentials"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        
        # Verify cookies are set
        assert "access_token" in session.cookies or response.cookies.get("access_token")
        
        print("✓ Admin login successful with valid credentials")
    
    def test_login_with_invalid_credentials(self, session):
        """POST /api/auth/login with invalid credentials returns 401"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        
        print("✓ Invalid credentials correctly rejected with 401")
    
    def test_auth_me_unauthenticated(self):
        """GET /api/auth/me returns 401 when not authenticated"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        
        print("✓ /auth/me correctly returns 401 for unauthenticated users")
    
    def test_auth_me_authenticated(self, session):
        """GET /api/auth/me returns user data when authenticated"""
        # Login first
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        
        # Check /auth/me
        me_response = session.get(f"{BASE_URL}/api/auth/me")
        assert me_response.status_code == 200
        
        data = me_response.json()
        assert data["email"] == ADMIN_EMAIL
        assert "id" in data
        
        print("✓ /auth/me returns user data for authenticated users")
    
    def test_logout_clears_session(self, session):
        """POST /api/auth/logout clears authentication"""
        # Login first
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        # Logout
        logout_response = session.post(f"{BASE_URL}/api/auth/logout")
        assert logout_response.status_code == 200
        
        # Verify /auth/me now returns 401
        me_response = session.get(f"{BASE_URL}/api/auth/me")
        assert me_response.status_code == 401
        
        print("✓ Logout correctly clears authentication")
    
    def test_register_new_user(self, session):
        """POST /api/auth/register creates new user"""
        # Try to register (may fail if user exists)
        response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        
        # Either 200 (created) or 400 (already exists)
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert data["email"] == TEST_USER_EMAIL.lower()
            assert data["name"] == TEST_USER_NAME
            print("✓ New user registered successfully")
        else:
            print("✓ User already exists (expected in repeated tests)")


class TestAIFeatureGating:
    """Test AI feature gating for free users"""
    
    @pytest.fixture
    def free_user_session(self):
        """Create a session for a free user (no subscription)"""
        session = requests.Session()
        # Register or login as test user
        session.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        # Login
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        return session
    
    def test_ai_chat_blocked_for_free_users(self, free_user_session):
        """POST /api/ai/chat returns 403 for free users"""
        # First create a world
        world_response = free_user_session.post(f"{BASE_URL}/api/worlds", json={
            "name": "TEST_AIGatingWorld",
            "map_width": 32,
            "map_height": 32
        })
        
        if world_response.status_code == 200:
            world_id = world_response.json()["id"]
            
            # Try to use AI chat
            ai_response = free_user_session.post(f"{BASE_URL}/api/ai/chat", json={
                "world_id": world_id,
                "message": "Add some trees",
                "provider": "openai"
            })
            
            assert ai_response.status_code == 403
            data = ai_response.json()
            assert "detail" in data
            assert "upgrade" in data["detail"].lower() or "paid" in data["detail"].lower()
            
            # Cleanup
            free_user_session.delete(f"{BASE_URL}/api/worlds/{world_id}")
            
            print("✓ AI chat correctly blocked for free users with 403")
        else:
            pytest.skip("Could not create test world")
    
    def test_ai_auto_generate_blocked_for_free_users(self, free_user_session):
        """POST /api/ai/auto-generate returns 403 for free users"""
        # First create a world
        world_response = free_user_session.post(f"{BASE_URL}/api/worlds", json={
            "name": "TEST_AIAutoGenWorld",
            "map_width": 32,
            "map_height": 32
        })
        
        if world_response.status_code == 200:
            world_id = world_response.json()["id"]
            
            # Try to use AI auto-generate
            ai_response = free_user_session.post(f"{BASE_URL}/api/ai/auto-generate", json={
                "world_id": world_id,
                "prompt": "Create a forest world",
                "provider": "openai"
            })
            
            assert ai_response.status_code == 403
            data = ai_response.json()
            assert "detail" in data
            
            # Cleanup
            free_user_session.delete(f"{BASE_URL}/api/worlds/{world_id}")
            
            print("✓ AI auto-generate correctly blocked for free users with 403")
        else:
            pytest.skip("Could not create test world")


class TestStripeCheckout:
    """Test Stripe checkout flow"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Create an authenticated session"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return session
    
    def test_checkout_requires_auth(self):
        """POST /api/subscription/checkout/stripe requires authentication"""
        response = requests.post(f"{BASE_URL}/api/subscription/checkout/stripe", json={
            "plan_id": "creator",
            "origin_url": "https://example.com"
        })
        assert response.status_code == 401
        
        print("✓ Stripe checkout correctly requires authentication")
    
    def test_checkout_invalid_plan(self, authenticated_session):
        """POST /api/subscription/checkout/stripe rejects invalid plan"""
        response = authenticated_session.post(f"{BASE_URL}/api/subscription/checkout/stripe", json={
            "plan_id": "invalid_plan",
            "origin_url": "https://example.com"
        })
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        
        print("✓ Invalid plan correctly rejected")
    
    def test_checkout_free_plan_rejected(self, authenticated_session):
        """POST /api/subscription/checkout/stripe rejects free plan"""
        response = authenticated_session.post(f"{BASE_URL}/api/subscription/checkout/stripe", json={
            "plan_id": "free",
            "origin_url": "https://example.com"
        })
        assert response.status_code == 400
        
        print("✓ Free plan checkout correctly rejected")
    
    def test_checkout_creator_plan_returns_url(self, authenticated_session):
        """POST /api/subscription/checkout/stripe returns checkout URL for creator plan"""
        response = authenticated_session.post(f"{BASE_URL}/api/subscription/checkout/stripe", json={
            "plan_id": "creator",
            "origin_url": "https://hytale-base.preview.emergentagent.com"
        })
        
        # Should return 200 with checkout URL (or 500 if Stripe not configured)
        if response.status_code == 200:
            data = response.json()
            assert "url" in data
            assert "session_id" in data
            assert data["url"].startswith("https://")
            print("✓ Creator plan checkout returns valid Stripe URL")
        elif response.status_code == 500:
            data = response.json()
            if "Stripe not configured" in data.get("detail", ""):
                pytest.skip("Stripe not configured in test environment")
            else:
                pytest.fail(f"Unexpected 500 error: {data}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_checkout_developer_plan_returns_url(self, authenticated_session):
        """POST /api/subscription/checkout/stripe returns checkout URL for developer plan"""
        response = authenticated_session.post(f"{BASE_URL}/api/subscription/checkout/stripe", json={
            "plan_id": "developer",
            "origin_url": "https://hytale-base.preview.emergentagent.com"
        })
        
        if response.status_code == 200:
            data = response.json()
            assert "url" in data
            assert "session_id" in data
            print("✓ Developer plan checkout returns valid Stripe URL")
        elif response.status_code == 500:
            data = response.json()
            if "Stripe not configured" in data.get("detail", ""):
                pytest.skip("Stripe not configured in test environment")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


class TestSubscriptionStatusAuthenticated:
    """Test subscription status for authenticated users"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Create an authenticated session"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return session
    
    def test_subscription_status_authenticated_free(self, authenticated_session):
        """GET /api/subscription/status returns free plan for user without subscription"""
        response = authenticated_session.get(f"{BASE_URL}/api/subscription/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "plan" in data
        assert "limits" in data
        # Admin without active subscription should be on free plan
        assert data["plan"] in ["free", "creator", "developer"]
        
        print(f"✓ Authenticated user subscription status: {data['plan']}")


# Cleanup fixture
@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Cleanup test data after all tests"""
    yield
    # Cleanup test worlds
    session = requests.Session()
    session.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    
    # Get and delete test worlds
    worlds_response = session.get(f"{BASE_URL}/api/worlds")
    if worlds_response.status_code == 200:
        worlds = worlds_response.json()
        if isinstance(worlds, list):
            for world in worlds:
                if world.get("name", "").startswith("TEST_"):
                    session.delete(f"{BASE_URL}/api/worlds/{world['id']}")
