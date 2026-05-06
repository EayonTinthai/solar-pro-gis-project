# Quick Fix: Blank Page Issue

## Problem
Opening https://storage.googleapis.com/solar-weather-frontend/index.html shows a blank page.

## Solution (5 Steps)

### 1. Get Clerk Key
Visit https://dashboard.clerk.com/ and copy your Publishable Key

### 2. Update .env
Edit `frontend/.env`:
```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
```

### 3. Rebuild
```bash
cd frontend
npm run build
```

### 4. Redeploy
```bash
gcloud storage cp -r dist/* gs://solar-weather-frontend/
```

### 5. Test
Open https://storage.googleapis.com/solar-weather-frontend/index.html in incognito mode

## Done!
You should now see the login page or application interface.

---

## Quick Commands

Check deployment status:
```bash
./check-deployment.ps1
```

View backend health:
```bash
curl https://solar-weather-api-715107904640.asia-southeast1.run.app/health
```

---

For detailed troubleshooting, see `TROUBLESHOOTING.md`
