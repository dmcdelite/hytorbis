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
    
    def test_templates(self) -> bool:
        """Test P2: Templates endpoint"""
        try:
            response = requests.get(f"{API_BASE}/templates", timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if "templates" not in data:
                return False
            
            templates = data["templates"]
            expected_templates = ["adventure", "peaceful", "challenge", "exploration", "dungeon_crawler"]
            
            if len(templates) != 5:
                self.log(f"Expected 5 templates, got {len(templates)}")
                return False
            
            template_ids = [t["id"] for t in templates]
            for expected in expected_templates:
                if expected not in template_ids:
                    self.log(f"Missing template: {expected}")
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"Templates test failed: {e}")
            return False
    
    def test_create_from_template(self) -> bool:
        """Test P2: Create world from template"""
        try:
            template_data = {
                "name": f"Template World {datetime.now().strftime('%H%M%S')}",
                "template": "adventure",
                "map_width": 32,
                "map_height": 32
            }
            
            response = requests.post(f"{API_BASE}/worlds/from-template", json=template_data, timeout=15)
            if response.status_code != 200:
                self.log(f"Create from template failed with status: {response.status_code}")
                return False
            
            data = response.json()
            required_fields = ["id", "name", "seed", "terrain", "zones", "prefabs"]
            
            for field in required_fields:
                if field not in data:
                    self.log(f"Missing field in template world response: {field}")
                    return False
            
            # Check that zones and prefabs were generated
            if len(data["zones"]) == 0:
                self.log("Template world should have generated zones")
                return False
            
            if len(data["prefabs"]) == 0:
                self.log("Template world should have generated prefabs")
                return False
            
            # Store for later tests
            self.test_world_id = data["id"]
            self.log(f"Created template world with {len(data['zones'])} zones and {len(data['prefabs'])} prefabs")
            return True
            
        except Exception as e:
            self.log(f"Create from template failed: {e}")
            return False
    
    def test_import_world(self) -> bool:
        """Test P2: Import world from JSON config"""
        try:
            # Test with our format
            import_config = {
                "name": "Imported Test World",
                "seed": "ImportTest123",
                "map_width": 16,
                "map_height": 16,
                "terrain": {
                    "height_scale": 1.5,
                    "cave_density": 0.7,
                    "river_frequency": 0.4,
                    "mountain_scale": 0.8,
                    "ocean_level": 0.2
                },
                "zones": [
                    {
                        "type": "emerald_grove",
                        "x": 5,
                        "y": 5,
                        "difficulty": 3
                    }
                ],
                "prefabs": [
                    {
                        "type": "village",
                        "x": 8,
                        "y": 8,
                        "rotation": 90,
                        "scale": 1.2
                    }
                ]
            }
            
            import_data = {
                "config": import_config,
                "name": "Imported World Test"
            }
            
            response = requests.post(f"{API_BASE}/worlds/import", json=import_data, timeout=15)
            if response.status_code != 200:
                self.log(f"Import world failed with status: {response.status_code}")
                return False
            
            data = response.json()
            
            # Verify imported data
            if data["name"] != "Imported World Test":
                self.log("Import didn't preserve world name")
                return False
            
            if data["seed"] != "ImportTest123":
                self.log("Import didn't preserve seed")
                return False
            
            if len(data["zones"]) != 1 or data["zones"][0]["type"] != "emerald_grove":
                self.log("Import didn't preserve zones")
                return False
            
            if len(data["prefabs"]) != 1 or data["prefabs"][0]["type"] != "village":
                self.log("Import didn't preserve prefabs")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Import world failed: {e}")
            return False
    
    def test_ai_auto_generate(self) -> bool:
        """Test P2: AI auto-generate world content"""
        if not self.test_world_id:
            return False
            
        try:
            autogen_data = {
                "world_id": self.test_world_id,
                "prompt": "Create a small adventure world with 2-3 emerald grove zones and a few dungeons",
                "provider": "openai"
            }
            
            response = requests.post(f"{API_BASE}/ai/auto-generate", json=autogen_data, timeout=30)
            if response.status_code != 200:
                self.log(f"AI auto-generate failed with status: {response.status_code}")
                if response.status_code == 500:
                    self.log("AI service may not be configured properly")
                return False
            
            data = response.json()
            
            if "world" not in data or "generated" not in data:
                self.log("AI auto-generate response missing required fields")
                return False
            
            world = data["world"]
            generated = data["generated"]
            
            # Check that content was generated
            if "zones" not in generated or "prefabs" not in generated:
                self.log("AI didn't generate zones and prefabs")
                return False
            
            self.log(f"AI generated {len(generated['zones'])} zones and {len(generated['prefabs'])} prefabs")
            return True
            
        except Exception as e:
            self.log(f"AI auto-generate failed: {e}")
            return False
    
    def test_export_prefab(self) -> bool:
        """Test P2: Prefab export format"""
        if not self.test_world_id:
            return False
            
        try:
            response = requests.get(f"{API_BASE}/worlds/{self.test_world_id}/export/prefab", timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            required_fields = ["format", "version", "filename", "data"]
            
            for field in required_fields:
                if field not in data:
                    self.log(f"Missing field in prefab export: {field}")
                    return False
            
            if data["format"] != "prefab.json":
                self.log("Prefab export format incorrect")
                return False
            
            # Check prefab data structure
            prefab_data = data["data"]
            if "formatVersion" not in prefab_data or "prefabs" not in prefab_data:
                self.log("Prefab data structure incorrect")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Prefab export failed: {e}")
            return False
    
    def test_export_jar(self) -> bool:
        """Test P2: JAR export format"""
        if not self.test_world_id:
            return False
            
        try:
            response = requests.get(f"{API_BASE}/worlds/{self.test_world_id}/export/jar", timeout=15)
            if response.status_code != 200:
                return False
            
            data = response.json()
            required_fields = ["format", "version", "filename", "size_bytes", "data_base64", "contents"]
            
            for field in required_fields:
                if field not in data:
                    self.log(f"Missing field in JAR export: {field}")
                    return False
            
            if data["format"] != "jar":
                self.log("JAR export format incorrect")
                return False
            
            # Check that we have base64 data
            if not data["data_base64"] or len(data["data_base64"]) < 100:
                self.log("JAR export data seems too small")
                return False
            
            # Check contents list
            expected_contents = ["META-INF/MANIFEST.MF", "mod.json"]
            for content in expected_contents:
                if content not in data["contents"]:
                    self.log(f"Missing JAR content: {content}")
                    return False
            
            self.log(f"JAR export size: {data['size_bytes']} bytes")
            return True
            
        except Exception as e:
            self.log(f"JAR export failed: {e}")
            return False
    
    def test_3d_preview(self) -> bool:
        """Test P2: 3D preview data"""
        if not self.test_world_id:
            return False
            
        try:
            response = requests.get(f"{API_BASE}/worlds/{self.test_world_id}/preview-3d", timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            required_fields = ["world_id", "dimensions", "terrain", "height_map", "zones", "prefabs", "render_settings"]
            
            for field in required_fields:
                if field not in data:
                    self.log(f"Missing field in 3D preview: {field}")
                    return False
            
            # Check height map structure
            height_map = data["height_map"]
            if not isinstance(height_map, list) or len(height_map) == 0:
                self.log("Height map should be a non-empty list")
                return False
            
            # Check dimensions match height map
            dimensions = data["dimensions"]
            if len(height_map) != dimensions["height"]:
                self.log("Height map height doesn't match dimensions")
                return False
            
            if len(height_map[0]) != dimensions["width"]:
                self.log("Height map width doesn't match dimensions")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"3D preview failed: {e}")
            return False
    
    def test_collaboration(self) -> bool:
        """Test P2: Collaboration session management"""
        if not self.test_world_id:
            return False
            
        try:
            user_id = f"test_user_{datetime.now().strftime('%H%M%S')}"
            
            # Test join collaboration
            join_data = {
                "world_id": self.test_world_id,
                "user_id": user_id,
                "action": "join"
            }
            
            response = requests.post(f"{API_BASE}/collab/join", json=join_data, timeout=10)
            if response.status_code != 200:
                self.log(f"Collab join failed with status: {response.status_code}")
                return False
            
            join_result = response.json()
            if "session_id" not in join_result or "users" not in join_result:
                self.log("Collab join response missing required fields")
                return False
            
            if user_id not in join_result["users"]:
                self.log("User not found in collaboration session")
                return False
            
            # Test collaboration status
            response = requests.get(f"{API_BASE}/collab/{self.test_world_id}/status", timeout=10)
            if response.status_code != 200:
                self.log("Collab status check failed")
                return False
            
            status_data = response.json()
            if not status_data.get("active") or user_id not in status_data.get("users", []):
                self.log("Collaboration status doesn't show active session")
                return False
            
            # Test leave collaboration
            leave_data = {
                "world_id": self.test_world_id,
                "user_id": user_id,
                "action": "leave"
            }
            
            response = requests.post(f"{API_BASE}/collab/leave", json=leave_data, timeout=10)
            if response.status_code != 200:
                self.log("Collab leave failed")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Collaboration test failed: {e}")
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
        self.log("🚀 Starting Hytale World Builder P2 Features API Tests")
        self.log(f"Testing against: {API_BASE}")
        
        # Core API tests + P2 Features
        tests = [
            ("API Health Check", self.test_health_endpoint),
            ("Seed Generation", self.test_seed_generation),
            ("P2: Templates", self.test_templates),
            ("P2: Create from Template", self.test_create_from_template),
            ("List Worlds", self.test_list_worlds),
            ("Get World", self.test_get_world),
            ("Add Zone", self.test_add_zone),
            ("Add Prefab", self.test_add_prefab),
            ("Update World", self.test_update_world),
            ("P2: Import World", self.test_import_world),
            ("P2: AI Auto-Generate", self.test_ai_auto_generate),
            ("Export JSON", self.test_export_json),
            ("Export Hytale", self.test_export_hytale),
            ("P2: Export Prefab", self.test_export_prefab),
            ("P2: Export JAR", self.test_export_jar),
            ("P2: 3D Preview", self.test_3d_preview),
            ("P2: Collaboration", self.test_collaboration),
            ("Reference Data", self.test_reference_data),
            ("AI Chat", self.test_ai_chat),
            ("Remove Zone", self.test_remove_zone),
            ("Remove Prefab", self.test_remove_prefab),
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