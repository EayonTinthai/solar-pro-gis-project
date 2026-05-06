# Troubleshooting Guide

## Issue: Blank Page After Deployment

### Symptoms
- Opening https://storage.googleapis.com/solar-weather-frontend/index.html shows a blank white page
- No content is visible
- Browser console may show errors related to Clerk

### Root Cause
The application requires a valid Clerk authentication key to initialize. If the key is missing, invalid, or expired, the app will fail to load.

### Solution

#### Step 1: Get Valid Clerk Publishable Key

1. Visit https://dashboard.clerk.com/
2. Sign in with your account (or create a new one)
3. Create a new application or select your existing application
4. Navigate to "API Keys" section
5. Copy the "Publishable Key" (starts with `pk_test_` or `pk_live_`)

#### Step 2: Update Environment Configuration

Edit the file `frontend/.env`:

```bash
# Replace with your actual Clerk key
VITE_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_ACTUAL_KEY_HERE

# Verify other settings are correct
VITE_BUILDINGS_API_URL=https://solar-weather-api-715107904640.asia-southeast1.run.app
VITE_STRIPE_PRO_PRICE_DISPLAY="฿299 / month"
```

#### Step 3: Rebuild Frontend

```bash
cd solar-panel-detection-main-fromFonend/frontend
npm run build
```

#### Step 4: Redeploy to Cloud Storage

```bash
gcloud storage cp -r dist/* gs://solar-weather-frontend/
```

#### Step 5: Clear Browser Cache

- Windows/Linux: Press `Ctrl + Shift + R`
- Mac: Press `Cmd + Shift + R`
- Or open the URL in incognito/private mode

#### Step 6: Verify Deployment

Open https://storage.googleapis.com/solar-weather-frontend/index.html

You should now see the login page or the application interface.

## Issue: API Connection Errors

### Symptoms
- Frontend loads but shows "Failed to fetch" errors
- Weather data doesn't load
- Building data doesn't appear

### Solution

#### Check API Health

```bash
curl https://solar-weather-api-715107904640.asia-southeast1.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "weather_api": "available"
}
```

#### Verify CORS Configuration

The backend API should allow requests from the frontend domain. Check the backend CORS settings in `backend/api_weather_only.py` or `backend/api_bigquery.py`.

#### Check Environment Variables

Verify `frontend/.env` has the correct API URL:
```bash
VITE_BUILDINGS_API_URL=https://solar-weather-api-715107904640.asia-southeast1.run.app
```

## Issue: Weather Data Not Loading

### Symptoms
- Weather panel shows loading state indefinitely
- Weather toggle button doesn't work
- Console shows 401 or 403 errors

### Solution

#### Verify Weather API Key

Check that the backend has the correct WxTech API key in `backend/.env`:
```bash
WXTECH_API_KEY=pEfaXCQdGHdWpuSbGM0k2CoxnCWToODm26xfs890
```

#### Test Weather API Directly

```bash
curl "https://solar-weather-api-715107904640.asia-southeast1.run.app/weather/forecast?lat=13.7563&lon=100.5018"
```

Expected response should include weather data with temperature, precipitation, and solar radiation.

## Issue: Authentication Errors

### Symptoms
- "Unauthorized" errors
- Can't access protected features
- Clerk authentication fails

### Solution

#### Verify Clerk Configuration

1. Check that `VITE_CLERK_PUBLISHABLE_KEY` is set correctly
2. Ensure the key matches your Clerk application
3. Verify the Clerk application is active (not suspended)

#### Check Clerk Dashboard

1. Go to https://dashboard.clerk.com/
2. Check application status
3. Verify API keys are active
4. Check usage limits haven't been exceeded

## Issue: Build Errors

### Symptoms
- `npm run build` fails
- Vite build errors
- Missing dependencies

### Solution

#### Clean Install Dependencies

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### Check Node Version

Ensure you're using Node.js 18 or higher:
```bash
node --version
```

If needed, update Node.js from https://nodejs.org/

## Issue: Deployment Fails

### Symptoms
- `gcloud storage cp` fails
- Permission denied errors
- Bucket not found

### Solution

#### Verify GCP Authentication

```bash
gcloud auth list
gcloud config get-value project
```

Should show:
- Active account: your email
- Project: trim-descent-452802-t2

#### Re-authenticate if Needed

```bash
gcloud auth login
gcloud config set project trim-descent-452802-t2
```

#### Verify Bucket Exists

```bash
gcloud storage ls gs://solar-weather-frontend/
```

If bucket doesn't exist, create it:
```bash
gcloud storage buckets create gs://solar-weather-frontend --location=asia-southeast1 --public-access-prevention=unspecified
```

## Getting Help

### Check Logs

#### Frontend Console Logs
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Look for error messages

#### Backend Logs
```bash
gcloud run services logs read solar-weather-api --region=asia-southeast1 --limit=50
```

### Test API Endpoints

Use the test script:
```bash
./test-weather-integration.ps1
```

### Contact Support

If issues persist:
1. Check the error messages in browser console
2. Review backend logs
3. Verify all environment variables are set correctly
4. Ensure API keys are valid and not expired

## Common Error Messages

### "Missing VITE_CLERK_PUBLISHABLE_KEY"
- **Cause**: Clerk key not set in `.env`
- **Fix**: Add valid Clerk key to `frontend/.env` and rebuild

### "Failed to fetch"
- **Cause**: API endpoint unreachable or CORS issue
- **Fix**: Verify API URL and check CORS configuration

### "401 Unauthorized"
- **Cause**: Invalid or missing authentication
- **Fix**: Check Clerk configuration and API keys

### "Network Error"
- **Cause**: Backend API is down or unreachable
- **Fix**: Check API health endpoint and backend logs

### "Cannot read properties of undefined"
- **Cause**: Missing data or API response format mismatch
- **Fix**: Check API response format matches expected structure

## Performance Issues

### Slow Loading
- Check network tab in browser DevTools
- Verify API response times
- Consider enabling CDN for Cloud Storage

### High Memory Usage
- Clear browser cache
- Check for memory leaks in console
- Reduce map tile cache size

## Security Considerations

### API Keys
- Never commit API keys to version control
- Use environment variables for all secrets
- Rotate keys regularly

### CORS Configuration
- Only allow necessary origins
- Don't use wildcard (*) in production
- Verify CORS headers in API responses

## Additional Resources

- **Clerk Documentation**: https://clerk.com/docs
- **Vite Documentation**: https://vitejs.dev/
- **Google Cloud Run**: https://cloud.google.com/run/docs
- **WxTech API**: Contact WxTech support for API documentation
