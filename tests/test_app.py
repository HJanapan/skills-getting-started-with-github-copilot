import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test suite for the /activities endpoint"""

    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_activities_have_required_fields(self):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignupEndpoint:
    """Test suite for the /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=testuser@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_nonexistent_activity(self):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=testuser@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_email(self):
        """Test signup with email already registered"""
        email = "duplicate@mergington.edu"
        activity = "Soccer Club"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_url_encoding(self):
        """Test signup with special characters in email"""
        response = client.post(
            "/activities/Art%20Club/signup?email=test%2Bspecial@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Test suite for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unregister@mergington.edu"
        activity = "Drama Club"
        
        # First signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_not_signed_up(self):
        """Test unregister when user is not signed up"""
        response = client.delete(
            "/activities/Debate Team/unregister?email=notsignedup@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_url_encoding(self):
        """Test unregister with special characters in email"""
        response = client.delete(
            "/activities/Science%20Club/unregister?email=test%2Bspecial@mergington.edu"
        )
        # Will get 400 because user wasn't signed up, but tests the URL encoding
        assert response.status_code in [400, 404]


class TestActivityParticipantManagement:
    """Test suite for managing activity participants"""

    def test_signup_updates_participant_list(self):
        """Test that signup adds participant to the activity"""
        email = "participant@mergington.edu"
        activity = "Basketball Team"
        
        # Get initial participant count
        response1 = client.get("/activities")
        initial_count = len(response1.json()[activity]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check participant count increased
        response2 = client.get("/activities")
        new_count = len(response2.json()[activity]["participants"])
        assert new_count == initial_count + 1
        assert email in response2.json()[activity]["participants"]

    def test_unregister_removes_participant(self):
        """Test that unregister removes participant from the activity"""
        email = "removeuser@mergington.edu"
        activity = "Soccer Club"
        
        # Sign up first
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify signup
        response1 = client.get("/activities")
        assert email in response1.json()[activity]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Verify removal
        response2 = client.get("/activities")
        assert email not in response2.json()[activity]["participants"]
