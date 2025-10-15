"""
Tests for Voice Settings API
"""

import pytest
from httpx import AsyncClient
from backend.app.main import app
from backend.app.models.voice import VoiceSettings


@pytest.mark.asyncio
class TestVoiceSettingsAPI:
    """Test Voice Settings API endpoints."""

    @pytest.fixture
    async def client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_get_voice_settings_default(self, client):
        """Test getting default voice settings for new user."""
        response = await client.get("/api/voice-settings/test-user-123")

        assert response.status_code == 200
        data = response.json()

        # Check defaults
        assert data['vad_threshold'] == 0.02
        assert data['silence_timeout_ms'] == 700
        assert data['min_recording_duration_ms'] == 500
        assert data['vad_check_interval_ms'] == 250
        assert data['backend_vad_enabled'] is True
        assert data['backend_vad_mode'] == 3
        assert data['use_compression'] is False

    async def test_update_voice_settings(self, client):
        """Test updating voice settings."""
        new_settings = {
            "vad_threshold": 0.03,
            "silence_timeout_ms": 1000,
            "use_compression": True,
            "compression_bitrate": 128000
        }

        response = await client.put(
            "/api/voice-settings/test-user-456",
            json=new_settings
        )

        assert response.status_code == 200
        data = response.json()

        # Check updated values
        assert data['vad_threshold'] == 0.03
        assert data['silence_timeout_ms'] == 1000
        assert data['use_compression'] is True
        assert data['compression_bitrate'] == 128000

    async def test_update_voice_settings_validation(self, client):
        """Test voice settings validation."""
        # Invalid VAD threshold (too high)
        invalid_settings = {
            "vad_threshold": 0.5  # Max is 0.1
        }

        response = await client.put(
            "/api/voice-settings/test-user-789",
            json=invalid_settings
        )

        # Should reject invalid value
        assert response.status_code == 422

    async def test_reset_voice_settings(self, client):
        """Test resetting voice settings to defaults."""
        # First, update settings
        await client.put(
            "/api/voice-settings/test-user-reset",
            json={"vad_threshold": 0.05}
        )

        # Then reset
        response = await client.delete("/api/voice-settings/test-user-reset")

        assert response.status_code == 200
        assert "reset" in response.json()['message'].lower()

        # Verify defaults restored
        get_response = await client.get("/api/voice-settings/test-user-reset")
        data = get_response.json()
        assert data['vad_threshold'] == 0.02  # Back to default

    async def test_get_vad_presets(self, client):
        """Test getting VAD presets."""
        response = await client.get("/api/voice-settings/any-user/presets")

        assert response.status_code == 200
        data = response.json()

        # Check all presets exist
        assert 'sensitive' in data
        assert 'balanced' in data
        assert 'strict' in data

        # Check preset structure
        assert data['sensitive']['vad_threshold'] == 0.01
        assert data['balanced']['vad_threshold'] == 0.02
        assert data['strict']['vad_threshold'] == 0.03

    async def test_get_compression_info(self, client):
        """Test getting compression information."""
        response = await client.get("/api/voice-settings/any-user/compression-info")

        assert response.status_code == 200
        data = response.json()

        # Check formats
        assert 'formats' in data
        assert 'wav' in data['formats']
        assert 'opus' in data['formats']

        # Check recommendations
        assert 'recommendations' in data
        assert data['recommendations']['mobile'] == 'opus'
        assert data['recommendations']['desktop'] == 'wav'


class TestVoiceSettingsModel:
    """Test VoiceSettings Pydantic model."""

    def test_default_values(self):
        """Test default values are set correctly."""
        settings = VoiceSettings()

        assert settings.vad_threshold == 0.02
        assert settings.silence_timeout_ms == 700
        assert settings.min_recording_duration_ms == 500
        assert settings.vad_check_interval_ms == 250
        assert settings.backend_vad_mode == 3
        assert settings.backend_energy_threshold == 500.0
        assert settings.use_compression is False
        assert settings.compression_codec == "opus"
        assert settings.compression_bitrate == 64000

    def test_validation_vad_threshold_min(self):
        """Test VAD threshold minimum validation."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            VoiceSettings(vad_threshold=0.005)  # Below minimum 0.01

    def test_validation_vad_threshold_max(self):
        """Test VAD threshold maximum validation."""
        with pytest.raises(Exception):
            VoiceSettings(vad_threshold=0.15)  # Above maximum 0.1

    def test_validation_silence_timeout_min(self):
        """Test silence timeout minimum validation."""
        with pytest.raises(Exception):
            VoiceSettings(silence_timeout_ms=200)  # Below minimum 300

    def test_validation_silence_timeout_max(self):
        """Test silence timeout maximum validation."""
        with pytest.raises(Exception):
            VoiceSettings(silence_timeout_ms=3000)  # Above maximum 2000

    def test_validation_vad_mode(self):
        """Test VAD mode validation."""
        with pytest.raises(Exception):
            VoiceSettings(backend_vad_mode=5)  # Above maximum 3

    def test_custom_values(self):
        """Test creating settings with custom values."""
        settings = VoiceSettings(
            vad_threshold=0.03,
            silence_timeout_ms=1000,
            use_compression=True,
            compression_bitrate=128000
        )

        assert settings.vad_threshold == 0.03
        assert settings.silence_timeout_ms == 1000
        assert settings.use_compression is True
        assert settings.compression_bitrate == 128000

    def test_json_serialization(self):
        """Test JSON serialization/deserialization."""
        settings = VoiceSettings(
            vad_threshold=0.025,
            use_compression=True
        )

        # Serialize to JSON
        json_str = settings.model_dump_json()
        assert isinstance(json_str, str)

        # Deserialize from JSON
        restored = VoiceSettings.model_validate_json(json_str)
        assert restored.vad_threshold == 0.025
        assert restored.use_compression is True


@pytest.mark.integration
class TestVoiceSettingsIntegration:
    """Integration tests for voice settings with database and cache."""

    @pytest.fixture
    async def client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_settings_persistence(self, client):
        """Test settings persist across requests."""
        user_id = "test-persistence-user"

        # Update settings
        new_settings = {
            "vad_threshold": 0.025,
            "use_compression": True
        }

        await client.put(
            f"/api/voice-settings/{user_id}",
            json=new_settings
        )

        # Get settings (should retrieve from cache/db)
        response = await client.get(f"/api/voice-settings/{user_id}")
        data = response.json()

        assert data['vad_threshold'] == 0.025
        assert data['use_compression'] is True

    async def test_multiple_users_isolation(self, client):
        """Test settings are isolated per user."""
        # User 1 settings
        await client.put(
            "/api/voice-settings/user1",
            json={"vad_threshold": 0.01}
        )

        # User 2 settings
        await client.put(
            "/api/voice-settings/user2",
            json={"vad_threshold": 0.03}
        )

        # Verify isolation
        user1_response = await client.get("/api/voice-settings/user1")
        user2_response = await client.get("/api/voice-settings/user2")

        assert user1_response.json()['vad_threshold'] == 0.01
        assert user2_response.json()['vad_threshold'] == 0.03
