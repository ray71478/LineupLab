"""
Unit tests for WeightProfileService.

Tests CRUD operations, default profile handling, and validation.
"""

import pytest
from sqlalchemy.orm import Session
from backend.services.weight_profile_service import WeightProfileService
from backend.exceptions import ProfileNotFoundError, ProfileNameExistsError, CannotDeleteDefaultError
from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig


class TestWeightProfileService:
    """Test suite for WeightProfileService."""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create WeightProfileService instance."""
        return WeightProfileService(db_session)

    @pytest.fixture
    def default_weights(self):
        """Default weight profile."""
        return WeightProfile(
            W1=0.125,
            W2=0.125,
            W3=0.125,
            W4=0.125,
            W5=0.125,
            W6=0.125,
            W7=0.125,
            W8=0.125,
        )

    @pytest.fixture
    def default_config(self):
        """Default config."""
        return ScoreConfig(
            projection_source="ETR",
            eighty_twenty_enabled=True,
            eighty_twenty_threshold=20.0,
        )

    def test_create_profile(self, service, default_weights, default_config):
        """Test creating a new profile."""
        profile = service.create_profile(
            name="Test Profile",
            weights=default_weights,
            config=default_config,
            is_default=False,
        )
        
        assert profile.id is not None
        assert profile.name == "Test Profile"
        assert profile.weights == default_weights
        assert profile.config == default_config
        assert profile.is_default is False

    def test_get_profile(self, service, default_weights, default_config):
        """Test retrieving a profile."""
        created = service.create_profile(
            name="Test Profile",
            weights=default_weights,
            config=default_config,
            is_default=False,
        )
        
        retrieved = service.get_profile(created.id)
        
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_profile_not_found(self, service):
        """Test retrieving non-existent profile raises error."""
        with pytest.raises(ProfileNotFoundError):
            service.get_profile(99999)

    def test_list_profiles(self, service, default_weights, default_config):
        """Test listing all profiles."""
        # Create multiple profiles
        service.create_profile("Profile 1", default_weights, default_config, False)
        service.create_profile("Profile 2", default_weights, default_config, False)
        
        profiles = service.list_profiles()
        
        assert len(profiles) >= 2

    def test_update_profile(self, service, default_weights, default_config):
        """Test updating a profile."""
        created = service.create_profile(
            "Test Profile",
            default_weights,
            default_config,
            False,
        )
        
        new_weights = WeightProfile(
            W1=0.2, W2=0.15, W3=0.1, W4=0.15,
            W5=0.1, W6=0.1, W7=0.1, W8=0.1,
        )
        
        updated = service.update_profile(
            created.id,
            name="Updated Profile",
            weights=new_weights,
        )
        
        assert updated.name == "Updated Profile"
        assert updated.weights == new_weights

    def test_delete_profile(self, service, default_weights, default_config):
        """Test deleting a profile."""
        created = service.create_profile(
            "Test Profile",
            default_weights,
            default_config,
            False,
        )
        
        service.delete_profile(created.id)
        
        with pytest.raises(ProfileNotFoundError):
            service.get_profile(created.id)

    def test_get_default_profile(self, service, default_weights, default_config):
        """Test getting default profile."""
        # Create default profile
        default = service.create_profile(
            "Default Profile",
            default_weights,
            default_config,
            is_default=True,
        )
        
        retrieved = service.get_default_profile()
        
        assert retrieved.id == default.id
        assert retrieved.is_default is True

    def test_cannot_delete_default_profile(self, service, default_weights, default_config):
        """Test that default profile cannot be deleted."""
        default = service.create_profile(
            "Default Profile",
            default_weights,
            default_config,
            is_default=True,
        )
        
        with pytest.raises(CannotDeleteDefaultError):
            service.delete_profile(default.id)

    def test_duplicate_profile_name(self, service, default_weights, default_config):
        """Test that duplicate profile names raise error."""
        service.create_profile(
            "Test Profile",
            default_weights,
            default_config,
            False,
        )
        
        with pytest.raises(ProfileNameExistsError):
            service.create_profile(
                "Test Profile",
                default_weights,
                default_config,
                False,
            )

