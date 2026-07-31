# 🚀 Dr. Khare AI - Complete Deployment & Hosting Guide

This guide covers everything needed for a colleague to download, run, and ultimately host this project on the public internet. 

---

## Phase 1: Local Development Setup (On Their Computer)

When someone clones this repository from GitHub, their database will be completely empty. Here is the exact step-by-step process they need to follow to get it running on their computer.

### Step 1: Clone the Repository
```bash
git clone https://github.com/Krishlayy/dr-khare-ai.git
cd dr-khare-ai
```

### Step 2: Receive and Setup API Keys
Since `.env` files are never pushed to GitHub for security reasons, you must securely send them the `.env` file (e.g., via Slack or Discord).
1. They should place the `.env` file directly in the main `dr_khare_ai` folder.
2. The file must contain the `GROQ_API_KEY` and other necessary environment variables.

### Step 3: Start the Backend (Python/FastAPI)
1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install the Python dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Go back to the main directory and initialize the database (this creates `app.db`):
   ```bash
   cd ..
   python init_db.py
   ```
4. Start the backend server:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```
*The backend is now listening at `http://127.0.0.1:8000`.*

### Step 4: Start the Frontend (React/Vite)
1. Open a **new** terminal window and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
*The frontend is now available in the browser at `http://localhost:5173`.*

> [!TIP]
> **Data Restoration:** Because `chroma_db` is ignored in Git, the AI won't know anything about Dr. Khare initially. The new developer must either log into the Admin Dashboard (`http://localhost:5173/admin`) and upload the PDFs manually, or you must share your `backend/chroma_db/` folder as a ZIP file for them to extract.

---

## Phase 2: Production Hosting Strategy

Hosting this app requires deploying two separate pieces:
1. **The Frontend (Static Files)**: Hosted on a fast CDN like Vercel or Netlify.
2. **The Backend (Server & Database)**: Hosted on a Virtual Private Server (VPS) because it requires a persistent hard drive for ChromaDB and SQLite.

### Part A: Hosting the Frontend (Vercel)

Vercel is the easiest and free way to host a React/Vite app.

1. Create a free account at [Vercel.com](https://vercel.com/) and link it to your GitHub account.
2. Click **Add New Project** and select the `dr-khare-ai` repository.
3. **Configure the Project**:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend` (Important!)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. **Environment Variables**: Add your `VITE_API_URL` (this will be the URL of your hosted backend, which we will set up in Part B). For now, you can leave it blank or put a placeholder.
5. Click **Deploy**. Vercel will give you a public URL (e.g., `https://dr-khare-ai.vercel.app`).

### Part B: Hosting the Backend (VPS via DigitalOcean or Render)

Because the backend uses ChromaDB (which saves files locally) and SQLite, you **cannot** use serverless hosting like Heroku or AWS Lambda. You need a server with a persistent disk. We recommend **Render** (using a Persistent Disk) or a **DigitalOcean Droplet**.

#### Option 1: Using Render (Easiest)
1. Go to [Render.com](https://render.com/) and link your GitHub.
2. Create a new **Web Service**.
3. Select your `dr-khare-ai` repository.
4. **Configuration**:
   - **Root Directory**: `.` (leave empty or use root)
   - **Environment**: Python
   - **Build Command**: `pip install -r backend/requirements.txt && python init_db.py`
   - **Start Command**: `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. **Advanced Settings (Crucial)**:
   - Add a **Disk** to the service. 
   - Name: `chroma_data`
   - Mount Path: `/opt/render/project/src/backend/chroma_db`
   - *This ensures your AI doesn't forget its documents every time the server restarts!*
6. **Environment Variables**: Add your `GROQ_API_KEY`, `SECRET_KEY`, and set `ENVIRONMENT=production`.
7. Deploy! Render will give you a URL (e.g., `https://dr-khare-backend.onrender.com`).

#### Option 2: Using a VPS (DigitalOcean Droplet / AWS EC2)
If you want to use the `docker-compose.yml` file provided in the repository (which uses Postgres, Redis, and MinIO for a highly scalable setup):
1. Rent an Ubuntu server (Droplet) on DigitalOcean ($5-$10/mo).
2. SSH into the server: `ssh root@your_server_ip`
3. Install Docker and Git:
   ```bash
   apt update && apt install docker.io docker-compose git -y
   ```
4. Clone your repository:
   ```bash
   git clone https://github.com/Krishlayy/dr-khare-ai.git
   cd dr-khare-ai
   ```
5. Create your `.env` file on the server with nano:
   ```bash
   nano .env
   # Paste your GROQ keys and Postgres passwords here, then save.
   ```
6. Start the services using Docker:
   ```bash
   docker-compose up -d
   ```
7. Configure a Reverse Proxy (like Nginx or Caddy) to expose port 8000 to the public internet securely with SSL/HTTPS.

### Part C: Connecting the Two

Once your backend is live (e.g., `https://dr-khare-backend.onrender.com`):
1. Go back to Vercel (where your frontend is hosted).
2. Go to **Settings > Environment Variables**.
3. Update `VITE_API_URL` to point to your new backend URL.
4. Redeploy the frontend.

> [!IMPORTANT]  
> **CORS Configuration:** Ensure your FastAPI backend has CORS enabled and allows the Vercel frontend URL. You can check `backend/main.py` to ensure `allow_origins=["https://dr-khare-ai.vercel.app"]` (or `["*"]`) is set in your `CORSMiddleware`.

### Final Step: Embedding on Dr. Khare's Website
Once the Vercel frontend is live and talking to the backend successfully, you can embed the Vercel URL directly into Dr. Khare's official website using a simple iframe:

```html
<iframe 
  src="https://dr-khare-ai.vercel.app" 
  width="400" 
  height="600" 
  style="border:none; position:fixed; bottom:20px; right:20px; border-radius:12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"
></iframe>
```
