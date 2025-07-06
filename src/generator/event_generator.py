"""
Event generator for CDP protocol events.

Generates Python TypedDict classes for CDP events.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple


class EventGenerator:
    """Generates Python TypedDict classes for CDP events."""

    def __init__(self):
        self.imports = set()
        self.generated_events = set()
        self.type_checking_imports = set()

    def generate_events(self, domain: Dict[str, Any]) -> str:
        """Generate events.py content for a domain."""
        self.imports.clear()
        self.generated_events.clear()
        self.type_checking_imports.clear()

        domain_name = domain["domain"]
        events = domain.get("events", [])

        # Always add basic imports
        self.imports.add("from typing import Any, Dict, List, Optional, Union")
        self.imports.add("from typing_extensions import TypedDict")

        content = f'"""CDP {domain_name} Domain Events"""'
        content += "\n\n"

        # Generate event definitions
        event_definitions = []
        for event in events:
            event_content = self.generate_event_definition(event, domain_name)
            if event_content:
                event_definitions.append(event_content)

        # Add imports
        if self.imports:
            content += "\n".join(sorted(self.imports))
            content += "\n\n"

        # Add TYPE_CHECKING imports if any
        if self.type_checking_imports:
            content += "from typing import TYPE_CHECKING\n\n"
            content += "if TYPE_CHECKING:\n"
            for imp in sorted(self.type_checking_imports):
                content += f"    {imp}\n"
            content += "\n"

        # Add event definitions
        if event_definitions:
            content += "\n\n\n".join(event_definitions)
        else:
            content += "# No events defined for this domain"

        return content

    def generate_event_definition(self, event: Dict[str, Any], domain_name: str) -> str:
        """Generate a single event definition."""
        event_name = event["name"]
        description = event.get("description", "")
        parameters = event.get("parameters", [])

        # Generate event parameter type
        return self.generate_event_type(
            event_name, parameters, domain_name, description
        )

    def generate_event_type(
        self,
        event_name: str,
        parameters: List[Dict[str, Any]],
        domain_name: str,
        description: str,
    ) -> str:
        """Generate event TypedDict for an event."""
        class_name = self.to_class_name(event_name) + "Event"

        content = ""
        if description:
            # Escape all quotes in descriptions
            escaped_desc = description.replace("\\", "\\\\").replace('"', '\\"')
            content += f'"""{escaped_desc}"""\n'

        content += f"class {class_name}(TypedDict"

        # Check if all parameters are optional
        required_params = []
        optional_params = []

        for param in parameters:
            if param.get("optional", False):
                optional_params.append(param)
            else:
                required_params.append(param)

        # Use total=False if all parameters are optional
        if optional_params and not required_params:
            content += ", total=False"

        content += "):\n"

        if not parameters:
            content += "    pass\n"
        else:
            for param in parameters:
                param_name = param["name"]
                param_type = self.resolve_parameter_type(param, domain_name)
                param_desc = param.get("description", "")

                # Handle optional parameters
                if param.get("optional", False) and required_params:
                    param_type = f"Optional[{param_type}]"

                content += f'    {param_name}: "{param_type}"\n'

                if param_desc:
                    # Escape all quotes in descriptions
                    escaped_desc = param_desc.replace("\\", "\\\\").replace('"', '\\"')
                    content += f'    """{escaped_desc}"""\n'

        self.generated_events.add(class_name)
        return content

    def resolve_parameter_type(self, param: Dict[str, Any], domain_name: str) -> str:
        """Resolve the Python type for a parameter."""
        # Check for $ref first
        if "$ref" in param:
            return self.resolve_type_reference(param, domain_name)

        # Handle inline types
        param_type = param.get("type", "any")

        if param_type == "array":
            items = param.get("items", {})
            item_type = self.resolve_type_reference(items, domain_name)
            return f"List[{item_type}]"

        if param_type == "object":
            return "Dict[str, Any]"

        return self.map_primitive_type(param_type)

    def resolve_type_reference(
        self, type_ref: Dict[str, Any], current_domain: str = ""
    ) -> str:
        """Resolve a type reference ($ref)."""
        if "$ref" in type_ref:
            ref = type_ref["$ref"]

            # Handle cross-domain references
            if "." in ref:
                # Format: DomainName.TypeName
                parts = ref.split(".")
                domain_ref = parts[0].lower()
                type_name = parts[1]
                # Add import for cross-domain reference in TYPE_CHECKING
                self.type_checking_imports.add(
                    f"from ..{domain_ref}.types import {type_name}"
                )
                return type_name
            else:
                # Same domain reference - always import from types module in events
                self.type_checking_imports.add(f"from .types import {ref}")
                return ref

        # Handle inline type definitions
        if "type" in type_ref:
            return self.map_primitive_type(type_ref["type"])

        return "Any"

    def map_primitive_type(self, cdp_type: str) -> str:
        """Map CDP primitive types to Python types."""
        mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "any": "Any",
            "object": "Dict[str, Any]",
        }
        return mapping.get(cdp_type, "Any")

    def to_class_name(self, name: str) -> str:
        """Convert an event name to a class name."""
        # Convert camelCase to PascalCase
        if name:
            return name[0].upper() + name[1:]
        return name

    def sanitize_name(self, name: str) -> str:
        """Sanitize a name to be a valid Python identifier."""
        # Replace invalid characters
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Ensure it starts with a letter or underscore
        if name and name[0].isdigit():
            name = "_" + name

        return name
