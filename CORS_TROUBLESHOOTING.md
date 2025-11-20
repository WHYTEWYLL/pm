# CORS Troubleshooting for corta.ai

## Issue
CORS errors when accessing backend from `https://www.corta.ai`:
```
Access to XMLHttpRequest at 'https://backend-production-d593.up.railway.app/api/auth/register' 
from origin 'https://www.corta.ai' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Solution Steps

### 1. Verify Backend is Deployed with Latest Code
The CORS configuration in `app/api/main.py` includes:
- `https://www.corta.ai`
- `https://corta.ai`

**Make sure you've deployed the latest code to Railway!**

### 2. Check Railway Environment Variables
In your Railway dashboard, verify these environment variables are set:

```bash
ENV=production
FRONTEND_ORIGIN=https://www.corta.ai,https://corta.ai  # Optional, already in code
```

### 3. Verify CORS Configuration is Active
The code should automatically include `corta.ai` domains. To verify:

1. Check Railway logs for CORS debug messages (in development mode)
2. Test the backend directly:
   ```bash
   curl -X OPTIONS https://backend-production-d593.up.railway.app/api/auth/register \
     -H "Origin: https://www.corta.ai" \
     -H "Access-Control-Request-Method: POST" \
     -v
   ```
   
   You should see `Access-Control-Allow-Origin: https://www.corta.ai` in the response headers.

### 4. Check Frontend API URL
Make sure your frontend is pointing to the correct backend:

```bash
# In frontend/.env.local or production environment
NEXT_PUBLIC_API_URL=https://backend-production-d593.up.railway.app
```

### 5. Common Issues

#### Issue: Backend not deployed with latest code
**Fix**: Push and deploy the latest code to Railway

#### Issue: CORS middleware not working
**Fix**: Check Railway logs for errors. The middleware should be added before routes.

#### Issue: Preflight requests failing
**Fix**: Make sure `allow_methods=["*"]` includes OPTIONS (it does with `*`)

#### Issue: Credentials not being sent
**Fix**: Frontend needs to send `credentials: 'include'` in axios requests

### 6. Test CORS Manually

```bash
# Test from command line
curl -X POST https://backend-production-d593.up.railway.app/api/auth/register \
  -H "Origin: https://www.corta.ai" \
  -H "Content-Type: application/json" \
  -H "Access-Control-Request-Method: POST" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test"}' \
  -v
```

Look for these headers in the response:
- `Access-Control-Allow-Origin: https://www.corta.ai`
- `Access-Control-Allow-Credentials: true`

### 7. Railway-Specific Notes

- Railway may cache deployments - try redeploying
- Check Railway service logs for CORS-related errors
- Verify the service is actually running the latest code

### 8. Quick Fix: Force Redeploy

If CORS still isn't working after deploying:

1. **Redeploy on Railway**: 
   - Go to Railway dashboard
   - Click "Redeploy" on your backend service
   - Or push a new commit to trigger deployment

2. **Verify deployment**:
   - Check Railway logs for startup messages
   - Verify the service is healthy

3. **Test again** from `https://www.corta.ai`

## Debugging

Add this temporary endpoint to check CORS config:

```python
@app.get("/debug/cors")
async def debug_cors():
    return {
        "allowed_origins": default_origins,
        "env": os.getenv("ENV"),
        "frontend_origin": os.getenv("FRONTEND_ORIGIN"),
    }
```

Then visit: `https://backend-production-d593.up.railway.app/debug/cors`

## Still Not Working?

1. Check Railway service logs for errors
2. Verify the backend service is actually running
3. Check if there's a proxy/load balancer in front that might be stripping CORS headers
4. Verify the frontend is making requests to the correct backend URL


