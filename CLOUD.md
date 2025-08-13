# CodeCompanion Cloud Deployment Guide

## Cloud Platform Overview

CodeCompanion can be deployed on all major cloud platforms with platform-specific optimizations for security, scalability, and cost-effectiveness.

## AWS Deployment

### AWS Elastic Beanstalk (Easiest)

**Quick Deploy:**
```bash
# Install EB CLI
pip install awsebcli

# Initialize application
eb init codecompanion --platform "Python 3.11"

# Create environment
eb create codecompanion-prod --instance-type t3.medium

# Set environment variables
eb setenv \
  ANTHROPIC_API_KEY=your-claude-key \
  OPENAI_API_KEY=your-gpt4-key \
  GEMINI_API_KEY=your-gemini-key \
  CC_LOG_LEVEL=INFO

# Deploy
eb deploy
```

**Ebextensions Configuration:**
```yaml
# .ebextensions/01-codecompanion.config
option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: /var/app/current
    CC_WORKERS: 4
  aws:ec2:instances:
    InstanceTypes: t3.medium,t3.large
  aws:autoscaling:asg:
    MinSize: 1
    MaxSize: 10
  aws:elasticbeanstalk:healthreporting:system:
    SystemType: enhanced
    HealthCheckSuccessThreshold: Ok

container_commands:
  01_install_dependencies:
    command: "pip install -r requirements.txt"
  02_run_migrations:
    command: "python -c 'from database.setup import init_database; init_database()'"
    leader_only: true
```

### AWS ECS with Fargate

