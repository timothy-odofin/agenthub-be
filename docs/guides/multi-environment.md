# Running AgentHub in Different Environments

Ever needed to run your app with different configs for dev, staging, and production? This guide shows you how to use different `.env` files for each environment.

## Why This Matters

When you're developing locally, you want debug mode on, detailed logs, and maybe connecting to local databases. In production, you need security locked down, minimal logging, and real database credentials.

Instead of changing your `.env` file every time you deploy, you can have separate files:
- `.env.dev` for development
- `.env.staging` for testing before production  
- `.env.production` for the real deal

## Basic Usage

If you don't specify anything, AgentHub uses `.env` (the default):

```bash
python -m uvicorn app.main:app --reload
```

To use a specific environment file:

```bash
# Development
python -m uvicorn app.main:app --env .env.dev --reload

# Staging
python -m uvicorn app.main:app --env .env.staging

# Production
python -m uvicorn app.main:app --env .env.production
```

That's it. The `--env` flag tells AgentHub which file to load.

## What's in Each Environment File

We've included three example files to get you started:

**`.env.dev`** (Development)
- Debug mode on
- Verbose logging
- Local database connections
- CORS allows localhost origins

**`.env.staging`** (Pre-production Testing)
- Debug mode off
- Info-level logging
- Uses placeholders for secrets (mount real ones at runtime)
- Production-like CORS settings

**`.env.production`** (Live Deployment)
- Everything locked down
- Warning-level logging only
- All secrets are placeholders (NEVER commit real production secrets)
- Strict CORS settings

Each file has the same structure:

```bash
# Environment type
APP_ENV=development
DEBUG=true

# Databases
POSTGRES_HOST=localhost
REDIS_HOST=localhost

# Your API keys
OPENAI_API_KEY=sk-...

# Who can access your API
ALLOWED_ORIGINS=http://localhost:3000

# How chatty the logs should be
LOG_LEVEL=DEBUG
```

## Using the Makefile

We've added shortcuts to the Makefile for convenience:

```bash
make run-api-dev      # Runs with .env.dev
make run-api-staging  # Runs with .env.staging
make run-api-prod     # Runs with .env.production (4 workers)
```

Much easier than typing out the full uvicorn command each time.

## Docker Deployments

### Development Setup

Here's a simple development Dockerfile that uses `.env.dev`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
COPY .env.dev .env

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload"]
```

```bash
docker build -t agenthub:dev .
docker run -p 8000:8000 agenthub:dev
```

### Production - Mount Secrets at Runtime

For production, never bake secrets into the image. Mount them when you run the container:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# No .env copied - we'll mount it later
CMD ["uvicorn", "app.main:app", "--env", "/secrets/.env", "--host", "0.0.0.0"]
```

```bash
docker build -t agenthub:prod .

# Mount your production .env from a secure location
docker run -p 8000:8000 \
  -v /secure/production/.env:/secrets/.env:ro \
  agenthub:prod
```

The `:ro` makes it read-only for extra safety.

## Kubernetes Setup

If you're running on Kubernetes, here's the pattern:

Put non-sensitive config in a ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agenthub-config
data:
  APP_ENV: "production"
  DEBUG: "false"
  POSTGRES_HOST: "postgres-service"
```

Put secrets in a Secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: agenthub-secrets
type: Opaque
stringData:
  POSTGRES_PASSWORD: "your-db-password"
  OPENAI_API_KEY: "sk-..."
```

Then mount both in your deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agenthub
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: agenthub
        image: agenthub:latest
        command:
          - uvicorn
          - app.main:app
          - --env
          - /config/.env
          - --host
          - 0.0.0.0
        envFrom:
        - configMapRef:
            name: agenthub-config
        - secretRef:
            name: agenthub-secrets
```

The system environment variables from ConfigMap and Secret take precedence over the `.env` file, so you get the best of both worlds.

## Cloud Platform Examples

### AWS ECS

```bash
# Store your .env in AWS Secrets Manager
aws secretsmanager create-secret \
  --name agenthub/env-file \
  --secret-string file://.env.production

