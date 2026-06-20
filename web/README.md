# Teta Converter

A multi-format file converter web app built with FastAPI. Convert PDFs, images, audio, video, spreadsheets, and documents — all from your browser.

## Features

| Converter | Formats | Options |
|---|---|---|
| **PDF** | PDF → Markdown, JSON, Word (.docx) | — |
| **Image** | PNG, JPG, WebP, BMP, ICO, TIFF, GIF | Quality, resize |
| **Audio** | MP3, WAV, AAC, FLAC, OGG, M4A, WMA | Bitrate |
| **Video to GIF** | MP4, AVI, MOV, MKV, WebM → GIF | FPS, width, trim |
| **Spreadsheet** | XLSX, CSV, TSV, JSON, HTML, Markdown | — |
| **Document** | DOCX, HTML, Markdown, TXT → PDF, HTML | — |

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn
- **PDF Engine:** OpenDataLoader PDF (Java JAR)
- **Image:** Pillow
- **Audio:** Pydub (requires ffmpeg)
- **Video:** MoviePy (requires ffmpeg)
- **Spreadsheets:** Pandas, OpenPyXL
- **Documents:** python-docx, WeasyPrint, Markdown

---

## Local Development

### Prerequisites

- Python 3.11+
- Java 17+ (for PDF conversion)
- Maven (to build the Java JAR)
- ffmpeg (for audio/video conversion)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/youruser/teta-converter.git
cd teta-converter

# 2. Build the Java JAR (for PDF conversion)
cd java
mvn -B clean package -DskipTests
cd ..

# 3. Install Python dependencies
cd web
pip install -r requirements.txt

# 4. Install ffmpeg (if not installed)
# Windows: winget install ffmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg

# 5. Run the server
python server.py

# 6. Open http://localhost:8000
```

---

## Deploy to Railway

Railway is the easiest way to deploy. It supports Python natively and handles everything for you.

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/youruser/teta-converter.git
git push -u origin main
```

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub Repo**
3. Select your repo
4. Railway will auto-detect it's a Python app

### Step 3: Add a Start Command

In Railway dashboard, go to **Settings** → **Deploy** and set:

```
Start Command: cd web && uvicorn server:app --host 0.0.0.0 --port $PORT
```

### Step 4: Add ffmpeg Buildpack (for audio/video)

1. In your Railway project, go to **Settings** → **Build**
2. Add a **Nixpacks** or **Dockerfile** (see below)

### Recommended: Use a Dockerfile for Railway

Create a `Dockerfile` in the repo root:

```dockerfile
FROM python:3.11-slim

# Install Java (for PDF conversion)
RUN apt-get update && apt-get install -y \
    default-jdk \
    maven \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Java source and build JAR
COPY java/ java/
RUN cd java && mvn -B clean package -DskipTests

# Copy web app
COPY web/ web/
WORKDIR /app/web
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then in Railway:
1. Go to **Settings** → **Build**
2. Set **Builder** to **Dockerfile**
3. Deploy

### Step 5: Set Environment Variable (optional)

In Railway **Variables**, add:
```
PORT=8000
```

### Step 6: Generate Domain

1. Go to **Settings** → **Networking**
2. Click **Generate Domain** to get a public URL

---

## Deploy to CyberPanel (VPS with GUI only)

If you only have CyberPanel GUI access (no SSH), deployment is limited. Here are your options:

### Option A: CyberPanel with SSH (Recommended)

If you can get SSH access enabled:

```bash
# 1. SSH into your VPS
ssh root@your-vps-ip

# 2. Install dependencies
apt update && apt install -y default-jdk maven ffmpeg python3-pip python3-venv

# 3. Upload files (from your local machine)
scp -r web/ root@your-vps-ip:/home/teta-converter/
scp -r java/ root@your-vps-ip:/home/teta-converter/
scp Dockerfile root@your-vps-ip:/home/teta-converter/

# 4. Build and setup (on VPS)
cd /home/teta-converter
cd java && mvn -B clean package -DskipTests
cd ../web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Create systemd service
cat > /etc/systemd/system/teta-converter.service << 'EOF'
[Unit]
Description=Teta Converter
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/teta-converter/web
ExecStart=/home/teta-converter/web/venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable teta-converter
systemctl start teta-converter
```

### Option B: CyberPanel GUI Only (Limited)

With only File Manager access:

1. **Build locally first:**
   ```bash
   cd java && mvn -B clean package -DskipTests
   ```

2. **Upload via CyberPanel File Manager:**
   - Upload `web/` folder
   - Upload `java/opendataloader-pdf-cli/target/opendataloader-pdf-cli-0.0.0.jar`
   - Upload a startup script (see below)

3. **Create a startup script** (`start.sh`):
   ```bash
   #!/bin/bash
   export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
   export PATH=$JAVA_HOME/bin:$PATH
   cd /home/teta-converter/web
   pip install -r requirements.txt
   python server.py
   ```

4. **Use CyberPanel Cron Jobs** to run `start.sh` on boot

**Note:** This approach requires Java and ffmpeg to be pre-installed on the server, which is unlikely without SSH access.

### Option C: Docker on CyberPanel (If Docker is supported)

If your CyberPanel has Docker support:

1. Build the Docker image locally:
   ```bash
   docker build -t teta-converter .
   docker save teta-converter > teta-converter.tar
   ```

2. Upload `teta-converter.tar` via File Manager

3. Load and run via CyberPanel's Docker interface:
   ```bash
   docker load < teta-converter.tar
   docker run -d -p 8000:8000 --name teta-converter teta-converter
   ```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Web UI |
| `GET` | `/health` | Health check |
| `POST` | `/convert` | PDF → MD/JSON/DOCX |
| `POST` | `/convert-image` | Image format conversion |
| `POST` | `/convert-audio` | Audio format conversion |
| `POST` | `/video-to-gif` | Video → GIF |
| `POST` | `/convert-spreadsheet` | Spreadsheet conversion |
| `POST` | `/convert-document` | Document → PDF/HTML |

---

## Project Structure

```
teta-converter/
├── web/
│   ├── server.py          # FastAPI backend
│   ├── converter.py       # All conversion logic
│   ├── requirements.txt   # Python dependencies
│   └── static/
│       └── index.html     # Frontend UI
├── java/                  # OpenDataLoader PDF engine
├── Dockerfile             # For Docker/Railway deployment
└── README.md
```

---

## License

MIT License. Built by TetaDigitals.
