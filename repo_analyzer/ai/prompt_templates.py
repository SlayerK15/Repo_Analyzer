"""
AI Prompt Templates for RepoAnalyzer.

This module contains prompt templates for various AI analysis tasks in the
RepoAnalyzer. These templates are used to generate prompts for LLM analysis
of code, architecture, and quality.
"""

# Framework/Technology Detection Prompt
FRAMEWORK_DETECTION_PROMPT = """
Please analyze the following code file to identify frameworks, libraries, and technologies used.

Filename: {filename}
Language: {language}

CODE:
```
{code}
```

Analyze the code and respond with a JSON object that includes:
1. A list of frameworks and technologies detected
2. Confidence scores (0-100) for each detection
3. Evidence for each detection (specific code patterns, imports, etc.)

Format your response as a JSON object with the following structure:
```json
{{
  "technologies": [
    {{
      "name": "Framework/Technology Name",
      "category": "framework|library|language|database|build_system|package_manager|frontend|devops|other",
      "confidence": 85,
      "evidence": ["Evidence 1", "Evidence 2", ...]
    }}
  ],
  "suggestions": [
    {{
      "text": "Suggestion text",
      "severity": "low|medium|high",
      "reason": "Reason for suggestion"
    }}
  ]
}}
```

Be precise in your detection, only include technologies with clear evidence.
If you're unsure about a technology, include it with a lower confidence score.
For any technologies you detect, categorize them appropriately.
"""

# Architecture Pattern Detection Prompt
ARCHITECTURE_DETECTION_PROMPT = """
Please analyze the following code file to identify architectural patterns and code organization.

Filename: {filename}
Language: {language}

CODE:
```
{code}
```

Analyze the code and respond with a JSON object that includes:
1. Architectural patterns detected (MVC, MVVM, layered, microservices, etc.)
2. Code organization patterns (modular, object-oriented, functional, etc.)
3. Confidence scores (0-100) for each detection
4. Evidence for each detection

Format your response as a JSON object with the following structure:
```json
{{
  "patterns": [
    {{
      "name": "Pattern Name",
      "type": "architecture|organization|design",
      "confidence": 85,
      "evidence": ["Evidence 1", "Evidence 2", ...]
    }}
  ],
  "suggestions": [
    {{
      "text": "Suggestion for architectural improvement",
      "severity": "low|medium|high",
      "reason": "Reason for suggestion"
    }}
  ]
}}
```

Be precise in your detection, only include patterns with clear evidence.
If the file is part of a larger pattern that may not be fully visible in this single file, note that in your analysis.
Consider the file's structure, class relationships, dependency patterns, and overall organization in your analysis.
"""

# Code Quality Assessment Prompt
CODE_QUALITY_PROMPT = """
Please analyze the following code file for code quality, best practices, and potential improvements.

Filename: {filename}
Language: {language}

CODE:
```
{code}
```

Analyze the code and respond with a JSON object that includes:
1. Code quality assessment (readability, maintainability, performance)
2. Best practices adherence
3. Potential issues or anti-patterns
4. Suggestions for improvement

Format your response as a JSON object with the following structure:
```json
{{
  "quality_assessment": {{
    "readability": {{
      "score": 85,
      "strengths": ["Strength 1", "Strength 2"],
      "weaknesses": ["Weakness 1", "Weakness 2"]
    }},
    "maintainability": {{
      "score": 75,
      "strengths": ["Strength 1", "Strength 2"],
      "weaknesses": ["Weakness 1", "Weakness 2"]
    }},
    "performance": {{
      "score": 90,
      "strengths": ["Strength 1", "Strength 2"],
      "weaknesses": ["Weakness 1", "Weakness 2"]
    }}
  }},
  "issues": [
    {{
      "type": "anti-pattern|code-smell|performance|security",
      "severity": "low|medium|high",
      "description": "Description of the issue",
      "location": "Line number or method name"
    }}
  ],
  "suggestions": [
    {{
      "text": "Suggestion for improvement",
      "severity": "low|medium|high",
      "reason": "Reason for suggestion"
    }}
  ]
}}
```

Be thorough but fair in your assessment. Consider language-specific best practices and conventions.
Focus on meaningful improvements rather than nitpicking. If there are conflicting best practices,
acknowledge the tradeoffs.
"""

# Repository Overview Prompt
REPOSITORY_OVERVIEW_PROMPT = """
I'm going to provide you with a summary of a code repository. Please analyze the information
and generate an overall assessment of the project's technology stack, architecture, and quality.

Repository Information:
{repo_info}

Primary Technologies:
{primary_technologies}

Detected Technologies:
{technologies}

Architecture Patterns:
{architecture_patterns}

Code Quality:
{code_quality}

Based on this information, please provide:
1. A concise summary of the repository's purpose and main functionality
2. An assessment of the technology choices and their appropriateness
3. Identification of any potential issues or areas for improvement
4. Recommendations for enhancing the repository

Format your response as a JSON object with the following structure:
```json
{{
  "repository_summary": "Concise summary of purpose and functionality",
  "technology_assessment": "Assessment of technology choices",
  "potential_issues": [
    "Issue 1", 
    "Issue 2"
  ],
  "recommendations": [
    {{
      "text": "Recommendation text",
      "priority": "high|medium|low",
      "reason": "Reason for recommendation"
    }}
  ]
}}
```

Be concise, insightful, and practical in your assessment. Focus on high-impact observations
rather than minor details.
"""

# Technology Recommendation Prompt
TECHNOLOGY_RECOMMENDATION_PROMPT = """
Based on the detected technology stack for this repository, please provide recommendations
for improving or complementing the stack with additional technologies.

Current Technology Stack:
{technology_stack}

Please analyze this technology stack and provide recommendations for:
1. Missing technologies that would complement the current stack
2. Potential upgrades or replacements for existing technologies
3. Best practices for the identified tech stack

Format your response as a JSON array of recommendations:
```json
[
  {{
    "text": "Clear recommendation text",
    "severity": "high|medium|low",
    "reason": "Brief reason for this recommendation"
  }}
]
```

Focus on practical, commonly-accepted best practices rather than personal preferences.
Consider compatibility between technologies, industry standards, and modern development practices.
Provide 3-5 specific, actionable recommendations.
"""

# Export prompt templates map for easy access
PROMPT_TEMPLATES = {
    "framework_detection": FRAMEWORK_DETECTION_PROMPT,
    "architecture_detection": ARCHITECTURE_DETECTION_PROMPT,
    "code_quality": CODE_QUALITY_PROMPT,
    "repository_overview": REPOSITORY_OVERVIEW_PROMPT,
    "technology_recommendation": TECHNOLOGY_RECOMMENDATION_PROMPT
}