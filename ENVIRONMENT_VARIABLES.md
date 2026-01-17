# Environment Variables Setup for Hugging Face

## 🔧 How to Add Environment Variables to Your Space

### Step 1: Go to Space Settings
**URL**: https://huggingface.co/spaces/oyejidet/agenthub-backend/settings

### Step 2: Find "Variables and secrets" Section
Look for either:
- "Variables and secrets" tab
- "Repository secrets" section
- "Settings" → "Secrets"

### Step 3: Click "New secret"

### Step 4: Add Each Variable Below

---

## 📋 Required Environment Variables

### **Database Connections** (All 3 Required)

#### PostgreSQL Database
```
Name: DATABASE_URL
Value: postgresql://username:password@host:port/database_name
```
**Example**:
```
postgresql://myuser:mypass123@ep-cool-grass-123456.us-east-2.aws.neon.tech/agenthub?sslmode=require
```

#### MongoDB Database
```
Name: MONGODB_URL
Value: mongodb://username:password@host:port/database_name
```
**Example**:
```
mongodb+srv://myuser:mypass123@cluster0.abc123.mongodb.net/agenthub?retryWrites=true&w=majority
```

#### Redis Cache
```
Name: REDIS_URL
Value: redis://default:password@host:port
```
**Example**:
```
redis://default:mypass123@upstash-redis-host.upstash.io:6379
```

---

## 🤖 LLM Provider API Keys (At Least One Required)

Choose at least one LLM provider:

### OpenAI (Recommended)
```
Name: OPENAI_API_KEY
Value: sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
Get from: https://platform.openai.com/api-keys

### Anthropic Claude
```
Name: ANTHROPIC_API_KEY
Value: sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
Get from: https://console.anthropic.com/settings/keys

### Google AI
```
Name: GOOGLE_API_KEY
Value: AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
Get from: https://makersuite.google.com/app/apikey

### Groq (Fast & Free Alternative)
```
Name: GROQ_API_KEY
Value: gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
Get from: https://console.groq.com/keys

---

## 🔐 Security Variables (Recommended)

### JWT Secret Key
```
Name: JWT_SECRET_KEY
Value: <generate-a-random-32-character-string>
```

**Generate one**:
```bash
# On Mac/Linux
openssl rand -hex 32

# Or use this
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### CORS Origins
```
Name: ALLOWED_ORIGINS
Value: https://your-frontend.com,https://oyejidet-agenthub-backend.hf.space
```

---

## 🎯 Optional Variables

### Environment
```
Name: ENVIRONMENT
Value: production
```

### Log Level
```
Name: LOG_LEVEL
Value: INFO
```

### Port (Usually not needed - HF uses 7860 by default)
```
Name: PORT
Value: 7860
```

---

## 🆓 Free Database Setup Guide

### PostgreSQL - Neon (Recommended)

1. Go to: https://neon.tech
2. Sign up (free)
3. Create new project → "Create project"
4. Copy connection string (looks like):
   ```
   postgresql://username:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
   ```
5. Use this as your `DATABASE_URL`

### MongoDB - MongoDB Atlas

1. Go to: https://www.mongodb.com/cloud/atlas
2. Sign up (free)
3. Create cluster → "Build a Database" → "Free tier"
4. Create database user (remember username/password)
5. Network Access → Add IP → "Allow from anywhere" (0.0.0.0/0)
6. Connect → "Connect your application" → Copy connection string
7. Replace `<password>` and `<dbname>` in the string
8. Use this as your `MONGODB_URL`

### Redis - Upstash (Recommended)

1. Go to: https://upstash.com
2. Sign up (free)
3. Create Database → Select "Global" → Create
4. Copy the connection string from "Redis Connect" section
5. Use format: `redis://default:password@host:port`
6. Use this as your `REDIS_URL`

---

## 📝 Complete Example Configuration

Here's what your secrets should look like:

```bash
# Databases
DATABASE_URL=postgresql://myuser:pass@ep-cool-123.us-east-2.aws.neon.tech/agenthub?sslmode=require
MONGODB_URL=mongodb+srv://myuser:pass@cluster0.abc123.mongodb.net/agenthub?retryWrites=true&w=majority
REDIS_URL=redis://default:pass@upstash-host.upstash.io:6379

# LLM Provider (choose at least one)
OPENAI_API_KEY=sk-proj-abc123def456...
# ANTHROPIC_API_KEY=sk-ant-abc123...
# GOOGLE_API_KEY=AIza123...

# Security
JWT_SECRET_KEY=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
ALLOWED_ORIGINS=https://your-frontend.com,https://another-domain.com

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## ✅ Verification Checklist

After adding all variables:

- [ ] DATABASE_URL (PostgreSQL connection)
- [ ] MONGODB_URL (MongoDB connection)
- [ ] REDIS_URL (Redis connection)
- [ ] At least one LLM API key (OpenAI/Anthropic/Google)
- [ ] JWT_SECRET_KEY (generated random string)
- [ ] ALLOWED_ORIGINS (your frontend URLs)

---

## 🔄 After Adding Variables

1. **Save all secrets** in Hugging Face Space settings
2. **Restart the Space** (it may restart automatically)
3. **Check logs** at: https://huggingface.co/spaces/oyejidet/agenthub-backend
4. **Wait 2-3 minutes** for the app to start
5. **Test the health endpoint**: https://oyejidet-agenthub-backend.hf.space/health

---

## 🆘 Troubleshooting

### "Cannot connect to database"
- Check DATABASE_URL format is correct
- Verify database allows connections from Hugging Face IPs
- For Neon: ensure `?sslmode=require` is in the URL

### "MongoDB connection failed"
- Check MONGODB_URL has correct username/password
- Verify MongoDB Atlas allows connections from anywhere (0.0.0.0/0)
- Ensure `?retryWrites=true&w=majority` is in the URL

### "Redis connection timeout"
- Verify REDIS_URL format: `redis://default:password@host:port`
- Check Upstash allows public access

### "No LLM provider configured"
- Ensure at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY is set
- Verify API key is valid and has credits

---

## 📚 Additional Resources

- **Hugging Face Spaces Docs**: https://huggingface.co/docs/hub/spaces-overview
- **Environment Variables Guide**: https://huggingface.co/docs/hub/spaces-overview#managing-secrets
- **Your Space Settings**: https://huggingface.co/spaces/oyejidet/agenthub-backend/settings

---

**Need help?** Check the Hugging Face Discord: https://discord.gg/JfAtkvEtRb
