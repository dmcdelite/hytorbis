"""
Iteration 14 Feature Tests
Tests for:
1. Context split (AuthContext, SubscriptionContext, SocialContext) - via API verification
2. OG meta tags endpoint GET /api/og/{share_token}
3. CORS monitoring middleware
4. Facebook share button (frontend - verified via Playwright)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hytale-base.preview.emergentagent.com').rstrip('/')

class TestOGEndpoint:
    """Tests for OG meta tags HTML endpoint"""
    
    def test_og_endpoint_returns_html(self):
        """GET /api/og/{token} - Returns HTML with OG meta tags"""
        response = requests.get(f"{BASE_URL}/api/og/298a3d8d-81c")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), "Should return HTML"
        
        html = response.text
        
        # Check for OG meta tags
        assert 'og:title' in html, "Should contain og:title"
        assert 'og:description' in html, "Should contain og:description"
        assert 'og:image' in html, "Should contain og:image"
        assert 'og:url' in html, "Should contain og:url"
        assert 'og:type' in html, "Should contain og:type"
        assert 'og:site_name' in html, "Should contain og:site_name"
        
        # Check for Twitter card meta tags
        assert 'twitter:card' in html, "Should contain twitter:card"
        assert 'twitter:title' in html, "Should contain twitter:title"
        assert 'twitter:description' in html, "Should contain twitter:description"
        assert 'twitter:image' in html, "Should contain twitter:image"
        
        # Check for redirect
        assert 'http-equiv="refresh"' in html, "Should contain redirect meta tag"
        
        print("OG endpoint returns valid HTML with all required meta tags")
    
    def test_og_endpoint_contains_world_name(self):
        """GET /api/og/{token} - HTML contains world name"""
        response = requests.get(f"{BASE_URL}/api/og/298a3d8d-81c")
        
        assert response.status_code == 200
        html = response.text
        
        # Check for world name in title
        assert 'Test World' in html, "Should contain world name 'Test World'"
        assert 'Hyt Orbis' in html, "Should contain 'Hyt Orbis' branding"
        
        print("OG endpoint contains correct world name")
    
    def test_og_endpoint_invalid_token(self):
        """GET /api/og/{token} - Invalid token returns 404"""
        response = requests.get(f"{BASE_URL}/api/og/invalid-token-xyz")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Invalid OG token correctly returns 404")


class TestContextSplitRegression:
    """Regression tests to verify context split didn't break functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hytorbis.com",
            "password": "Lucky420420$"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Admin login failed")
        
        self.user = login_response.json()
    
    def test_auth_context_login(self):
        """AuthContext: Login works correctly"""
        # Already logged in via setup
        assert self.user is not None, "User should be set after login"
        assert "email" in self.user, "User should have email"
        assert self.user["email"] == "admin@hytorbis.com", "Email should match"
        print(f"AuthContext login works: {self.user['email']}")
    
    def test_auth_context_me_endpoint(self):
        """AuthContext: GET /api/auth/me returns current user"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "email" in data, "Should return user email"
        assert data["email"] == "admin@hytorbis.com", "Email should match"
        print("AuthContext /auth/me works correctly")
    
    def test_subscription_context_status(self):
        """SubscriptionContext: GET /api/subscription/status works"""
        response = self.session.get(f"{BASE_URL}/api/subscription/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "plan" in data, "Should return subscription plan"
        print(f"SubscriptionContext works: plan={data.get('plan')}")
    
    def test_social_context_notifications(self):
        """SocialContext: GET /api/notifications works"""
        response = self.session.get(f"{BASE_URL}/api/notifications")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "notifications" in data or "unread_count" in data, "Should return notifications data"
        print(f"SocialContext notifications works: unread={data.get('unread_count', 0)}")
    
    def test_app_context_worlds(self):
        """AppContext: GET /api/worlds works"""
        response = self.session.get(f"{BASE_URL}/api/worlds")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Should return list of worlds"
        print(f"AppContext worlds works: {len(data)} worlds")
    
    def test_app_context_templates(self):
        """AppContext: GET /api/templates works"""
        response = self.session.get(f"{BASE_URL}/api/templates")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "templates" in data, "Should return templates"
        print(f"AppContext templates works: {len(data.get('templates', []))} templates")
    
    def test_app_context_custom_prefabs(self):
        """AppContext: GET /api/prefabs/custom works"""
        response = self.session.get(f"{BASE_URL}/api/prefabs/custom")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "prefabs" in data, "Should return prefabs"
        print(f"AppContext custom prefabs works: {len(data.get('prefabs', []))} prefabs")


class TestCORSMonitoring:
    """Tests for CORS monitoring middleware"""
    
    def test_cors_allows_valid_origin(self):
        """CORS: Valid origin is allowed"""
        headers = {
            "Origin": "https://hytale-base.preview.emergentagent.com",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/api/health", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("CORS allows valid origin")
    
    def test_health_endpoint(self):
        """Health endpoint works"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "healthy", "Should return healthy status"
        print(f"Health endpoint works: {data}")


class TestShareDialogFeatures:
    """Tests for Share dialog features (backend verification)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hytorbis.com",
            "password": "Lucky420420$"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Admin login failed")
    
    def test_share_info_endpoint(self):
        """GET /api/worlds/{id}/share - Returns share info"""
        # Get a world first
        worlds_response = self.session.get(f"{BASE_URL}/api/worlds")
        worlds = worlds_response.json()
        
        if not worlds:
            pytest.skip("No worlds available")
        
        world_id = worlds[0]["id"]
        
        response = self.session.get(f"{BASE_URL}/api/worlds/{world_id}/share")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "share_enabled" in data, "Should return share_enabled"
        assert "share_token" in data, "Should return share_token"
        print(f"Share info: enabled={data['share_enabled']}, token={data.get('share_token')}")
    
    def test_shared_world_public_endpoint(self):
        """GET /api/shared/{token} - Public endpoint works"""
        response = requests.get(f"{BASE_URL}/api/shared/298a3d8d-81c")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "world" in data, "Should return world data"
        assert "stats" in data, "Should return stats"
        assert "thumbnail" in data, "Should return thumbnail"
        
        world = data["world"]
        assert world["name"] == "Test World", "Should return correct world"
        print(f"Public shared endpoint works: {world['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
