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
