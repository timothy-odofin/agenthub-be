# Deployment Overview

Complete guide to deploying AgentHub to production environments including Docker, Kubernetes, and major cloud providers (AWS, Google Cloud, Azure).

---

## Table of Contents

- [Deployment Architecture](#deployment-architecture)
- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
  - [Docker Compose (Local/Development)](#docker-compose-localdevelopment)
  - [Render (Managed Platform)](#render-managed-platform)
  - [AWS (Amazon Web Services)](#aws-amazon-web-services)
  - [Google Cloud Platform](#google-cloud-platform)
  - [Microsoft Azure](#microsoft-azure)
  - [Kubernetes (Self-Managed)](#kubernetes-self-managed)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Monitoring & Observability](#monitoring--observability)
- [Security Best Practices](#security-best-practices)

---

## Deployment Architecture

AgentHub consists of multiple components that need to be deployed:

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer / CDN                     │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│   FastAPI App   │            │  Celery Workers │
│   (Main API)    │            │ (Background)    │
└────────┬────────┘            └────────┬────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│   PostgreSQL    │            │     Redis       │
│  (Vector DB)    │            │   (Cache +      │
│                 │            │    Broker)      │
└─────────────────┘            └─────────────────┘
                  │
         ┌────────▼────────┐
         │    MongoDB      │
         │  (Sessions)     │
         └─────────────────┘
                  │
         ┌────────▼────────┐
         │     Qdrant      │
         │ (Vector Store)  │
         └─────────────────┘
```

### Components:

1. **FastAPI Application** - Main REST API server
2. **Celery Workers** - Background task processing (data ingestion, etc.)
3. **PostgreSQL (pgvector)** - Relational database with vector support
4. **MongoDB** - Session storage and chat history
5. **Redis** - Cache and Celery message broker
6. **Qdrant** - Vector database for embeddings
7. **External Services** - OpenAI, Groq, LangChain, Jira, Confluence

---

## Prerequisites

Before deploying, ensure you have:

### Required:
- Python 3.11+ application tested locally
- Environment variables configured (see `.env.example`)
- API keys for LLM providers (OpenAI, Groq, etc.)
- MongoDB connection string (Atlas or self-hosted)
- Qdrant cluster (cloud or self-hosted)
- Domain name (for production)
- SSL certificate (Let's Encrypt or cloud provider)

### Optional:
- Jira/Confluence credentials (if using integrations)
- GitHub App credentials (if using GitHub integration)
- Datadog API keys (for monitoring)

---

## Deployment Options

### Docker Compose (Local/Development)

**Best for**: Local development, testing, small deployments

**Pros**: Easy setup, all services included, reproducible
**Cons**: Single-machine, not auto-scaling, manual updates

#### Quick Start:

```bash
# 1. Clone repository
git clone https://github.com/timothy-odofin/agenthub-be.git
cd agenthub-be

# 2. Copy environment file
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
docker-compose up -d

# 4. Check logs
docker-compose logs -f app

# 5. Access API
curl http://localhost:8000/health
```

#### Services Started:
- PostgreSQL (pgvector): `localhost:5432`
- MongoDB: `localhost:27017`
- Redis: `localhost:6379`
- FastAPI: `localhost:8000`
- pgAdmin: `localhost:5050`
- Mongo Express: `localhost:8081`

**See**: `docker-compose.yml` for full configuration

---

### Render (Managed Platform)

**Best for**: Quick production deployment, startups, MVP

**Pros**: Zero DevOps, free tier, auto-scaling, managed databases
**Cons**: Limited customization, vendor lock-in

#### Architecture on Render:

```
Render Services:
├── Web Service (FastAPI)
├── Background Worker (Celery)
├── Redis (Managed)
└── External: MongoDB Atlas, Qdrant Cloud
```

#### Deployment Steps:

1. **Push to GitHub**:
```bash
git push origin main
```

2. **Create Render Account**: [dashboard.render.com](https://dashboard.render.com)

3. **Create Web Service**:
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Configure:
     - **Name**: `agenthub-api`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`

4. **Add Redis**:
   - Click "New +" → "Redis"
   - Name: `agenthub-redis`
   - Plan: Free or Starter

5. **Configure Environment Variables**:
   - Go to service → "Environment" tab
   - Add all variables from `.env.example`
   - Use Render's Redis URL for `REDIS_URL`

6. **Deploy**:
   - Render auto-deploys on git push
   - View logs in dashboard

**See**: `docs/deployment/render-setup.md` for detailed guide

---

### AWS (Amazon Web Services)

**Best for**: Enterprise, high-scale, full control

**Pros**: Most features, global regions, mature ecosystem
**Cons**: Complex, expensive, steep learning curve

#### Recommended AWS Architecture:

```
AWS Services:
├── ECS/Fargate (FastAPI containers)
├── ECS/Fargate (Celery workers)
├── RDS PostgreSQL (with pgvector extension)
├── DocumentDB (MongoDB-compatible)
├── ElastiCache Redis
├── ALB (Application Load Balancer)
├── Route 53 (DNS)
├── CloudFront (CDN)
├── S3 (static files, backups)
├── Secrets Manager (API keys)
├── CloudWatch (monitoring)
└── WAF (security)
```

#### Deployment Options:

**Option 1: ECS Fargate (Serverless Containers)**

1. **Create ECR Repository**:
```bash
# Create repository
aws ecr create-repository --repository-name agenthub-api

# Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t agenthub-api .
docker tag agenthub-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/agenthub-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/agenthub-api:latest
```

2. **Create ECS Cluster**:
```bash
aws ecs create-cluster --cluster-name agenthub-cluster
```

3. **Create Task Definition** (`ecs-task-definition.json`):
```json
{
  "family": "agenthub-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "agenthub-api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/agenthub-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:agenthub/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/agenthub-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

4. **Create RDS PostgreSQL**:
```bash
aws rds create-db-instance \
  --db-instance-identifier agenthub-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username admin \
  --master-user-password <secure-password> \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxxx \
  --db-subnet-group-name agenthub-subnet-group \
  --backup-retention-period 7 \
  --storage-encrypted
```

5. **Create ElastiCache Redis**:
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id agenthub-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxxxxxxxx
```

6. **Create ALB and Target Group**:
```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name agenthub-alb \
  --subnets subnet-xxxxxxxx subnet-yyyyyyyy \
  --security-groups sg-xxxxxxxxx

# Create target group
aws elbv2 create-target-group \
  --name agenthub-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxxxxxx \
  --target-type ip \
  --health-check-path /health
```

7. **Deploy ECS Service**:
```bash
aws ecs create-service \
  --cluster agenthub-cluster \
  --service-name agenthub-api \
  --task-definition agenthub-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxx,subnet-yyyyyyyy],securityGroups=[sg-xxxxxxxxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=agenthub-api,containerPort=8000"
```

**Option 2: Elastic Beanstalk (Managed Platform)**

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 agenthub-api --region us-east-1

# Create environment
eb create agenthub-prod

# Deploy
eb deploy

# Configure environment variables
eb setenv OPENAI_API_KEY=sk-xxx MONGODB_CONNECTION_STRING=mongodb+srv://...
```

**Option 3: Lambda + API Gateway (Serverless)**

1. **Create Lambda function** with container image
2. **Add API Gateway** for HTTP routing
3. **Use SQS + Lambda** for Celery replacement
4. **Costs**: Pay only for requests (best for low traffic)

#### AWS Cost Estimate (Monthly):

| Component | Service | Cost |
|-----------|---------|------|
| Web App (2 containers) | ECS Fargate | $30-50 |
| Workers (2 containers) | ECS Fargate | $30-50 |
| PostgreSQL | RDS db.t3.small | $25-35 |
| MongoDB | DocumentDB | $50-100 |
| Redis | ElastiCache | $15-25 |
| Load Balancer | ALB | $20-30 |
| Data Transfer | Outbound | $10-50 |
| **Total** | | **$180-340/month** |

---

### Google Cloud Platform

**Best for**: Kubernetes-native, machine learning workloads, global scale

**Pros**: Best Kubernetes (GKE), great AI/ML tools, competitive pricing
**Cons**: Less mature than AWS, smaller ecosystem

#### Recommended GCP Architecture:

```
GCP Services:
├── Cloud Run (FastAPI containers)
├── Cloud Run Jobs (Celery workers)
├── Cloud SQL (PostgreSQL with pgvector)
├── Cloud Memorystore (Redis)
├── MongoDB Atlas (partner integration)
├── Cloud Load Balancing
├── Cloud CDN
├── Cloud Storage (backups)
├── Secret Manager
└── Cloud Monitoring
```

#### Deployment Steps:

**Option 1: Cloud Run (Serverless Containers)**

1. **Enable APIs**:
```bash
gcloud services enable run.googleapis.com \
  sql-component.googleapis.com \
  redis.googleapis.com
```

2. **Build and Deploy**:
```bash
# Build container with Cloud Build
gcloud builds submit --tag gcr.io/PROJECT_ID/agenthub-api

# Deploy to Cloud Run
gcloud run deploy agenthub-api \
  --image gcr.io/PROJECT_ID/agenthub-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ENVIRONMENT=production" \
  --set-secrets "OPENAI_API_KEY=openai-key:latest,MONGODB_CONNECTION_STRING=mongodb-uri:latest" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 10
```

3. **Create Cloud SQL (PostgreSQL)**:
```bash
gcloud sql instances create agenthub-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=<secure-password> \
  --backup

# Create database
gcloud sql databases create polyagent --instance=agenthub-postgres
```

4. **Create Redis Instance**:
```bash
gcloud redis instances create agenthub-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

5. **Configure Secrets**:
```bash
# Create secrets
echo -n "sk-xxx" | gcloud secrets create openai-key --data-file=-
echo -n "mongodb+srv://..." | gcloud secrets create mongodb-uri --data-file=-

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding openai-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

6. **Deploy Celery Workers**:
```bash
gcloud run jobs create agenthub-worker \
  --image gcr.io/PROJECT_ID/agenthub-worker \
  --region us-central1 \
  --task-timeout 3600 \
  --max-retries 3 \
  --set-env-vars "WORKER_TYPE=celery" \
  --set-secrets "OPENAI_API_KEY=openai-key:latest"
```

**Option 2: GKE (Google Kubernetes Engine)**

```bash
# Create cluster
gcloud container clusters create agenthub-cluster \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --region us-central1 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10

# Deploy with Helm or kubectl
kubectl apply -f k8s/
```

#### GCP Cost Estimate (Monthly):

| Component | Service | Cost |
|-----------|---------|------|
| Web App | Cloud Run | $20-40 |
| Workers | Cloud Run Jobs | $15-30 |
| PostgreSQL | Cloud SQL | $25-50 |
| Redis | Memorystore | $30-50 |
| MongoDB | Atlas (external) | $0-57 |
| Load Balancer | Cloud LB | $18-25 |
| **Total** | | **$108-252/month** |

---

### Microsoft Azure

**Best for**: Enterprise, .NET integration, hybrid cloud, Microsoft ecosystem

**Pros**: Best hybrid cloud, great for enterprises, strong compliance
**Cons**: Complex pricing, less Python-focused

#### Recommended Azure Architecture:

```
Azure Services:
├── App Service (FastAPI)
├── Container Apps (alternative)
├── Azure Functions (workers)
├── Azure Database for PostgreSQL
├── Azure Cache for Redis
├── Cosmos DB (MongoDB API)
├── Application Gateway
├── Azure CDN
├── Azure Storage
├── Key Vault (secrets)
└── Application Insights
```

#### Deployment Steps:

**Option 1: Azure App Service**

1. **Create Resource Group**:
```bash
az group create --name agenthub-rg --location eastus
```

2. **Create App Service Plan**:
```bash
az appservice plan create \
  --name agenthub-plan \
  --resource-group agenthub-rg \
  --sku B1 \
  --is-linux
```

3. **Create Web App**:
```bash
az webapp create \
  --resource-group agenthub-rg \
  --plan agenthub-plan \
  --name agenthub-api \
  --runtime "PYTHON:3.11" \
  --deployment-local-git
```

4. **Deploy Code**:
```bash
# Add Azure remote
git remote add azure https://<username>@agenthub-api.scm.azurewebsites.net/agenthub-api.git

# Push
git push azure main
```

5. **Create PostgreSQL**:
```bash
az postgres flexible-server create \
  --name agenthub-postgres \
  --resource-group agenthub-rg \
  --location eastus \
  --admin-user azureuser \
  --admin-password <secure-password> \
  --sku-name Standard_B1ms \
  --version 15
```

6. **Create Redis**:
```bash
az redis create \
  --name agenthub-redis \
  --resource-group agenthub-rg \
  --location eastus \
  --sku Basic \
  --vm-size c0
```

7. **Configure Environment Variables**:
```bash
az webapp config appsettings set \
  --resource-group agenthub-rg \
  --name agenthub-api \
  --settings \
    OPENAI_API_KEY="@Microsoft.KeyVault(SecretUri=https://agenthub-kv.vault.azure.net/secrets/openai-key/)" \
    MONGODB_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://agenthub-kv.vault.azure.net/secrets/mongodb-uri/)"
```

**Option 2: Azure Container Apps**

```bash
# Create container app
az containerapp create \
  --name agenthub-api \
  --resource-group agenthub-rg \
  --image agenthub.azurecr.io/agenthub-api:latest \
  --environment agenthub-env \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 0.5 \
  --memory 1Gi
```

#### Azure Cost Estimate (Monthly):

| Component | Service | Cost |
|-----------|---------|------|
| Web App | App Service B1 | $13-55 |
| Workers | Functions | $15-30 |
| PostgreSQL | Flexible Server | $30-60 |
| Redis | Cache Basic | $15-25 |
| MongoDB | Cosmos DB | $25-100 |
| Gateway | App Gateway | $25-50 |
| **Total** | | **$123-320/month** |

---

### Kubernetes (Self-Managed)

**Best for**: Multi-cloud, maximum control, large scale

**Pros**: Cloud-agnostic, maximum flexibility, industry standard
**Cons**: Complex, requires expertise, higher maintenance

#### Quick Start with Helm:

1. **Create namespace**:
```bash
kubectl create namespace agenthub
```

2. **Install PostgreSQL with Helm**:
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami

helm install postgres bitnami/postgresql \
  --namespace agenthub \
  --set auth.postgresPassword=admin123 \
  --set primary.persistence.size=10Gi
```

3. **Install Redis**:
```bash
helm install redis bitnami/redis \
  --namespace agenthub \
  --set auth.password=admin123
```

4. **Deploy Application**:
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

**See**: `docs/deployment/kubernetes.md` for complete Kubernetes guide

---

## Environment Configuration

### Production Environment Variables:

Create `.env.production` with:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://your-domain.com

# Security
JWT_SECRET_KEY=<generate-strong-random-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
POSTGRES_HOST=<production-host>
POSTGRES_PORT=5432
POSTGRES_USER=<secure-user>
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=polyagent

# MongoDB
MONGODB_CONNECTION_STRING=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/polyagent_sessions?retryWrites=true&w=majority

# Redis
REDIS_URL=redis://:<password>@<host>:6379/0

# Vector Database
QDRANT_ENDPOINT=https://<cluster-id>.cloud.qdrant.io
QDRANT_API_KEY=<your-api-key>
QDRANT_CLUSTER_ID=<cluster-id>

# LLM Providers
OPENAI_API_KEY=sk-<your-key>
GROQ_API_KEY=gsk_<your-key>
ANTHROPIC_API_KEY=sk-ant-<your-key>

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Monitoring (optional)
DATADOG_API_KEY=<your-key>
SENTRY_DSN=<your-dsn>
```

### Generate Secure Keys:

```python
import secrets

# Generate JWT secret
print("JWT_SECRET_KEY=" + secrets.token_urlsafe(32))

# Generate random passwords
print("DB_PASSWORD=" + secrets.token_urlsafe(24))
```

---

## Database Setup

### PostgreSQL (pgvector):

1. **Install pgvector extension**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **Run migrations**:
```bash
# Using Alembic (if configured)
alembic upgrade head

# Or run init.sql
psql -h <host> -U <user> -d polyagent -f init.sql
```

### MongoDB:

1. **Create database and user**:
```javascript
use polyagent_sessions

db.createUser({
  user: "agenthub_user",
  pwd: "<secure-password>",
  roles: [
    { role: "readWrite", db: "polyagent_sessions" }
  ]
})
```

2. **Create indexes**:
```javascript
db.sessions.createIndex({ "user_id": 1 })
db.sessions.createIndex({ "created_at": 1 }, { expireAfterSeconds: 2592000 }) // 30 days
db.messages.createIndex({ "session_id": 1 })
```

### Qdrant:

1. **Create collection**:
```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url=os.getenv("QDRANT_ENDPOINT"),
    api_key=os.getenv("QDRANT_API_KEY")
)

client.create_collection(
    collection_name="documents",
    vectors_config={"size": 1536, "distance": "Cosine"}
)
```

---

## Monitoring & Observability

### Health Checks:

```bash
# Application health
curl https://your-domain.com/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600
}
```

### Logging:

**Structured JSON Logs**:
```python
# app/core/logging.py already configured
import logging

logger = logging.getLogger(__name__)
logger.info("User logged in", extra={"user_id": user_id})
```

### Monitoring Tools:

1. **Application Performance**:
   - Datadog APM
   - New Relic
   - Sentry (error tracking)

2. **Infrastructure**:
   - CloudWatch (AWS)
   - Cloud Monitoring (GCP)
   - Application Insights (Azure)
   - Prometheus + Grafana (self-hosted)

3. **Uptime Monitoring**:
   - Pingdom
   - UptimeRobot
   - Datadog Synthetics

### Metrics to Track:

- Request rate (req/s)
- Response time (p50, p95, p99)
- Error rate (%)
- CPU/Memory usage (%)
- Database connections
- Cache hit rate (%)
- Celery queue length
- Token usage (OpenAI API)

---

## Security Best Practices

### 1. Secrets Management:

**Don't**:
- Commit `.env` files to Git
- Hardcode API keys in code
- Use same keys for dev/prod

**Do**:
- Use cloud secret managers (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)
- Rotate keys regularly
- Use different keys per environment

### 2. Network Security:

- Use HTTPS only (SSL/TLS certificates)
- Enable CORS with specific origins
- Use VPC/Private networks for databases
- Configure security groups/firewalls
- Enable DDoS protection (CloudFlare, AWS Shield)

### 3. Authentication:

- JWT tokens with short expiration
- Refresh token rotation
- Rate limiting on auth endpoints
- Password complexity requirements
- Consider OAuth2/OpenID Connect

### 4. Database Security:

- Use SSL connections
- Restrict IP whitelist
- Regular backups (automated)
- Encrypted at rest
- Principle of least privilege (users/roles)

### 5. Application Security:

- Input validation (Pydantic models)
- SQL injection protection (parameterized queries)
- XSS protection (FastAPI handles this)
- CSRF tokens (for cookie-based auth)
- Security headers (Helmet.js equivalent)

### 6. Compliance:

- GDPR (data privacy)
- HIPAA (healthcare data)
- SOC 2 (security controls)
- PCI DSS (payment data)

---

## Deployment Checklist

Before going to production:

### Pre-Deployment:
- [ ] All environment variables configured
- [ ] Database migrations run
- [ ] SSL certificate installed
- [ ] Domain DNS configured
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] Load testing completed
- [ ] Security scan passed

### Post-Deployment:
- [ ] Health check returns 200
- [ ] API endpoints respond correctly
- [ ] Database connections working
- [ ] Celery workers processing tasks
- [ ] Logs flowing to monitoring
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team notified

---

## Scaling Strategies

### Horizontal Scaling (Recommended):

```
Load Balancer
    │
    ├─► FastAPI Instance 1
    ├─► FastAPI Instance 2
    ├─► FastAPI Instance 3
    └─► FastAPI Instance N
```

**Auto-scaling triggers**:
- CPU > 70%
- Memory > 80%
- Request queue > 100

### Vertical Scaling:

- Increase CPU/RAM per instance
- Useful for CPU-intensive tasks
- Limited by machine size

### Database Scaling:

1. **Read Replicas** (PostgreSQL, MongoDB)
2. **Connection Pooling** (PgBouncer)
3. **Caching** (Redis for frequent queries)
4. **Sharding** (for very large datasets)

---

## Troubleshooting

### Common Issues:

**1. Health check failing**:
```bash
# Check logs
docker logs <container-id>
kubectl logs <pod-name>

# Verify environment variables
env | grep -E "OPENAI|MONGODB|REDIS"
```

**2. Database connection errors**:
```bash
# Test connection
psql -h <host> -U <user> -d polyagent
mongosh "mongodb+srv://<connection-string>"

# Check firewall/security groups
telnet <host> 5432
```

**3. Out of memory**:
```bash
# Check memory usage
docker stats
kubectl top pods

# Increase memory limits
# In docker-compose.yml: mem_limit: 2g
# In Kubernetes: resources.limits.memory: 2Gi
```

**4. Slow API responses**:
```bash
# Check database query performance
EXPLAIN ANALYZE SELECT * FROM ...;

# Check Redis connection
redis-cli ping

# Monitor Celery workers
celery -A src.app.workers.celery_app inspect active
```

---

## Cost Optimization

### Tips to Reduce Costs:

1. **Use managed services for databases** (often cheaper than self-managed)
2. **Enable auto-scaling** (scale down during low traffic)
3. **Use spot instances** (AWS, GCP) for non-critical workloads
4. **Implement caching aggressively** (reduce database queries)
5. **Optimize LLM usage** (cache embeddings, use cheaper models)
6. **Set up budget alerts** (prevent unexpected charges)
7. **Use CDN for static assets** (reduce bandwidth costs)
8. **Clean up unused resources** (old snapshots, images, etc.)

---

## Next Steps

1. **Choose deployment platform** based on your needs
2. **Set up staging environment** (test before production)
3. **Configure monitoring** (know when things break)
4. **Document runbooks** (how to respond to incidents)
5. **Plan disaster recovery** (backups, failover)
6. **Set up CI/CD pipeline** (automated deployments)

## Related Documentation

- [Render Setup Guide](./render-setup.md) - Detailed Render.com deployment
- [Kubernetes Guide](./kubernetes.md) - Complete Kubernetes deployment
- [Docker Guide](./docker.md) - Docker and Docker Compose
- [Architecture Overview](../architecture/overview.md) - System architecture
- [Configuration Guide](../guides/configuration/README.md) - Environment setup

---

## Support

- **Documentation**: https://github.com/timothy-odofin/agenthub-be/docs
- **Issues**: https://github.com/timothy-odofin/agenthub-be/issues
- **Discussions**: https://github.com/timothy-odofin/agenthub-be/discussions

---

**Last Updated**: January 2026
**Maintained by**: AgentHub Team