# Reference it in your task definition
{
  "containerDefinitions": [{
    "command": [
      "uvicorn", "app.main:app",
      "--env", "/secrets/.env",
      "--host", "0.0.0.0"
    ],
    "secrets": [{
      "name": "ENV_FILE",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:agenthub/env-file"
    }]
  }]
}
```

### GCP Cloud Run

```bash
# Create secret
gcloud secrets create agenthub-env --data-file=.env.production

# Deploy with secret mounted
gcloud run deploy agenthub \
  --image gcr.io/project/agenthub \
  --update-secrets=/secrets/.env=agenthub-env:latest \
  --set-env-vars="ENV_FILE=/secrets/.env"
```

### Azure Container Apps

```bash
# Create secret
az containerapp secret set \
  --name agenthub \
  --secrets env-file=@.env.production

# Update command
az containerapp update \
  --name agenthub \
  --command "uvicorn app.main:app --env /secrets/.env --host 0.0.0.0"
```

## How Environment Variables are Loaded

AgentHub loads variables in this order (highest priority first):

1. System environment variables
2. File specified by `--env` flag
3. Default `.env` file (if no `--env` specified)
4. Hardcoded defaults in the code

So if you set `DEBUG=false` in your shell, it wins even if `.env` says `DEBUG=true`.

Example:

```bash
# Your .env.dev has DEBUG=true
# But you want to test with debug off temporarily

export DEBUG=false
python -m uvicorn app.main:app --env .env.dev

# DEBUG will be false (from shell, not file)
```

## Security Best Practices

Things to remember:

**Development**
- Keep `.env.dev` in git (it has fake credentials anyway)
- Create `.env.local` for personal overrides (gitignored automatically)

**Staging**
- Use placeholder values in `.env.staging`
- Inject real secrets via system environment variables or secret managers

**Production**
- NEVER commit `.env.production` with real secrets
- Always mount from secure storage (AWS Secrets Manager, HashiCorp Vault, etc.)
- Use `--env-required` flag to fail fast if env file is missing
- Rotate secrets regularly

**Example secure production setup**:

```bash
# Mount from secure location
python -m uvicorn app.main:app \
  --env /mnt/secrets/.env.production \
  --env-required \
  --host 0.0.0.0
```

## Troubleshooting

### "Environment file not found"

Check the file path. By default, it just warns and continues. Use `--env-required` to make it fail:

```bash
python -m uvicorn app.main:app --env .env.prod --env-required
# Error: Environment file not found: .env.prod
```

### "Wrong environment loaded"

Check startup logs for which file was loaded:

```
✓ Loaded environment variables from: .env.dev
```

Or verify programmatically:

```bash
python -c "from app.core.utils import env; print(env.get_string('APP_ENV'))"
```

### "My variable isn't being read"

Remember: system environment variables override file variables.

```bash
# Check what's in your shell
echo $POSTGRES_HOST

# Clear it if needed
unset POSTGRES_HOST
```

## Migrating from Single .env

If you currently just use `.env`:

1. Copy it to create environment-specific versions:
```bash
cp .env .env.dev
cp .env .env.staging
cp .env .env.production
```

2. Edit each file for its environment:
- `.env.dev` - keep debug on, local databases
- `.env.staging` - debug off, staging databases  
- `.env.production` - use placeholders for secrets

3. Update your deployment commands:
```bash
# Old way
python -m uvicorn app.main:app

# New way
python -m uvicorn app.main:app --env .env.production
```

4. Keep your original `.env` - it still works as the default, so no breaking changes.

## Additional CLI Options

There are a few more flags available:

```bash
# Require environment file to exist (fail if missing)
python -m uvicorn app.main:app --env .env.prod --env-required

# Override debug mode (ignores env file)
python -m uvicorn app.main:app --env .env.prod --debug

# Override log level
python -m uvicorn app.main:app --env .env.dev --log-level INFO

# Show version
python -m uvicorn app.main:app --version
```

Run `--help` to see all options:

```bash
python -m uvicorn app.main:app --help
```

## That's It

The multi-environment system is designed to be simple:
- Use `--env` to pick your environment file
- System variables override file variables
- Default to `.env` if nothing specified
- Never commit production secrets

Questions? Open an issue on GitHub.
