"""
DevOps Detector module for repository analysis.

This module identifies DevOps tools and practices in a repository, including:
- Containerization (Docker, Kubernetes, etc.)
- CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins, etc.)
- Infrastructure as Code (Terraform, CloudFormation, Pulumi, etc.)
- Configuration management (Ansible, Chef, Puppet, etc.)
- Monitoring and logging solutions
- Cloud provider specific configurations
"""

import os
import re
from collections import defaultdict
from typing import Dict, List, Any

class DevOpsDetector:
    """
    Detector for DevOps tools and practices used in a repository.
    
    This class identifies containerization, CI/CD, infrastructure as code,
    configuration management, monitoring, and cloud-specific technologies
    by examining configuration files, scripts, and code patterns.
    """
    
    def __init__(self):
        """Initialize the DevOps Detector with detection patterns."""
        # Containerization files and directories
        self.containerization_files = {
            "Docker": [
                "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
                ".dockerignore", "docker-entrypoint.sh", ".docker",
                "docker-compose.override.yml", "docker-stack.yml"
            ],
            "Kubernetes": [
                "kubernetes/", "k8s/", "charts/", "manifests/",
                "deployment.yaml", "service.yaml", "ingress.yaml", "configmap.yaml",
                "statefulset.yaml", "daemonset.yaml", "job.yaml", "cronjob.yaml",
                "pod.yaml", "replicaset.yaml", "deployment.yml", "service.yml",
                "kustomization.yaml", "kustomization.yml", "Chart.yaml"
            ],
            "Helm": [
                "Chart.yaml", "values.yaml", "templates/", "charts/",
                "helm/", ".helmignore", "requirements.yaml"
            ],
            "Podman": [
                "podman-compose.yml", "podman-compose.yaml", "podman-docker-compose.yml"
            ],
            "Buildah": [
                "buildah.sh", "buildah-script.sh"
            ],
            "Skaffold": [
                "skaffold.yaml", "skaffold.yml"
            ],
            "OpenShift": [
                "openshift/", "template.yaml", "template.yml", "buildconfig.yaml",
                "route.yaml", "route.yml", "imagestream.yaml", "imagestream.yml"
            ],
            "Istio": [
                "istio/", "VirtualService.yaml", "Gateway.yaml", "ServiceEntry.yaml",
                "DestinationRule.yaml", "EnvoyFilter.yaml"
            ],
            "Containerd": [
                "containerd.toml", "containerd.conf", "config.toml"
            ],
            "Docker Swarm": [
                "docker-stack.yml", "docker-stack.yaml"
            ],
            "Docker Compose": [
                "docker-compose.yml", "docker-compose.yaml"
            ]
        }
        
        # CI/CD files and directories
        self.cicd_files = {
            "GitHub Actions": [
                ".github/workflows/", ".github/actions/", ".github/workflows/*.yml",
                ".github/workflows/*.yaml", "action.yml", "action.yaml"
            ],
            "GitLab CI": [
                ".gitlab-ci.yml", ".gitlab-ci.yaml", ".gitlab/", "gitlab-ci.yml"
            ],
            "Jenkins": [
                "Jenkinsfile", "jenkins/", "jenkins.yaml", "jenkins.yml",
                "pipeline.jenkins", "jenkins-pipeline.groovy"
            ],
            "Travis CI": [
                ".travis.yml", ".travis.yaml"
            ],
            "CircleCI": [
                ".circleci/", ".circleci/config.yml", ".circleci/config.yaml",
                "circle.yml"
            ],
            "Azure Pipelines": [
                "azure-pipelines.yml", "azure-pipelines.yaml", ".azure-pipelines/",
                ".azure-pipelines.yml", ".azure-pipelines.yaml"
            ],
            "AWS CodePipeline": [
                "buildspec.yml", "buildspec.yaml", "appspec.yml", "appspec.yaml"
            ],
            "Bitbucket Pipelines": [
                "bitbucket-pipelines.yml", "bitbucket-pipelines.yaml"
            ],
            "Bamboo": [
                "bamboo-specs/", "bamboo-specs.yml", "bamboo-specs.yaml"
            ],
            "TeamCity": [
                ".teamcity/", "teamcity-build.xml", "teamcity-settings.kts"
            ],
            "Drone": [
                ".drone.yml", ".drone.yaml"
            ],
            "GoCD": [
                ".gocd.yml", ".gocd.yaml"
            ],
            "Concourse": [
                "pipeline.yml", "concourse/", "ci/pipeline.yml"
            ],
            "ArgoCD": [
                "argocd/", "argo-cd/", "application.yaml", "application.yml"
            ],
            "FluxCD": [
                "flux/", "flux-system/", "gotk-components.yaml", "kustomization.yaml"
            ],
            "Tekton": [
                "tekton/", "task.yaml", "pipeline.yaml", "pipelinerun.yaml"
            ],
            "Spinnaker": [
                "spinnaker/", "pipeline.json"
            ]
        }
        
        # Infrastructure as Code files
        self.iac_files = {
            "Terraform": [
                "*.tf", "terraform/", "modules/", "terraform.tfstate",
                "terraform.tfvars", "variables.tf", "outputs.tf", "main.tf",
                ".terraform/", ".terraform.lock.hcl"
            ],
            "CloudFormation": [
                "*.template", "*.template.json", "*.template.yaml", "*.template.yml",
                "cloudformation/", "cf/", "stack.json", "stack.yaml", "stack.yml"
            ],
            "AWS CDK": [
                "cdk.json", "cdk.context.json", "cdk.out/", "lib/", "bin/cdk.ts"
            ],
            "Pulumi": [
                "Pulumi.yaml", "Pulumi.yml", "pulumi/", "index.ts", "__main__.py",
                "Pulumi.*.yaml"
            ],
            "Serverless Framework": [
                "serverless.yml", "serverless.yaml", "serverless.json", ".serverless/"
            ],
            "Ansible": [
                "ansible/", "playbooks/", "roles/", "inventory/", "hosts",
                "ansible.cfg", "site.yml", "main.yml", "requirements.yml", "tasks/"
            ],
            "Chef": [
                "chef/", "cookbooks/", "recipes/", "kitchen.yml", "Berksfile",
                "metadata.rb", "recipes/default.rb"
            ],
            "Puppet": [
                "puppet/", "manifests/", "modules/", "Puppetfile",
                "environments/", "site.pp"
            ],
            "Salt": [
                "salt/", "pillar/", "states/", "reactor/", "top.sls",
                "Saltfile", "minion", "master"
            ],
            "Packer": [
                "*.pkr.hcl", "packer.json", "templates/", "packer/"
            ],
            "Vagrant": [
                "Vagrantfile", ".vagrant/"
            ],
            "Bicep": [
                "*.bicep", "bicep/", "main.bicep", "modules/"
            ],
            "AWS SAM": [
                "template.yaml", "sam.yaml", "samconfig.toml", "sam.toml"
            ],
            "Crossplane": [
                "crossplane/", "composition.yaml", "definition.yaml"
            ],
            "Kustomize": [
                "kustomization.yaml", "kustomization.yml", "kustomize/", "base/", "overlays/"
            ]
        }
        
        # Monitoring and logging files
        self.monitoring_files = {
            "Prometheus": [
                "prometheus.yml", "prometheus.yaml", "prometheus/", "rules/",
                "alerts.yml", "alerts.yaml", "rules.yml", "rules.yaml"
            ],
            "Grafana": [
                "grafana/", "dashboards/", "datasources/", "grafana.ini",
                "dashboard.json", "datasource.yaml", "datasource.yml"
            ],
            "ELK Stack": [
                "elasticsearch/", "kibana/", "logstash/", "elasticsearch.yml",
                "kibana.yml", "logstash.conf", "filebeat.yml", "metricbeat.yml"
            ],
            "Loki": [
                "loki/", "loki.yaml", "loki-config.yaml", "promtail.yaml"
            ],
            "Jaeger": [
                "jaeger/", "jaeger.yaml", "tracing.yaml"
            ],
            "New Relic": [
                "newrelic.yml", "newrelic.yaml", "newrelic.config.js"
            ],
            "Datadog": [
                "datadog/", "datadog.yaml", "datadog.yml"
            ],
            "Fluentd": [
                "fluentd/", "fluent.conf", "fluentd.conf"
            ],
            "Graylog": [
                "graylog/", "graylog.conf", "graylog-server.json"
            ],
            "StatsD": [
                "statsd/", "statsd.conf"
            ]
        }
        
        # Cloud provider specific files
        self.cloud_files = {
            "AWS": [
                ".aws/", "aws-config.json", "aws/", "cloudformation/",
                "s3/", "lambda/", "ec2/", "ecs/", "eks/", "rds/"
            ],
            "Google Cloud": [
                ".gcp/", "gcp/", "gcloud/", "app.yaml", "cloudbuild.yaml",
                "cloudfunctions/", "appengine/", "gke/"
            ],
            "Azure": [
                "azure/", ".azure/", "azuredeploy.json", "azuredeploy.parameters.json",
                "arm-templates/", "azure-pipelines.yml"
            ],
            "Digital Ocean": [
                ".do/", "digitalocean/", "do/"
            ],
            "Heroku": [
                "Procfile", "app.json", "heroku.yml"
            ],
            "IBM Cloud": [
                ".bluemix/", "manifest.yml", "cloud-functions/"
            ],
            "Alibaba Cloud": [
                "aliyun/", "acs/", "ros-templates/"
            ],
            "Oracle Cloud": [
                "oci/", "oracle/", "oci-config"
            ],
            "Vercel": [
                "vercel.json", ".vercel/", "now.json"
            ],
            "Netlify": [
                "netlify.toml", ".netlify/"
            ],
            "Firebase": [
                "firebase.json", ".firebaserc", "firestore.rules", "firestore.indexes.json"
            ]
        }
        
        # DevOps content patterns
        self.devops_patterns = {
            "Docker": [
                r"FROM\s+\w+", r"WORKDIR\s+", r"EXPOSE\s+\d+", r"ENTRYPOINT\s+",
                r"VOLUME\s+", r"RUN\s+", r"docker run", r"docker-compose up"
            ],
            "Kubernetes": [
                r"apiVersion:", r"kind:\s+Deployment", r"kind:\s+Service", r"kubectl apply",
                r"kubectl get", r"kind:\s+Pod", r"kind:\s+ConfigMap"
            ],
            "Terraform": [
                r"provider\s+\"", r"resource\s+\"", r"module\s+\"", r"variable\s+\"",
                r"output\s+\"", r"terraform\s+{", r"locals\s+{"
            ],
            "AWS": [
                r"aws_\w+", r"AWS::CloudFormation::Stack", r"AWS::Lambda::",
                r"AWS::EC2::", r"AWS::S3::", r"AWS::DynamoDB::"
            ],
            "Google Cloud": [
                r"google_\w+", r"gcloud\s+", r"GOOGLE_CLOUD", r"GCP_",
                r"Google\s+Cloud\s+Platform"
            ],
            "Azure": [
                r"azurerm_\w+", r"az\s+", r"AZURE_", r"Microsoft.Storage",
                r"Microsoft.Compute", r"Microsoft.Network"
            ],
            "CI/CD": [
                r"steps:", r"jobs:", r"pipeline:", r"stages:", r"on:\s+push",
                r"on:\s+pull_request", r"workflow_dispatch", r"build:", r"test:", r"deploy:"
            ]
        }
    
    # NEW METHOD: Validate DevOps matches to reduce false positives
    def _validate_devops_matches(self, devops_matches, files, files_content):
        """Apply validation rules to reduce false positives in DevOps tool detection."""
        
        # Validate Helm detection
        if "Helm" in devops_matches:
            # Helm requires a Chart.yaml file with specific fields
            has_chart_yaml = False
            has_helm_structure = False
            
            for file_path, content in files_content.items():
                if file_path.endswith("Chart.yaml") or file_path.endswith("Chart.yml"):
                    if re.search(r"apiVersion:.*helm", content, re.IGNORECASE):
                        has_chart_yaml = True
                    
            # Check for templates directory structure
            has_templates_dir = any("templates/" in file for file in files)
            has_values_yaml = any(file.endswith("values.yaml") or file.endswith("values.yml") for file in files)
            
            has_helm_structure = has_chart_yaml or (has_templates_dir and has_values_yaml)
            
            # If not a valid Helm chart, significantly reduce confidence
            if not has_helm_structure:
                devops_matches["Helm"] = devops_matches.get("Helm", 0) // 10
        
        # Validate Packer detection
        if "Packer" in devops_matches:
            # Packer requires specific JSON or HCL structure
            packer_patterns = [
                r"\"builders\":\s*\[", r"\"provisioners\":\s*\[",
                r"source\s+\".*\"\s+\".*\"\s+{", r"build\s+{"
            ]
            
            has_packer_structure = False
            for _, content in files_content.items():
                if any(re.search(pattern, content) for pattern in packer_patterns):
                    has_packer_structure = True
                    break
            
            # If no specific Packer structure, significantly reduce confidence
            if not has_packer_structure:
                devops_matches["Packer"] = devops_matches.get("Packer", 0) // 10
    
    def detect(self, files: List[str], files_content: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Detect DevOps tools and practices used in the repository.
        
        This method examines file names, paths, and contents to identify
        containerization, CI/CD, infrastructure as code, monitoring, and
        cloud-specific technologies used in the project.
        
        Args:
            files: List of file paths in the repository
            files_content: Dict mapping file paths to their content
            
        Returns:
            Dict mapping DevOps technology names to dicts containing:
                - matches: Number of pattern matches found
                - confidence: Confidence score (0-100)
                - category: Category of the DevOps technology
                    (containerization, cicd, iac, monitoring, cloud)
        """
        # Track matches for DevOps technologies
        devops_matches = defaultdict(int)
        devops_categories = {}
        devops_evidence = defaultdict(list)
        
        # Step 1: Check for DevOps technology files
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # Check for containerization files
            for tech, patterns in self.containerization_files.items():
                if filename in patterns:
                    devops_matches[tech] += 15  # High weight for exact match
                    devops_categories[tech] = "containerization"
                    devops_evidence[tech].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns):
                    devops_matches[tech] += 10  # Medium weight for partial match
                    devops_categories[tech] = "containerization"
                    devops_evidence[tech].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns):
                    devops_matches[tech] += 5  # Lower weight for path match
                    devops_categories[tech] = "containerization"
                    devops_evidence[tech].append(f"Found pattern in path: {file_path}")
            
            # Check for CI/CD files
            for tech, patterns in self.cicd_files.items():
                if filename in patterns:
                    devops_matches[tech] += 15
                    devops_categories[tech] = "cicd"
                    devops_evidence[tech].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns):
                    devops_matches[tech] += 10
                    devops_categories[tech] = "cicd"
                    devops_evidence[tech].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns):
                    devops_matches[tech] += 5
                    devops_categories[tech] = "cicd"
                    devops_evidence[tech].append(f"Found pattern in path: {file_path}")
            
            # Check for infrastructure as code files
            for tech, patterns in self.iac_files.items():
                # Check for file extensions (*.tf, *.yml, etc.)
                for pattern in patterns:
                    if pattern.startswith("*."):
                        ext = pattern[1:]  # Remove the *
                        if filename.endswith(ext):
                            devops_matches[tech] += 15
                            devops_categories[tech] = "iac"
                            devops_evidence[tech].append(f"Found file with extension: {filename}")
                            break
                
                # Check for exact filename matches
                if filename in patterns:
                    devops_matches[tech] += 15
                    devops_categories[tech] = "iac"
                    devops_evidence[tech].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns if not pattern.startswith("*.")):
                    devops_matches[tech] += 10
                    devops_categories[tech] = "iac"
                    devops_evidence[tech].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns if not pattern.startswith("*.")):
                    devops_matches[tech] += 5
                    devops_categories[tech] = "iac"
                    devops_evidence[tech].append(f"Found pattern in path: {file_path}")
            
            # Check for monitoring and logging files
            for tech, patterns in self.monitoring_files.items():
                if filename in patterns:
                    devops_matches[tech] += 15
                    devops_categories[tech] = "monitoring"
                    devops_evidence[tech].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns):
                    devops_matches[tech] += 10
                    devops_categories[tech] = "monitoring"
                    devops_evidence[tech].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns):
                    devops_matches[tech] += 5
                    devops_categories[tech] = "monitoring"
                    devops_evidence[tech].append(f"Found pattern in path: {file_path}")
            
            # Check for cloud provider specific files
            for provider, patterns in self.cloud_files.items():
                if filename in patterns:
                    devops_matches[provider] += 15
                    devops_categories[provider] = "cloud"
                    devops_evidence[provider].append(f"Found file: {filename}")
                elif any(pattern in filename for pattern in patterns):
                    devops_matches[provider] += 10
                    devops_categories[provider] = "cloud"
                    devops_evidence[provider].append(f"Found pattern in filename: {filename}")
                elif any(pattern in file_path for pattern in patterns):
                    devops_matches[provider] += 5
                    devops_categories[provider] = "cloud"
                    devops_evidence[provider].append(f"Found pattern in path: {file_path}")
        
        # Step 2: Check file content for DevOps patterns
        for file_path, content in files_content.items():
            # Skip large files
            if len(content) > 500000:  # Skip files over 500KB
                continue
            
            # Check for DevOps patterns in content
            for tech, patterns in self.devops_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        match_count = len(matches)
                        if match_count > 10:
                            # Cap at 10 to avoid a single file dominating
                            match_count = 10
                        devops_matches[tech] += match_count
                        
                        # Extract category if not already set
                        if tech not in devops_categories:
                            # Try to determine category
                            if tech in self.containerization_files:
                                devops_categories[tech] = "containerization"
                            elif tech in self.cicd_files:
                                devops_categories[tech] = "cicd"
                            elif tech in self.iac_files:
                                devops_categories[tech] = "iac"
                            elif tech in self.monitoring_files:
                                devops_categories[tech] = "monitoring"
                            elif tech in self.cloud_files:
                                devops_categories[tech] = "cloud"
                            else:
                                devops_categories[tech] = "other"
                        
                        # Add pattern match as evidence
                        if matches:
                            match_text = matches[0]
                            if len(match_text) > 60:  # Truncate long matches
                                match_text = match_text[:57] + "..."
                            devops_evidence[tech].append(f"Pattern match: {match_text}")
            
            # Special case for Dockerfiles (they may not have standard names)
            if "FROM " in content and "RUN " in content:
                if "WORKDIR " in content or "COPY " in content or "CMD " in content:
                    devops_matches["Docker"] += 15
                    devops_categories["Docker"] = "containerization"
                    devops_evidence["Docker"].append(f"Found Dockerfile-like content in: {os.path.basename(file_path)}")
            
            # Special case for Kubernetes YAML
            if "apiVersion: " in content and "kind: " in content:
                if "metadata:" in content and "spec:" in content:
                    devops_matches["Kubernetes"] += 15
                    devops_categories["Kubernetes"] = "containerization"
                    devops_evidence["Kubernetes"].append(f"Found Kubernetes manifest in: {os.path.basename(file_path)}")
            
            # Special case for GitHub Actions workflow
            if "name: " in content and "on: " in content and "jobs:" in content:
                if "steps:" in content and "uses: " in content:
                    devops_matches["GitHub Actions"] += 15
                    devops_categories["GitHub Actions"] = "cicd"
                    devops_evidence["GitHub Actions"].append(f"Found GitHub Actions workflow in: {os.path.basename(file_path)}")
        
        # Step 3: Post-processing for multi-platform technologies
        # Docker Compose implies Docker
        if "Docker Compose" in devops_matches and "Docker" in devops_matches:
            # Ensure Docker has at least the same confidence as Docker Compose
            if devops_matches["Docker"] < devops_matches["Docker Compose"]:
                devops_matches["Docker"] = max(devops_matches["Docker"], devops_matches["Docker Compose"] - 5)
        
        # Helm implies Kubernetes
        if "Helm" in devops_matches and "Kubernetes" in devops_matches:
            # Ensure Kubernetes has at least the same confidence as Helm
            if devops_matches["Kubernetes"] < devops_matches["Helm"]:
                devops_matches["Kubernetes"] = max(devops_matches["Kubernetes"], devops_matches["Helm"] - 5)
        
        # AWS CDK implies AWS
        if "AWS CDK" in devops_matches:
            devops_matches["AWS"] = max(devops_matches.get("AWS", 0), devops_matches["AWS CDK"] - 5)
            devops_categories["AWS"] = "cloud"
        
        # Step 3b: Apply validation to reduce false positives
        self._validate_devops_matches(devops_matches, files, files_content)
        
        # Step 4: Calculate confidence scores
        devops_technologies = {}
        
        if devops_matches:
            # Find maximum number of matches for normalization
            max_matches = max(devops_matches.values())
            
            for tech, matches in devops_matches.items():
                # Calculate confidence score (0-100)
                confidence = min(100, (matches / max_matches) * 100)
                
                # Only include technologies with reasonable confidence
                # Increased threshold from 15 to 40 to reduce false positives
                if confidence >= 40:
                    # Keep only unique evidence and limit to 5 examples
                    unique_evidence = list(dict.fromkeys(devops_evidence[tech]))[:5]
                    
                    devops_technologies[tech] = {
                        "matches": matches,
                        "confidence": round(confidence, 2),
                        "category": devops_categories.get(tech, "other"),
                        "evidence": unique_evidence
                    }
        
        return devops_technologies