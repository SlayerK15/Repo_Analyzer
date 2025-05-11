"""
Build System and Package Manager Detector module for repository analysis.

This module identifies build systems and package managers used in a repository
by analyzing configuration files, dependency declarations, build scripts, and 
other artifacts that indicate how the project is built and its dependencies managed.
"""

import os
import re
import json
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
        
        # Build system and package manager usage indicators
        self.usage_indicators = {
            "Maven": [
                r"mvn\s+clean", r"mvn\s+compile", r"mvn\s+install", r"mvn\s+deploy", 
                r"./mvnw", r"mvn\s+package"
            ],
            "Gradle": [
                r"gradle\s+build", r"./gradlew", r"gradlew.bat", r"gradle\s+assemble",
                r"gradle\s+clean", r"gradle\s+test"
            ],
            "Make": [
                r"make\s+all", r"make\s+clean", r"make\s+install", r"make\s+test"
            ],
            "npm": [
                r"npm\s+install", r"npm\s+ci", r"npm\s+run", r"npm\s+start", 
                r"npm\s+test", r"npm\s+build"
            ],
            "Yarn": [
                r"yarn\s+install", r"yarn\s+add", r"yarn\s+run", r"yarn\s+start",
                r"yarn\s+test", r"yarn\s+build"
            ],
            "pip": [
                r"pip\s+install", r"pip\s+install\s+-r", r"python\s+-m\s+pip"
            ],
            "Cargo": [
                r"cargo\s+build", r"cargo\s+run", r"cargo\s+test"
            ],
            "Go Modules": [
                r"go\s+build", r"go\s+install", r"go\s+run", r"go\s+test"
            ]
        }
    
    def _apply_context_validation(self, build_matches, package_matches, files, files_content):
        """
        Apply context-aware validation to reduce false positives in build system and package manager detection.
        
        Args:
            build_matches: Dict of build system matches and their counts
            package_matches: Dict of package manager matches and their counts
            files: List of file paths
            files_content: Dict mapping file paths to their content
        """
        # Special handling for mixed repositories: look through all subdirectories
        # and see if there are separate frontend and backend directories
        has_frontend_backend_split = False
        frontend_dir = None
        backend_dir = None
        
        # Check for common frontend/backend directory patterns
        common_structures = [
            ("frontend", "backend"),
            ("client", "server"),
            ("ui", "api"),
            ("app", "api"),
            ("web", "api")
        ]
        
        # Get first-level directories
        first_level_dirs = set()
        for file_path in files:
            parts = file_path.split(os.sep)
            if len(parts) > 1:
                first_level_dirs.add(parts[0])
        
        # Check if any common frontend/backend pattern exists
        for front, back in common_structures:
            if front in first_level_dirs and back in first_level_dirs:
                has_frontend_backend_split = True
                frontend_dir = front
                backend_dir = back
                break
        
        # If we have a frontend/backend split, adjust package manager detections
        if has_frontend_backend_split:
            # Check for package.json in frontend directory
            frontend_has_npm = any(f.startswith(frontend_dir) and os.path.basename(f) == "package.json" for f in files)
            
            # Check for requirements.txt in backend directory
            backend_has_pip = any(f.startswith(backend_dir) and os.path.basename(f) == "requirements.txt" for f in files)
            
            # If frontend has npm-related files, boost npm confidence
            if frontend_has_npm:
                package_matches["npm"] = package_matches.get("npm", 0) + 30
            
            # If backend has pip-related files, boost pip confidence
            if backend_has_pip:
                package_matches["pip"] = package_matches.get("pip", 0) + 30
        
        # Check for actual usage of build systems and package managers
        for system, patterns in self.usage_indicators.items():
            # Look in shell scripts, GitHub workflows, and other CI configurations
            potential_files = []
            for file_path in files:
                if (file_path.endswith('.sh') or 
                    '.github/workflows/' in file_path or 
                    file_path.endswith('.yml') or 
                    file_path.endswith('.yaml') or
                    'jenkins' in file_path.lower() or
                    'travis' in file_path.lower() or
                    'gitlab-ci' in file_path.lower() or
                    'dockerfile' in file_path.lower()):
                    potential_files.append(file_path)
            
            found_usage = False
            for file_path in potential_files:
                if file_path in files_content:
                    content = files_content[file_path]
                    for pattern in patterns:
                        if re.search(pattern, content):
                            found_usage = True
                            if system in build_matches:
                                build_matches[system] += 10  # Strong evidence of usage
                            if system in package_matches:
                                package_matches[system] += 10
                            break
                    if found_usage:
                        break
        
        # Validate npm by checking if package.json exists and has content
        if "npm" in package_matches or any(file.endswith("package.json") for file in files):
            has_package_json = False
            has_dependencies = False
            
            for file_path, content in files_content.items():
                if file_path.endswith('package.json'):
                    has_package_json = True
                    try:
                        package_data = json.loads(content)
                        if ('dependencies' in package_data or 'devDependencies' in package_data):
                            has_dependencies = True
                    except:
                        pass
                    break
            
            if has_package_json:
                # Even if just the file exists, boost npm confidence
                package_matches["npm"] = package_matches.get("npm", 0) + 20
                
                # If it has dependencies, boost further
                if has_dependencies:
                    package_matches["npm"] = package_matches.get("npm", 0) + 10
        
        # Validate pip by checking if requirements.txt or setup.py has actual dependencies
        if "pip" in package_matches or any(file.endswith(("requirements.txt", "setup.py")) for file in files):
            has_valid_pip_file = False
            
            for file_path, content in files_content.items():
                if file_path.endswith('requirements.txt') or file_path.endswith('setup.py'):
                    has_valid_pip_file = True
                    
                    # Check if requirements.txt has package names
                    if file_path.endswith('requirements.txt'):
                        # Requirements.txt should have at least one line with a package name
                        lines = content.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                package_matches["pip"] = package_matches.get("pip", 0) + 10
                                break
                    
                    # Check if setup.py has install_requires
                    elif file_path.endswith('setup.py'):
                        if 'install_requires' in content and '[' in content and ']' in content:
                            package_matches["pip"] = package_matches.get("pip", 0) + 10
            
            if has_valid_pip_file:
                # Even if just the file exists, boost pip confidence
                package_matches["pip"] = package_matches.get("pip", 0) + 20
        
        # Validate Maven by checking if pom.xml has proper Maven structure
        if "Maven" in build_matches or "Maven" in package_matches:
            has_valid_pom = False
            
            for file_path, content in files_content.items():
                if file_path.endswith('pom.xml'):
                    if ('<project' in content and 
                        ('<groupId>' in content or '<parent>' in content) and 
                        '<artifactId>' in content):
                        has_valid_pom = True
                        break
            
            if not has_valid_pom:
                if "Maven" in build_matches:
                    build_matches["Maven"] = build_matches["Maven"] // 2
                if "Maven" in package_matches:
                    package_matches["Maven"] = package_matches["Maven"] // 2
        
        # Validate Gradle by checking if build.gradle has repositories and dependencies
        if "Gradle" in build_matches or "Gradle" in package_matches:
            has_valid_gradle = False
            
            for file_path, content in files_content.items():
                if file_path.endswith('build.gradle') or file_path.endswith('build.gradle.kts'):
                    if ('repositories' in content and 
                        'dependencies' in content):
                        has_valid_gradle = True
                        break
            
            if not has_valid_gradle:
                if "Gradle" in build_matches:
                    build_matches["Gradle"] = build_matches["Gradle"] // 2
                if "Gradle" in package_matches:
                    package_matches["Gradle"] = package_matches["Gradle"] // 2
        
        # Validate Webpack by checking webpack.config.js
        if "Webpack" in build_matches:
            has_valid_webpack = False
            
            for file_path, content in files_content.items():
                if 'webpack' in file_path.lower() and file_path.endswith('.js'):
                    if ('module.exports' in content and 
                        ('entry' in content or 'output' in content or 'module' in content)):
                        has_valid_webpack = True
                        break
            
            if not has_valid_webpack:
                build_matches["Webpack"] = build_matches["Webpack"] // 2
        
        # Lower threshold for npm in mixed repositories
        # If both pip and npm have some evidence but below threshold, boost both
        if "pip" in package_matches and package_matches.get("npm", 0) > 0:
            # This is likely a mixed repository, so keep npm even with lower confidence
            package_matches["npm"] = max(package_matches["npm"], 10)
    
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
            
            # Special case for package.json to detect npm
            if filename == "package.json":
                package_matches["npm"] += 20  # Higher weight for package.json
                package_evidence["npm"].append(f"Found file: {filename}")
            
            # Special case for requirements.txt to detect pip
            if filename == "requirements.txt":
                package_matches["pip"] += 20  # Higher weight for requirements.txt
                package_evidence["pip"].append(f"Found file: {filename}")
        
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
                            match_text = str(matches[0]) if matches else pattern
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
                            match_text = str(matches[0]) if matches else pattern
                        package_evidence[manager].append(f"Pattern match: {match_text}")
        
        # Step 3: Apply context validation to reduce false positives
        self._apply_context_validation(build_matches, package_matches, files, files_content)
        
        # Step 4: Calculate confidence scores for build systems
        build_systems = {}
        
        if build_matches:
            # Find maximum number of matches for normalization
            max_build_matches = max(build_matches.values()) if build_matches else 1
            
            for system, matches in build_matches.items():
                # Calculate confidence score (0-100)
                confidence = min(100, (matches / max_build_matches) * 100)
                
                # Only include build systems with reasonable confidence
                if confidence >= 35:
                    # Keep only unique evidence and limit to 5 examples
                    unique_evidence = list(set(build_evidence[system]))[:5]
                    
                    build_systems[system] = {
                        "matches": matches,
                        "confidence": round(confidence, 2),
                        "evidence": unique_evidence
                    }
        
        # Step 5: Calculate confidence scores for package managers
        package_managers = {}
        
        if package_matches:
            # Find maximum number of matches for normalization
            max_package_matches = max(package_matches.values()) if package_matches else 1
            
            for manager, matches in package_matches.items():
                # Calculate confidence score (0-100)
                confidence = min(100, (matches / max_package_matches) * 100)
                
                # Lower threshold for npm in mixed repositories
                threshold = 25 if manager == "npm" else 35
                
                # Only include package managers with reasonable confidence
                if confidence >= threshold:
                    # Keep only unique evidence and limit to 5 examples
                    unique_evidence = list(set(package_evidence[manager]))[:5]
                    
                    package_managers[manager] = {
                        "matches": matches,
                        "confidence": round(confidence, 2),
                        "evidence": unique_evidence
                    }
        
        # Step 6: Handle cross-listed technologies (e.g., Maven is both a build system and package manager)
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