**Task Definition:**
```json
{
  "family": "codecompanion",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/codecompanionTaskRole",
  "containerDefinitions": [
    {
      "name": "codecompanion",
      "image": "codecompanion/codecompanion:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "CC_LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:ssm:region:account:parameter/codecompanion/anthropic-key"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:ssm:region:account:parameter/codecompanion/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/codecompanion",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

**ECS Service with ALB:**
```yaml
# cloudformation/ecs-service.yml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  CodeCompanionService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref CodeCompanionTaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          SecurityGroups:
            - !Ref CodeCompanionSecurityGroup
          Subnets:
            - !Ref PrivateSubnet1
            - !Ref PrivateSubnet2
      LoadBalancers:
        - ContainerName: codecompanion
          ContainerPort: 8000
          TargetGroupArn: !Ref CodeCompanionTargetGroup
      HealthCheckGracePeriodSeconds: 120

  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Scheme: internet-facing
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2

  CodeCompanionTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Port: 8000
      Protocol: HTTP
      VpcId: !Ref VPC
      TargetType: ip
      HealthCheckPath: /health
      HealthCheckIntervalSeconds: 30
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 5
```

### AWS Lambda (Serverless)

**Serverless Framework Configuration:**
```yaml
# serverless.yml
service: codecompanion

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  environment:
    CC_LOG_LEVEL: INFO
    CC_SERVERLESS: true
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - ssm:GetParameter
          Resource: 
            - arn:aws:ssm:*:*:parameter/codecompanion/*

functions:
  api:
    handler: lambda_handler.handler
    timeout: 30
    memorySize: 1024
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
      - http:
          path: /
          method: ANY
          cors: true

plugins:
  - serverless-python-requirements
  - serverless-wsgi

custom:
  wsgi:
    app: app.app
  pythonRequirements:
    dockerizePip: true
    slim: true
```

**Lambda Handler:**
```python
# lambda_handler.py
import json
from mangum import Mangum
from app import app

handler = Mangum(app)

def lambda_handler(event, context):
    """AWS Lambda handler for CodeCompanion"""
    return handler(event, context)
```

## Google Cloud Platform (GCP)

### Cloud Run (Serverless Containers)

**Deploy to Cloud Run:**
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/codecompanion

# Deploy to Cloud Run
gcloud run deploy codecompanion \
  --image gcr.io/PROJECT-ID/codecompanion \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --port 8000 \
  --set-env-vars CC_LOG_LEVEL=INFO \
  --set-secrets ANTHROPIC_API_KEY=anthropic-key:latest,OPENAI_API_KEY=openai-key:latest
```

**Cloud Run YAML:**
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: codecompanion
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/PROJECT-ID/codecompanion
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
        env:
        - name: CC_LOG_LEVEL
          value: "INFO"
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              key: latest
              name: anthropic-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              key: latest
              name: openai-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
```

### Google Kubernetes Engine (GKE)

**GKE Cluster Setup:**
```bash
# Create cluster
gcloud container clusters create codecompanion-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --machine-type e2-medium

# Get credentials
gcloud container clusters get-credentials codecompanion-cluster --zone us-central1-a

# Deploy application
kubectl apply -f kubernetes/
```

### App Engine

**app.yaml:**
```yaml
runtime: python311

env_variables:
  CC_LOG_LEVEL: INFO
  CC_WORKERS: 4

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 1
  disk_size_gb: 10

health_check:
  enable_health_check: true
  check_interval_sec: 30
  timeout_sec: 4
  unhealthy_threshold: 2
  healthy_threshold: 2
```

**Deploy:**
```bash
gcloud app deploy --version production
```

## Microsoft Azure

### Azure Container Instances (ACI)

**Deploy with Azure CLI:**
```bash
# Create resource group
az group create --name codecompanion-rg --location eastus

# Create container instance
az container create \
  --resource-group codecompanion-rg \
  --name codecompanion \
  --image codecompanion/codecompanion:latest \
  --dns-name-label codecompanion-unique \
  --ports 8000 \
  --environment-variables CC_LOG_LEVEL=INFO \
  --secure-environment-variables \
    ANTHROPIC_API_KEY=your-claude-key \
    OPENAI_API_KEY=your-gpt4-key \
  --cpu 1 \
  --memory 2
```

**ARM Template:**
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "resources": [
    {
      "type": "Microsoft.ContainerInstance/containerGroups",
      "apiVersion": "2021-07-01",
      "name": "codecompanion",
      "location": "[resourceGroup().location]",
      "properties": {
        "containers": [
          {
            "name": "codecompanion",
            "properties": {
              "image": "codecompanion/codecompanion:latest",
              "ports": [
                {
                  "port": 8000,
                  "protocol": "TCP"
                }
              ],
              "environmentVariables": [
                {
                  "name": "CC_LOG_LEVEL",
                  "value": "INFO"
                }
              ],
              "resources": {
                "requests": {
                  "cpu": 1,
                  "memoryInGB": 2
                }
              }
            }
          }
        ],
        "osType": "Linux",
        "ipAddress": {
          "type": "Public",
          "ports": [
            {
              "port": 8000,
              "protocol": "TCP"
            }
          ],
          "dnsNameLabel": "codecompanion-unique"
        }
      }
    }
  ]
}
```

### Azure App Service

**Deploy from Docker Hub:**
```bash
# Create App Service plan
az appservice plan create \
  --name codecompanion-plan \
  --resource-group codecompanion-rg \
  --sku B2 \
  --is-linux

# Create web app
az webapp create \
  --resource-group codecompanion-rg \
  --plan codecompanion-plan \
  --name codecompanion-app \
  --deployment-container-image-name codecompanion/codecompanion:latest

# Configure container settings
az webapp config appsettings set \
  --resource-group codecompanion-rg \
  --name codecompanion-app \
  --settings \
    WEBSITES_PORT=8000 \
    CC_LOG_LEVEL=INFO \
    ANTHROPIC_API_KEY=your-claude-key \
    OPENAI_API_KEY=your-gpt4-key
```

### Azure Kubernetes Service (AKS)

**Create AKS Cluster:**
```bash
# Create AKS cluster
az aks create \
  --resource-group codecompanion-rg \
  --name codecompanion-aks \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials \
  --resource-group codecompanion-rg \
  --name codecompanion-aks

# Deploy application
kubectl apply -f kubernetes/
```

## Heroku Deployment

### Container Deployment

**heroku.yml:**
```yaml
build:
  docker:
    web: Dockerfile
run:
  web: python -m uvicorn app:app --host 0.0.0.0 --port $PORT
```

**Deploy Commands:**
```bash
# Login to Heroku
heroku login

# Create app
heroku create codecompanion-app

# Set stack to container
heroku stack:set container

# Set environment variables
heroku config:set \
  ANTHROPIC_API_KEY=your-claude-key \
  OPENAI_API_KEY=your-gpt4-key \
  CC_LOG_LEVEL=INFO

# Deploy
git push heroku main

# Scale dynos
heroku ps:scale web=2
```

### Buildpack Deployment

**Procfile:**
```
web: python -m uvicorn app:app --host 0.0.0.0 --port $PORT
worker: python -m codecompanion.worker
```

**runtime.txt:**
```
python-3.11.0
```

## DigitalOcean

### App Platform

**app.yaml:**
```yaml
name: codecompanion
services:
- name: web
  source_dir: /
  github:
    repo: your-username/codecompanion
    branch: main
  run_command: python -m uvicorn app:app --host 0.0.0.0 --port 8080
  environment_slug: python
  instance_count: 2
  instance_size_slug: basic-xxs
  http_port: 8080
  health_check:
    http_path: /health
  envs:
  - key: CC_LOG_LEVEL
    value: INFO
  - key: ANTHROPIC_API_KEY
    value: your-claude-key
    type: SECRET
  - key: OPENAI_API_KEY
    value: your-gpt4-key
    type: SECRET

databases:
- name: codecompanion-db
  engine: PG
  version: "14"
  size: db-s-dev-database
```

### Kubernetes (DOKS)

**Deploy to DOKS:**
```bash
# Install doctl
snap install doctl

# Authenticate
doctl auth init

# Create cluster
doctl kubernetes cluster create codecompanion-cluster \
  --region nyc1 \
  --size s-2vcpu-2gb \
  --count 3

# Get kubeconfig
doctl kubernetes cluster kubeconfig save codecompanion-cluster

# Deploy application
kubectl apply -f kubernetes/
```

## Multi-Cloud Deployment

### Terraform Configuration

**main.tf:**
```hcl
# Multi-cloud Terraform configuration
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# AWS deployment
module "aws_deployment" {
  source = "./modules/aws"
  
  instance_type = var.aws_instance_type
  api_keys = var.api_keys
}

# GCP deployment
module "gcp_deployment" {
  source = "./modules/gcp"
  
  project_id = var.gcp_project_id
  region = var.gcp_region
  api_keys = var.api_keys
}

# Azure deployment
module "azure_deployment" {
  source = "./modules/azure"
  
  resource_group = var.azure_resource_group
  location = var.azure_location
  api_keys = var.api_keys
}
```

## Cost Optimization

### AWS Cost Optimization

```bash
# Use Spot Instances for development
aws ec2 request-spot-instances \
  --spot-price "0.05" \
  --instance-count 1 \
  --type "one-time" \
  --launch-specification file://launch-spec.json

# Auto-scaling policies
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/codecompanion-cluster/codecompanion \
  --min-capacity 1 \
  --max-capacity 10
```

### GCP Cost Optimization

```bash
# Use preemptible instances
gcloud compute instances create codecompanion-instance \
  --preemptible \
  --machine-type e2-medium \
  --zone us-central1-a

# Set up autoscaling
gcloud compute instance-groups managed set-autoscaling codecompanion-ig \
  --max-num-replicas 10 \
  --min-num-replicas 1 \
  --target-cpu-utilization 0.6
```

## Monitoring and Logging

### Cloud-Native Monitoring

**AWS CloudWatch:**
```yaml
# cloudwatch-dashboard.yml
DashboardBody: |
  {
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "codecompanion"],
            [".", "MemoryUtilization", ".", "."]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "ECS Service Metrics"
        }
      }
    ]
  }
```

**GCP Monitoring:**
```bash
# Create alerting policy
gcloud alpha monitoring policies create \
  --policy-from-file=monitoring-policy.json
```

**Azure Monitor:**
```bash
# Create action group
az monitor action-group create \
  --resource-group codecompanion-rg \
  --name codecompanion-alerts \
  --short-name cc-alerts
```

## Security Best Practices

### Secret Management

**AWS Secrets Manager:**
```bash
# Store API keys
aws secretsmanager create-secret \
  --name codecompanion/api-keys \
  --description "CodeCompanion API Keys" \
  --secret-string '{"anthropic": "sk-ant-...", "openai": "sk-..."}'
```

**GCP Secret Manager:**
```bash
# Create secrets
echo "sk-ant-..." | gcloud secrets create anthropic-api-key --data-file=-
echo "sk-..." | gcloud secrets create openai-api-key --data-file=-
```

**Azure Key Vault:**
```bash
# Create key vault
az keyvault create \
  --name codecompanion-vault \
  --resource-group codecompanion-rg \
  --location eastus

# Store secrets
az keyvault secret set \
  --vault-name codecompanion-vault \
  --name anthropic-api-key \
  --value "sk-ant-..."
```

## Disaster Recovery

### Backup Strategies

**Multi-Region Backup:**
```bash
# AWS S3 cross-region replication
aws s3api put-bucket-replication \
  --bucket codecompanion-backups \
  --replication-configuration file://replication.json

# GCP Cloud Storage multi-region
gsutil cp -r gs://codecompanion-primary/* gs://codecompanion-backup/

# Azure Blob Storage geo-redundancy
az storage account create \
  --name codecompanionbackup \
  --resource-group codecompanion-rg \
  --sku Standard_GRS
```

This comprehensive cloud deployment guide provides platform-specific instructions for deploying CodeCompanion across all major cloud providers with security, scalability, and cost optimization in mind.