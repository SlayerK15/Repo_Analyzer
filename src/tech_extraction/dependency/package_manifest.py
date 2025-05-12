"""
Package Manifest Parser for the Technology Extraction System.

This module provides functionality for parsing various package manifest files
and extracting dependency information from them.
"""
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import toml
import yaml
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
import semver

from tech_extraction.models.dependency import (
    Dependency,
    DependencyType,
    DependencyScope,
    ManifestInfo,
)

logger = logging.getLogger(__name__)


class PackageManifestParser:
    """
    Parser for extracting dependency information from package manifest files.
    
    Supports various manifest formats:
    - JavaScript/Node.js: package.json, yarn.lock, package-lock.json
    - Python: requirements.txt, setup.py, Pipfile, poetry.lock
    - Java: pom.xml, build.gradle, build.gradle.kts
    - Ruby: Gemfile, gemspec
    - .NET: .csproj, .vbproj, packages.config
    - Go: go.mod, go.sum
    - Rust: Cargo.toml, Cargo.lock
    """
    
    def __init__(self):
        """Initialize the package manifest parser."""
        # Registry of parsers by file name
        self.parsers = {
            "package.json": self._parse_package_json,
            "yarn.lock": self._parse_yarn_lock,
            "package-lock.json": self._parse_package_lock,
            "requirements.txt": self._parse_requirements_txt,
            "setup.py": self._parse_setup_py,
            "Pipfile": self._parse_pipfile,
            "poetry.lock": self._parse_poetry_lock,
            "pom.xml": self._parse_pom_xml,
            "build.gradle": self._parse_gradle,
            "build.gradle.kts": self._parse_gradle_kts,
            "Gemfile": self._parse_gemfile,
            "go.mod": self._parse_go_mod,
            "go.sum": self._parse_go_sum,
            "Cargo.toml": self._parse_cargo_toml,
            "Cargo.lock": self._parse_cargo_lock,
        }
        
        # Additional matchers by extension or partial name
        self.extension_parsers = {
            ".csproj": self._parse_csproj,
            ".vbproj": self._parse_vbproj,
            "packages.config": self._parse_packages_config,
            ".gemspec": self._parse_gemspec,
        }
    
    def parse_manifest(self, file_path: Path) -> Optional[ManifestInfo]:
        """
        Parse a package manifest file.
        
        Args:
            file_path: Path to the manifest file
            
        Returns:
            ManifestInfo object containing parsed dependencies
        """
        filename = file_path.name
        
        # Check for exact filename matches
        if filename in self.parsers:
            parser = self.parsers[filename]
            return parser(file_path)
        
        # Check for extension or partial name matches
        for pattern, parser in self.extension_parsers.items():
            if filename.endswith(pattern):
                return parser(file_path)
        
        # No matching parser found
        logger.debug(f"No parser found for {file_path}")
        return None
    
    def _parse_package_json(self, file_path: Path) -> ManifestInfo:
        """Parse a Node.js package.json file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dependencies = []
            
            # Regular dependencies
            if "dependencies" in data:
                for name, version in data["dependencies"].items():
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=self._normalize_npm_version(version),
                            type=DependencyType.RUNTIME,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            # Dev dependencies
            if "devDependencies" in data:
                for name, version in data["devDependencies"].items():
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=self._normalize_npm_version(version),
                            type=DependencyType.DEVELOPMENT,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            # Optional dependencies
            if "optionalDependencies" in data:
                for name, version in data["optionalDependencies"].items():
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=self._normalize_npm_version(version),
                            type=DependencyType.RUNTIME,
                            scope=DependencyScope.DIRECT,
                            optional=True,
                            source=str(file_path)
                        )
                    )
            
            # Peer dependencies
            if "peerDependencies" in data:
                for name, version in data["peerDependencies"].items():
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=self._normalize_npm_version(version),
                            type=DependencyType.RUNTIME,
                            scope=DependencyScope.PEER,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="npm",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing package.json {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="npm",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_yarn_lock(self, file_path: Path) -> ManifestInfo:
        """Parse a Yarn lock file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex-based parsing for yarn.lock
            package_blocks = re.split(r'\n\n', content)
            
            for block in package_blocks:
                if not block.strip():
                    continue
                
                # Extract package name and version range
                match = re.match(r'^([\w@][^@\n"]+@[^\n"]+):\n', block)
                if match:
                    package_spec = match.group(1)
                    # Extract actual resolved version
                    version_match = re.search(r'version "(.*?)"', block)
                    version = version_match.group(1) if version_match else "unknown"
                    
                    # Extract package name from spec
                    name_match = re.match(r'([\w@][^@]+)(?:@.+)?', package_spec)
                    name = name_match.group(1) if name_match else package_spec
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=DependencyType.UNKNOWN,  # Can't tell from lock file alone
                            scope=DependencyScope.TRANSITIVE,  # Most are transitive
                            optional=False,  # Can't tell from lock file alone
                            source=str(file_path)
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="npm",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing yarn.lock {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="npm",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_package_lock(self, file_path: Path) -> ManifestInfo:
        """Parse a package-lock.json file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dependencies = []
            
            # Process packages from the modern format (v2+)
            if "packages" in data:
                for package_path, package_info in data["packages"].items():
                    # Skip the root package
                    if package_path == "":
                        continue
                    
                    # Extract package name from path
                    if "node_modules/" in package_path:
                        # For nested dependencies
                        name = package_path.split("/")[-1]
                    else:
                        # For top-level dependencies
                        name = package_path
                    
                    version = package_info.get("version", "unknown")
                    
                    dev = package_info.get("dev", False)
                    optional = package_info.get("optional", False)
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=DependencyType.DEVELOPMENT if dev else DependencyType.RUNTIME,
                            scope=DependencyScope.DIRECT if package_path.count("/") <= 1 else DependencyScope.TRANSITIVE,
                            optional=optional,
                            source=str(file_path)
                        )
                    )
            
            # Legacy format (v1)
            elif "dependencies" in data:
                def extract_deps(deps_dict, is_dev=False, path=""):
                    for name, info in deps_dict.items():
                        version = info.get("version", "unknown")
                        # Remove the version prefix (e.g., "npm:") if present
                        if version.startswith("npm:"):
                            version = version[4:]
                            
                        optional = info.get("optional", False)
                        
                        dependencies.append(
                            Dependency(
                                name=name,
                                version=version,
                                type=DependencyType.DEVELOPMENT if is_dev else DependencyType.RUNTIME,
                                scope=DependencyScope.DIRECT if not path else DependencyScope.TRANSITIVE,
                                optional=optional,
                                source=str(file_path)
                            )
                        )
                        
                        # Process nested dependencies
                        if "requires" in info:
                            for sub_name, sub_version in info["requires"].items():
                                # Skip if we already added this as a direct dependency
                                if not any(d.name == sub_name and d.version == sub_version for d in dependencies):
                                    dependencies.append(
                                        Dependency(
                                            name=sub_name,
                                            version=sub_version,
                                            type=DependencyType.RUNTIME,
                                            scope=DependencyScope.TRANSITIVE,
                                            optional=False,
                                            source=str(file_path)
                                        )
                                    )
                
                extract_deps(data["dependencies"])
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="npm",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing package-lock.json {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="npm",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_requirements_txt(self, file_path: Path) -> ManifestInfo:
        """Parse a Python requirements.txt file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Skip options and editable installs for simplicity
                if line.startswith('-') or line.startswith('--'):
                    continue
                
                try:
                    req = Requirement(line)
                    version = str(req.specifier) if req.specifier else ""
                    
                    dependencies.append(
                        Dependency(
                            name=req.name,
                            version=version,
                            type=DependencyType.RUNTIME,  # All requirements.txt are runtime by default
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
                except Exception as e:
                    logger.debug(f"Error parsing requirement '{line}': {e}")
                    # Try a simple fallback for complex requirements
                    parts = re.split(r'[<>=~!]', line, 1)
                    name = parts[0].strip()
                    version = line[len(name):].strip() if len(parts) > 1 else ""
                    
                    if name:
                        dependencies.append(
                            Dependency(
                                name=name,
                                version=version,
                                type=DependencyType.RUNTIME,
                                scope=DependencyScope.DIRECT,
                                optional=False,
                                source=str(file_path)
                            )
                        )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="python",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing requirements.txt {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="python",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_setup_py(self, file_path: Path) -> ManifestInfo:
        """
        Parse a Python setup.py file.
        
        This is a simplified parser that uses regex to extract dependencies.
        For production use, a proper AST parser would be more robust.
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract install_requires
            install_requires_match = re.search(
                r'install_requires\s*=\s*\[(.*?)\]',
                content,
                re.DOTALL
            )
            
            if install_requires_match:
                install_requires = install_requires_match.group(1)
                # Extract each quoted package
                for pkg_match in re.finditer(r'[\'"](.+?)[\'"]', install_requires):
                    pkg = pkg_match.group(1)
                    
                    try:
                        req = Requirement(pkg)
                        version = str(req.specifier) if req.specifier else ""
                        
                        dependencies.append(
                            Dependency(
                                name=req.name,
                                version=version,
                                type=DependencyType.RUNTIME,
                                scope=DependencyScope.DIRECT,
                                optional=False,
                                source=str(file_path)
                            )
                        )
                    except Exception as e:
                        logger.debug(f"Error parsing requirement '{pkg}': {e}")
                        # Simple fallback
                        parts = re.split(r'[<>=~!]', pkg, 1)
                        name = parts[0].strip()
                        version = pkg[len(name):].strip() if len(parts) > 1 else ""
                        
                        if name:
                            dependencies.append(
                                Dependency(
                                    name=name,
                                    version=version,
                                    type=DependencyType.RUNTIME,
                                    scope=DependencyScope.DIRECT,
                                    optional=False,
                                    source=str(file_path)
                                )
                            )
            
            # Extract extras_require
            extras_require_match = re.search(
                r'extras_require\s*=\s*{(.*?)}',
                content,
                re.DOTALL
            )
            
            if extras_require_match:
                extras_require = extras_require_match.group(1)
                # Extract each extra section
                for section_match in re.finditer(r'[\'"](.+?)[\'"]\s*:\s*\[(.*?)\]', extras_require, re.DOTALL):
                    section_name = section_match.group(1)
                    section_deps = section_match.group(2)
                    
                    for pkg_match in re.finditer(r'[\'"](.+?)[\'"]', section_deps):
                        pkg = pkg_match.group(1)
                        
                        try:
                            req = Requirement(pkg)
                            version = str(req.specifier) if req.specifier else ""
                            
                            # Determine if this is a dev dependency
                            is_dev = section_name in ('dev', 'test', 'testing', 'development')
                            
                            dependencies.append(
                                Dependency(
                                    name=req.name,
                                    version=version,
                                    type=DependencyType.DEVELOPMENT if is_dev else DependencyType.RUNTIME,
                                    scope=DependencyScope.DIRECT,
                                    optional=True,  # Extras are optional
                                    source=str(file_path),
                                    group=section_name
                                )
                            )
                        except Exception as e:
                            logger.debug(f"Error parsing extra requirement '{pkg}': {e}")
                            # Simple fallback
                            parts = re.split(r'[<>=~!]', pkg, 1)
                            name = parts[0].strip()
                            version = pkg[len(name):].strip() if len(parts) > 1 else ""
                            
                            if name:
                                dependencies.append(
                                    Dependency(
                                        name=name,
                                        version=version,
                                        type=DependencyType.DEVELOPMENT if section_name in ('dev', 'test') else DependencyType.RUNTIME,
                                        scope=DependencyScope.DIRECT,
                                        optional=True,
                                        source=str(file_path),
                                        group=section_name
                                    )
                                )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="python",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing setup.py {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="python",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_pipfile(self, file_path: Path) -> ManifestInfo:
        """Parse a Python Pipfile."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # Process default packages (runtime dependencies)
            if "packages" in data:
                for name, version_spec in data["packages"].items():
                    # Handle different version specification formats
                    version = self._normalize_pipfile_version(version_spec)
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=DependencyType.RUNTIME,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            # Process dev packages
            if "dev-packages" in data:
                for name, version_spec in data["dev-packages"].items():
                    version = self._normalize_pipfile_version(version_spec)
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=DependencyType.DEVELOPMENT,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="python",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing Pipfile {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="python",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_poetry_lock(self, file_path: Path) -> ManifestInfo:
        """Parse a Python poetry.lock file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # Process packages
            if "package" in data:
                for package in data["package"]:
                    name = package.get("name", "")
                    version = package.get("version", "")
                    
                    # Determine dependency type and scope
                    category = package.get("category", "main")
                    optional = package.get("optional", False)
                    
                    dep_type = DependencyType.DEVELOPMENT if category == "dev" else DependencyType.RUNTIME
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=dep_type,
                            scope=DependencyScope.DIRECT,  # Simplified, would need pyproject.toml to distinguish
                            optional=optional,
                            source=str(file_path)
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="python",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing poetry.lock {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="python",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_pom_xml(self, file_path: Path) -> ManifestInfo:
        """Parse a Java pom.xml file."""
        dependencies = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle namespaces in Maven POM files
            ns = {'': 'http://maven.apache.org/POM/4.0.0'}
            
            # Extract dependencies
            for dep_elem in root.findall('.//dependencies/dependency', ns):
                group_id = dep_elem.find('groupId', ns)
                artifact_id = dep_elem.find('artifactId', ns)
                version = dep_elem.find('version', ns)
                scope_elem = dep_elem.find('scope', ns)
                optional_elem = dep_elem.find('optional', ns)
                
                if group_id is not None and artifact_id is not None:
                    # Create the dependency name as groupId:artifactId
                    name = f"{group_id.text}:{artifact_id.text}"
                    version_str = version.text if version is not None else ""
                    
                    # Determine scope and type
                    scope_value = scope_elem.text if scope_elem is not None else "compile"
                    
                    # Map Maven scope to our scope types
                    if scope_value in ('compile', 'runtime'):
                        dep_type = DependencyType.RUNTIME
                    elif scope_value in ('test', 'provided'):
                        dep_type = DependencyType.DEVELOPMENT
                    else:
                        dep_type = DependencyType.UNKNOWN
                    
                    # Determine if optional
                    is_optional = False
                    if optional_elem is not None:
                        is_optional = optional_elem.text.lower() == 'true'
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version_str,
                            type=dep_type,
                            scope=DependencyScope.DIRECT,
                            optional=is_optional,
                            source=str(file_path),
                            group=scope_value
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="maven",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing pom.xml {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="maven",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_gradle(self, file_path: Path) -> ManifestInfo:
        """
        Parse a Gradle build file.
        
        This is a simplified parser that uses regex to extract dependencies.
        For production use, a proper Gradle parser would be more robust.
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all dependency declarations
            # This is a simple regex to catch common patterns, not exhaustive
            dep_pattern = r'(?:implementation|api|compile|testImplementation|testCompile|runtimeOnly|developmentOnly)\s*[\(\s][\'"]([^\'"]*)[\'"]\)?'
            for match in re.finditer(dep_pattern, content):
                dep_spec = match.group(1)
                
                # Parse the dependency specification (group:name:version)
                parts = dep_spec.split(':')
                if len(parts) >= 2:
                    group_id = parts[0]
                    artifact_id = parts[1]
                    version = parts[2] if len(parts) > 2 else ""
                    
                    # Determine the dependency type based on the configuration
                    configuration = match.group(0).split('(')[0].strip()
                    if configuration in ('testImplementation', 'testCompile'):
                        dep_type = DependencyType.DEVELOPMENT
                    else:
                        dep_type = DependencyType.RUNTIME
                    
                    dependencies.append(
                        Dependency(
                            name=f"{group_id}:{artifact_id}",
                            version=version,
                            type=dep_type,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path),
                            group=configuration
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="gradle",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing build.gradle {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="gradle",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_gradle_kts(self, file_path: Path) -> ManifestInfo:
        """Parse a Kotlin-based Gradle build file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all dependency declarations in Kotlin DSL syntax
            dep_pattern = r'(?:implementation|api|compile|testImplementation|testCompile|runtimeOnly|developmentOnly)\s*\([\s\n]*["\'](.*?)["\']'
            for match in re.finditer(dep_pattern, content):
                dep_spec = match.group(1)
                
                # Parse the dependency specification (group:name:version)
                parts = dep_spec.split(':')
                if len(parts) >= 2:
                    group_id = parts[0]
                    artifact_id = parts[1]
                    version = parts[2] if len(parts) > 2 else ""
                    
                    # Determine the dependency type based on the configuration
                    configuration = match.group(0).split('(')[0].strip()
                    if configuration in ('testImplementation', 'testCompile'):
                        dep_type = DependencyType.DEVELOPMENT
                    else:
                        dep_type = DependencyType.RUNTIME
                    
                    dependencies.append(
                        Dependency(
                            name=f"{group_id}:{artifact_id}",
                            version=version,
                            type=dep_type,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path),
                            group=configuration
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="gradle",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing build.gradle.kts {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="gradle",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_gemfile(self, file_path: Path) -> ManifestInfo:
        """
        Parse a Ruby Gemfile.
        
        This is a simplified parser that uses regex to extract dependencies.
        For production use, a more robust parser would be better.
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Match gem declarations
            gem_pattern = r'gem\s+[\'"]([^\'"]+)[\'"](?:,\s*[\'"]([^\'"]+)[\'"])?'
            for match in re.finditer(gem_pattern, content):
                name = match.group(1)
                version = match.group(2) or ""
                
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        type=DependencyType.RUNTIME,  # Default to runtime
                        scope=DependencyScope.DIRECT,
                        optional=False,
                        source=str(file_path)
                    )
                )
            
            # Match group declarations
            group_pattern = r'group\s+:([a-z_]+)(?:,\s*:([a-z_]+))?\s+do(.*?)end'
            for match in re.finditer(group_pattern, content, re.DOTALL):
                # Extract group names
                groups = [g for g in [match.group(1), match.group(2)] if g]
                group_content = match.group(3)
                
                # Determine dependency type based on group
                is_dev = any(g in ('development', 'test') for g in groups)
                
                # Extract gems in this group
                for gem_match in re.finditer(gem_pattern, group_content):
                    name = gem_match.group(1)
                    version = gem_match.group(2) or ""
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=DependencyType.DEVELOPMENT if is_dev else DependencyType.RUNTIME,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path),
                            group=','.join(groups)
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="ruby",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing Gemfile {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="ruby",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_gemspec(self, file_path: Path) -> ManifestInfo:
        """
        Parse a Ruby gemspec file.
        
        This is a simplified parser that uses regex to extract dependencies.
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Match various dependency declarations in gemspec
            dep_patterns = [
                (r'add_dependency\s+[\'"]([^\'"]+)[\'"](?:,\s*[\'"]([^\'"]+)[\'"])?', DependencyType.RUNTIME),
                (r'add_runtime_dependency\s+[\'"]([^\'"]+)[\'"](?:,\s*[\'"]([^\'"]+)[\'"])?', DependencyType.RUNTIME),
                (r'add_development_dependency\s+[\'"]([^\'"]+)[\'"](?:,\s*[\'"]([^\'"]+)[\'"])?', DependencyType.DEVELOPMENT),
            ]
            
            for pattern, dep_type in dep_patterns:
                for match in re.finditer(pattern, content):
                    name = match.group(1)
                    version = match.group(2) or ""
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=dep_type,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="ruby",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing gemspec {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="ruby",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_csproj(self, file_path: Path) -> ManifestInfo:
        """Parse a .NET .csproj file."""
        dependencies = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Find all PackageReference elements
            for ref_elem in root.findall('.//PackageReference'):
                include = ref_elem.get('Include')
                version = ref_elem.get('Version')
                
                if include:
                    dependencies.append(
                        Dependency(
                            name=include,
                            version=version or "",
                            type=DependencyType.RUNTIME,  # Default to runtime
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            # Find project references
            for ref_elem in root.findall('.//ProjectReference'):
                include = ref_elem.get('Include')
                
                if include:
                    # Extract project name from path
                    project_name = os.path.basename(include)
                    if project_name.endswith('.csproj'):
                        project_name = project_name[:-7]
                    
                    dependencies.append(
                        Dependency(
                            name=project_name,
                            version="",
                            type=DependencyType.RUNTIME,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path),
                            is_project_reference=True
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="nuget",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing .csproj {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="nuget",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_vbproj(self, file_path: Path) -> ManifestInfo:
        """Parse a .NET .vbproj file."""
        # VB.NET project files use the same format as C# project files
        return self._parse_csproj(file_path)
    
    def _parse_packages_config(self, file_path: Path) -> ManifestInfo:
        """Parse a .NET packages.config file."""
        dependencies = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Find all package elements
            for pkg_elem in root.findall('.//package'):
                id_attr = pkg_elem.get('id')
                version = pkg_elem.get('version')
                
                if id_attr:
                    # Check if it's a development dependency
                    dev_dep = pkg_elem.get('developmentDependency', 'false').lower() == 'true'
                    
                    dependencies.append(
                        Dependency(
                            name=id_attr,
                            version=version or "",
                            type=DependencyType.DEVELOPMENT if dev_dep else DependencyType.RUNTIME,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="nuget",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing packages.config {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="nuget",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_go_mod(self, file_path: Path) -> ManifestInfo:
        """Parse a Go go.mod file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract module name
            module_match = re.search(r'module\s+(.+)', content)
            module_name = module_match.group(1).strip() if module_match else "unknown"
            
            # Extract require block
            require_block_match = re.search(r'require\s+\((.+?)\)', content, re.DOTALL)
            
            if require_block_match:
                require_block = require_block_match.group(1)
                # Extract individual requirements
                for line in require_block.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse "package version" format
                    parts = line.split()
                    if len(parts) >= 2:
                        package = parts[0]
                        version = parts[1]
                        
                        dependencies.append(
                            Dependency(
                                name=package,
                                version=version,
                                type=DependencyType.RUNTIME,
                                scope=DependencyScope.DIRECT,
                                optional=False,
                                source=str(file_path)
                            )
                        )
            
            # Also look for standalone require statements
            for match in re.finditer(r'require\s+([^\s]+)\s+([^\s]+)', content):
                package = match.group(1)
                version = match.group(2)
                
                # Skip if we already added this dependency
                if not any(d.name == package and d.version == version for d in dependencies):
                    dependencies.append(
                        Dependency(
                            name=package,
                            version=version,
                            type=DependencyType.RUNTIME,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="go",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing go.mod {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="go",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_go_sum(self, file_path: Path) -> ManifestInfo:
        """Parse a Go go.sum file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Track unique packages
            unique_deps = set()
            
            # Parse each line
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Format is: module_path version [checksum]
                parts = line.split()
                if len(parts) >= 2:
                    package = parts[0]
                    version = parts[1]
                    
                    # Skip go.mod directives
                    if package == "go.mod":
                        continue
                    
                    # Keep track to avoid duplicates
                    key = (package, version)
                    if key not in unique_deps:
                        unique_deps.add(key)
                        
                        dependencies.append(
                            Dependency(
                                name=package,
                                version=version,
                                type=DependencyType.RUNTIME,
                                scope=DependencyScope.TRANSITIVE,  # go.sum includes transitive deps
                                optional=False,
                                source=str(file_path)
                            )
                        )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="go",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing go.sum {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="go",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_cargo_toml(self, file_path: Path) -> ManifestInfo:
        """Parse a Rust Cargo.toml file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # Process dependencies
            if "dependencies" in data:
                for name, version_info in data["dependencies"].items():
                    # Version can be a string or a table
                    if isinstance(version_info, str):
                        version = version_info
                        optional = False
                    elif isinstance(version_info, dict):
                        version = version_info.get("version", "")
                        optional = version_info.get("optional", False)
                    else:
                        continue
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=DependencyType.RUNTIME,
                            scope=DependencyScope.DIRECT,
                            optional=optional,
                            source=str(file_path)
                        )
                    )
            
            # Process dev-dependencies
            if "dev-dependencies" in data:
                for name, version_info in data["dev-dependencies"].items():
                    if isinstance(version_info, str):
                        version = version_info
                    elif isinstance(version_info, dict):
                        version = version_info.get("version", "")
                    else:
                        continue
                    
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=DependencyType.DEVELOPMENT,
                            scope=DependencyScope.DIRECT,
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            # Process dependencies in target-specific tables
            if "target" in data:
                for target_spec, target_data in data["target"].items():
                    if "dependencies" in target_data:
                        for name, version_info in target_data["dependencies"].items():
                            if isinstance(version_info, str):
                                version = version_info
                                optional = False
                            elif isinstance(version_info, dict):
                                version = version_info.get("version", "")
                                optional = version_info.get("optional", False)
                            else:
                                continue
                            
                            dependencies.append(
                                Dependency(
                                    name=name,
                                    version=version,
                                    type=DependencyType.RUNTIME,
                                    scope=DependencyScope.DIRECT,
                                    optional=optional,
                                    source=str(file_path),
                                    group=f"target:{target_spec}"
                                )
                            )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="cargo",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing Cargo.toml {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="cargo",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _parse_cargo_lock(self, file_path: Path) -> ManifestInfo:
        """Parse a Rust Cargo.lock file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # Process package entries
            if "package" in data:
                for package in data["package"]:
                    name = package.get("name", "")
                    version = package.get("version", "")
                    
                    # All packages in Cargo.lock are considered direct or transitive
                    # We can't easily determine which without parsing Cargo.toml
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=DependencyType.RUNTIME,  # Assuming runtime by default
                            scope=DependencyScope.UNKNOWN,  # Can't easily determine
                            optional=False,
                            source=str(file_path)
                        )
                    )
            
            return ManifestInfo(
                path=str(file_path),
                ecosystem="cargo",
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.warning(f"Error parsing Cargo.lock {file_path}: {e}")
            return ManifestInfo(
                path=str(file_path),
                ecosystem="cargo",
                dependencies=[],
                parse_error=str(e)
            )
    
    def _normalize_npm_version(self, version_str: str) -> str:
        """Normalize NPM version strings to a consistent format."""
        if not version_str:
            return ""
        
        # Handle git URLs, local paths, etc.
        if any(prefix in version_str for prefix in ('git://', 'github:', 'http://', 'https://', 'file:', '/')):
            return version_str
        
        # Handle scoped packages
        if version_str.startswith('@'):
            return version_str
        
        # Handle version ranges
        # Just return as-is for now, could implement more sophisticated normalization
        return version_str
    
    def _normalize_pipfile_version(self, version_spec: Union[str, Dict]) -> str:
        """Normalize Pipfile version specifications."""
        if isinstance(version_spec, str):
            return version_spec
        
        if isinstance(version_spec, dict):
            # Check for various version specifiers
            if "version" in version_spec:
                return version_spec["version"]
            elif "ref" in version_spec:
                return f"ref:{version_spec['ref']}"
            elif "git" in version_spec:
                return f"git:{version_spec['git']}"
            
            # Fall back to returning the first key-value pair
            try:
                key, value = next(iter(version_spec.items()))
                return f"{key}:{value}"
            except StopIteration:
                return ""
        
        return ""