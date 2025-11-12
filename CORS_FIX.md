# CORS Fix for corta.ai

## Issue
CORS errors when trying to login or register from `https://www.corta.ai/register`

## Solution
Updated CORS configuration in `app/api/main.py` to include production domains:
- `https://www.corta.ai`
- `https://corta.ai`

## Changes Made

### Backend (`app/api/main.py`)
- Added `corta.ai` domains to allowed origins
- Both `www` and non-`www` versions are supported
- Production origins are always included (not just in production mode)

## Environment Variables

Make sure your backend has the correct API URL configured:

```bash
# Backend environment variables
FRONTEND_ORIGIN=https://www.corta.ai,https://corta.ai  # Optional, already included by default
```

## Frontend Configuration

Make sure your frontend has the correct API URL:

```bash
# Frontend .env.local or production environment
NEXT_PUBLIC_API_URL=https://your-api-domain.com  # Your backend API URL
```

## Testing

After deploying the backend changes:

1. **Test registration** from `https://www.corta.ai/register`
   - Should work without CORS errors

2. **Test login** from `https://www.corta.ai/login`
   - Should work without CORS errors

3. **Check browser console**
   - No CORS errors should appear
   - Network requests should succeed

## Common Issues

### Still getting CORS errors?
1. **Check backend is deployed** with the latest code
2. **Verify API URL** in frontend matches your backend domain
3. **Check browser console** for exact error message
4. **Verify credentials** are being sent correctly

### API URL Configuration
- Frontend at: `https://www.corta.ai`
- Backend API should be at: `https://api.corta.ai` (or your backend domain)
- Make sure `NEXT_PUBLIC_API_URL` points to your backend

## Next Steps

1. **Deploy backend** with updated CORS configuration
2. **Verify frontend** has correct `NEXT_PUBLIC_API_URL`
3. **Test registration/login** from production domain
4. **Monitor logs** for any CORS-related issues

