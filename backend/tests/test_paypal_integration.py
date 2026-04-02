"""
Test PayPal Integration for Hyt Orbis World Builder
Tests the new PayPal checkout flow alongside existing Stripe checkout
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPayPalIntegration:
    """PayPal checkout endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with admin credentials
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hytale.builder",
            "password": "HytaleAdmin123!"
        })
        if login_response.status_code != 200:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        self.user = login_response.json()
        yield
        
        # Logout after tests
        try:
            self.session.post(f"{BASE_URL}/api/auth/logout")
        except:
            pass
    
    # ========== PayPal Checkout Tests ==========
    
    def test_paypal_checkout_requires_auth(self):
        """POST /api/subscription/checkout/paypal requires authentication"""
        # Use a fresh session without auth
        fresh_session = requests.Session()
        response = fresh_session.post(f"{BASE_URL}/api/subscription/checkout/paypal", json={
            "plan_id": "creator",
            "origin_url": "https://hytale-base.preview.emergentagent.com"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ PayPal checkout requires authentication (401)")
    
    def test_paypal_checkout_rejects_invalid_plan(self):
        """POST /api/subscription/checkout/paypal rejects invalid plan"""
        response = self.session.post(f"{BASE_URL}/api/subscription/checkout/paypal", json={
            "plan_id": "invalid_plan",
            "origin_url": "https://hytale-base.preview.emergentagent.com"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ PayPal checkout rejects invalid plan (400)")
    
    def test_paypal_checkout_rejects_free_plan(self):
        """POST /api/subscription/checkout/paypal rejects free plan"""
        response = self.session.post(f"{BASE_URL}/api/subscription/checkout/paypal", json={
            "plan_id": "free",
            "origin_url": "https://hytale-base.preview.emergentagent.com"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ PayPal checkout rejects free plan (400)")
    
    def test_paypal_checkout_requires_origin_url(self):
        """POST /api/subscription/checkout/paypal requires origin_url"""
        response = self.session.post(f"{BASE_URL}/api/subscription/checkout/paypal", json={
            "plan_id": "creator"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ PayPal checkout requires origin_url (400)")
    
    def test_paypal_checkout_creator_plan(self):
        """POST /api/subscription/checkout/paypal creates order for creator plan"""
        response = self.session.post(f"{BASE_URL}/api/subscription/checkout/paypal", json={
            "plan_id": "creator",
            "origin_url": "https://hytale-base.preview.emergentagent.com"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "url" in data, "Response should contain approval URL"
        assert "order_id" in data, "Response should contain order_id"
        assert data["url"].startswith("https://www.sandbox.paypal.com"), f"URL should be PayPal sandbox: {data['url']}"
        assert len(data["order_id"]) > 0, "Order ID should not be empty"
        print(f"✓ PayPal checkout for creator plan returns approval URL: {data['url'][:60]}...")
        print(f"  Order ID: {data['order_id']}")
    
    def test_paypal_checkout_developer_plan(self):
        """POST /api/subscription/checkout/paypal creates order for developer plan"""
        response = self.session.post(f"{BASE_URL}/api/subscription/checkout/paypal", json={
            "plan_id": "developer",
            "origin_url": "https://hytale-base.preview.emergentagent.com"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "url" in data, "Response should contain approval URL"
        assert "order_id" in data, "Response should contain order_id"
        assert data["url"].startswith("https://www.sandbox.paypal.com"), f"URL should be PayPal sandbox: {data['url']}"
        print(f"✓ PayPal checkout for developer plan returns approval URL")
        print(f"  Order ID: {data['order_id']}")
    
    # ========== PayPal Capture Tests ==========
    
    def test_paypal_capture_requires_auth(self):
        """POST /api/subscription/paypal/capture/{order_id} requires authentication"""
        fresh_session = requests.Session()
        response = fresh_session.post(f"{BASE_URL}/api/subscription/paypal/capture/FAKE_ORDER_ID")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ PayPal capture requires authentication (401)")
    
    def test_paypal_capture_invalid_order(self):
        """POST /api/subscription/paypal/capture/{order_id} returns 404 for invalid order"""
        response = self.session.post(f"{BASE_URL}/api/subscription/paypal/capture/NONEXISTENT_ORDER_123")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PayPal capture returns 404 for invalid order")
    
    # ========== Stripe Still Works ==========
    
    def test_stripe_checkout_still_works(self):
        """POST /api/subscription/checkout/stripe still works alongside PayPal"""
        response = self.session.post(f"{BASE_URL}/api/subscription/checkout/stripe", json={
            "plan_id": "creator",
            "origin_url": "https://hytale-base.preview.emergentagent.com"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "url" in data, "Response should contain checkout URL"
        assert "session_id" in data, "Response should contain session_id"
        assert "stripe.com" in data["url"], f"URL should be Stripe: {data['url']}"
        print(f"✓ Stripe checkout still works alongside PayPal")
    
    # ========== Subscription Plans ==========
    
    def test_subscription_plans_endpoint(self):
        """GET /api/subscription/plans returns all 3 plans"""
        response = self.session.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "plans" in data, "Response should contain plans"
        plans = data["plans"]
        
        # Verify all 3 plans exist
        assert "free" in plans, "Should have free plan"
        assert "creator" in plans, "Should have creator plan"
        assert "developer" in plans, "Should have developer plan"
        
        # Verify prices
        assert plans["free"]["price"] == 0, "Free plan should be $0"
        assert plans["creator"]["price"] == 9.0, "Creator plan should be $9"
        assert plans["developer"]["price"] == 29.0, "Developer plan should be $29"
        
        # Verify AI gating
        assert plans["free"]["ai_enabled"] == False, "Free plan should not have AI"
        assert plans["creator"]["ai_enabled"] == True, "Creator plan should have AI"
        assert plans["developer"]["ai_enabled"] == True, "Developer plan should have AI"
        
        print("✓ Subscription plans endpoint returns all 3 plans with correct prices")
    
    def test_subscription_status_endpoint(self):
        """GET /api/subscription/status returns current plan"""
        response = self.session.get(f"{BASE_URL}/api/subscription/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "plan" in data, "Response should contain plan"
        assert "limits" in data, "Response should contain limits"
        print(f"✓ Subscription status returns plan: {data['plan']}")
    
    # ========== AI Gating Still Works ==========
    
    def test_ai_chat_gating(self):
        """POST /api/ai/chat returns 403 for free users"""
        # First check subscription status
        status_response = self.session.get(f"{BASE_URL}/api/subscription/status")
        status = status_response.json()
        
        if status.get("plan") != "free":
            pytest.skip("User has paid plan - skipping AI gating test")
        
        # Create a test world first
        world_response = self.session.post(f"{BASE_URL}/api/worlds", json={
            "name": "TEST_PayPal_World",
            "map_width": 32,
            "map_height": 32
        })
        
        if world_response.status_code == 201:
            world_id = world_response.json().get("id")
            
            # Try AI chat
            ai_response = self.session.post(f"{BASE_URL}/api/ai/chat", json={
                "world_id": world_id,
                "message": "Add a forest",
                "provider": "openai"
            })
            
            # Cleanup
            self.session.delete(f"{BASE_URL}/api/worlds/{world_id}")
            
            assert ai_response.status_code == 403, f"Expected 403, got {ai_response.status_code}"
            print("✓ AI chat returns 403 for free users (subscription gating works)")
        else:
            print(f"⚠ Could not create test world: {world_response.status_code}")


class TestPayPalEndpointsNoAuth:
    """Test PayPal endpoints without authentication"""
    
    def test_paypal_checkout_no_auth(self):
        """PayPal checkout requires authentication"""
        response = requests.post(f"{BASE_URL}/api/subscription/checkout/paypal", json={
            "plan_id": "creator",
            "origin_url": "https://hytale-base.preview.emergentagent.com"
        })
        assert response.status_code == 401
        print("✓ PayPal checkout requires auth (401)")
    
    def test_paypal_capture_no_auth(self):
        """PayPal capture requires authentication"""
        response = requests.post(f"{BASE_URL}/api/subscription/paypal/capture/test_order")
        assert response.status_code == 401
        print("✓ PayPal capture requires auth (401)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
