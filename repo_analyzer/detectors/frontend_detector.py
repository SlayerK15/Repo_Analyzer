"""
Frontend Technology Detector module for repository analysis.

This module identifies frontend technologies, UI frameworks, CSS frameworks,
state management libraries, and other client-side tools used in a repository
by analyzing file patterns, import statements, and configuration files.
"""

import os
import re
from collections import defaultdict
from typing import Dict, List, Any

class FrontendDetector:
    """
    Detector for frontend technologies used in a repository.
    
    This class identifies web frameworks, CSS frameworks, UI component libraries,
    state management solutions, and other frontend technologies by examining
    specific files, import statements, and code patterns.
    """
    
    def __init__(self):
        """Initialize the Frontend Technology Detector with detection patterns."""
        # Frontend framework detection files
        self.framework_files = {
            "React": ["jsx", "tsx", ".jsx", ".tsx", "react.js", "react.min.js", "react-dom.js"],
            "Vue.js": [".vue", "vue.js", "vue.min.js", "vue.config.js", "vue.config.ts"],
            "Angular": ["angular.json", ".angular-cli.json", "ng-app", "app.module.ts"],
            "Svelte": [".svelte", "svelte.config.js", "rollup-plugin-svelte"],
            "Next.js": ["next.config.js", "pages/_app.js", "pages/_document.js", "pages/index.js"],
            "Nuxt.js": ["nuxt.config.js", "layouts/default.vue", "pages/index.vue"],
            "Gatsby": ["gatsby-config.js", "gatsby-node.js", "gatsby-browser.js"],
            "Preact": ["preact.js", "preact.min.js", "preact.config.js"],
            "Ember.js": ["ember-cli-build.js", "app/templates/", "app/routes/"],
            "Backbone.js": ["backbone.js", "backbone.min.js"],
            "jQuery": ["jquery.js", "jquery.min.js"],
            "Alpine.js": ["alpine.js", "alpine.min.js", "x-data", "x-bind"],
            "Lit": ["lit-element", "lit-html", "LitElement"],
            "Solid.js": ["solid-js", ".solid", "createSignal", "createEffect"],
            "Web Components": ["customElements.define", "attachShadow"],
        }
        
        # CSS framework detection files
        self.css_framework_files = {
            "Bootstrap": ["bootstrap.css", "bootstrap.min.css", "bootstrap.js", "bootstrap.min.js", "bootstrap.bundle.js"],
            "Tailwind CSS": ["tailwind.config.js", "tailwind.css", "tailwind.min.css", "tailwind.config.cjs"],
            "Material-UI": ["@material-ui", "@mui/material", "createTheme", "ThemeProvider"],
            "Chakra UI": ["@chakra-ui", "ChakraProvider", "useDisclosure"],
            "Ant Design": ["antd", "@ant-design", "ConfigProvider", "Layout"],
            "Semantic UI": ["semantic.css", "semantic.min.css", "semantic.js", "semantic.min.js"],
            "Bulma": ["bulma.css", "bulma.min.css", "bulma-extensions"],
            "Foundation": ["foundation.css", "foundation.min.css", "foundation.js", "foundation.min.js"],
            "Materialize": ["materialize.css", "materialize.min.css", "materialize.js", "materialize.min.js"],
            "Styled Components": ["styled-components", "createGlobalStyle", "css`"],
            "Emotion": ["@emotion/react", "@emotion/styled", "css`"],
            "SASS/SCSS": [".scss", ".sass", "sass", "node-sass"],
            "LESS": [".less", "less", "less-loader"],
            "PostCSS": ["postcss.config.js", "postcss.config.cjs", "postcss.js", "autoprefixer"],
            "CSS Modules": [".module.css", ".module.scss", ".module.sass", ".module.less"],
        }
        
        # State management library detection files
        self.state_management_files = {
            "Redux": ["redux", "createStore", "combineReducers", "applyMiddleware", "connect"],
            "MobX": ["mobx", "observable", "action", "computed", "observer"],
            "Vuex": ["vuex", "createStore", "state", "mutations", "actions", "getters"],
            "Pinia": ["pinia", "defineStore", "createPinia"],
            "Recoil": ["recoil", "atom", "selector", "useRecoilState", "useRecoilValue"],
            "Jotai": ["jotai", "atom", "useAtom", "useAtomValue"],
            "Zustand": ["zustand", "create", "useStore"],
            "XState": ["xstate", "createMachine", "interpret", "useMachine"],
            "Context API": ["createContext", "useContext", "Provider", "Consumer"],
            "NgRx": ["@ngrx/store", "createReducer", "createAction", "createEffect"],
            "RxJS": ["rxjs", "Observable", "Subject", "BehaviorSubject", "pipe"],
            "Apollo Client": ["@apollo/client", "ApolloClient", "useQuery", "useMutation"],
            "SWR": ["swr", "useSWR", "mutate", "SWRConfig"],
            "React Query": ["react-query", "useQuery", "useMutation", "QueryClient"],
        }
        
        # UI component libraries
        self.component_library_files = {
            "Material UI": ["@material-ui", "@mui/material", "makeStyles", "createTheme"],
            "Chakra UI": ["@chakra-ui", "ChakraProvider", "useDisclosure"],
            "Ant Design": ["antd", "@ant-design", "Form", "Button", "Table"],
            "React Bootstrap": ["react-bootstrap", "Navbar", "Container", "Row", "Col"],
            "Blueprint": ["@blueprintjs", "Button", "Popover", "Dialog"],
            "Mantine": ["@mantine", "MantineProvider", "createStyles"],
            "Headless UI": ["@headlessui", "Transition", "Dialog", "Disclosure"],
            "Radix UI": ["@radix-ui", "DialogRoot", "PopoverContent"],
            "PrimeReact": ["primereact", "DataTable", "InputText", "Calendar"],
            "NgBootstrap": ["@ng-bootstrap", "NgbModule", "NgbModal"],
            "Angular Material": ["@angular/material", "MatButton", "MatDialog"],
            "Vuetify": ["vuetify", "v-app", "v-btn", "v-card"],
            "Quasar": ["quasar", "QBtn", "QCard", "QInput"],
            "PrimeVue": ["primevue", "DataTable", "InputText", "Calendar"],
            "Element Plus": ["element-plus", "el-button", "el-form", "el-table"],
        }
        
        # Testing libraries
        self.testing_library_files = {
            "Jest": ["jest.config.js", "jest.config.ts", "jest.setup.js", "test.js", "spec.js", "expect"],
            "Testing Library": ["@testing-library/react", "@testing-library/vue", "render", "screen", "fireEvent"],
            "Cypress": ["cypress.json", "cypress.config.js", "cypress/integration", "cy.visit", "cy.get"],
            "Playwright": ["playwright.config.js", "page.goto", "page.click", "expect(page)"],
            "Selenium": ["selenium-webdriver", "webdriver", "By.", "driver.findElement"],
            "Storybook": [".storybook", "stories.js", "stories.ts", "stories.mdx", "storiesOf"],
            "Vitest": ["vitest.config.js", "vitest.config.ts", "import { test } from 'vitest'"],
        }
        
        # Code patterns for frontend technologies
        self.frontend_patterns = {
            # Framework patterns
            "React": [
                r"import\s+React", r"from\s+['\"]react['\"]", r"React\.Component",
                r"extends\s+Component", r"useState", r"useEffect", r"<\w+\s+/>"
            ],
            "Vue.js": [
                r"import\s+Vue", r"from\s+['\"]vue['\"]", r"new\s+Vue\(\{",
                r"createApp", r"<template>", r"v-if", r"v-for", r"v-model", r"v-on"
            ],
            "Angular": [
                r"import\s+{\s*Component", r"from\s+['\"]@angular/core['\"]",
                r"@Component\(\{", r"@NgModule\(\{", r"@Injectable\(\{", r"[(ngModel)]"
            ],
            "Svelte": [
                r"<script>", r"export\s+let", r"{#if", r"{#each", r"{:else}",
                r"on:click", r"bind:"
            ],
            
            # CSS frameworks
            "Bootstrap": [
                r"class=\"[^\"]*btn[^\"]*\"", r"class=\"[^\"]*col-[^\"]*\"",
                r"class=\"[^\"]*row[^\"]*\"", r"class=\"[^\"]*container[^\"]*\""
            ],
            "Tailwind CSS": [
                r"class=\"[^\"]*bg-[^\"]*\"", r"class=\"[^\"]*text-[^\"]*\"",
                r"class=\"[^\"]*flex[^\"]*\"", r"class=\"[^\"]*p-[^\"]*\"",
                r"class=\"[^\"]*m-[^\"]*\""
            ],
            
            # State management
            "Redux": [
                r"createStore", r"combineReducers", r"useSelector", r"useDispatch",
                r"mapStateToProps", r"connect\("
            ],
            "MobX": [
                r"observable", r"action", r"computed", r"observer",
                r"makeObservable", r"makeAutoObservable"
            ],
            
            # Component libraries
            "Material UI": [
                r"import\s+{\s*Button", r"from\s+['\"]@mui/material['\"]",
                r"from\s+['\"]@material-ui/core['\"]", r"makeStyles", r"createTheme"
            ],
        }
    
    # NEW METHOD: Context validation to reduce false positives
    def _apply_context_validation(self, frontend_matches, files_content):
        """
        Apply context-aware validation to reduce false positives.
        """
        # Check for Django template patterns which might be confused with Angular
        django_patterns = [
            r"{%\s+.+\s+%}", r"{{\s+.+\s+}}", r"{% extends", r"{% block", r"{% include",
            r"from django\.template", r"from django\.shortcuts import render"
        ]
        
        has_django_templates = False
        for _, content in files_content.items():
            if any(re.search(pattern, content) for pattern in django_patterns):
                has_django_templates = True
                break
        
        # If Django templates are found, reduce confidence in Angular
        if has_django_templates and "Angular" in frontend_matches:
            # Check if there are actual Angular-specific patterns
            angular_specific = [
                r"@angular/core", r"@Component\(\{", r"@NgModule\(\{", 
                r"platformBrowserDynamic\(\)", r"Angular\.(module|bootstrap)"
            ]
            
            has_specific_angular = False
            for _, content in files_content.items():
                if any(re.search(pattern, content) for pattern in angular_specific):
                    has_specific_angular = True
                    break
            
            # If no Angular-specific patterns, significantly reduce confidence
            if not has_specific_angular:
                frontend_matches["Angular"] = frontend_matches.get("Angular", 0) // 5
        
        # Make Tailwind CSS detection more specific
        if "Tailwind CSS" in frontend_matches:
            tailwind_specific_patterns = [
                r"tailwind\.config\.js", r"@tailwind\s+base", r"@tailwind\s+components", 
                r"@tailwind\s+utilities", r"require\(['\"]tailwindcss['\"]"
            ]
            
            has_specific_tailwind = False
            for file_path, content in files_content.items():
                if "tailwind.config.js" in file_path or any(re.search(pattern, content) for pattern in tailwind_specific_patterns):
                    has_specific_tailwind = True
                    break
            
            # If no specific Tailwind patterns, significantly reduce confidence
            if not has_specific_tailwind:
                frontend_matches["Tailwind CSS"] = frontend_matches.get("Tailwind CSS", 0) // 5

    def detect(self, files: List[str], files_content: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Detect frontend technologies used in the repository.
        
        This method examines file names, paths, and contents to identify
        frontend frameworks, CSS frameworks, state management libraries,
        and UI component libraries used in the project.
        
        Args:
            files: List of file paths in the repository
            files_content: Dict mapping file paths to their content
            
        Returns:
            Dict mapping frontend technology names to dicts containing:
                - matches: Number of pattern matches found
                - confidence: Confidence score (0-100)
                - category: Category of the frontend technology
                    (framework, css, state_management, component_library, testing)
        """
        # Track matches for frontend technologies
        frontend_matches = defaultdict(int)
        frontend_categories = {}
        frontend_evidence = defaultdict(list)
        
        # Step 1: Check for frontend technology files
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # Check for frontend framework files
            for framework, patterns in self.framework_files.items():
                if filename in patterns:
                    frontend_matches[framework] += 10  # High weight for exact match
                    frontend_categories[framework] = "framework"
                    frontend_evidence[framework].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns):
                    frontend_matches[framework] += 5  # Medium weight for partial match
                    frontend_categories[framework] = "framework"
                    frontend_evidence[framework].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns):
                    frontend_matches[framework] += 3  # Lower weight for path match
                    frontend_categories[framework] = "framework"
                    frontend_evidence[framework].append(f"Found pattern in path: {file_path}")
            
            # Check for CSS framework files
            for framework, patterns in self.css_framework_files.items():
                if filename in patterns:
                    frontend_matches[framework] += 10
                    frontend_categories[framework] = "css"
                    frontend_evidence[framework].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns):
                    frontend_matches[framework] += 5
                    frontend_categories[framework] = "css"
                    frontend_evidence[framework].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns):
                    frontend_matches[framework] += 3
                    frontend_categories[framework] = "css"
                    frontend_evidence[framework].append(f"Found pattern in path: {file_path}")
            
            # Check for state management library files
            for lib, patterns in self.state_management_files.items():
                if filename in patterns:
                    frontend_matches[lib] += 10
                    frontend_categories[lib] = "state_management"
                    frontend_evidence[lib].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns):
                    frontend_matches[lib] += 5
                    frontend_categories[lib] = "state_management"
                    frontend_evidence[lib].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns):
                    frontend_matches[lib] += 3
                    frontend_categories[lib] = "state_management"
                    frontend_evidence[lib].append(f"Found pattern in path: {file_path}")
            
            # Check for component library files
            for lib, patterns in self.component_library_files.items():
                if filename in patterns:
                    frontend_matches[lib] += 10
                    frontend_categories[lib] = "component_library"
                    frontend_evidence[lib].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns):
                    frontend_matches[lib] += 5
                    frontend_categories[lib] = "component_library"
                    frontend_evidence[lib].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns):
                    frontend_matches[lib] += 3
                    frontend_categories[lib] = "component_library"
                    frontend_evidence[lib].append(f"Found pattern in path: {file_path}")
            
            # Check for testing library files
            for lib, patterns in self.testing_library_files.items():
                if filename in patterns:
                    frontend_matches[lib] += 10
                    frontend_categories[lib] = "testing"
                    frontend_evidence[lib].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns):
                    frontend_matches[lib] += 5
                    frontend_categories[lib] = "testing"
                    frontend_evidence[lib].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns):
                    frontend_matches[lib] += 3
                    frontend_categories[lib] = "testing"
                    frontend_evidence[lib].append(f"Found pattern in path: {file_path}")
        
        # Step 2: Check file content for frontend patterns
        for file_path, content in files_content.items():
            # Check for large files and skip them for performance
            if len(content) > 500000:  # Skip files over 500KB
                continue
            
            # Check for package.json dependencies
            if os.path.basename(file_path) == "package.json":
                # Try to parse as JSON and extract dependencies
                try:
                    import json
                    package_data = json.loads(content)
                    
                    # Check dependencies and devDependencies
                    for dep_type in ["dependencies", "devDependencies"]:
                        if dep_type in package_data and isinstance(package_data[dep_type], dict):
                            deps = package_data[dep_type]
                            
                            # Framework dependencies
                            if "react" in deps:
                                frontend_matches["React"] += 15
                                frontend_categories["React"] = "framework"
                                frontend_evidence["React"].append(f"Found in {dep_type}: react")
                            
                            if "vue" in deps:
                                frontend_matches["Vue.js"] += 15
                                frontend_categories["Vue.js"] = "framework"
                                frontend_evidence["Vue.js"].append(f"Found in {dep_type}: vue")
                            
                            if "@angular/core" in deps:
                                frontend_matches["Angular"] += 15
                                frontend_categories["Angular"] = "framework"
                                frontend_evidence["Angular"].append(f"Found in {dep_type}: @angular/core")
                            
                            if "svelte" in deps:
                                frontend_matches["Svelte"] += 15
                                frontend_categories["Svelte"] = "framework"
                                frontend_evidence["Svelte"].append(f"Found in {dep_type}: svelte")
                            
                            # Next.js, Nuxt.js, Gatsby
                            if "next" in deps:
                                frontend_matches["Next.js"] += 15
                                frontend_categories["Next.js"] = "framework"
                                frontend_evidence["Next.js"].append(f"Found in {dep_type}: next")
                            
                            if "nuxt" in deps:
                                frontend_matches["Nuxt.js"] += 15
                                frontend_categories["Nuxt.js"] = "framework"
                                frontend_evidence["Nuxt.js"].append(f"Found in {dep_type}: nuxt")
                            
                            if "gatsby" in deps:
                                frontend_matches["Gatsby"] += 15
                                frontend_categories["Gatsby"] = "framework"
                                frontend_evidence["Gatsby"].append(f"Found in {dep_type}: gatsby")
                            
                            # CSS frameworks
                            if "bootstrap" in deps:
                                frontend_matches["Bootstrap"] += 15
                                frontend_categories["Bootstrap"] = "css"
                                frontend_evidence["Bootstrap"].append(f"Found in {dep_type}: bootstrap")
                            
                            if "tailwindcss" in deps:
                                frontend_matches["Tailwind CSS"] += 15
                                frontend_categories["Tailwind CSS"] = "css"
                                frontend_evidence["Tailwind CSS"].append(f"Found in {dep_type}: tailwindcss")
                            
                            # Check for common UI libraries
                            for lib in [
                                "@material-ui/core", "@mui/material", "@chakra-ui/react",
                                "antd", "react-bootstrap", "@blueprintjs/core",
                                "@mantine/core", "@headlessui/react", "@radix-ui/react-dialog",
                                "primereact", "vuetify", "quasar"
                            ]:
                                if lib in deps:
                                    # Extract library name
                                    if lib.startswith("@material-ui") or lib.startswith("@mui"):
                                        name = "Material UI"
                                    elif lib.startswith("@chakra-ui"):
                                        name = "Chakra UI"
                                    elif lib == "antd":
                                        name = "Ant Design"
                                    elif lib == "react-bootstrap":
                                        name = "React Bootstrap"
                                    elif lib.startswith("@blueprintjs"):
                                        name = "Blueprint"
                                    elif lib.startswith("@mantine"):
                                        name = "Mantine"
                                    elif lib.startswith("@headlessui"):
                                        name = "Headless UI"
                                    elif lib.startswith("@radix-ui"):
                                        name = "Radix UI"
                                    elif lib == "primereact":
                                        name = "PrimeReact"
                                    elif lib == "vuetify":
                                        name = "Vuetify"
                                    elif lib == "quasar":
                                        name = "Quasar"
                                    else:
                                        name = lib
                                    
                                    frontend_matches[name] += 15
                                    frontend_categories[name] = "component_library"
                                    frontend_evidence[name].append(f"Found in {dep_type}: {lib}")
                            
                            # Check for state management libraries
                            for lib in [
                                "redux", "react-redux", "@reduxjs/toolkit",
                                "mobx", "mobx-react", "vuex", "pinia",
                                "recoil", "jotai", "zustand", "xstate",
                                "@ngrx/store", "rxjs", "@apollo/client",
                                "swr", "react-query"
                            ]:
                                if lib in deps:
                                    # Extract library name
                                    if lib.startswith("redux") or lib.startswith("@reduxjs") or lib == "react-redux":
                                        name = "Redux"
                                    elif lib.startswith("mobx"):
                                        name = "MobX"
                                    elif lib == "vuex":
                                        name = "Vuex"
                                    elif lib == "pinia":
                                        name = "Pinia"
                                    elif lib == "recoil":
                                        name = "Recoil"
                                    elif lib == "jotai":
                                        name = "Jotai"
                                    elif lib == "zustand":
                                        name = "Zustand"
                                    elif lib == "xstate":
                                        name = "XState"
                                    elif lib.startswith("@ngrx"):
                                        name = "NgRx"
                                    elif lib == "rxjs":
                                        name = "RxJS"
                                    elif lib.startswith("@apollo"):
                                        name = "Apollo Client"
                                    elif lib == "swr":
                                        name = "SWR"
                                    elif lib == "react-query":
                                        name = "React Query"
                                    else:
                                        name = lib
                                    
                                    frontend_matches[name] += 15
                                    frontend_categories[name] = "state_management"
                                    frontend_evidence[name].append(f"Found in {dep_type}: {lib}")
                            
                            # Check for testing libraries
                            for lib in [
                                "jest", "@testing-library/react", "@testing-library/vue",
                                "cypress", "playwright", "selenium-webdriver",
                                "@storybook/react", "@storybook/vue", "vitest"
                            ]:
                                if lib in deps:
                                    # Extract library name
                                    if lib == "jest":
                                        name = "Jest"
                                    elif lib.startswith("@testing-library"):
                                        name = "Testing Library"
                                    elif lib == "cypress":
                                        name = "Cypress"
                                    elif lib == "playwright":
                                        name = "Playwright"
                                    elif lib == "selenium-webdriver":
                                        name = "Selenium"
                                    elif lib.startswith("@storybook"):
                                        name = "Storybook"
                                    elif lib == "vitest":
                                        name = "Vitest"
                                    else:
                                        name = lib
                                    
                                    frontend_matches[name] += 15
                                    frontend_categories[name] = "testing"
                                    frontend_evidence[name].append(f"Found in {dep_type}: {lib}")
                            
                except Exception as e:
                    # If we can't parse package.json, just continue
                    pass
            
            # Check for content patterns
            for tech, patterns in self.frontend_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        match_count = len(matches)
                        if match_count > 10:
                            # Cap at 10 to avoid a single file dominating
                            match_count = 10
                        frontend_matches[tech] += match_count
                        
                        # Extract category if not already set
                        if tech not in frontend_categories:
                            # Try to determine category
                            if tech in self.framework_files:
                                frontend_categories[tech] = "framework"
                            elif tech in self.css_framework_files:
                                frontend_categories[tech] = "css"
                            elif tech in self.state_management_files:
                                frontend_categories[tech] = "state_management"
                            elif tech in self.component_library_files:
                                frontend_categories[tech] = "component_library"
                            elif tech in self.testing_library_files:
                                frontend_categories[tech] = "testing"
                            else:
                                frontend_categories[tech] = "other"
                        
                        # Add pattern match as evidence
                        if matches:
                            match_text = matches[0]
                            if len(match_text) > 60:  # Truncate long matches
                                match_text = match_text[:57] + "..."
                            frontend_evidence[tech].append(f"Pattern match: {match_text}")
        
        # Step 3: Apply context validation to reduce false positives
        self._apply_context_validation(frontend_matches, files_content)
        
        # Step 4: Calculate confidence scores
        frontend_technologies = {}
        
        if frontend_matches:
            # Find maximum number of matches for normalization
            max_matches = max(frontend_matches.values())
            
            for tech, matches in frontend_matches.items():
                # Calculate confidence score (0-100)
                confidence = min(100, (matches / max_matches) * 100)
                
                # Only include technologies with reasonable confidence
                # Increased threshold from 15 to 35 to reduce false positives
                if confidence >= 35:
                    # Keep only unique evidence and limit to 5 examples
                    unique_evidence = list(dict.fromkeys(frontend_evidence[tech]))[:5]
                    
                    frontend_technologies[tech] = {
                        "matches": matches,
                        "confidence": round(confidence, 2),
                        "category": frontend_categories.get(tech, "other"),
                        "evidence": unique_evidence
                    }
        
        return frontend_technologies