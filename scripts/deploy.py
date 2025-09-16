#!/usr/bin/env python3
"""
Deployment utilities for AI4SupplyChain
"""
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime


def run_command(command, description="", check=True, capture_output=False):
    """Run a shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        if capture_output and result.stdout:
            return result.stdout.strip()
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if capture_output and e.stderr:
            print(f"Error details: {e.stderr}")
        return False


def check_deployment_prerequisites():
    """Check if deployment tools are available"""
    print("🔍 Checking deployment prerequisites...")
    
    prerequisites = {
        "docker": "Docker for containerization",
        "docker-compose": "Docker Compose for multi-service deployment"
    }
    
    missing = []
    for tool, description in prerequisites.items():
        if not shutil.which(tool):
            print(f"❌ {tool} not found - {description}")
            missing.append(tool)
        else:
            print(f"✅ {tool} found")
    
    if missing:
        print(f"\n📋 Install missing tools:")
        print("   Docker: https://docs.docker.com/get-docker/")
        print("   Docker Compose: https://docs.docker.com/compose/install/")
        return False
    
    return True


def build_docker_image(tag="ai4supplychain:latest"):
    """Build Docker image"""
    print(f"\n🐳 Building Docker image: {tag}")
    
    # Check if Dockerfile exists
    if not Path("Dockerfile").exists():
        print("❌ Dockerfile not found")
        return False
    
    # Build image
    build_cmd = f"docker build -t {tag} ."
    return run_command(build_cmd, f"Building Docker image {tag}")


def run_docker_container(tag="ai4supplychain:latest", port=8000, detached=True):
    """Run Docker container"""
    print(f"\n🚀 Running Docker container from {tag}")
    
    # Check if .env file exists
    env_file_arg = ""
    if Path(".env").exists():
        env_file_arg = "--env-file .env"
    
    # Run container
    detach_arg = "-d" if detached else ""
    run_cmd = f"docker run {detach_arg} -p {port}:8000 {env_file_arg} --name ai4supplychain-app {tag}"
    
    return run_command(run_cmd, f"Starting container on port {port}")


def deploy_with_docker_compose(environment="development"):
    """Deploy using Docker Compose"""
    print(f"\n🐙 Deploying with Docker Compose ({environment})...")
    
    # Check if docker-compose.yml exists
    if not Path("docker-compose.yml").exists():
        print("❌ docker-compose.yml not found")
        return False
    
    # Set environment
    env_vars = {
        "COMPOSE_PROJECT_NAME": "ai4supplychain",
        "ENVIRONMENT": environment
    }
    
    # Update environment
    current_env = os.environ.copy()
    current_env.update(env_vars)
    
    # Deploy
    deploy_cmd = "docker-compose up -d --build"
    result = subprocess.run(
        deploy_cmd, 
        shell=True, 
        check=True,
        env=current_env
    )
    
    if result.returncode == 0:
        print("✅ Docker Compose deployment successful")
        print("\n📋 Services status:")
        run_command("docker-compose ps", "Checking service status")
        return True
    
    return False


def create_production_config():
    """Create production configuration files"""
    print("\n⚙️ Creating production configuration...")
    
    # Create production .env template
    prod_env_content = """# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@db:5432/ai4supplychain

# LLM APIs (Choose one or both)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
PRIMARY_LLM_PROVIDER=openai

# OCR Provider (Choose one)
OCR_PROVIDER=tesseract
GOOGLE_CLOUD_VISION_CREDENTIALS=path/to/credentials.json
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Security
SECRET_KEY=your_super_secret_key_change_this_in_production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=storage/logs/app.log

# Performance
WORKERS=4
MAX_CONNECTIONS=100
"""
    
    with open(".env.production", "w") as f:
        f.write(prod_env_content)
    
    print("✅ Created .env.production template")
    
    # Create production docker-compose override
    prod_compose_content = """version: '3.8'

