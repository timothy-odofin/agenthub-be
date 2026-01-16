# Hugging Face Deployment - Quick Start

## 🎯 What I've Created For You

I've set up everything you need to deploy your AgentHub backend to Hugging Face Spaces:

### New Files Created:
1. **Dockerfile** - Docker configuration for Hugging Face
2. **README_HUGGINGFACE.md** - Hugging Face Space description
3. **README_HF.md** - Space metadata configuration
4. **.dockerignore** - Optimizes Docker build
5. **start.sh** - Application startup script
6. **deploy_to_huggingface.sh** - Automated deployment helper
7. **test_docker.sh** - Local Docker testing
8. **DEPLOYMENT_HUGGINGFACE.md** - Complete deployment guide

## 🚀 Quick Deployment (3 Steps)

### Step 1: Create Your Hugging Face Space
1. Go to https://huggingface.co/new-space
2. Fill in:
   - **Space name**: `agenthub-backend`
   - **SDK**: Docker (IMPORTANT!)
   - **Space hardware**: CPU basic (free) or upgrade
3. Click "Create Space"

### Step 2: Run the Deployment Helper
```bash
./deploy_to_huggingface.sh
```

This script will:
- Guide you through setup
- Add Hugging Face as a git remote
- Show you the next steps

### Step 3: Configure & Deploy

#### A. Set Environment Variables
Go to your Space settings and add these secrets:

**Required:**
```
DATABASE_URL=postgresql://user:password@host:port/dbname
MONGODB_URL=mongodb://user:password@host:port/dbname
REDIS_URL=redis://host:port
```

**LLM Providers (at least one):**
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

**Optional:**
```
JWT_SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=https://your-frontend.com
```

#### B. Deploy Your Code
```bash
# Commit changes
git add .
git commit -m "Add Hugging Face deployment configuration"

# Push to Hugging Face
git push huggingface feature/huggingface-deployment:main
```

## 🗄️ Database Setup

If you don't have databases yet, use these free services:

### PostgreSQL (Choose one):
- **Neon** (Recommended): https://neon.tech
- **Supabase**: https://supabase.com
- **ElephantSQL**: https://www.elephantsql.com

### MongoDB:
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas

### Redis:
- **Upstash** (Recommended): https://upstash.com
- **Redis Cloud**: https://redis.com/cloud

## 📊 After Deployment

Your API will be available at:
```
https://YOUR-USERNAME-SPACE-NAME.hf.space
```

Test endpoints:
- Health: `https://YOUR-USERNAME-SPACE-NAME.hf.space/health`
- API Docs: `https://YOUR-USERNAME-SPACE-NAME.hf.space/docs`
- Root: `https://YOUR-USERNAME-SPACE-NAME.hf.space/`

## 🧪 Local Testing (Optional)

Test the Docker build locally before deploying:

```bash
./test_docker.sh
```

Or manually:
```bash
# Build
docker build -t agenthub-backend:test .

# Run (with your environment variables)
docker run -p 7860:7860 \
  -e DATABASE_URL=your_db_url \
  -e MONGODB_URL=your_mongo_url \
  -e REDIS_URL=your_redis_url \
  -e OPENAI_API_KEY=your_key \
  agenthub-backend:test

# Visit http://localhost:7860/docs
```

## 💰 Cost Comparison

### Render (Current)
- Free tier: Very slow, sleeps after inactivity
- Paid: $7-25/month

### Hugging Face Spaces
- **CPU basic**: FREE (community-supported)
- **CPU upgrade**: $0.60/hour (~$432/month for 24/7)
- **T4 small GPU**: $0.60/hour (same price, includes GPU!)
- **A10G GPU**: $3.15/hour (high performance)

### Recommendation:
1. Start with **FREE CPU basic** tier for testing
2. Upgrade to **CPU upgrade** or **T4 small** for production
3. Use managed databases (also have free tiers)

## 🔧 Troubleshooting

### Build Fails?
1. Check build logs in Hugging Face
2. Verify all dependencies in requirements.txt
3. Test locally with `./test_docker.sh`

### App Crashes?
1. Check Space logs
2. Verify environment variables are set
3. Test database connections
4. Ensure external services are accessible

### Slow Performance?
1. Upgrade Space hardware
2. Use connection pooling for databases
3. Enable Redis caching
4. Optimize queries

## 📚 Documentation

For detailed information, see:
- **DEPLOYMENT_HUGGINGFACE.md** - Complete deployment guide
- **README_HUGGINGFACE.md** - Space description
- **Dockerfile** - Container configuration

## 🆘 Need Help?

- Hugging Face Discord: https://discord.gg/JfAtkvEtRb
- Hugging Face Forums: https://discuss.huggingface.co
- Documentation: https://huggingface.co/docs/hub/spaces-overview

## 📋 Deployment Checklist

- [ ] Create Hugging Face account
- [ ] Create new Space (Docker SDK)
- [ ] Set up databases (Neon, MongoDB Atlas, Upstash)
- [ ] Configure environment variables in Space settings
- [ ] Run `./deploy_to_huggingface.sh`
- [ ] Push code to Hugging Face
- [ ] Wait for build (5-10 minutes)
- [ ] Test API endpoints
- [ ] Update frontend URLs
- [ ] Monitor logs and performance

## 🎉 Advantages Over Render

✅ **FREE tier available** (community-supported)
✅ **No cold starts** on paid tiers
✅ **GPU support** at competitive prices
✅ **Better community** and documentation
✅ **Easier scaling** options
✅ **Built-in CI/CD** with git push
✅ **Real-time logs** in dashboard
✅ **Health monitoring** included

## 🔄 Migration from Render

1. Set up Hugging Face Space with databases
2. Test deployment thoroughly
3. Keep Render running during testing
4. Update frontend API URLs
5. Monitor for 24-48 hours
6. Scale down/remove Render if successful
7. Update DNS/CDN if needed

---

**Ready to deploy?** Run `./deploy_to_huggingface.sh` to get started! 🚀
