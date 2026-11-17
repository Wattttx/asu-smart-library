# Free Cloud Hosting Guide
## Assam Skill University Central Library Smart Portal

This guide provides step-by-step instructions to deploy the application online for **100% free** with zero hosting costs, automatic SSL/HTTPS certificates, and a public URL you can share with your professors, students, and evaluators.

---

## 🎯 Comparison of Free Hosting Platforms

| Platform | Best For | Free Tier Features | Setup Complexity |
|---|---|---|---|
| **Vercel** | Fast CDN, serverless API, professional presentation | Free `.vercel.app` URL, instant GitHub integration, global edge network | ⭐ Very Easy |
| **Render.com** | Full-stack Python server with persistent SQLite DB | Free `.onrender.com` URL, native Python 3 runtime, auto-deploy from GitHub | ⭐ Very Easy (Recommended for DB persistence) |
| **PythonAnywhere** | Academic/university Python hosting | Free `user.pythonanywhere.com` URL, built-in SQLite browser, web console | ⭐ Easy |
| **Koyeb** | High-performance container/Python hosting | Free micro-instance, global edge, automatic SSL | ⭐ Easy |

---

## 🚀 Option 1: Deploy to Vercel (1-Click via GitHub)

All required configuration files (`vercel.json`, `api/index.py`, and `requirements.txt`) are already created and configured in this project.

### Step 1: Push your project to GitHub
1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd C:\Users\HP\.gemini\antigravity\scratch\asu_smart_library
   ```
2. Initialize git and commit:
   ```powershell
   git init
   git add .
   git commit -m "Initial commit - ASU Smart Library System"
   ```
3. Create a new repository on [GitHub](https://github.com/new) named `asu-smart-library`.
4. Link and push:
   ```powershell
   git branch -M main
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/asu-smart-library.git
   git push -u origin main
   ```

### Step 2: Import into Vercel
1. Go to [Vercel](https://vercel.com) and sign in (or sign up free with GitHub).
2. Click **"Add New..."** > **"Project"**.
3. Under *Import Git Repository*, find your `asu-smart-library` repo and click **"Import"**.
4. Leave all default settings as-is (Vercel automatically detects `vercel.json` and `api/index.py`).
5. Click **"Deploy"**.

Within 45 seconds, your app will be live at:
👉 **`https://asu-smart-library-xxxx.vercel.app`**

---

## 🚀 Option 2: Deploy to Render.com (Recommended for Persistent SQLite)

Render runs your full Python backend as a persistent service, keeping all newly cataloged books, student borrowings, and seat states active.

### Step 1: Push project to GitHub
Follow Step 1 from the Vercel guide above to push your code to a GitHub repository.

### Step 2: Deploy on Render
1. Go to [Render.com](https://render.com) and sign up/sign in (free with GitHub).
2. Click the **"New +"** button at the top right and select **"Web Service"**.
3. Select your `asu-smart-library` repository and click **"Connect"**.
4. Configure the service:
   * **Name**: `asu-smart-library`
   * **Region**: *Singapore (Southeast Asia)* or *Frankfurt* (closest to India)
   * **Branch**: `main`
   * **Runtime**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `python server.py`
   * **Instance Type**: **Free** ($0/month)
5. Click **"Create Web Service"**.

Render will install dependencies, seed the SQLite database, and launch the server. Within 2 minutes, your portal will be live at:
👉 **`https://asu-smart-library.onrender.com`**

---

## 🚀 Option 3: Deploy to PythonAnywhere (Academic Free Tier)

1. Sign up for a free account at [PythonAnywhere](https://www.pythonanywhere.com).
2. Open a **Bash Console** from your dashboard.
3. Clone your GitHub repository:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/asu-smart-library.git
   ```
4. Go to the **Web** tab:
   * Click **"Add a new web app"**.
   * Choose **Manual configuration** > **Python 3.10** or **3.11**.
   * In the **Virtualenv / WSGI configuration file**, point to `server.py` or launch the built-in HTTP server.

---

## 🔧 Cloud Compatibility Features Built-In

This project is already pre-configured with several cloud-ready mechanisms:
* **Dynamic Port Binding**: `server.py` reads `os.environ.get("PORT")` and binds to `0.0.0.0` automatically when running on cloud hosts like Render or Railway.
* **Serverless Read-Only Protection**: In `database.py`, if the root filesystem is read-only (as on Vercel), it automatically stages and executes writes on `/tmp/library.db` so transactions succeed without crashing.
* **Static Asset Routing**: Both the main portal (`/`), the design thinking deck (`/presentation.html`), and the PowerPoint download (`/Design_Thinking_Smart_Library.pptx`) are mapped to clean public routes in `vercel.json`.
