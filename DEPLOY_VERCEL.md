# Deploying Backend to Vercel

This guide explains how to deploy the Flask backend as Vercel serverless functions.

## Structure

The backend has been converted to Vercel serverless functions:
- `api/leaderboard.py` - Leaderboard endpoint
- `api/events.py` - Events endpoint
- `api/utils.py` - Shared utilities

**Important**: Vercel automatically detects Python files in the `api/` directory. The files should be accessible at:
- `/api/leaderboard` → `api/leaderboard.py`
- `/api/events` → `api/events.py`

## Deployment Steps

### 1. Install Vercel CLI

**Option A: Install locally (Recommended - no permissions needed)**
```bash
cd wic_backend
npm install vercel --save-dev
```

Then use `npx vercel` instead of `vercel` for all commands.

**Option B: Use npx (No installation needed)**
```bash
npx vercel
```

**Option C: Install globally (requires sudo)**
```bash
sudo npm i -g vercel
```

**Option D: Fix npm permissions (Best long-term solution)**
```bash
# Create a directory for global packages
mkdir ~/.npm-global

# Configure npm to use the new directory
npm config set prefix '~/.npm-global'

# Add to your ~/.bashrc or ~/.zshrc
export PATH=~/.npm-global/bin:$PATH

# Reload shell
source ~/.bashrc  # or source ~/.zshrc

# Now install without sudo
npm i -g vercel
```

### 2. Login to Vercel
```bash
# If installed locally:
npx vercel login

# If installed globally:
vercel login
```

### 3. Deploy from Backend Directory

**Option A: Deploy as Separate Project (Recommended)**
```bash
cd wic_backend

# If using npx or local install:
npx vercel

# If installed globally:
vercel
```

Follow the prompts:
- Set up and deploy? **Yes**
- Which scope? (Select your account)
- Link to existing project? **No**
- Project name? `wic-backend` (or your preferred name)
- Directory? `./` (current directory)
- Override settings? **No**

**Option B: Deploy in Same Project as Frontend (Monorepo)**

If your frontend and backend are in the same repository, you can deploy both from the root:

1. Create `vercel.json` in the **root** directory (`/home/nicolelu/git/wic_website/`):
```json
{
  "version": 2,
  "builds": [
    {
      "src": "wic_frontend/package.json",
      "use": "@vercel/next"
    },
    {
      "src": "wic_backend/api/**/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/wic_backend/api/$1.py"
    },
    {
      "src": "/(.*)",
      "dest": "/wic_frontend/$1"
    }
  ]
}
```

2. Deploy from root:
```bash
cd /home/nicolelu/git/wic_website
npx vercel
```

3. When prompted:
   - Link to existing project? **Yes**
   - Select your existing `wic-frontend` project
   - This will add the backend API routes to your existing frontend deployment

**Note**: With Option B, your API will be at:
- `https://wic-frontend.vercel.app/api/leaderboard`
- `https://wic-frontend.vercel.app/api/events`

And you'd set `NEXT_PUBLIC_API_URL` to your frontend URL (or use relative paths like `/api/leaderboard`).

### 4. Set Environment Variables

After deployment, set environment variables in Vercel dashboard:

1. Go to your project on [vercel.com](https://vercel.com)
2. Go to **Settings** → **Environment Variables**
3. Add the following:
   - `NOTION_API_KEY` = your Notion API key
   - `NOTION_DATABASE_ID` = your Notion database ID
   - `SHEET_ID` = your Google Sheets ID
   - `GOOGLE_API_KEY` = your Google Sheets API key

4. **Important**: After adding env vars, redeploy:
   - Go to **Deployments** tab
   - Click the three dots on latest deployment
   - Click **Redeploy**

### 5. Get Your Backend URL

After deployment, Vercel will show you a preview URL like:
- `https://wic-backend-kgouueyju-wic-northwesterns-projects.vercel.app`

**To get your production domain:**
1. Go to your project: https://vercel.com/wic-northwesterns-projects/wic-backend
2. Go to **Settings** → **Domains**
3. Your production domain will be: `https://wic-backend.vercel.app` (or you can add a custom domain)

**Your API endpoints will be:**
- `https://wic-backend.vercel.app/api/leaderboard` (or use the preview URL for testing)
- `https://wic-backend.vercel.app/api/events` (or use the preview URL for testing)

**Note:** The preview URL (with the hash) works immediately. The production domain (`wic-backend.vercel.app`) is available after the first deployment.

### 6. Update Frontend Environment Variable

**If deployed as separate project (Option A):**
In your **frontend** Vercel project:
1. Go to **Settings** → **Environment Variables**
2. Set `NEXT_PUBLIC_API_URL` = `https://wic-backend.vercel.app` (your backend URL)
3. Redeploy the frontend

**If deployed in same project (Option B):**
You can either:
- Set `NEXT_PUBLIC_API_URL` = `https://wic-frontend.vercel.app` (same domain)
- Or update `api-config.ts` to use relative paths:
  ```typescript
  export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
  export const API_ENDPOINTS = {
    leaderboard: `${API_BASE_URL}/api/leaderboard`,
    events: `${API_BASE_URL}/api/events`,
  } as const;
  ```
  Then set `NEXT_PUBLIC_API_URL` to empty string or omit it to use relative paths.

## Testing

Test your endpoints:
```bash
curl https://wic-backend.vercel.app/api/leaderboard
curl https://wic-backend.vercel.app/api/events
```

## Troubleshooting 404 Errors

If you get a 404 NOT_FOUND error:

1. **Check file structure**: Ensure files are in `api/` directory:
   ```
   wic_backend/
   ├── api/
   │   ├── leaderboard.py
   │   ├── events.py
   │   └── utils.py
   └── vercel.json
   ```

2. **Check Vercel logs**: 
   ```bash
   npx vercel inspect <your-url> --logs
   ```

3. **Verify deployment**: Check the Vercel dashboard → Deployments → View Function Logs

4. **Redeploy**: After making changes, redeploy:
   ```bash
   npx vercel --prod
   ```

5. **Check handler function**: Ensure each Python file has a `handler(request)` function that returns a dict with `statusCode`, `headers`, and `body`.

## Local Development

For local development, continue using the Flask app:
```bash
cd wic_backend
source venv/bin/activate
python app.py
```

The serverless functions are only used in production on Vercel.

## Troubleshooting

- **404 errors**: 
  - Check that files are in `api/` directory
  - Verify `handler(request)` function exists in each Python file
  - Check Vercel function logs in dashboard
  - Ensure `vercel.json` is minimal (or remove it to use auto-detection)
  
- **500 errors**: Check Vercel function logs in dashboard
- **Missing env vars**: Ensure all environment variables are set and project is redeployed
- **CORS errors**: CORS headers are already included in the serverless functions
