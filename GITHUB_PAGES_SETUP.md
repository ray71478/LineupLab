# GitHub Pages Setup Guide for LineupLab

## Current Status

✅ Code is configured for GitHub Pages
✅ GitHub Actions workflow created for automatic deployment
⚠️ Need to authenticate and push to repository

## Authentication Options

Since the repository is under `ray71478` but your local git is configured for `raybargas`, you need to authenticate. Choose one method:

### Option 1: Personal Access Token (Easiest)

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name it "LineupLab Deploy"
4. Select scopes: `repo` (full control)
5. Copy the token (you'll only see it once!)

6. Use it when pushing:
```bash
cd /Users/raybargas/Documents/Cortex
git push https://<YOUR_TOKEN>@github.com/ray71478/LineupLab.git main
```

### Option 2: SSH Key (Recommended for ongoing use)

1. Check if you have SSH keys:
```bash
ls -la ~/.ssh/id_*.pub
```

2. If you don't have one, create it:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

3. Add to GitHub:
   - Copy the public key: `cat ~/.ssh/id_ed25519.pub`
   - Go to GitHub.com → Settings → SSH and GPG keys → New SSH key
   - Paste and save

4. Update remote to use SSH:
```bash
cd /Users/raybargas/Documents/Cortex
git remote set-url origin git@github.com:ray71478/LineupLab.git
git push -u origin main
```

### Option 3: GitHub CLI (Simple)

1. Install GitHub CLI (if not installed):
```bash
brew install gh
```

2. Authenticate:
```bash
gh auth login
```

3. Push:
```bash
cd /Users/raybargas/Documents/Cortex
git push -u origin main
```

## After Pushing

Once code is pushed, enable GitHub Pages:

1. Go to: https://github.com/ray71478/LineupLab/settings/pages
2. Under "Source", select:
   - Branch: `gh-pages`
   - Folder: `/ (root)`
3. Click "Save"

The site will be available at:
- **https://ray71478.github.io/LineupLab/**

## Automatic Deployment

The GitHub Actions workflow will automatically:
- Build the frontend when you push to `main`
- Deploy to the `gh-pages` branch
- Your site updates automatically!

## Manual Deployment (Alternative)

If you prefer manual deployment:

```bash
cd frontend
npm install -g gh-pages
npm run deploy
```

## Troubleshooting

### If the site shows 404:
- Wait 5-10 minutes after first push (GitHub needs time to build)
- Check Actions tab for deployment status
- Verify base path in `vite.config.ts` is `/LineupLab/`

### If assets don't load:
- Make sure `base: '/LineupLab/'` is set in `vite.config.ts`
- Clear browser cache
- Check browser console for errors

### If API calls fail:
- The frontend expects API at `http://localhost:8000` (for local dev)
- For production, you'll need to update the API URL in your frontend config
- Consider using environment variables for API URL

## Next Steps

1. ✅ Push code to repository (choose authentication method above)
2. ✅ Enable GitHub Pages in repository settings
3. ✅ Test the site at https://ray71478.github.io/LineupLab/
4. ⚠️ Update API endpoint for production use (backend needs to be deployed separately)

