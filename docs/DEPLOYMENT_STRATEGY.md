# Deployment Strategy

---

## Current State: Local / Demo

The system runs fully locally on a single machine:

```
python3 rag/api.py
→ http://localhost:8000
```

No external infrastructure required beyond an Anthropic API key.

---

## Path to Production

### Option A — Internal Server (Recommended)

Deploy on a CACEIS internal server (on-premise), accessible via VPN:

```
gunicorn rag.api:app --workers 2 --bind 0.0.0.0:8000
# or
uvicorn rag.api:app --host 0.0.0.0 --port 8000 --workers 2
```

**Requirements:**
- Python 3.9+ runtime
- ~1GB disk (ChromaDB + dependencies)
- Anthropic API key stored as environment variable (not in code)
- HTTPS termination via nginx reverse proxy

**Why on-premise:** Source HR files never leave CACEIS infrastructure. ChromaDB index stays local. Only anonymised BU aggregates reach Anthropic.

---

### Option B — Cloud (Azure / AWS)

If cloud deployment is required:

1. Package the app as a Docker container (Dockerfile to be created)
2. Deploy ChromaDB on a persistent volume (not ephemeral storage)
3. Store `ANTHROPIC_API_KEY` in Azure Key Vault / AWS Secrets Manager
4. Do NOT mount source data files — re-run `ingest_all.py` post-deploy with files uploaded to secure storage

**GDPR note:** Ensure the cloud region is EU-based if processing data from EU employees.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key — never commit this |

Copy `.env.example` to `.env` and fill in values.

---

## Scaling Considerations

- ChromaDB is single-node by default; sufficient for 26 BUs and a small user base
- Claude API calls are on-demand (per scorecard generation); no background jobs needed
- The dashboard is a static HTML file — can be served from any CDN or web server

---

## Security Checklist

- [ ] `.env` is gitignored and never committed
- [ ] API key is rotated if accidentally exposed
- [ ] CORS is restricted to the internal domain in production (currently `allow_origins=["*"]`)
- [ ] Source data files are access-controlled on the server
- [ ] HTTPS is enforced (no HTTP in production)