services:
  web:
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    restart: unless-stopped
    
  db:
    environment:
      - POSTGRES_DB=ai4supplychain_prod
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_prod_data:
"""
    
    with open("docker-compose.prod.yml", "w") as f:
        f.write(prod_compose_content)
    
    print("✅ Created docker-compose.prod.yml")
    
    return True


def backup_database(backup_dir="storage/exports/backups"):
    """Create database backup"""
    print(f"\n💾 Creating database backup...")
    
    # Create backup directory
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(backup_dir) / f"backup_{timestamp}.sql"
    
    # For SQLite (development)
    sqlite_db = Path("storage/database/inventory.db")
    if sqlite_db.exists():
        backup_sqlite = Path(backup_dir) / f"inventory_backup_{timestamp}.db"
        shutil.copy2(sqlite_db, backup_sqlite)
        print(f"✅ SQLite backup created: {backup_sqlite}")
    
    # For PostgreSQL (production)
    pg_backup_cmd = f"docker-compose exec -T db pg_dump -U postgres ai4supplychain > {backup_file}"
    result = run_command(pg_backup_cmd, "Creating PostgreSQL backup", check=False)
    
    if result and backup_file.exists():
        print(f"✅ PostgreSQL backup created: {backup_file}")
    
    return True


def deploy_to_cloud(provider="docker", **kwargs):
    """Deploy to cloud provider"""
    print(f"\n☁️ Deploying to {provider}...")
    
    if provider == "docker":
        # Generic Docker deployment
        return build_docker_image() and run_docker_container()
    
    elif provider == "heroku":
        print("📋 Heroku deployment steps:")
        print("1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli")
        print("2. heroku create your-app-name")
        print("3. heroku addons:create heroku-postgresql:hobby-dev")
        print("4. heroku config:set OPENAI_API_KEY=your_key")
        print("5. git push heroku main")
        return True
    
    elif provider == "aws":
        print("📋 AWS deployment options:")
        print("1. AWS ECS with Fargate")
        print("2. AWS Elastic Beanstalk")
        print("3. AWS EC2 with Docker")
        print("4. AWS Lambda (for API only)")
        return True
    
    elif provider == "gcp":
        print("📋 Google Cloud deployment options:")
        print("1. Google Cloud Run")
        print("2. Google Kubernetes Engine (GKE)")
        print("3. Google Compute Engine")
        return True
    
    else:
        print(f"❌ Unknown provider: {provider}")
        return False


def health_check(url="http://localhost:8000/health"):
    """Perform deployment health check"""
    print(f"\n🏥 Performing health check on {url}...")
    
    try:
        import requests
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
    except ImportError:
        print("⚠️ requests library not available, using curl")
        return run_command(f"curl -f {url}", "Health check with curl", check=False)
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def rollback_deployment(backup_tag="previous"):
    """Rollback to previous deployment"""
    print(f"\n🔄 Rolling back to {backup_tag}...")
    
    rollback_commands = [
        f"docker stop ai4supplychain-app",
        f"docker rm ai4supplychain-app",
        f"docker run -d -p 8000:8000 --name ai4supplychain-app ai4supplychain:{backup_tag}"
    ]
    
    for cmd in rollback_commands:
        result = run_command(cmd, f"Rollback step: {cmd}", check=False)
        if not result:
            print("⚠️ Rollback step failed, continuing...")
    
    return health_check()


def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI4SupplyChain deployment utilities")
    parser.add_argument("--build", action="store_true", help="Build Docker image")
    parser.add_argument("--run", action="store_true", help="Run Docker container")
    parser.add_argument("--compose", action="store_true", help="Deploy with Docker Compose")
    parser.add_argument("--environment", default="development", choices=["development", "staging", "production"])
    parser.add_argument("--backup", action="store_true", help="Create database backup")
    parser.add_argument("--health-check", action="store_true", help="Perform health check")
    parser.add_argument("--rollback", action="store_true", help="Rollback deployment")
    parser.add_argument("--cloud", choices=["docker", "heroku", "aws", "gcp"], help="Deploy to cloud provider")
    parser.add_argument("--prod-config", action="store_true", help="Create production configuration")
    parser.add_argument("--tag", default="ai4supplychain:latest", help="Docker image tag")
    parser.add_argument("--port", type=int, default=8000, help="Application port")
    
    args = parser.parse_args()
    
    # Check prerequisites
    if not check_deployment_prerequisites():
        return 1
    
    success = True
    
    if args.prod_config:
        success = create_production_config()
    elif args.build:
        success = build_docker_image(args.tag)
    elif args.run:
        success = run_docker_container(args.tag, args.port)
    elif args.compose:
        success = deploy_with_docker_compose(args.environment)
    elif args.backup:
        success = backup_database()
    elif args.health_check:
        success = health_check()
    elif args.rollback:
        success = rollback_deployment()
    elif args.cloud:
        success = deploy_to_cloud(args.cloud)
    else:
        # Default: full deployment
        print("🚀 Starting full deployment process...")
        success = (
            build_docker_image(args.tag) and
            run_docker_container(args.tag, args.port) and
            health_check()
        )
        if success:
            print("\n🎉 Deployment completed successfully!")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
