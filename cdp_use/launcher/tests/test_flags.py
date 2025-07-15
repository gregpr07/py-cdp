"""Tests for the flags module."""

import pytest

from cdp_use.launcher.flags import Flag, FlagManager


class TestFlag:
    """Test Flag enum."""
    
    def test_normalize(self):
        """Test flag normalization."""
        assert Flag.USER_DATA_DIR.normalize() == "user-data-dir"
        assert Flag.HEADLESS.normalize() == "headless"
    
    def test_check_valid(self):
        """Test flag validation for valid flags."""
        Flag.USER_DATA_DIR.check()  # Should not raise
    
    def test_check_invalid(self):
        """Test flag validation for invalid flags."""
        # Create an invalid flag manually for testing
        invalid_flag = Flag("invalid=flag")
        with pytest.raises(ValueError, match="Flag name should not contain '='"):
            invalid_flag.check()


class TestFlagManager:
    """Test FlagManager class."""
    
    def test_set_and_get(self):
        """Test setting and getting flags."""
        manager = FlagManager()
        manager.set(Flag.USER_DATA_DIR, "/path/to/data")
        
        assert manager.get(Flag.USER_DATA_DIR) == "/path/to/data"
        assert manager.has(Flag.USER_DATA_DIR)
    
    def test_set_multiple_values(self):
        """Test setting flags with multiple values."""
        manager = FlagManager()
        manager.set("disable-features", "feature1", "feature2")
        
        values = manager.get_all("disable-features")
        assert values == ["feature1", "feature2"]
    
    def test_append(self):
        """Test appending values to flags."""
        manager = FlagManager()
        manager.set("disable-features", "feature1")
        manager.append("disable-features", "feature2", "feature3")
        
        values = manager.get_all("disable-features")
        assert values == ["feature1", "feature2", "feature3"]
    
    def test_delete(self):
        """Test deleting flags."""
        manager = FlagManager()
        manager.set(Flag.HEADLESS)
        assert manager.has(Flag.HEADLESS)
        
        manager.delete(Flag.HEADLESS)
        assert not manager.has(Flag.HEADLESS)
    
    def test_format_args_boolean_flag(self):
        """Test formatting boolean flags."""
        manager = FlagManager()
        manager.set(Flag.HEADLESS)
        
        args = manager.format_args()
        assert "--headless" in args
    
    def test_format_args_value_flag(self):
        """Test formatting flags with values."""
        manager = FlagManager()
        manager.set(Flag.USER_DATA_DIR, "/path/to/data")
        
        args = manager.format_args()
        assert "--user-data-dir=/path/to/data" in args
    
    def test_format_args_multiple_values(self):
        """Test formatting flags with multiple values."""
        manager = FlagManager()
        manager.set("disable-features", "feature1", "feature2")
        
        args = manager.format_args()
        assert "--disable-features=feature1,feature2" in args
    
    def test_format_args_excludes_rod_flags(self):
        """Test that rod- prefixed flags are excluded from command line."""
        manager = FlagManager()
        manager.set(Flag.BIN, "/path/to/browser")
        manager.set(Flag.HEADLESS)
        
        args = manager.format_args()
        assert "--headless" in args
        assert "--rod-bin" not in args
    
    def test_format_args_positional_arguments(self):
        """Test handling of positional arguments."""
        manager = FlagManager()
        manager.set(Flag.ARGUMENTS, "http://example.com", "arg2")
        manager.set(Flag.HEADLESS)
        
        args = manager.format_args()
        assert "http://example.com" in args
        assert "arg2" in args
        assert "--headless" in args
    
    def test_copy(self):
        """Test copying flag manager."""
        manager = FlagManager()
        manager.set(Flag.HEADLESS)
        manager.set("custom-flag", "value1", "value2")
        
        copy_manager = manager.copy()
        
        # Original and copy should have same flags
        assert copy_manager.has(Flag.HEADLESS)
        assert copy_manager.get_all("custom-flag") == ["value1", "value2"]
        
        # Modifying copy shouldn't affect original
        copy_manager.delete(Flag.HEADLESS)
        assert manager.has(Flag.HEADLESS)  # Original still has it
        assert not copy_manager.has(Flag.HEADLESS)  # Copy doesn't