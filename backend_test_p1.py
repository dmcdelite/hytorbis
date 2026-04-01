#!/usr/bin/env python3
"""
Hytale World Builder P1 Features Backend Test Suite
Tests P1 specific features: large map sizes, enhanced properties, etc.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Use the public endpoint from frontend .env
BACKEND_URL = "https://hytale-base.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class HytaleP1Tester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.test_worlds = []  # Store multiple test worlds
        
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
    
    def test_create_256x256_world(self) -> bool:
        """Test creating a 256x256 world"""
        try:
            world_data = {
                "name": f"Large World 256x256 {datetime.now().strftime('%H%M%S')}",
                "description": "Test large world 256x256",
                "map_width": 256,
                "map_height": 256
            }
            
            response = requests.post(f"{API_BASE}/worlds", json=world_data, timeout=15)
            if response.status_code != 200:
                self.log(f"Create 256x256 world failed with status: {response.status_code}")
                return False
            
            data = response.json()
            if data["map_width"] != 256 or data["map_height"] != 256:
                self.log(f"World size mismatch: expected 256x256, got {data['map_width']}x{data['map_height']}")
                return False
            
            self.test_worlds.append(data["id"])
            self.log(f"Created 256x256 world with ID: {data['id']}")
            return True
            
        except Exception as e:
            self.log(f"256x256 world creation failed: {e}")
            return False
    
    def test_create_512x512_world(self) -> bool:
        """Test creating a 512x512 world (maximum size)"""
        try:
            world_data = {
                "name": f"Max World 512x512 {datetime.now().strftime('%H%M%S')}",
                "description": "Test maximum world size 512x512",
                "map_width": 512,
                "map_height": 512
            }
            
            response = requests.post(f"{API_BASE}/worlds", json=world_data, timeout=15)
            if response.status_code != 200:
                self.log(f"Create 512x512 world failed with status: {response.status_code}")
                return False
            
            data = response.json()
            if data["map_width"] != 512 or data["map_height"] != 512:
                self.log(f"World size mismatch: expected 512x512, got {data['map_width']}x{data['map_height']}")
                return False
            
            self.test_worlds.append(data["id"])
            self.log(f"Created 512x512 world with ID: {data['id']}")
            return True
            
        except Exception as e:
            self.log(f"512x512 world creation failed: {e}")
            return False
    
    def test_create_custom_size_world(self) -> bool:
        """Test creating a world with custom size"""
        try:
            world_data = {
                "name": f"Custom World 128x64 {datetime.now().strftime('%H%M%S')}",
                "description": "Test custom world size 128x64",
                "map_width": 128,
                "map_height": 64
            }
            
            response = requests.post(f"{API_BASE}/worlds", json=world_data, timeout=15)
            if response.status_code != 200:
                self.log(f"Create custom world failed with status: {response.status_code}")
                return False
            
            data = response.json()
            if data["map_width"] != 128 or data["map_height"] != 64:
                self.log(f"World size mismatch: expected 128x64, got {data['map_width']}x{data['map_height']}")
                return False
            
            self.test_worlds.append(data["id"])
            self.log(f"Created custom 128x64 world with ID: {data['id']}")
            return True
            
        except Exception as e:
            self.log(f"Custom world creation failed: {e}")
            return False
    
    def test_world_size_limits(self) -> bool:
        """Test world size validation limits"""
        try:
            # Test size too small (below 5)
            world_data = {
                "name": "Too Small World",
                "map_width": 3,
                "map_height": 3
            }
            
            response = requests.post(f"{API_BASE}/worlds", json=world_data, timeout=10)
            if response.status_code == 200:
                self.log("Expected validation error for size too small, but got success")
                return False
            
            # Test size too large (above 512)
            world_data = {
                "name": "Too Large World",
                "map_width": 600,
                "map_height": 600
            }
            
            response = requests.post(f"{API_BASE}/worlds", json=world_data, timeout=10)
            if response.status_code == 200:
                self.log("Expected validation error for size too large, but got success")
                return False
            
            self.log("Size validation working correctly")
            return True
            
        except Exception as e:
            self.log(f"Size limits test failed: {e}")
            return False
    
    def test_zone_with_biomes(self) -> bool:
        """Test creating zones with biome configurations"""
        if not self.test_worlds:
            return False
            
        try:
            world_id = self.test_worlds[0]
            
            zone_data = {
                "type": "emerald_grove",
                "x": 10,
                "y": 10,
                "width": 3,
                "height": 3,
                "difficulty": 5,
                "biomes": [
                    {"type": "forest", "density": 0.7, "variation": 0.4},
                    {"type": "plains", "density": 0.3, "variation": 0.2}
                ]
            }
            
            response = requests.post(f"{API_BASE}/worlds/{world_id}/zones", 
                                   json=zone_data, timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if "zones" not in data or len(data["zones"]) == 0:
                return False
            
            # Check if biomes were saved correctly
            zone = data["zones"][-1]
            if len(zone.get("biomes", [])) != 2:
                self.log(f"Expected 2 biomes, got {len(zone.get('biomes', []))}")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Zone with biomes test failed: {e}")
            return False
    
    def test_prefab_with_properties(self) -> bool:
        """Test creating prefabs with rotation and scale"""
        if not self.test_worlds:
            return False
            
        try:
            world_id = self.test_worlds[0]
            
            prefab_data = {
                "type": "tower",
                "x": 15,
                "y": 15,
                "rotation": 180,
                "scale": 1.5
            }
            
            response = requests.post(f"{API_BASE}/worlds/{world_id}/prefabs", 
                                   json=prefab_data, timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if "prefabs" not in data or len(data["prefabs"]) == 0:
                return False
            
            # Check if properties were saved correctly
            prefab = data["prefabs"][-1]
            if prefab.get("rotation") != 180 or prefab.get("scale") != 1.5:
                self.log(f"Prefab properties not saved correctly: rotation={prefab.get('rotation')}, scale={prefab.get('scale')}")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Prefab with properties test failed: {e}")
            return False
    
    def test_update_world_size(self) -> bool:
        """Test updating world map size"""
        if not self.test_worlds:
            return False
            
        try:
            world_id = self.test_worlds[-1]  # Use last created world
            
            update_data = {
                "map_width": 100,
                "map_height": 100
            }
            
            response = requests.put(f"{API_BASE}/worlds/{world_id}", 
                                  json=update_data, timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            return (data["map_width"] == 100 and data["map_height"] == 100)
            
        except Exception as e:
            self.log(f"Update world size test failed: {e}")
            return False
    
    def cleanup_test_worlds(self) -> bool:
        """Clean up test worlds"""
        success = True
        for world_id in self.test_worlds:
            try:
                response = requests.delete(f"{API_BASE}/worlds/{world_id}", timeout=10)
                if response.status_code != 200:
                    success = False
                    self.log(f"Failed to delete world {world_id}")
            except Exception as e:
                success = False
                self.log(f"Error deleting world {world_id}: {e}")
        
        if success:
            self.log(f"Cleaned up {len(self.test_worlds)} test worlds")
        return success
    
    def run_all_tests(self):
        """Run all P1 feature tests"""
        self.log("🚀 Starting Hytale World Builder P1 Feature Tests")
        self.log(f"Testing against: {API_BASE}")
        
        # P1 specific tests
        tests = [
            ("Create 256x256 World", self.test_create_256x256_world),
            ("Create 512x512 World", self.test_create_512x512_world),
            ("Create Custom Size World", self.test_create_custom_size_world),
            ("World Size Limits Validation", self.test_world_size_limits),
            ("Zone with Biomes", self.test_zone_with_biomes),
            ("Prefab with Properties", self.test_prefab_with_properties),
            ("Update World Size", self.test_update_world_size),
            ("Cleanup Test Worlds", self.cleanup_test_worlds),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Print summary
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        self.log(f"\n📊 P1 Test Results: {self.tests_passed}/{self.tests_run} passed ({success_rate:.1f}%)")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 All P1 tests passed!", "SUCCESS")
            return 0
        else:
            self.log(f"⚠️  {self.tests_run - self.tests_passed} P1 tests failed", "ERROR")
            return 1

def main():
    """Main test runner"""
    tester = HytaleP1Tester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())