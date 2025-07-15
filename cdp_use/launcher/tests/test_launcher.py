"""Tests for the launcher module."""

import pytest
from unittest.mock import Mock, patch

from cdp_use.launcher.launcher import Launcher, LauncherConfig, new, new_user_mode, new_app_mode
from cdp_use.launcher.errors import AlreadyLaunchedError


class TestLauncherConfig:
    """Test LauncherConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LauncherConfig()
        
        assert config.bin_path is None
        assert config.headless is True
        assert config.no_sandbox is False
        assert config.remote_debugging_port == 0
        assert config.leakless is True
        assert config.user_data_dir is not None  # Should be set by __post_init__
        assert "session-" in config.user_data_dir
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = LauncherConfig(
            headless=False,
            window_size=(1920, 1080),
            proxy_server="proxy.example.com:8080"
        )
        
        assert config.headless is False
        assert config.window_size == (1920, 1080)
        assert config.proxy_server == "proxy.example.com:8080"


class TestLauncher:
    """Test Launcher class."""
    
    def test_init_default_config(self):
        """Test launcher initialization with default config."""
        launcher = Launcher()
        
        assert launcher.config is not None
        assert launcher.config.headless is True
        assert launcher._launched is False
    
    def test_init_custom_config(self):
        """Test launcher initialization with custom config."""
        config = LauncherConfig(headless=False)
        launcher = Launcher(config)
        
        assert launcher.config is config
        assert launcher.config.headless is False
    
    def test_fluent_api_bin(self):
        """Test fluent API for setting binary path."""
        launcher = Launcher()
        result = launcher.bin("/path/to/chrome")
        
        assert result is launcher  # Should return self for chaining
        assert launcher.config.bin_path == "/path/to/chrome"
    
    def test_fluent_api_headless(self):
        """Test fluent API for headless setting."""
        launcher = Launcher()
        
        # Test enabling headless
        launcher.headless(True)
        assert launcher.config.headless is True
        assert launcher.config.headless_new is False
        
        # Test disabling headless
        launcher.headless(False)
        assert launcher.config.headless is False
    
    def test_fluent_api_headless_new(self):
        """Test fluent API for new headless mode."""
        launcher = Launcher()
        
        launcher.headless_new(True)
        assert launcher.config.headless_new is True
        assert launcher.config.headless is False  # Should disable regular headless
    
    def test_fluent_api_window_size(self):
        """Test fluent API for window size."""
        launcher = Launcher()
        launcher.window_size(1920, 1080)
        
        assert launcher.config.window_size == (1920, 1080)
    
    def test_fluent_api_env(self):
        """Test fluent API for environment variables."""
        launcher = Launcher()
        launcher.env(TZ="America/New_York", DISPLAY=":0")
        
        assert launcher.config.env["TZ"] == "America/New_York"
        assert launcher.config.env["DISPLAY"] == ":0"
    
    def test_fluent_api_flag(self):
        """Test fluent API for custom flags."""
        launcher = Launcher()
        launcher.flag("custom-flag", "value1", "value2")
        
        assert launcher.config.custom_flags["custom-flag"] == ["value1", "value2"]
    
    def test_fluent_api_delete_flag(self):
        """Test fluent API for deleting flags."""
        launcher = Launcher()
        launcher.flag("custom-flag", "value")
        assert "custom-flag" in launcher.config.custom_flags
        
        launcher.delete_flag("custom-flag")
        assert "custom-flag" not in launcher.config.custom_flags
    
    def test_fluent_api_chaining(self):
        """Test fluent API method chaining."""
        launcher = (Launcher()
                   .headless(False)
                   .window_size(1920, 1080)
                   .no_sandbox(True)
                   .remote_debugging_port(9222))
        
        assert launcher.config.headless is False
        assert launcher.config.window_size == (1920, 1080)
        assert launcher.config.no_sandbox is True
        assert launcher.config.remote_debugging_port == 9222
    
    @patch('cdp_use.launcher.launcher.subprocess.Popen')
    @patch('cdp_use.launcher.launcher.find_installed_browser')
    def test_launch_already_launched(self, mock_find_browser, mock_popen):
        """Test launching when already launched raises error."""
        mock_find_browser.return_value = "/usr/bin/chrome"
        
        launcher = Launcher()
        launcher._launched = True
        
        with pytest.raises(AlreadyLaunchedError):
            launcher.launch()
    
    def test_pid_property(self):
        """Test PID property."""
        launcher = Launcher()
        assert launcher.pid is None
        
        # Mock a process
        mock_process = Mock()
        mock_process.pid = 12345
        launcher._process = mock_process
        
        assert launcher.pid == 12345
    
    @patch('cdp_use.launcher.launcher.os_utils.kill_process_group')
    def test_kill(self, mock_kill_group):
        """Test killing browser process."""
        launcher = Launcher()
        
        # Mock a process
        mock_process = Mock()
        mock_process.pid = 12345
        launcher._process = mock_process
        
        launcher.kill()
        
        mock_kill_group.assert_called_once_with(12345)
        mock_process.terminate.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_new(self):
        """Test new() function."""
        launcher = new()
        
        assert isinstance(launcher, Launcher)
        assert launcher.config.headless is True
    
    def test_new_user_mode(self):
        """Test new_user_mode() function."""
        launcher = new_user_mode()
        
        assert isinstance(launcher, Launcher)
        assert launcher.config.headless is False
        assert launcher.config.leakless is False
        assert launcher.config.remote_debugging_port == 37712
    
    def test_new_app_mode(self):
        """Test new_app_mode() function."""
        url = "https://example.com"
        launcher = new_app_mode(url)
        
        assert isinstance(launcher, Launcher)
        assert launcher.config.headless is False
        assert launcher.config.start_url == url
        assert launcher.config.leakless is True