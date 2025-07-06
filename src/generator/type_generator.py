"""
Type generator for CDP protocol types.

Converts CDP protocol JSON type definitions to Python TypedDict classes.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple


class TypeGenerator:
    """Generates Python TypedDict classes from CDP protocol type definitions."""

    def __init__(self):
        self.imports = set()
        self.generated_types = set()
        self.type_checking_imports = set()

    def generate_types(self, domain: Dict[str, Any]) -> str:
        """Generate types.py content for a domain."""
        self.imports.clear()
        self.generated_types.clear()
        self.type_checking_imports.clear()

        domain_name = domain["domain"]
        types = domain.get("types", [])

        # Always add basic imports
        self.imports.add("from typing import Any, Dict, List, Optional, Union")
        self.imports.add("from typing_extensions import TypedDict")
        self.imports.add("from enum import Enum")

        # First pass: collect all type names that will be defined in this domain
        for type_def in types:
            self.generated_types.add(type_def["id"])

        content = f'"""CDP {domain_name} Domain Types"""'
        content += "\n\n"

        # Generate type definitions
        type_definitions = []
        for type_def in types:
            type_content = self.generate_type_definition(type_def, domain_name)
            if type_content:
                type_definitions.append(type_content)

        # Add imports (excluding self-imports)
        external_imports = {
            imp
            for imp in self.imports
            if not imp.startswith(f"from ..{domain_name.lower()}.types import")
        }
        if external_imports:
            content += "\n".join(sorted(external_imports))
            content += "\n\n"

        # Add TYPE_CHECKING imports if any
        if self.type_checking_imports:
            content += "from typing import TYPE_CHECKING\n\n"
            content += "if TYPE_CHECKING:\n"
            for imp in sorted(self.type_checking_imports):
                content += f"    {imp}\n"
            content += "\n"

        # Add type definitions
        if type_definitions:
            content += "\n\n\n".join(type_definitions)
        else:
            content += "# No types defined for this domain"

        return content

    def generate_type_definition(
        self, type_def: Dict[str, Any], domain_name: str
    ) -> str:
        """Generate a single type definition."""
        type_id = type_def["id"]
        type_type = type_def.get("type", "object")
        description = type_def.get("description", "")

        # Handle enum types
        if type_type == "string" and "enum" in type_def:
            return self.generate_enum_type(type_id, type_def, description)

        # Handle primitive types with restrictions
        if type_type in ["string", "integer", "number", "boolean"]:
            return self.generate_primitive_type(type_id, type_def, description)

        # Handle object types
        if type_type == "object":
            return self.generate_object_type(
                type_id, type_def, description, domain_name
            )

        # Handle array types
        if type_type == "array":
            return self.generate_array_type(type_id, type_def, description, domain_name)

        return ""

    def generate_enum_type(
        self, type_id: str, type_def: Dict[str, Any], description: str
    ) -> str:
        """Generate an enum type."""
        enum_values = type_def["enum"]

        content = ""
        if description:
            # Escape all quotes in descriptions
            escaped_desc = description.replace("\\", "\\\\").replace('"', '\\"')
            content += f'"""{escaped_desc}"""\n'

        content += f"class {type_id}(Enum):\n"

        for value in enum_values:
            # Convert enum value to valid Python identifier
            attr_name = self.to_python_identifier(value)
            content += f'    {attr_name} = "{value}"\n'

        self.generated_types.add(type_id)
        return content

    def generate_primitive_type(
        self, type_id: str, type_def: Dict[str, Any], description: str
    ) -> str:
        """Generate a primitive type alias."""
        type_type = type_def["type"]
        python_type = self.map_primitive_type(type_type)

        content = ""
        if description:
            # Escape all quotes in descriptions
            escaped_desc = description.replace("\\", "\\\\").replace('"', '\\"')
            content += f'"""{escaped_desc}"""\n'

        content += f"{type_id} = {python_type}\n"

        self.generated_types.add(type_id)
        return content

    def generate_object_type(
        self, type_id: str, type_def: Dict[str, Any], description: str, domain_name: str
    ) -> str:
        """Generate a TypedDict for object types."""
        properties = type_def.get("properties", [])

        content = ""
        if description:
            # Escape all quotes in descriptions
            escaped_desc = description.replace("\\", "\\\\").replace('"', '\\"')
            content += f'"""{escaped_desc}"""\n'

        content += f"class {type_id}(TypedDict"

        # Check if all properties are optional
        required_props = set()
        optional_props = set()

        for prop in properties:
            prop_name = prop["name"]
            is_optional = prop.get("optional", False)

            if is_optional:
                optional_props.add(prop_name)
            else:
                required_props.add(prop_name)

        # Use total=False if all properties are optional
        if optional_props and not required_props:
            content += ", total=False"

        content += "):\n"

        if not properties:
            content += "    pass\n"
        else:
            for prop in properties:
                prop_name = prop["name"]
                prop_type = self.resolve_property_type(prop, domain_name)
                prop_desc = prop.get("description", "")

                # Handle optional properties
                if prop.get("optional", False) and required_props:
                    prop_type = f"Optional[{prop_type}]"

                content += f'    {prop_name}: "{prop_type}"\n'

                if prop_desc:
                    # Escape all quotes in descriptions
                    escaped_desc = prop_desc.replace("\\", "\\\\").replace('"', '\\"')
                    content += f'    """{escaped_desc}"""\n'

        self.generated_types.add(type_id)
        return content

    def generate_array_type(
        self,
        type_id: str,
        type_def: Dict[str, Any],
        description: str,
        domain_name: str = "",
    ) -> str:
        """Generate an array type alias."""
        items = type_def.get("items", {})
        item_type = self.resolve_type_reference(items, domain_name)

        content = ""
        if description:
            # Escape all quotes in descriptions
            escaped_desc = description.replace("\\", "\\\\").replace('"', '\\"')
            content += f'"""{escaped_desc}"""\n'

        content += f"{type_id} = List[{item_type}]\n"

        self.generated_types.add(type_id)
        return content

    def resolve_property_type(self, prop: Dict[str, Any], domain_name: str) -> str:
        """Resolve the Python type for a property."""
        # Check for $ref first
        if "$ref" in prop:
            return self.resolve_type_reference(prop, domain_name)

        # Handle inline types
        prop_type = prop.get("type", "any")

        if prop_type == "array":
            items = prop.get("items", {})
            item_type = self.resolve_type_reference(items, domain_name)
            return f"List[{item_type}]"

        if prop_type == "object":
            return "Dict[str, Any]"

        return self.map_primitive_type(prop_type)

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
                current_domain_lower = current_domain.lower()

                # Only add import if it's actually a different domain OR if it's the same domain but the type is not defined in this file
                if domain_ref != current_domain_lower:
                    # Add import for cross-domain reference in TYPE_CHECKING
                    self.type_checking_imports.add(
                        f"from ..{domain_ref}.types import {type_name}"
                    )
                elif type_name not in self.generated_types:
                    # Same domain but type not defined in this file - shouldn't happen but add import as fallback
                    self.type_checking_imports.add(
                        f"from ..{domain_ref}.types import {type_name}"
                    )
                # If same domain and type IS defined in this file, don't import - just return the type name
                return type_name
            else:
                # Same domain reference - only import if not defined in this file
                if ref not in self.generated_types:
                    # Type not defined in this file, import it
                    self.type_checking_imports.add(f"from .types import {ref}")
                # If type IS defined in this file, don't import it
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

    def to_python_identifier(self, name: str) -> str:
        """Convert a string to a valid Python identifier."""
        # Replace invalid characters with underscores
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Ensure it starts with a letter or underscore
        if name and name[0].isdigit():
            name = "_" + name

        # Convert to uppercase for enum values
        return name.upper()

    def sanitize_name(self, name: str) -> str:
        """Sanitize a name to be a valid Python identifier."""
        # Replace invalid characters
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Ensure it starts with a letter or underscore
        if name and name[0].isdigit():
            name = "_" + name

        return name
