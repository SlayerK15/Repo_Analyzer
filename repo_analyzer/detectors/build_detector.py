"""
Build System and Package Manager Detector module for repository analysis.

This module identifies build systems and package managers used in a repository
by analyzing configuration files, dependency declarations, build scripts, and 
other artifacts that indicate how the project is built and its dependencies managed.
"""

import os
import re
from collections import defaultdict
from typing import Dict, List, Any, Tuple

class BuildDetector:
    """
    Detector for build systems and package managers used in a repository.
    
    This class identifies build tools, dependency management systems, and
    package managers by examining specific files, directory structures,
    and configuration patterns within the codebase.
    """
    
    def __init__(self):
        """Initialize the Build System and Package Manager Detector."""
        # Build system detection files and patterns
        self.build_system_files = {
            "Maven": ["pom.xml"],
            "Gradle": ["build.gradle", "build.gradle.kts", "settings.gradle", "gradle.properties", "gradlew"],
            "Ant": ["build.xml"],
            "Make": ["Makefile", "makefile", "GNUmakefile"],
            "CMake": ["CMakeLists.txt", "cmake"],
            "Bazel": ["BUILD", "WORKSPACE", ".bazelrc"],
            "MSBuild": [".csproj", ".vbproj", ".vcxproj", ".sln"],
            "Webpack": ["webpack.config.js", "webpack.config.ts", "webpack.common.js"],
            "Vite": ["vite.config.js", "vite.config.ts"],
            "Rollup": ["rollup.config.js", "rollup.config.ts"],
            "Parcel": [".parcelrc", "parcel.config.js"],
            "Gulp": ["gulpfile.js", "gulpfile.ts"],
            "Grunt": ["Gruntfile.js"],
            "Rake": ["Rakefile"],
            "SCons": ["SConstruct", "SConscript"],
            "Buck": ["BUCK", ".buckconfig"],
            "Pants": ["pants", "pants.ini"],
            "setuptools": ["setup.py"],
            "Meson": ["meson.build"],
            "Ninja": ["build.ninja"],
            "esbuild": ["esbuild.config.js"],
            "swc": [".swcrc"],
            "Babel": [".babelrc", "babel.config.js"],
            "tsc": ["tsconfig.json"],
            "Rome": ["rome.json"],
            "Snowpack": ["snowpack.config.js", "snowpack.config.mjs"],
        }
        
        # Package manager detection files and patterns
        self.package_manager_files = {
            "npm": ["package.json", "package-lock.json", "node_modules/"],
            "Yarn": ["yarn.lock", ".yarnrc", ".yarnrc.yml"],
            "pnpm": ["pnpm-lock.yaml", ".pnpmfile.cjs"],
            "Bower": ["bower.json", ".bowerrc"],
            "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
            "Pipenv": ["Pipfile", "Pipfile.lock"],
            "Poetry": ["pyproject.toml", "poetry.lock"],
            "Conda": ["environment.yml", "conda-env.yml", "meta.yaml"],
            "RubyGems": ["Gemfile", "Gemfile.lock", ".gemspec"],
            "Bundler": ["Gemfile", "Gemfile.lock"],
            "CocoaPods": ["Podfile", "Podfile.lock", ".podspec"],
            "Carthage": ["Cartfile", "Cartfile.resolved"],
            "Composer": ["composer.json", "composer.lock"],
            "NuGet": ["packages.config", ".nuspec", ".nupkg", "paket.dependencies"],
            "Cargo": ["Cargo.toml", "Cargo.lock"],
            "Go Modules": ["go.mod", "go.sum"],
            "Dep": ["Gopkg.toml", "Gopkg.lock"],
            "Maven": ["pom.xml"],
            "Gradle": ["build.gradle", "build.gradle.kts"],
            "Ivy": ["ivy.xml"],
            "Leiningen": ["project.clj"],
            "sbt": ["build.sbt"],
            "rebar": ["rebar.config"],
            "hex": ["mix.exs", "mix.lock"],
            "dpkg": ["debian/"],
            "RPM": ["SPECS/", ".spec"],
            "Pacman": ["PKGBUILD"],
            "Swift Package Manager": ["Package.swift"],
            "vcpkg": ["vcpkg.json"],
            "Conan": ["conanfile.txt", "conanfile.py"],
        }
        
        # Additional content patterns for build systems
        self.build_system_patterns = {
            "Maven": [
                r"<project\s+xmlns=\"http://maven\.apache\.org/POM",
                r"<groupId>.*?</groupId>", 
                r"<artifactId>.*?</artifactId>",
                r"mvn\s+(?:clean|compile|package|install|deploy)"
            ],
            "Gradle": [
                r"apply\s+plugin:", r"plugins\s*{", r"repositories\s*{",
                r"dependencies\s*{", r"implementation\s+[\'\"]",
                r"gradle\s+(?:clean|build|assemble|check)"
            ],
            "MSBuild": [
                r"<Project\s+Sdk=\"Microsoft\.NET\.Sdk", r"<PropertyGroup>",
                r"<TargetFramework>", r"<PackageReference\s+"
            ],
            "Webpack": [
                r"module\.exports\s*=", r"const\s+webpack\s*=\s*require",
                r"entry\s*:", r"output\s*:", r"module\s*:\s*{\s*rules\s*:"
            ],
            "setuptools": [
                r"from\s+setuptools\s+import", r"setup\(", r"packages\s*=",
                r"install_requires\s*="
            ],
            "tsc": [
                r"\"compilerOptions\"\s*:", r"\"target\"\s*:", r"\"module\"\s*:",
                r"\"outDir\"\s*:", r"\"rootDir\"\s*:"
            ],
            "Babel": [
                r"\"presets\"\s*:", r"\"plugins\"\s*:", r"babel-preset-",
                r"@babel/preset-", r"@babel/plugin-"
            ]
        }
        
        # Additional content patterns for package managers
        self.package_manager_patterns = {
            "npm": [
                r"\"dependencies\"\s*:", r"\"devDependencies\"\s*:",
                r"\"scripts\"\s*:", r"npm\s+(?:install|ci|run)"
            ],
            "Yarn": [
                r"yarn\s+(?:add|remove|upgrade|install)",
                r"\"resolutions\"\s*:"
            ],
            "pip": [
                r"pip\s+(?:install|freeze|download)",
                r"from\s+\w+\s+import", r"import\s+\w+"
            ],
            "Cargo": [
                r"\[dependencies\]", r"\[dev-dependencies\]",
                r"cargo\s+(?:build|run|test|check)"
            ],
            "Go Modules": [
                r"go\s+(?:build|run|test|mod)", r"import\s+\(", r"require\s+\("
            ],
            "Composer": [
                r"\"require\"\s*:", r"\"require-dev\"\s*:",
                r"composer\s+(?:install|update|require)"
            ]
        }
    
    def detect(self, files: List[str], files_content: Dict[str, str]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        Detect build systems and package managers used in the repository.
        
        This method examines file names, paths, and contents to identify
        build systems and package managers used in the project.
        
        Args:
            files: List of file paths in the repository
            files_content: Dict mapping file paths to their content
            
        Returns:
            Tuple containing:
                - Dict mapping build system names to confidence data
                - Dict mapping package manager names to confidence data
        """
        # Track matches for build systems and package managers
        build_matches = defaultdict(int)
        package_matches = defaultdict(int)
        
        build_evidence = defaultdict(list)
        package_evidence = defaultdict(list)
        
        # Step 1: Check for build system files
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # Check for build system files
            for system, filenames in self.build_system_files.items():
                if filename in filenames:
                    build_matches[system] += 10  # High weight for exact filename match
                    build_evidence[system].append(f"Found file: {filename}")
                elif any(filename.endswith(f) for f in filenames):
                    build_matches[system] += 8  # Slightly lower weight for extension match
                    build_evidence[system].append(f"Found file: {filename}")
                elif any(pattern in file_path for pattern in filenames):
                    build_matches[system] += 5  # Lower weight for path match
                    build_evidence[system].append(f"Found pattern in path: {file_path}")
            
            # Check for package manager files
            for manager, filenames in self.package_manager_files.items():
                if filename in filenames:
                    package_matches[manager] += 10  # High weight for exact filename match
                    package_evidence[manager].append(f"Found file: {filename}")
                elif any(filename.endswith(f) for f in filenames):
                    package_matches[manager] += 8  # Slightly lower weight for extension match
                    package_evidence[manager].append(f"Found file: {filename}")
                elif any(pattern in file_path for pattern in filenames):
                    package_matches[manager] += 5  # Lower weight for path match
                    package_evidence[manager].append(f"Found pattern in path: {file_path}")
        
        # Step 2: Check file content for build system and package manager patterns
        for file_path, content in files_content.items():
            # Skip checking large files for performance reasons
            if len(content) > 500000:  # Skip files larger than 500KB
                continue
                
            # Check for build system patterns
            for system, patterns in self.build_system_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # Weight based on number of matches
                        match_count = len(matches)
                        build_matches[system] += match_count * 2
                        
                        # Add first match as evidence
                        if matches and len(matches[0]) > 60:  # Truncate long matches
                            match_text = matches[0][:57] + "..."
                        else:
                            match_text = matches[0]
                        build_evidence[system].append(f"Pattern match: {match_text}")
            
            # Check for package manager patterns
            for manager, patterns in self.package_manager_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # Weight based on number of matches
                        match_count = len(matches)
                        package_matches[manager] += match_count * 2
                        
                        # Add first match as evidence
                        if matches and len(matches[0]) > 60:  # Truncate long matches
                            match_text = matches[0][:57] + "..."
                        else:
                            match_text = matches[0]
                        package_evidence[manager].append(f"Pattern match: {match_text}")
        
        # Step 3: Calculate confidence scores for build systems
        build_systems = {}
        
        if build_matches:
            # Find maximum number of matches for normalization
            max_build_matches = max(build_matches.values())
            
            for system, matches in build_matches.items():
                # Calculate confidence score (0-100)
                confidence = min(100, (matches / max_build_matches) * 100)
                
                # Only include build systems with reasonable confidence
                if confidence >= 15:
                    # Keep only unique evidence and limit to 5 examples
                    unique_evidence = list(set(build_evidence[system]))[:5]
                    
                    build_systems[system] = {
                        "matches": matches,
                        "confidence": round(confidence, 2),
                        "evidence": unique_evidence
                    }
        
        # Step 4: Calculate confidence scores for package managers
        package_managers = {}
        
        if package_matches:
            # Find maximum number of matches for normalization
            max_package_matches = max(package_matches.values())
            
            for manager, matches in package_matches.items():
                # Calculate confidence score (0-100)
                confidence = min(100, (matches / max_package_matches) * 100)
                
                # Only include package managers with reasonable confidence
                if confidence >= 15:
                    # Keep only unique evidence and limit to 5 examples
                    unique_evidence = list(set(package_evidence[manager]))[:5]
                    
                    package_managers[manager] = {
                        "matches": matches,
                        "confidence": round(confidence, 2),
                        "evidence": unique_evidence
                    }
        
        # Step 5: Handle cross-listed technologies (e.g., Maven is both a build system and package manager)
        # Ensure consistency of confidence scores for technologies that appear in both categories
        for tech in set(build_systems.keys()).intersection(set(package_managers.keys())):
            build_conf = build_systems[tech]["confidence"]
            pkg_conf = package_managers[tech]["confidence"]
            
            # If confidence scores differ significantly, adjust the lower one
            if abs(build_conf - pkg_conf) > 20:
                # Use the higher confidence score as the reference
                if build_conf > pkg_conf:
                    # Adjust package manager confidence (slightly lower than build confidence)
                    package_managers[tech]["confidence"] = max(build_conf - 10, pkg_conf)
                else:
                    # Adjust build system confidence (slightly lower than package confidence)
                    build_systems[tech]["confidence"] = max(pkg_conf - 10, build_conf)
        
        return build_systems, package_managers