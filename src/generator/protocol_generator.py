"""
Protocol generator for CDP client protocol.

Generates a Python stub file (.pyi) with overloaded send methods for type-safe CDP communication.
"""

from typing import Any, Dict, List


class ProtocolGenerator:
    """Generates the CDPClientProtocol with overloaded send methods."""

    def __init__(self):
        self.overloads = []

    def generate_protocol(self, domains: List[Dict[str, Any]]) -> str:
        """Generate the main protocol file with overloaded send methods."""
        # Clear previous overloads
        self.overloads.clear()

        # Collect all command imports and generate overloads
        type_imports = set()

        for domain in domains:
            domain_name = domain["domain"]
            domain_lower = domain_name.lower()

            # Add imports for parameter and return types
            commands = domain.get("commands", [])
            for command in commands:
                command_name = command["name"]
                method_name = f"{domain_name}.{command_name}"

                # Generate parameter imports
                parameters = command.get("parameters", [])
                if parameters:
                    param_class = self.to_class_name(command_name) + "Parameters"
                    type_imports.add(
                        f"from .{domain_lower}.commands import {param_class}"
                    )

                # Generate return imports
                returns = command.get("returns", [])
                if returns:
                    return_class = self.to_class_name(command_name) + "Returns"
                    type_imports.add(
                        f"from .{domain_lower}.commands import {return_class}"
                    )

                # Generate overload
                self.generate_command_overload(domain_name, command)

        # Build the complete protocol file
        content = self.build_protocol_file(type_imports)
        return content

    def generate_command_overload(
        self, domain_name: str, command: Dict[str, Any]
    ) -> None:
        """Generate an overload for a single command."""
        command_name = command["name"]
        method_name = f"{domain_name}.{command_name}"

        parameters = command.get("parameters", [])
        returns = command.get("returns", [])

        # Determine parameter type
        if parameters:
            param_type = self.to_class_name(command_name) + "Parameters"
        else:
            param_type = "None"

        # Determine return type
        if returns:
            return_type = self.to_class_name(command_name) + "Returns"
        else:
            return_type = "Dict[str, Any]"

        # Generate overload
        overload = f"""    @overload
    async def send(
        self,
        method: Literal["{method_name}"],
        params: {param_type},
        session_id: Optional[str] = None,
    ) -> {return_type}: ..."""

        # Handle commands with no parameters
        if parameters:
            overload = overload.replace(
                f"params: {param_type}", f"params: {param_type}"
            )
        else:
            overload = overload.replace(f"params: {param_type}", "params: None = None")

        self.overloads.append(overload)

    def build_protocol_file(self, type_imports: set) -> str:
        """Build the complete protocol file content."""
        content = '"""CDP Client Protocol"""\n\n'

        # Basic imports
        content += "from typing import Any, Dict, List, Optional, Union, overload\n"
        content += "from typing_extensions import Protocol, Literal\n\n"

        # TYPE_CHECKING section for all command imports
        content += "from typing import TYPE_CHECKING\n\n"
        content += "if TYPE_CHECKING:\n"
        for imp in sorted(type_imports):
            content += f"    {imp}\n"
        content += "\n"

        # Protocol class definition
        content += "class CDPClientProtocol(Protocol):\n"
        content += '    """Protocol for CDP client with type-safe send methods."""\n\n'

        # Add all overloads
        for overload in self.overloads:
            content += overload + "\n"

        return content

    def to_class_name(self, name: str) -> str:
        """Convert a command name to a class name."""
        # Convert camelCase to PascalCase
        if name:
            return name[0].upper() + name[1:]
        return name
