# Gmail MCP setup (getwarmth@gmail.com)

Warmth creates **drafts** in the Warmth Gmail inbox via a local MCP bridge. Lightfern then polishes them inside Gmail; a human sends.

## Architecture

```
Warmth API  →  GoogleMCPClient  →  http://localhost:3000/gmail/drafts
                                         ↓
                              Gmail MCP bridge (this server)
                                         ↓
                              Gmail API (OAuth as getwarmth@gmail.com)
```

## One-time setup

### 1. Google Cloud Console

Project: **warmth-gtm-hackathon**

1. **APIs & Services → Library** → enable **Gmail API**
2. **APIs & Services → OAuth consent screen** → External → add `getwarmth@gmail.com` as test user
3. **Credentials → Create credentials → OAuth client ID → Desktop app**
4. Download JSON → save as `warmth/google-oauth-client.json`

> Do **not** use the GCP **service account** JSON for Gmail. Personal Gmail requires OAuth.

### 2. Install deps

```bash
cd warmth
make install-gmail
```

### 3. OAuth (sign in as getwarmth@gmail.com)

```bash
make setup-gmail-mcp
```

Writes `warmth/google-gmail-oauth.json`.

### 4. Configure `.env`

```bash
GOOGLE_MCP_CREDENTIALS=google-gmail-oauth.json
GOOGLE_MCP_SERVER_URL=http://localhost:3000
WARMTH_CLIENT_EMAIL=getwarmth@gmail.com
WARMTH_CLIENT_NAME=Warmth
```

### 5. Run the bridge

```bash
make run-gmail-mcp
```

Health check: `curl http://localhost:3000/health`

### 6. Run Warmth API (separate terminal)

```bash
make run-api
```

After a meet/signal, drafts are created in the **getwarmth@gmail.com** Gmail drafts folder (when MCP is up).

## Troubleshooting

| Error | Fix |
|-------|-----|
| `service account` error | Point `GOOGLE_MCP_CREDENTIALS` at `google-gmail-oauth.json`, not `gcp-credentials.json` |
| `invalid_grant` | Re-run `make setup-gmail-mcp` |
| Connection refused :3000 | Start `make run-gmail-mcp` |
| Draft not visible | Confirm you’re logged into getwarmth@gmail.com in Gmail |

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Bridge status |
| POST | `/gmail/drafts` | Create draft |
| POST | `/gmail/send` | Send (Warmth uses drafts only in normal flow) |
