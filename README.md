# Furniture Inventory Simulator - multi-user, with a database

Azure Static Web Apps (Free) + Python API + Cosmos DB (free tier) + GitHub sign-in.

## Files
    index.html                    The page (looks + buttons)
    staticwebapp.config.json      Python version, and "API needs sign-in"
    api/host.json                 Azure Functions settings (leave alone)
    api/requirements.txt          Python packages: azure-functions, azure-cosmos
    api/simulate/function.json    Function answers GET and POST at /api/simulate
    api/simulate/__init__.py      Thin wrapper Azure calls
    api/simulate/handler.py       Who is asking? What do they want? Saves safely
    api/simulate/store.py         Talks to Cosmos DB
    api/simulate/inventory.py     The simulation rules (plain Python)

## Deploy (do the database FIRST)

### A. Create the free database
1. portal.azure.com > search "Azure Cosmos DB" > Create > "Azure Cosmos DB for NoSQL".
2. Resource group: use `inventory-rg` (create it if needed). Account name: any unique name.
3. Region: pick one your subscription allows (if you get "disallowed by Azure", try another).
4. IMPORTANT: switch ON "Apply Free Tier Discount". Only one account per subscription gets it,
   and it can only be set at creation.
5. Capacity mode: Provisioned throughput. Review + create > Create (takes a few minutes).
6. Open the account > Settings > Keys. Copy two values: URI and PRIMARY KEY.
   Keep the key private. Never put it in your code or on GitHub.

### B. Put the code on GitHub
7. New public repo `inventory-sim`. Upload `index.html`, `staticwebapp.config.json` and
   the whole `api` folder to the TOP LEVEL of the repo. Commit.

### C. Create the Static Web App
8. Azure portal > Static Web Apps > Create. Resource group `inventory-rg`, name `inventory-sim`,
   Plan **Free**, a region that works for you, Source GitHub, your repo, branch `main`.
9. Build Presets **Custom**. App location `/`. Api location `api`. Output location empty.
10. Create. Wait 1-3 minutes (GitHub "Actions" tab: green check).

### D. Connect the app to the database
11. Static Web App > Settings > Environment variables > Add:
      COSMOS_ENDPOINT = the URI from step 6
      COSMOS_KEY      = the primary key from step 6
      ALLOWED_USERS   = comma-separated GitHub usernames allowed in, e.g.  you,friend1,friend2
    Save. (If ALLOWED_USERS is empty, ANY GitHub user who finds the link can sign in
    and press reset, so set it.)
12. Open your site URL, click "Sign in with GitHub", approve, and you are in.
    First load creates the database and container automatically.

### E. Multiple users
Everyone on the ALLOWED_USERS list opens the same URL, signs in with their own GitHub
account, and sees the same warehouse. The page refreshes every 5 seconds.

## Troubleshooting
- "Missing app setting COSMOS_ENDPOINT": step 11 not saved. Save, wait a minute, refresh.
- "not on the allowed list": add that GitHub username to ALLOWED_USERS (exact spelling).
- "Server error": Static Web App > Functions / Application Insights, or re-check the key.
- Red X in GitHub Actions: `api` folder must be at repo top level; Api location = `api`.

## Keeping it free
- Cosmos: free tier = first 1000 RU/s + 25 GB. This app asks for 400 RU/s shared. Do NOT
  create other databases/containers with their own throughput in that account.
- Static Web Apps: stay on Free plan.
- Delete everything when done: delete `inventory-rg` (and the Cosmos account if it's elsewhere).
