#!/usr/bin/env python3
"""
Main CDP generator script.

Generates Python type-safe bindings for Chrome DevTools Protocol.
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Set

from .command_generator import CommandGenerator
from .event_generator import EventGenerator
from .protocol_generator import ProtocolGenerator
from .type_generator import TypeGenerator


class CDPGenerator:
    def __init__(self, output_dir: str = "src/cdp"):
        self.output_dir = Path(output_dir)
        self.type_generator = TypeGenerator()
        self.command_generator = CommandGenerator()
        self.event_generator = EventGenerator()
        self.protocol_generator = ProtocolGenerator()

    def load_protocols(self) -> Dict[str, Any]:
        """Load and merge multiple protocol JSON files."""
        import sys

        if len(sys.argv) < 2:
            raise ValueError("Please provide at least one protocol JSON file path")

        protocol_files = sys.argv[1:]
        merged_protocol = {"version": {"major": "1", "minor": "0"}, "domains": []}
        seen_domains = set()

        for file_path in protocol_files:
            print(f"Loading protocol file: {file_path}")
            with open(file_path, "r") as f:
                protocol = json.load(f)

            for domain in protocol.get("domains", []):
                domain_name = domain["domain"]
                if domain_name not in seen_domains:
                    merged_protocol["domains"].append(domain)
                    seen_domains.add(domain_name)

        print(
            f"Merged {len(merged_protocol['domains'])} domains from {len(protocol_files)} files"
        )
        return merged_protocol

    def clean_output_dir(self) -> None:
        """Clean the output directory."""
        if self.output_dir.exists():
            import shutil

            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True)

    def generate_all(self) -> None:
        """Generate all types, commands, events, and protocol classes."""
        protocol = self.load_protocols()
        domains = protocol.get("domains", [])

        print(f"Generating CDP types for {len(domains)} domains...")

        # Clean output directory
        self.clean_output_dir()

        # Generate for each domain
        for domain in domains:
            self.generate_domain(domain)

        # Generate main protocol file
        self.generate_protocol_file(domains)

        # Generate main __init__.py
        self.generate_main_init(domains)

        print("Generation complete!")

    def generate_domain(self, domain: Dict[str, Any]) -> None:
        """Generate types, commands, and events for a single domain."""
        domain_name = domain["domain"]
        print(f"  Generating {domain_name}...")

        # Create domain directory
        domain_dir = self.output_dir / domain_name.lower()
        domain_dir.mkdir(exist_ok=True)

        # Generate types
        types_content = self.type_generator.generate_types(domain)
        self.write_file(domain_dir / "types.py", types_content)

        # Generate commands
        commands_content = self.command_generator.generate_commands(domain)
        self.write_file(domain_dir / "commands.py", commands_content)

        # Generate events
        events_content = self.event_generator.generate_events(domain)
        self.write_file(domain_dir / "events.py", events_content)

        # Generate domain __init__.py
        init_content = self.generate_domain_init(domain)
        self.write_file(domain_dir / "__init__.py", init_content)

    def generate_protocol_file(self, domains: List[Dict[str, Any]]) -> None:
        """Generate the main protocol file."""
        content = self.protocol_generator.generate_protocol(domains)
        self.write_file(self.output_dir / "protocol.pyi", content)

    def generate_domain_init(self, domain: Dict[str, Any]) -> str:
        """Generate __init__.py for a domain."""
        domain_name = domain["domain"]

        content = f'"""CDP {domain_name} Domain"""'
        content += "\n\n"
        content += "from .types import *\n"
        content += "from .commands import *\n"
        content += "from .events import *\n"

        return content

    def generate_main_init(self, domains: List[Dict[str, Any]]) -> None:
        """Generate main __init__.py file."""
        content = '"""CDP Type-Safe Client"""'
        content += "\n\n"

        # Import all domains
        for domain in domains:
            domain_name = domain["domain"].lower()
            content += f"from . import {domain_name}\n"

        content += "\nfrom .protocol import CDPClientProtocol\n"

        # List all domains for easy access
        content += "\n__all__ = [\n"
        for domain in domains:
            domain_name = domain["domain"].lower()
            content += f'    "{domain_name}",\n'
        content += '    "CDPClientProtocol",\n'
        content += "]\n"

        self.write_file(self.output_dir / "__init__.py", content)

    def write_file(self, path: Path, content: str) -> None:
        """Write content to a file."""
        with open(path, "w") as f:
            f.write(content)


def main():
    generator = CDPGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()
