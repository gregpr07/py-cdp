"""
Library generator for CDP client library.

Generates a Python class library with domain-specific clients for type-safe CDP communication.
"""

from typing import Any, Dict, List


class LibraryGenerator:
    """Generates the CDP client library with domain-specific client classes."""

    def __init__(self):
        self.domain_clients = []

    def generate_domain_library(self, domain: Dict[str, Any]) -> str:
        """Generate a domain-specific library file."""
        domain_name = domain["domain"]
        client_class_name = f"{domain_name}Client"

        # Collect imports for this domain
        type_imports = set()
        commands = domain.get("commands", [])

        for command in commands:
            command_name = command["name"]

            # Generate parameter imports
            parameters = command.get("parameters", [])
            if parameters:
                param_class = self.to_class_name(command_name) + "Parameters"
                type_imports.add(f"from .commands import {param_class}")

            # Generate return imports
            returns = command.get("returns", [])
            if returns:
                return_class = self.to_class_name(command_name) + "Returns"
                type_imports.add(f"from .commands import {return_class}")

        # Generate the domain client class
        client_class = self.generate_domain_client(domain, client_class_name)

        # Build the complete domain library file
        content = self.build_domain_library_file(
            type_imports, client_class, domain_name
        )
        return content

    def generate_main_library(self, domains: List[Dict[str, Any]]) -> str:
        """Generate the main library file that combines all domain clients."""
        # Clear previous domain clients
        self.domain_clients.clear()

        # Collect domain info
        for domain in domains:
            domain_name = domain["domain"]
            domain_lower = domain_name.lower()
            client_class_name = f"{domain_name}Client"

            self.domain_clients.append(
                {
                    "name": domain_name,
                    "class_name": client_class_name,
                    "lower_name": domain_lower,
                }
            )

        # Build the main library file
        content = self.build_main_library_file()
        return content

    def generate_domain_client(
        self, domain: Dict[str, Any], client_class_name: str
    ) -> str:
        """Generate a client class for a single domain."""
        domain_name = domain["domain"]
        commands = domain.get("commands", [])

        content = f"class {client_class_name}:\n"
        content += f'    """Client for {domain_name} domain commands."""\n\n'
        content += "    def __init__(self, client: 'CDPClient'):\n"
        content += "        self._client = client\n\n"

        # Generate methods for each command
        for command in commands:
            command_method = self.generate_command_method(command, domain_name)
            content += command_method + "\n"

        return content

    def generate_command_method(self, command: Dict[str, Any], domain_name: str) -> str:
        """Generate a method for a single command."""
        command_name = command["name"]
        method_name = self.to_method_name(command_name)
        cdp_method_name = f"{domain_name}.{command_name}"

        parameters = command.get("parameters", [])
        returns = command.get("returns", [])

        # Determine parameter type with proper optional handling (quoted for forward references)
        if parameters:
            param_class = '"' + self.to_class_name(command_name) + 'Parameters"'
            # Check if all parameters are optional
            all_optional = all(param.get("optional", False) for param in parameters)
            if all_optional:
                param_arg = f"params: Optional[{param_class}] = None"
            else:
                param_arg = f"params: {param_class}"
        else:
            param_arg = "params: None = None"

        # Determine return type (quoted for forward references)
        if returns:
            return_type = '"' + self.to_class_name(command_name) + 'Returns"'
        else:
            return_type = '"Dict[str, Any]"'

        # Generate method
        content = f"    async def {method_name}(\n"
        content += "        self,\n"
        content += f"        {param_arg},\n"
        content += "        session_id: Optional[str] = None,\n"
        content += f"    ) -> {return_type}:\n"

        # Add docstring if command has description
        description = command.get("description", "")
        if description:
            escaped_desc = description.replace("\\", "\\\\").replace('"', '\\"')
            content += f'        """{escaped_desc}"""\n'

        # Use cast for type safety
        content += f"        return cast({return_type}, await self._client.send_raw(\n"
        content += f'            method="{cdp_method_name}",\n'
        content += "            params=params,\n"
        content += "            session_id=session_id,\n"
        content += "        ))\n"

        return content

    def build_domain_library_file(
        self, type_imports: set, client_class: str, domain_name: str
    ) -> str:
        """Build a domain-specific library file."""
        # Start with auto-generated header
        content = """# This file is auto-generated by the CDP protocol generator.
# Do not edit this file manually as your changes will be overwritten.
# Generated from Chrome DevTools Protocol specifications.

"""
        content += f'"""CDP {domain_name} Domain Library"""\n\n'

        # Basic imports
        content += "from typing import Any, Dict, Optional, cast\n\n"

        # TYPE_CHECKING section for CDPClient and command imports
        content += "from typing import TYPE_CHECKING\n\n"
        content += "if TYPE_CHECKING:\n"
        content += "    from ...client import CDPClient\n"
        for imp in sorted(type_imports):
            content += f"    {imp}\n"
        content += "\n"

        # Add the domain client class
        content += client_class + "\n"

        return content

    def build_main_library_file(self) -> str:
        """Build the main library file that combines all domain clients."""
        # Start with auto-generated header
        content = """# This file is auto-generated by the CDP protocol generator.
# Do not edit this file manually as your changes will be overwritten.
# Generated from Chrome DevTools Protocol specifications.

"""
        content += '"""CDP Client Library"""\n\n'

        # Basic imports
        content += "from typing import TYPE_CHECKING\n\n"

        # TYPE_CHECKING section for CDPClient and domain clients
        content += "if TYPE_CHECKING:\n"
        content += "    from ..client import CDPClient\n"
        for domain_info in self.domain_clients:
            domain_lower = domain_info["lower_name"]
            client_class_name = domain_info["class_name"]
            content += f"    from .{domain_lower}.library import {client_class_name}\n"
        content += "\n"

        # Generate main library class
        content += "class CDPLibrary:\n"
        content += '    """Main CDP library with domain-specific clients."""\n\n'
        content += "    def __init__(self, client: 'CDPClient'):\n"
        content += "        self._client = client\n"

        # Add properties for each domain client (lazy imports to avoid circular dependencies)
        for domain_info in self.domain_clients:
            domain_name = domain_info["name"]
            domain_lower = domain_info["lower_name"]
            client_class_name = domain_info["class_name"]

            content += f"\n        # {domain_name} domain\n"
            content += (
                f"        from .{domain_lower}.library import {client_class_name}\n"
            )
            content += f"        self.{domain_name} = {client_class_name}(client)\n"

        content += "\n"

        return content

    def to_class_name(self, name: str) -> str:
        """Convert a command name to a class name."""
        # Convert camelCase to PascalCase
        if name:
            return name[0].upper() + name[1:]
        return name

    def to_method_name(self, name: str) -> str:
        """Convert a command name to a method name."""
        # Keep camelCase as is for method names
        return name
