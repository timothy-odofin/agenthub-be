# Deployment Guide: Hugging Face Spaces

This guide will help you deploy your AgentHub backend to Hugging Face Spaces.

## Prerequisites

1. A Hugging Face account (create one at https://huggingface.co)
2. Git installed on your machine
3. Access to external services (PostgreSQL, MongoDB, Redis)

## Option 1: Deploy from Current Repository

### Step 1: Create a Hugging Face Space

1. Go to https://huggingface.co/new-space
2. Fill in the details:
   - **Space name**: `agenthub-backend` (or your preferred name)
   - **License**: MIT
   - **Select the Space SDK**: Docker
   - **Space hardware**: CPU basic (free) or upgrade for better performance
3. Click "Create Space"

### Step 2: Push Your Code to Hugging Face

```bash
# Add Hugging Face as a remote (replace USERNAME and SPACE_NAME)
git remote add huggingface https://huggingface.co/spaces/USERNAME/SPACE_NAME

# Push your code
git push huggingface feature/huggingface-deployment:main
```

### Step 3: Configure Environment Variables

Go to your Space settings and add these secrets:

#### Required Database Configurations
```
DATABASE_URL=postgresql://user:password@host:port/dbname
MONGODB_URL=mongodb://user:password@host:port/dbname
REDIS_URL=redis://host:port
```

#### LLM Provider Keys (add at least one)
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

#### Optional Configurations
```
JWT_SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://your-frontend.com,https://agenthub-backend.hf.space
ENVIRONMENT=production
```

### Step 4: Wait for Build

Hugging Face will automatically build your Docker container. This may take 5-10 minutes.

## Option 2: Use Managed Database Services

If you don't have external databases, you can use these managed services:

### PostgreSQL
- **Neon**: https://neon.tech (Free tier available)
- **Supabase**: https://supabase.com (Free tier available)
- **ElephantSQL**: https://www.elephantsql.com (Free tier available)

### MongoDB
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas (Free tier available)

### Redis
- **Upstash**: https://upstash.com (Free tier available)
- **Redis Cloud**: https://redis.com/cloud (Free tier available)

## Testing Your Deployment

Once deployed, your API will be available at:
```
https://USERNAME-SPACE_NAME.hf.space
```

Test the endpoints:
- Health check: `https://USERNAME-SPACE_NAME.hf.space/health`
- API docs: `https://USERNAME-SPACE_NAME.hf.space/docs`
- Root: `https://USERNAME-SPACE_NAME.hf.space/`

## Performance Optimization

### Upgrade Space Hardware

For better performance, consider upgrading your Space:
- **CPU basic**: Free, suitable for testing
- **CPU upgrade**: $0.60/hour, better for production
- **T4 small**: $0.60/hour, includes GPU
- **A10G small**: $3.15/hour, high performance

### Database Optimization

1. Use connection pooling in your database URLs
2. Consider using read replicas for PostgreSQL
3. Enable Redis caching for frequently accessed data

## Monitoring and Logs

1. View logs in your Space's "Logs" tab
2. Set up monitoring with services like:
   - DataDog (already integrated in your code)
   - Better Uptime
   - Sentry

## Environment-Specific Configuration

You can create different environment files for Hugging Face:

```bash
# Create .env.huggingface
cp .env.production .env.huggingface
```

Then modify your Dockerfile to use it:
```dockerfile
# Copy environment file
COPY .env.huggingface ./src/.env
```

## Troubleshooting

### Build Failures

If the build fails:
1. Check the build logs in Hugging Face
2. Verify all dependencies in requirements.txt are compatible
3. Ensure system dependencies in Dockerfile are correct

### Runtime Errors

If the app crashes:
1. Check the Space logs
2. Verify all environment variables are set
3. Test database connections
4. Check if external services are accessible

### Performance Issues

If the app is slow:
1. Upgrade Space hardware
2. Optimize database queries
3. Enable Redis caching
4. Use connection pooling

## Continuous Deployment

Set up automatic deployment:

```bash
# In your local repository
git remote add huggingface https://huggingface.co/spaces/USERNAME/SPACE_NAME

# Deploy with a simple push
git push huggingface main
```

Or use GitHub Actions to automatically deploy on push (see below).

## GitHub Actions Integration (Optional)

Create `.github/workflows/deploy-huggingface.yml`:

```yaml
name: Deploy to Hugging Face

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Push to Hugging Face
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          git remote add huggingface https://user:$HF_TOKEN@huggingface.co/spaces/USERNAME/SPACE_NAME
          git push huggingface main
```

## Security Best Practices

1. **Never commit secrets**: Use Hugging Face Space secrets
2. **Rotate keys regularly**: Update API keys periodically
3. **Use HTTPS only**: Enable secure connections
4. **Implement rate limiting**: Already configured in your app
5. **Monitor access logs**: Check for suspicious activity

## Cost Estimation

### Free Tier
- CPU basic Space: $0/month
- Neon PostgreSQL: Free tier available
- MongoDB Atlas: Free tier available
- Upstash Redis: Free tier available

### Production Setup
- CPU upgrade Space: ~$432/month (24/7)
- Better database tier: $15-50/month
- Redis: $10-20/month
- **Total**: ~$460-500/month

Or use spot instances and scale down during low usage.

## Next Steps

1. ✅ Create Hugging Face Space
2. ✅ Push your code
3. ✅ Configure environment variables
4. ✅ Test the deployment
5. 📈 Monitor performance
6. 🔄 Set up CI/CD
7. 📊 Configure monitoring

## Support

If you need help:
- Hugging Face Discord: https://discord.gg/JfAtkvEtRb
- Hugging Face Forums: https://discuss.huggingface.co
- Documentation: https://huggingface.co/docs/hub/spaces-overview

## Migration from Render

To migrate from Render to Hugging Face:

1. Export your environment variables from Render
2. Set them up in Hugging Face Space secrets
3. Update your frontend to point to the new Hugging Face URL
4. Test thoroughly before switching DNS
5. Keep Render running until you verify Hugging Face works
6. Update all API endpoints in your frontend
7. Monitor for any issues

Good luck with your deployment! 🚀
