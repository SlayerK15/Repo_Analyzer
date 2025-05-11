"""
Testing Framework Detector module for repository analysis.

This module identifies testing frameworks, libraries, and patterns used in a 
repository by analyzing test directories, file naming patterns, and code content
related to testing.
"""

import os
import re
from collections import defaultdict
from typing import Dict, List, Any

class TestingDetector:
    """
    Detector for testing frameworks and patterns used in a repository.
    
    This class identifies unit testing, integration testing, end-to-end testing,
    and other testing tools by examining test files, directories, and code patterns.
    """
    
    def __init__(self):
        """Initialize the Testing Framework Detector with detection patterns."""
        # Test directory patterns
        self.test_directories = [
            "test/", "tests/", "spec/", "specs/", "__tests__/",
            "unit/", "unit-tests/", "integration/", "integration-tests/",
            "e2e/", "e2e-tests/", "cypress/", "playwright/",
            "Test/", "Tests/", "UnitTests/", "IntegrationTests/"
        ]
        
        # Test file patterns
        self.test_file_patterns = {
            "General": [
                r"test_.*\.py", r".*test\.py", r".*_test\.go", r".*_test\.rb",
                r".*Test\.java", r".*Tests\.cs", r".*\.spec\.js", r".*\.spec\.ts",
                r".*\.test\.js", r".*\.test\.ts", r".*_test\.php", r".*Test\.php"
            ],
            "JUnit": [
                r".*Test\.java", r".*Tests\.java", r"Test.*\.java"
            ],
            "PyTest": [
                r"test_.*\.py", r".*test\.py", r"conftest\.py"
            ],
            "unittest": [
                r"test_.*\.py", r".*_test\.py", r".*Test\.py"
            ],
            "RSpec": [
                r".*_spec\.rb", r"spec_.*\.rb"
            ],
            "Mocha": [
                r".*\.spec\.js", r".*\.test\.js", r".*_test\.js"
            ],
            "Jest": [
                r".*\.test\.js", r".*\.test\.jsx", r".*\.test\.ts", r".*\.test\.tsx",
                r".*\.spec\.js", r".*\.spec\.jsx", r".*\.spec\.ts", r".*\.spec\.tsx"
            ],
            "PHPUnit": [
                r".*Test\.php", r"Test.*\.php"
            ],
            "Xunit": [
                r".*Test\.cs", r".*Tests\.cs", r"Test.*\.cs"
            ],
            "NUnit": [
                r".*Test\.cs", r".*Tests\.cs", r"Test.*\.cs"
            ],
        }
        
        # Testing framework configuration files
        self.config_files = {
            "Jest": ["jest.config.js", "jest.config.ts", "jest.setup.js", "jest.json"],
            "Mocha": ["mocha.opts", ".mocharc.js", ".mocharc.json", ".mocharc.yml"],
            "PyTest": ["pytest.ini", "conftest.py", "tox.ini", "pyproject.toml"],
            "unittest": ["unittest.cfg"],
            "JUnit": ["junit.xml", "pom.xml"],
            "TestNG": ["testng.xml"],
            "Karma": ["karma.conf.js", "karma.conf.ts"],
            "Jasmine": ["jasmine.json", "spec/support/jasmine.json"],
            "Cypress": ["cypress.json", "cypress.config.js", "cypress.config.ts"],
            "Playwright": ["playwright.config.js", "playwright.config.ts"],
            "Selenium": ["selenium.yaml", "selenium.json", "webdriver.js"],
            "PHPUnit": ["phpunit.xml", "phpunit.xml.dist"],
            "Xunit": ["xunit.runner.json"],
            "NUnit": ["nunit.config", "nunit3-console.exe"],
            "Vitest": ["vitest.config.js", "vitest.config.ts"],
            "AVA": ["ava.config.js", "ava.config.cjs"],
            "Tape": ["tape.js"],
            "QUnit": ["qunit.html", "qunit.js"],
            "Nightwatch": ["nightwatch.conf.js", "nightwatch.json"],
            "Protractor": ["protractor.conf.js", "protractor.conf.ts"],
            "TestCafe": ["testcafe.js", ".testcaferc.json"],
            "Artillery": ["artillery.yml", "artillery.json"],
            "K6": ["k6.js", "k6.json"],
            "Gatling": ["gatling.conf", "gatling.scala"],
            "Robot Framework": ["robot.txt", "robot.robot"],
            "Cucumber": ["cucumber.js", "cucumber.yml", ".feature"],
            "TestCafe": ["testcafe.js", ".testcaferc.json"],
            "JMeter": [".jmx"],
            "SoapUI": [".xml", "soapui-project.xml"],
            "Postman": ["postman_collection.json"],
            "WebdriverIO": ["wdio.conf.js", "wdio.conf.ts"],
        }
        
        # Testing framework import/require patterns
        self.import_patterns = {
            "Jest": [
                r"import\s+.*\bfrom\s+['\"]jest['\"]",
                r"require\(['\"]jest['\"]\)",
                r"import\s+.*\bfrom\s+['\"]@jest/['\"]",
                r"jest\..*"
            ],
            "React Testing Library": [
                r"import\s+.*\bfrom\s+['\"]@testing-library/react['\"]",
                r"require\(['\"]@testing-library/react['\"]\)",
                r"render\(", r"screen\.", r"fireEvent\."
            ],
            "Vue Testing Library": [
                r"import\s+.*\bfrom\s+['\"]@testing-library/vue['\"]",
                r"require\(['\"]@testing-library/vue['\"]\)",
            ],
            "Angular Testing": [
                r"import\s+.*\bfrom\s+['\"]@angular/testing['\"]",
                r"TestBed", r"ComponentFixture"
            ],
            "PyTest": [
                r"import\s+pytest", r"from\s+pytest", r"@pytest\.", r"pytest\."
            ],
            "unittest": [
                r"import\s+unittest", r"from\s+unittest", r"TestCase"
            ],
            "Mocha": [
                r"import\s+.*\bfrom\s+['\"]mocha['\"]", r"require\(['\"]mocha['\"]\)",
                r"describe\(", r"it\(", r"before\(", r"after\("
            ],
            "Chai": [
                r"import\s+.*\bfrom\s+['\"]chai['\"]", r"require\(['\"]chai['\"]\)",
                r"expect\(", r"should\(", r"assert\."
            ],
            "Sinon": [
                r"import\s+.*\bfrom\s+['\"]sinon['\"]", r"require\(['\"]sinon['\"]\)",
                r"sinon\.", r"stub\(", r"spy\(", r"mock\("
            ],
            "JUnit": [
                r"import\s+org\.junit", r"@Test", r"Assert\."
            ],
            "TestNG": [
                r"import\s+org\.testng", r"@Test", r"@BeforeSuite", r"@AfterSuite"
            ],
            "Jasmine": [
                r"import\s+.*\bfrom\s+['\"]jasmine['\"]",
                r"require\(['\"]jasmine['\"]\)",
                r"describe\(", r"it\(", r"expect\("
            ],
            "Cypress": [
                r"import\s+.*\bfrom\s+['\"]cypress['\"]",
                r"require\(['\"]cypress['\"]\)",
                r"cy\.", r"describe\(", r"it\("
            ],
            "Playwright": [
                r"import\s+.*\bfrom\s+['\"]@playwright/test['\"]",
                r"require\(['\"]@playwright/test['\"]\)",
                r"test\(", r"expect\(", r"page\."
            ],
            "Selenium": [
                r"import\s+.*\bfrom\s+['\"]selenium['\"]",
                r"require\(['\"]selenium-webdriver['\"]\)",
                r"webdriver\.", r"By\.", r"driver\."
            ],
            "Enzyme": [
                r"import\s+.*\bfrom\s+['\"]enzyme['\"]",
                r"require\(['\"]enzyme['\"]\)",
                r"shallow\(", r"mount\(", r"render\("
            ],
            "Vitest": [
                r"import\s+.*\bfrom\s+['\"]vitest['\"]",
                r"import\s+{.*}\s+from\s+['\"]vitest['\"]",
                r"vi\.", r"test\(", r"describe\("
            ],
            "RSpec": [
                r"require\s+['\"]rspec['\"]\b", r"describe\s+", r"it\s+", r"expect\("
            ],
            "PHPUnit": [
                r"use\s+PHPUnit", r"extends\s+TestCase", r"@test", r"->assert"
            ],
        }
        
        # Testing framework code patterns
        self.code_patterns = {
            "Jest": [
                r"test\(\s*['\"].*['\"]\s*,\s*(?:async)?\s*(?:\([^\)]*\))?\s*=>\s*{",
                r"describe\(\s*['\"].*['\"]\s*,\s*(?:async)?\s*(?:\([^\)]*\))?\s*=>\s*{",
                r"expect\(.*\)\.to", r"beforeEach\(", r"afterEach\("
            ],
            "Mocha": [
                r"describe\(\s*['\"].*['\"]\s*,\s*function\s*\(\s*\)\s*{",
                r"it\(\s*['\"].*['\"]\s*,\s*function\s*\(\s*\)\s*{",
                r"before\(\s*function\s*\(\s*\)\s*{", r"after\(\s*function\s*\(\s*\)\s*{"
            ],
            "Chai": [
                r"expect\(.*\)\.to\..*", r"should\..*", r"assert\..*"
            ],
            "PyTest": [
                r"def\s+test_.*\(.*\):", r"@pytest\..*", r"assert\s+.*"
            ],
            "unittest": [
                r"class\s+.*\(.*TestCase.*\):", r"self\.assert.*\(", r"def\s+test_.*\(self.*\):"
            ],
            "JUnit": [
                r"@Test", r"public\s+void\s+test.*\(", r"Assert\.", r"@Before", r"@After"
            ],
            "TestNG": [
                r"@Test", r"@BeforeMethod", r"@AfterMethod", r"@DataProvider"
            ],
            "RSpec": [
                r"describe\s+(['\"]\w+['\"]|\w+)\s+do", r"it\s+['\"].*['\"]\s+do", 
                r"context\s+['\"].*['\"]\s+do", r"expect\(.*\)\.to"
            ],
            "Jasmine": [
                r"describe\(\s*['\"].*['\"]\s*,\s*function\s*\(\s*\)\s*{",
                r"it\(\s*['\"].*['\"]\s*,\s*function\s*\(\s*\)\s*{",
                r"beforeEach\(function\s*\(\s*\)\s*{", r"afterEach\(function\s*\(\s*\)\s*{"
            ],
            "PHPUnit": [
                r"public\s+function\s+test.*\(", r"\$this->assert.*\(", r"@test"
            ],
            "Xunit": [
                r"\[Fact\]", r"\[Theory\]", r"public\s+void\s+.*\(", r"Assert\."
            ],
            "NUnit": [
                r"\[Test\]", r"\[TestCase\]", r"\[TestFixture\]", r"Assert\."
            ],
            "Cypress": [
                r"cy\.\w+\(", r"cy\.visit\(", r"cy\.get\(", r"cy\.contains\("
            ],
            "Playwright": [
                r"test\(\s*['\"].*['\"]\s*,\s*async\s*\(\s*[{]*\s*page\s*[,}]*\s*\)\s*=>\s*{",
                r"await\s+page\.\w+\(", r"expect\(.*\)\.toHaveText"
            ],
            "Selenium": [
                r"driver\.\w+\(", r"driver\.findElement\(", r"By\.\w+\("
            ],
            "Robot Framework": [
                r"\*\*\* Test Cases \*\*\*", r"\*\*\* Settings \*\*\*", r"\*\*\* Variables \*\*\*"
            ],
            "Cucumber": [
                r"Feature\s*:", r"Scenario\s*:", r"Given\s+", r"When\s+", r"Then\s+"
            ],
        }
        
        # Package.json dependencies
        self.npm_dependencies = {
            "Jest": ["jest", "@jest/core", "jest-cli"],
            "Mocha": ["mocha"],
            "Chai": ["chai"],
            "Sinon": ["sinon"],
            "Jasmine": ["jasmine"],
            "Karma": ["karma"],
            "Enzyme": ["enzyme", "enzyme-adapter-react-16"],
            "React Testing Library": ["@testing-library/react"],
            "Vue Testing Library": ["@testing-library/vue"],
            "Angular Testing": ["@angular/testing"],
            "Cypress": ["cypress"],
            "Playwright": ["@playwright/test", "playwright"],
            "Selenium": ["selenium-webdriver"],
            "Puppeteer": ["puppeteer"],
            "WebdriverIO": ["webdriverio", "@wdio/cli"],
            "Nightwatch": ["nightwatch"],
            "TestCafe": ["testcafe"],
            "Protractor": ["protractor"],
            "Vitest": ["vitest"],
            "AVA": ["ava"],
            "Tape": ["tape"],
            "QUnit": ["qunit"],
            "Storybook": ["@storybook/react", "@storybook/vue", "@storybook/angular"],
        }
        
        # Requirements.txt, Pipfile, and requirements.in dependencies
        self.python_dependencies = {
            "PyTest": ["pytest", "pytest-cov", "pytest-django", "pytest-xdist"],
            "unittest": ["unittest2"],
            "Nose": ["nose", "nose2"],
            "Robot Framework": ["robotframework"],
            "Selenium": ["selenium"],
            "Behave": ["behave"],
            "Lettuce": ["lettuce"],
            "Cucumber": ["cucumber"],
            "PyTest-BDD": ["pytest-bdd"],
            "Hypothesis": ["hypothesis"],
            "PyHamcrest": ["pyhamcrest"],
            "Expects": ["expects"],
            "Playwright": ["playwright"],
            "Locust": ["locust"],
            "Tavern": ["tavern"],
            "PyTest-API": ["pytest-api"],
            "Mock": ["mock"],
            "Factory Boy": ["factory_boy", "factory-boy"],
            "Faker": ["faker"],
        }
        
        # Gemfile dependencies
        self.ruby_dependencies = {
            "RSpec": ["rspec", "rspec-rails"],
            "MiniTest": ["minitest"],
            "Cucumber": ["cucumber", "cucumber-rails"],
            "Capybara": ["capybara"],
            "Factory Bot": ["factory_bot", "factory_bot_rails"],
            "Faker": ["faker"],
            "Shoulda": ["shoulda", "shoulda-matchers"],
            "SimpleCov": ["simplecov"],
            "WebMock": ["webmock"],
            "VCR": ["vcr"],
        }
    
    # NEW METHOD: Apply context validation to reduce false positives
    def _apply_context_validation(self, testing_matches, testing_categories, files_content):
        """Apply context-aware validation to reduce false positives in testing framework detection."""
        
        # Check for primary language context
        has_python = False
        has_javascript = False
        has_ruby = False
        
        for file_path in files_content:
            if file_path.endswith('.py'):
                has_python = True
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                has_javascript = True
            elif file_path.endswith('.rb'):
                has_ruby = True
        
        # For React Testing Library and Enzyme (JavaScript testing libraries)
        if not has_javascript:
            # If the project doesn't have JavaScript files, these shouldn't be detected
            if "React Testing Library" in testing_matches:
                testing_matches["React Testing Library"] = 0
            if "Enzyme" in testing_matches:
                testing_matches["Enzyme"] = 0
        else:
            # Validate React Testing Library
            if "React Testing Library" in testing_matches:
                rtl_specific_patterns = [
                    r"from\s+['\"]\@testing-library\/react['\"]", 
                    r"import\s+.*\s+from\s+['\"]\@testing-library\/react['\"]",
                    r"render\(\s*<.*\/>\s*\)", r"screen\.getByText"
                ]
                
                has_specific_rtl = False
                for _, content in files_content.items():
                    if any(re.search(pattern, content) for pattern in rtl_specific_patterns):
                        has_specific_rtl = True
                        break
                
                if not has_specific_rtl:
                    testing_matches["React Testing Library"] = 0
            
            # Validate Enzyme
            if "Enzyme" in testing_matches:
                enzyme_specific_patterns = [
                    r"from\s+['\"]enzyme['\"]", 
                    r"import\s+.*\s+from\s+['\"]enzyme['\"]",
                    r"shallow\(\s*<.*\/>\s*\)", r"mount\(\s*<.*\/>\s*\)"
                ]
                
                has_specific_enzyme = False
                for _, content in files_content.items():
                    if any(re.search(pattern, content) for pattern in enzyme_specific_patterns):
                        has_specific_enzyme = True
                        break
                
                if not has_specific_enzyme:
                    testing_matches["Enzyme"] = 0
        
        # For RSpec (Ruby testing framework)
        if not has_ruby:
            if "RSpec" in testing_matches:
                testing_matches["RSpec"] = 0
        else:
            # Validate RSpec
            if "RSpec" in testing_matches:
                rspec_specific_patterns = [
                    r"require\s+['\"]rspec['\"]", 
                    r"RSpec\.describe", 
                    r"describe\s+.*\s+do\s+", 
                    r"it\s+['\"].*['\"]\s+do"
                ]
                
                has_specific_rspec = False
                for _, content in files_content.items():
                    if any(re.search(pattern, content) for pattern in rspec_specific_patterns):
                        has_specific_rspec = True
                        break
                
                if not has_specific_rspec:
                    testing_matches["RSpec"] = 0
    
    def detect(self, files: List[str], files_content: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Detect testing frameworks and patterns used in the repository.
        
        This method examines file names, paths, and contents to identify
        testing frameworks, libraries, and patterns used in the project.
        
        Args:
            files: List of file paths in the repository
            files_content: Dict mapping file paths to their content
            
        Returns:
            Dict mapping testing framework names to dicts containing:
                - matches: Number of pattern matches found
                - confidence: Confidence score (0-100)
                - category: Category of the testing framework
                - evidence: List of evidence found
        """
        # Track matches for testing frameworks
        testing_matches = defaultdict(int)
        testing_categories = {}
        testing_evidence = defaultdict(list)
        
        # Step 1: Check for test directories
        test_files = []
        for file_path in files:
            # Check if file is in a test directory
            if any(test_dir in file_path for test_dir in self.test_directories):
                test_files.append(file_path)
                # Identify which test directory it is
                for test_dir in self.test_directories:
                    if test_dir in file_path:
                        # Determine test category based on directory name
                        if "unit" in test_dir.lower():
                            category = "unit"
                        elif "integration" in test_dir.lower():
                            category = "integration"
                        elif "e2e" in test_dir.lower() or "end-to-end" in test_dir.lower():
                            category = "e2e"
                        elif "acceptance" in test_dir.lower():
                            category = "acceptance"
                        elif "functional" in test_dir.lower():
                            category = "functional"
                        else:
                            category = "general"
                        
                        # Generic "Tests" match
                        testing_matches["Tests"] += 2
                        testing_categories["Tests"] = category
                        testing_evidence["Tests"].append(f"Found test directory: {test_dir} in {file_path}")
                        break
        
        # Step 2: Check for test file naming patterns
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # General test file patterns
            for framework, patterns in self.test_file_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, filename):
                        testing_matches[framework] += 5
                        
                        # Set category if not already set
                        if framework not in testing_categories:
                            # Try to determine category
                            if "unit" in file_path.lower():
                                testing_categories[framework] = "unit"
                            elif "integration" in file_path.lower():
                                testing_categories[framework] = "integration"
                            elif "e2e" in file_path.lower() or "end-to-end" in file_path.lower():
                                testing_categories[framework] = "e2e"
                            else:
                                testing_categories[framework] = "general"
                        
                        testing_evidence[framework].append(f"Found test file: {filename}")
                        break
            
            # Check for testing framework config files
            for framework, config_files in self.config_files.items():
                if filename in config_files or any(filename.endswith(f) for f in config_files):
                    testing_matches[framework] += 15  # High weight for config files
                    
                    # Set category if not already set
                    if framework not in testing_categories:
                        # Categorize based on framework type
                        if framework in ["Cypress", "Playwright", "Selenium", "Nightwatch", "Protractor", "TestCafe", "WebdriverIO"]:
                            testing_categories[framework] = "e2e"
                        elif framework in ["JMeter", "K6", "Artillery", "Gatling", "Locust"]:
                            testing_categories[framework] = "performance"
                        elif framework in ["Cucumber", "Robot Framework"]:
                            testing_categories[framework] = "bdd"
                        else:
                            testing_categories[framework] = "general"
                    
                    testing_evidence[framework].append(f"Found config file: {filename}")
        
        # Step 3: Check for package.json dependencies
        for file_path, content in files_content.items():
            if os.path.basename(file_path) == "package.json":
                try:
                    import json
                    package_data = json.loads(content)
                    
                    # Check dependencies and devDependencies
                    for dep_type in ["dependencies", "devDependencies"]:
                        if dep_type in package_data and isinstance(package_data[dep_type], dict):
                            deps = package_data[dep_type]
                            
                            for framework, packages in self.npm_dependencies.items():
                                for pkg in packages:
                                    if pkg in deps:
                                        testing_matches[framework] += 15
                                        
                                        # Categorize based on framework type
                                        if framework in ["Cypress", "Playwright", "Selenium", "Nightwatch", "Protractor", "TestCafe", "WebdriverIO", "Puppeteer"]:
                                            testing_categories[framework] = "e2e"
                                        elif framework in ["Jest", "Mocha", "Jasmine", "Vitest", "AVA", "Tape", "QUnit"]:
                                            testing_categories[framework] = "unit"
                                        else:
                                            testing_categories[framework] = "general"
                                        
                                        testing_evidence[framework].append(f"Found in {dep_type}: {pkg}")
                except Exception:
                    # If we can't parse package.json, just continue
                    pass
            
            # Check for Python requirements files
            elif os.path.basename(file_path) in ["requirements.txt", "Pipfile", "pyproject.toml", "requirements.in"]:
                for framework, packages in self.python_dependencies.items():
                    for pkg in packages:
                        if pkg in content:
                            testing_matches[framework] += 15
                            
                            # Categorize based on framework type
                            if framework in ["Selenium", "Playwright"]:
                                testing_categories[framework] = "e2e"
                            elif framework in ["PyTest", "unittest", "Nose"]:
                                testing_categories[framework] = "unit"
                            elif framework in ["Behave", "Lettuce", "Cucumber", "PyTest-BDD", "Robot Framework"]:
                                testing_categories[framework] = "bdd"
                            elif framework in ["Locust"]:
                                testing_categories[framework] = "performance"
                            else:
                                testing_categories[framework] = "general"
                            
                            testing_evidence[framework].append(f"Found in requirements: {pkg}")
            
            # Check for Ruby Gemfile
            elif os.path.basename(file_path) in ["Gemfile", "Gemfile.lock"]:
                for framework, packages in self.ruby_dependencies.items():
                    for pkg in packages:
                        if pkg in content:
                            testing_matches[framework] += 15
                            
                            # Categorize based on framework type
                            if framework in ["Capybara"]:
                                testing_categories[framework] = "e2e"
                            elif framework in ["RSpec", "MiniTest"]:
                                testing_categories[framework] = "unit"
                            elif framework in ["Cucumber"]:
                                testing_categories[framework] = "bdd"
                            else:
                                testing_categories[framework] = "general"
                            
                            testing_evidence[framework].append(f"Found in Gemfile: {pkg}")
        
        # Step 4: Check file content for testing framework imports and patterns
        for file_path, content in files_content.items():
            # Skip large files
            if len(content) > 500000:  # Skip files over 500KB
                continue
            
            # Check for testing framework imports
            for framework, patterns in self.import_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        match_count = len(matches)
                        if match_count > 10:
                            # Cap at 10 to avoid a single file dominating
                            match_count = 10
                        testing_matches[framework] += match_count
                        
                        # Set category if not already set
                        if framework not in testing_categories:
                            # Categorize based on framework type
                            if framework in ["Cypress", "Playwright", "Selenium"]:
                                testing_categories[framework] = "e2e"
                            elif framework in ["Jest", "Mocha", "PyTest", "unittest", "JUnit", "RSpec"]:
                                testing_categories[framework] = "unit"
                            else:
                                testing_categories[framework] = "general"
                        
                        # Add pattern match as evidence
                        if matches:
                            match_text = matches[0]
                            if len(match_text) > 60:  # Truncate long matches
                                match_text = match_text[:57] + "..."
                            testing_evidence[framework].append(
                                f"Found import in {os.path.basename(file_path)}: {match_text}"
                            )
            
            # Check for testing framework code patterns
            for framework, patterns in self.code_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        match_count = len(matches)
                        if match_count > 10:
                            # Cap at 10 to avoid a single file dominating
                            match_count = 10
                        testing_matches[framework] += match_count
                        
                        # Set category if not already set
                        if framework not in testing_categories:
                            # Categorize based on framework type
                            if framework in ["Cypress", "Playwright", "Selenium"]:
                                testing_categories[framework] = "e2e"
                            elif framework in ["Jest", "Mocha", "PyTest", "unittest", "JUnit", "RSpec"]:
                                testing_categories[framework] = "unit"
                            elif framework in ["Cucumber", "Robot Framework"]:
                                testing_categories[framework] = "bdd"
                            else:
                                testing_categories[framework] = "general"
                        
                        # Add pattern match as evidence
                        if matches:
                            match_text = matches[0]
                            if len(match_text) > 60:  # Truncate long matches
                                match_text = match_text[:57] + "..."
                            testing_evidence[framework].append(
                                f"Found code pattern in {os.path.basename(file_path)}: {match_text}"
                            )
        
        # Step 5: Apply context validation to reduce false positives
        self._apply_context_validation(testing_matches, testing_categories, files_content)
        
        # Step 6: Calculate test coverage by counting test files vs source files
        if test_files:
            # Count test files for each extension
            test_extensions = {}
            for test_file in test_files:
                _, ext = os.path.splitext(test_file)
                if ext:
                    test_extensions[ext] = test_extensions.get(ext, 0) + 1
            
            # Count source files for each extension
            source_extensions = {}
            for file_path in files:
                if file_path not in test_files:  # Skip test files
                    _, ext = os.path.splitext(file_path)
                    if ext:
                        source_extensions[ext] = source_extensions.get(ext, 0) + 1
            
            # Calculate coverage for each extension
            for ext in test_extensions:
                if ext in source_extensions and source_extensions[ext] > 0:
                    coverage_ratio = test_extensions[ext] / source_extensions[ext]
                    if coverage_ratio >= 0.5:  # If at least 50% of files have tests
                        testing_matches["High Test Coverage"] = testing_matches.get("High Test Coverage", 0) + 10
                        testing_categories["High Test Coverage"] = "coverage"
                        testing_evidence["High Test Coverage"].append(
                            f"Found good test coverage for {ext} files: {test_extensions[ext]} tests for {source_extensions[ext]} source files"
                        )
        
        # Step 7: Calculate confidence scores
        testing_frameworks = {}
        
        if testing_matches:
            # Find maximum number of matches for normalization
            max_matches = max(testing_matches.values())
            
            # Only proceed if we have actual matches (avoid division by zero)
            if max_matches > 0:
                for framework, matches in testing_matches.items():
                    # Calculate confidence score (0-100)
                    confidence = min(100, (matches / max_matches) * 100)
                    
                    # Only include frameworks with reasonable confidence
                    # Increased threshold from 15 to 40 to reduce false positives
                    if confidence >= 40:
                        # Keep only unique evidence and limit to 5 examples
                        unique_evidence = list(dict.fromkeys(testing_evidence[framework]))[:5]
                        
                        testing_frameworks[framework] = {
                            "matches": matches,
                            "confidence": round(confidence, 2),
                            "category": testing_categories.get(framework, "general"),
                            "evidence": unique_evidence
                        }
        
        return testing_frameworks