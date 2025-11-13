# Debugging Vercel Deployment Issues

## Common Issues

### 401 Authentication Required (Most Common)

If you see `HTTP/2 401` with "Authentication Required", your deployment has **Deployment Protection** enabled.

**Fix:**
1. Go to: https://vercel.com/wic-northwesterns-projects/wic-backend/settings/deployment-protection
2. Disable protection for **Production** deployments
3. Set to **"No Protection"** or **"Public"**
4. Save and test again

See `FIX_401.md` for detailed instructions.

### 404 NOT_FOUND

If you see `404 NOT_FOUND`, the routes aren't being detected.

## Step 1: Check Function Logs

```bash
cd wic_backend
npx vercel inspect <your-url> --logs
```

Or check in Vercel dashboard:
1. Go to: https://vercel.com/wic-northwesterns-projects/wic-backend
2. Click on the latest deployment
3. Click "View Function Logs" or "Runtime Logs"

## Step 2: Verify File Structure

Your files should be:
```
wic_backend/
├── api/
│   ├── __init__.py
│   ├── leaderboard.py
│   ├── events.py
│   └── utils.py
├── vercel.json
└── requirements.txt
```

## Step 3: Test Direct Function Invocation

Test if the function is being called at all:

```bash
# Test leaderboard
curl -v https://wic-backend-j676taptc-wic-northwesterns-projects.vercel.app/api/leaderboard

# Test events
curl -v https://wic-backend-j676taptc-wic-northwesterns-projects.vercel.app/api/events
```

The `-v` flag will show you the full HTTP response including headers.

## Step 4: Check Vercel Dashboard

1. Go to: https://vercel.com/wic-northwesterns-projects/wic-backend
2. Go to **Deployments** tab
3. Click on the latest deployment
4. Check:
   - Build logs (should show Python files being detected)
   - Function logs (runtime errors)
   - Check if functions are listed under "Functions" section

## Step 5: Verify Environment Variables

1. Go to: https://vercel.com/wic-northwesterns-projects/wic-backend/settings/environment-variables
2. Verify all variables are set:
   - `SHEET_ID`
   - `GOOGLE_API_KEY`
   - `NOTION_API_KEY`
   - `NOTION_DATABASE_ID`
3. Make sure they're set for **Production** environment
4. After adding/updating, **redeploy**

## Step 6: Check vercel.json

The vercel.json should be minimal for auto-detection:

```json
{
  "version": 2
}
```

Or you can try removing it entirely - Vercel should auto-detect Python files in `api/`.

## Step 7: Test with a Simple Function

Create a test endpoint to verify the setup:

Create `api/test.py`:
```python
def handler(request):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": '{"message": "Hello from Vercel!"}'
    }
```

Then test: `curl https://your-url/api/test`

## Step 8: Check Deployment Status

```bash
cd wic_backend
npx vercel ls
```

This shows all deployments and their status.

## Common Issues:

1. **404 on all routes**: Files not in `api/` directory or wrong file structure
2. **404 on specific route**: Route not matching, check vercel.json routes
3. **Function crashes**: Check logs for Python errors
4. **Environment variables not working**: Make sure they're set for Production and redeployed

## Quick Fix: Redeploy Everything

```bash
cd wic_backend
npx vercel --prod --force
```

The `--force` flag forces a new deployment even if nothing changed.

