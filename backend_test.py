#!/usr/bin/env python3
"""
Hytale World Builder Backend API Test Suite
Tests all API endpoints for functionality and integration
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Use the public endpoint from frontend .env
BACKEND_URL = "https://hytale-base.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class HytaleAPITester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.test_world_id = None
        self.test_zone_id = None
        self.test_prefab_id = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_test(self, name: str, test_func) -> bool:
        """Run a single test and track results"""
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            success = test_func()
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - PASSED", "SUCCESS")
            else:
                self.log(f"❌ {name} - FAILED", "ERROR")
            return success
        except Exception as e:
            self.log(f"❌ {name} - ERROR: {str(e)}", "ERROR")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test API health check"""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return "status" in data and data["status"] == "healthy"
            return False
        except Exception as e:
            self.log(f"Health check failed: {e}")
            return False
    
    def test_seed_generation(self) -> bool:
        """Test seed generation endpoints"""
        try:
            # Test random seed
            response = requests.get(f"{API_BASE}/seed/random", timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if "seed" not in data:
                return False
            
            # Test styled seed generation
            response = requests.post(f"{API_BASE}/seed/generate", 
                                   json={"style": "adventure"}, timeout=10)
            if response.status_code != 200:
                return False
                
            data = response.json()
            return "seed" in data and "style" in data
            
        except Exception as e:
            self.log(f"Seed generation failed: {e}")
            return False
    
    def test_create_world(self) -> bool:
        """Test world creation"""
        try:
            world_data = {
                "name": f"Test World {datetime.now().strftime('%H%M%S')}",
                "description": "Test world for API testing",
                "map_width": 20,
                "map_height": 20
            }
            
            response = requests.post(f"{API_BASE}/worlds", json=world_data, timeout=10)
            if response.status_code != 200:
                self.log(f"Create world failed with status: {response.status_code}")
                return False
            
            data = response.json()
            required_fields = ["id", "name", "seed", "terrain", "zones", "prefabs"]
            
            for field in required_fields:
                if field not in data:
                    self.log(f"Missing field in world response: {field}")
                    return False
            
            self.test_world_id = data["id"]
            self.log(f"Created test world with ID: {self.test_world_id}")
            return True
            
        except Exception as e:
            self.log(f"World creation failed: {e}")
            return False
    
    def test_list_worlds(self) -> bool:
        """Test listing worlds"""
        try:
            response = requests.get(f"{API_BASE}/worlds", timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if not isinstance(data, list):
                return False
            
            # Should have at least our test world
            return len(data) > 0
            
        except Exception as e:
            self.log(f"List worlds failed: {e}")
            return False
    
    def test_get_world(self) -> bool:
        """Test getting a specific world"""
        if not self.test_world_id:
            return False
            
        try:
            response = requests.get(f"{API_BASE}/worlds/{self.test_world_id}", timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            return data["id"] == self.test_world_id
            
        except Exception as e:
            self.log(f"Get world failed: {e}")
            return False
    
    def test_add_zone(self) -> bool:
        """Test adding a zone to world"""
        if not self.test_world_id:
            return False
            
        try:
            zone_data = {
                "type": "emerald_grove",
                "x": 5,
                "y": 5,
                "width": 2,
                "height": 2,
                "difficulty": 3
            }
            
            response = requests.post(f"{API_BASE}/worlds/{self.test_world_id}/zones", 
                                   json=zone_data, timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if "zones" not in data or len(data["zones"]) == 0:
                return False
            
            # Store zone ID for later tests
            self.test_zone_id = data["zones"][-1]["id"]
            return True
            
        except Exception as e:
            self.log(f"Add zone failed: {e}")
            return False
    
    def test_add_prefab(self) -> bool:
        """Test adding a prefab to world"""
        if not self.test_world_id:
            return False
            
        try:
            prefab_data = {
                "type": "dungeon",
                "x": 10,
                "y": 10,
                "rotation": 90,
                "scale": 1.5
            }
            
            response = requests.post(f"{API_BASE}/worlds/{self.test_world_id}/prefabs", 
                                   json=prefab_data, timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if "prefabs" not in data or len(data["prefabs"]) == 0:
                return False
            
            # Store prefab ID for later tests
            self.test_prefab_id = data["prefabs"][-1]["id"]
            return True
            
        except Exception as e:
            self.log(f"Add prefab failed: {e}")
            return False
    
    def test_update_world(self) -> bool:
        """Test updating world settings"""
        if not self.test_world_id:
            return False
            
        try:
            update_data = {
                "description": "Updated test world",
                "terrain": {
                    "height_scale": 2.0,
                    "cave_density": 0.8,
                    "river_frequency": 0.6,
                    "mountain_scale": 0.7,
                    "ocean_level": 0.4
                }
            }
            
            response = requests.put(f"{API_BASE}/worlds/{self.test_world_id}", 
                                  json=update_data, timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            return (data["description"] == "Updated test world" and 
                   data["terrain"]["height_scale"] == 2.0)
            
        except Exception as e:
            self.log(f"Update world failed: {e}")
            return False
    
    def test_remove_zone(self) -> bool:
        """Test removing a zone from world"""
        if not self.test_world_id or not self.test_zone_id:
            return False
            
        try:
            response = requests.delete(f"{API_BASE}/worlds/{self.test_world_id}/zones/{self.test_zone_id}", 
                                     timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.log(f"Remove zone failed: {e}")
            return False
    
    def test_remove_prefab(self) -> bool:
        """Test removing a prefab from world"""
        if not self.test_world_id or not self.test_prefab_id:
            return False
            
        try:
            response = requests.delete(f"{API_BASE}/worlds/{self.test_world_id}/prefabs/{self.test_prefab_id}", 
                                     timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.log(f"Remove prefab failed: {e}")
            return False
    
    def test_export_json(self) -> bool:
        """Test JSON export"""
        if not self.test_world_id:
            return False
            
        try:
            response = requests.get(f"{API_BASE}/worlds/{self.test_world_id}/export/json", 
                                  timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            return ("format" in data and data["format"] == "json" and 
                   "world" in data)
            
        except Exception as e:
            self.log(f"JSON export failed: {e}")
            return False
    
    def test_export_hytale(self) -> bool:
        """Test Hytale format export"""
        if not self.test_world_id:
            return False
            
        try:
            response = requests.get(f"{API_BASE}/worlds/{self.test_world_id}/export/hytale", 
                                  timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            return ("format" in data and data["format"] == "hytale" and 
                   "config" in data and "worldgen" in data["config"])
            
        except Exception as e:
            self.log(f"Hytale export failed: {e}")
            return False
    
    def test_reference_data(self) -> bool:
        """Test reference data endpoints"""
        try:
            # Test zones reference
            response = requests.get(f"{API_BASE}/reference/zones", timeout=10)
            if response.status_code != 200:
                return False
            
            zones_data = response.json()
            if "zones" not in zones_data or len(zones_data["zones"]) != 5:
                return False
            
            # Test prefabs reference
            response = requests.get(f"{API_BASE}/reference/prefabs", timeout=10)
            if response.status_code != 200:
                return False
            
            prefabs_data = response.json()
            if "prefabs" not in prefabs_data or len(prefabs_data["prefabs"]) != 6:
                return False
            
            # Test biomes reference
            response = requests.get(f"{API_BASE}/reference/biomes", timeout=10)
            if response.status_code != 200:
                return False
            
            biomes_data = response.json()
            return "biomes" in biomes_data and len(biomes_data["biomes"]) > 0
            
        except Exception as e:
            self.log(f"Reference data failed: {e}")
            return False
    
    def test_ai_chat(self) -> bool:
        """Test AI chat functionality"""
        if not self.test_world_id:
            return False
            
        try:
            chat_data = {
                "world_id": self.test_world_id,
                "message": "Suggest some zones for my world",
                "provider": "openai"
            }
            
            response = requests.post(f"{API_BASE}/ai/chat", json=chat_data, timeout=30)
            if response.status_code != 200:
                self.log(f"AI chat failed with status: {response.status_code}")
                if response.status_code == 500:
                    self.log("AI service may not be configured properly")
                return False
            
            data = response.json()
            return "response" in data and len(data["response"]) > 0
            
        except Exception as e:
            self.log(f"AI chat failed: {e}")
            return False
    
    def test_delete_world(self) -> bool:
        """Test world deletion (cleanup)"""
        if not self.test_world_id:
            return False
            
        try:
            response = requests.delete(f"{API_BASE}/worlds/{self.test_world_id}", timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.log(f"Delete world failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all API tests in sequence"""
        self.log("🚀 Starting Hytale World Builder API Tests")
        self.log(f"Testing against: {API_BASE}")
        
        # Core API tests
        tests = [
            ("API Health Check", self.test_health_endpoint),
            ("Seed Generation", self.test_seed_generation),
            ("Create World", self.test_create_world),
            ("List Worlds", self.test_list_worlds),
            ("Get World", self.test_get_world),
            ("Add Zone", self.test_add_zone),
            ("Add Prefab", self.test_add_prefab),
            ("Update World", self.test_update_world),
            ("Remove Zone", self.test_remove_zone),
            ("Remove Prefab", self.test_remove_prefab),
            ("Export JSON", self.test_export_json),
            ("Export Hytale", self.test_export_hytale),
            ("Reference Data", self.test_reference_data),
            ("AI Chat", self.test_ai_chat),
            ("Delete World", self.test_delete_world),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Print summary
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        self.log(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} passed ({success_rate:.1f}%)")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 All tests passed!", "SUCCESS")
            return 0
        else:
            self.log(f"⚠️  {self.tests_run - self.tests_passed} tests failed", "ERROR")
            return 1

def main():
    """Main test runner"""
    tester = HytaleAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())