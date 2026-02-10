# OurTube (Project Revival)

Modern video downloader backend using FastAPI and `yt-dlp`. Designed to be exposed via Cloudflare Tunnel for frontend access (e.g., from Vercel).

## Architecture

- **Backend**: FastAPI app that wraps `yt-dlp`.
- **Frontend**: React/Vite app (running on Vercel).
- **Exposure**: Cloudflare Tunnel (`cloudflared`).

## Setup

### 1. Prerequisites
- Docker and Docker Compose installed.
- A Cloudflare account with Zero Trust enabled.

### 2. Environment Configuration
Copy the example environment file:
```bash
cp .env.example .env
```
Edit `.env` and add your `TUNNEL_TOKEN`.

### 3. Cloudflare Tunnel Setup
1. Go to the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/).
2. Navigate to **Networks** -> **Tunnels**.
3. Create a new tunnel (e.g., `ourtube-tunnel`).
4. Choose **Docker** as the environment.
5. Copy the **Token** provided in the command (it's the long string after `--token`).
6. Paste this token into your `.env` file as `TUNNEL_TOKEN`.
7. Configure a **Public Hostname** in the tunnel settings:
   - **Subdomain**: `api` (or whatever you prefer)
   - **Domain**: `yourdomain.com`
   - **Service**: `http://backend:8000` (Note: `backend` is the service name in `docker-compose.yml`)

### 4. Running the Project
```bash
docker-compose up -d --buildour-backend
```
If you want to run the tunnel alongside:
```bash
docker-compose up -d
```

## Portainer / Umbrel Deployment

To deploy this on your Umbrel Pi using Portainer:

1. **Open Portainer**: Navigate to your Umbrel dashboard and open the Portainer app.
2. **Create a Stack**:
   - Go to **Stacks** -> **Add stack**.
   - Give it a name (e.g., `ourtube-backend`).
   - Copy the contents of [`docker-compose.yml`](file:///home/xierra/Projects/OurTube/docker-compose.yml) into the Web editor.
3. **Environment Variables**:
   - Add a new environment variable in the "Environment variables" section:
     - **Name**: `TUNNEL_TOKEN`
     - **Value**: `your_cloudflare_tunnel_token_here`
4. **Deploy**: Click **Deploy the stack**.

> [!TIP]
> Since the frontend is on Vercel, ensure you point your frontend `API_URL` to the **Public Hostname** you configured in the Cloudflare Tunnel settings (e.g., `https://api.yourdomain.com`).

## API Endpoints

- `POST /api/downloads`: Start a download.
- `GET /api/downloads`: List completed downloads.
- `GET /api/download/{filename}`: Download a file.
- `DELETE /api/downloads/{filename}`: Delete a download.
- `WS /ws`: WebSocket for real-time progress updates.

## Notes
- Downloaded files are stored in the `downloads/` directory.
- The backend uses `yt-dlp` which is updated frequently to handle platform changes.
