"""Browser command-line flags management."""

from enum import Enum
from typing import Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self
else:
    try:
        from typing import Self
    except ImportError:
        from typing_extensions import Self


class Flag(str, Enum):
    """Browser command-line flags enumeration."""
    
    # Core browser flags
    USER_DATA_DIR = "user-data-dir"
    HEADLESS = "headless" 
    APP = "app"
    REMOTE_DEBUGGING_PORT = "remote-debugging-port"
    NO_SANDBOX = "no-sandbox"
    PROXY_SERVER = "proxy-server"
    WINDOW_SIZE = "window-size"
    WINDOW_POSITION = "window-position"
    PROFILE_DIRECTORY = "profile-directory"
    
    # Custom bu flags (prefixed with bu-)
    WORKING_DIR = "bu-working-dir"
    ENV = "bu-env"
    XVFB = "bu-xvfb"
    PREFERENCES = "bu-preferences"
    LEAKLESS = "bu-leakless"
    BIN = "bu-bin"
    KEEP_USER_DATA_DIR = "bu-keep-user-data-dir"
    ARGUMENTS = ""  # Special case for positional arguments
    
    def normalize(self) -> str:
        """Remove leading dashes from flag name."""
        return self.value.lstrip("-")
    
    def check(self) -> None:
        """Validate flag name doesn't contain equals sign."""
        if "=" in self.value:
            raise ValueError("Flag name should not contain '='")


class FlagManager:
    """Manages browser command-line flags."""
    
    def __init__(self):
        self._flags: Dict[str, List[str]] = {}
    
    def set(self, flag: Union[Flag, str], *values: str) -> Self:
        """Set a flag with one or more values."""
        if isinstance(flag, Flag):
            flag.check()
            flag_name = flag.normalize()
        else:
            flag_name = str(flag).lstrip("-")
        
        self._flags[flag_name] = list(values)
        return self
    
    def get(self, flag: Union[Flag, str]) -> Optional[str]:
        """Get the first value of a flag."""
        values = self.get_all(flag)
        return values[0] if values else None
    
    def get_all(self, flag: Union[Flag, str]) -> List[str]:
        """Get all values of a flag."""
        flag_name = flag.normalize() if isinstance(flag, Flag) else str(flag).lstrip("-")
        return self._flags.get(flag_name, [])
    
    def has(self, flag: Union[Flag, str]) -> bool:
        """Check if a flag is set."""
        flag_name = flag.normalize() if isinstance(flag, Flag) else str(flag).lstrip("-")
        return flag_name in self._flags
    
    def append(self, flag: Union[Flag, str], *values: str) -> Self:
        """Append values to an existing flag."""
        flag_name = flag.normalize() if isinstance(flag, Flag) else str(flag).lstrip("-")
        if flag_name not in self._flags:
            self._flags[flag_name] = []
        self._flags[flag_name].extend(values)
        return self
    
    def delete(self, flag: Union[Flag, str]) -> Self:
        """Remove a flag."""
        flag_name = flag.normalize() if isinstance(flag, Flag) else str(flag).lstrip("-")
        self._flags.pop(flag_name, None)
        return self
    
    def format_args(self) -> List[str]:
        """Format flags as command-line arguments."""
        args = []
        
        for flag_name, values in self._flags.items():
            if flag_name == Flag.ARGUMENTS.value:  # Special case for positional args
                continue
            
            if flag_name.startswith("bu-"):  # Skip internal bu flags
                continue
            
            # Format flag
            if values:
                flag_str = f"--{flag_name}={','.join(values)}"
            else:
                flag_str = f"--{flag_name}"
            
            args.append(flag_str)
        
        # Add positional arguments at the end
        if Flag.ARGUMENTS.value in self._flags:
            args.extend(self._flags[Flag.ARGUMENTS.value])
        
        return sorted(args)
    
    def copy(self) -> Self:
        """Create a copy of the flag manager."""
        new_manager = FlagManager()
        new_manager._flags = {k: v.copy() for k, v in self._flags.items()}
        return new_manager