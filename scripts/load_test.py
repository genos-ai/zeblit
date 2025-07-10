#!/usr/bin/env python3
"""
Load testing script for Zeblit AI Development Platform.

Usage:
    pip install locust
    locust -f load_test.py --host http://localhost:8000
"""

from locust import HttpUser, task, between
import json
import random
import string


class ZeblitUser(HttpUser):
    """Simulated user for load testing."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login when user starts."""
        # Create a unique test user
        self.username = f"loadtest_{''.join(random.choices(string.ascii_lowercase, k=8))}"
        self.email = f"{self.username}@test.com"
        self.password = "TestPassword123!"
        
        # Try to register first
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "username": self.username,
                "password": self.password,
                "full_name": "Load Test User"
            }
        )
        
        # Login
        response = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": self.email,
                "password": self.password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print(f"Login failed: {response.status_code}")
            self.headers = {}
    
    @task(1)
    def check_health(self):
        """Check health endpoint."""
        self.client.get("/api/v1/health/health")
    
    @task(3)
    def get_user_profile(self):
        """Get current user profile."""
        if hasattr(self, 'headers'):
            self.client.get("/api/v1/users/me", headers=self.headers)
    
    @task(5)
    def list_projects(self):
        """List user projects."""
        if hasattr(self, 'headers'):
            self.client.get("/api/v1/projects", headers=self.headers)
    
    @task(2)
    def create_project(self):
        """Create a new project."""
        if hasattr(self, 'headers'):
            project_name = f"test-project-{''.join(random.choices(string.ascii_lowercase, k=8))}"
            self.client.post(
                "/api/v1/projects",
                json={
                    "name": project_name,
                    "description": "Load test project",
                    "language": "python",
                    "framework": "fastapi",
                    "is_public": False
                },
                headers=self.headers
            )
    
    @task(4)
    def get_project_details(self):
        """Get project details if we have created any."""
        if hasattr(self, 'headers'):
            # First get list of projects
            response = self.client.get("/api/v1/projects", headers=self.headers)
            if response.status_code == 200:
                projects = response.json().get("items", [])
                if projects:
                    # Get details of a random project
                    project = random.choice(projects)
                    self.client.get(
                        f"/api/v1/projects/{project['id']}",
                        headers=self.headers
                    )
    
    @task(1)
    def list_agents(self):
        """List available agents."""
        if hasattr(self, 'headers'):
            self.client.get("/api/v1/agents", headers=self.headers)


class AdminUser(HttpUser):
    """Simulated admin user for testing admin endpoints."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login as admin."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin@zeblit.com",
                "password": "admin123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print(f"Admin login failed: {response.status_code}")
            self.headers = {}
    
    @task(3)
    def list_all_users(self):
        """List all users (admin only)."""
        if hasattr(self, 'headers'):
            self.client.get("/api/v1/users", headers=self.headers)
    
    @task(2)
    def get_system_stats(self):
        """Get system statistics."""
        if hasattr(self, 'headers'):
            self.client.get("/api/v1/health/detailed", headers=self.headers)
    
    @task(1)
    def check_container_pool(self):
        """Check container pool status."""
        if hasattr(self, 'headers'):
            self.client.get("/api/v1/containers/pool/status", headers=self.headers) 