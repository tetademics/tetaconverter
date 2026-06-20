# Teta Converter — Features

## 1. PDF Converter
- **Input:** PDF files
- **Output formats:** Markdown (.md), JSON (.json), Word (.docx)
- **Engine:** Java JAR (opendataloader-pdf-cli) for high-fidelity extraction
- **Markdown output:** Preserves headings, tables, lists, code blocks, blockquotes, and horizontal rules
- **JSON output:** Structured JSON representation of PDF content
- **Word output:** Full .docx generation with formatted headings, bullet lists, tables with grid styling, code blocks (Courier New), blockquotes (italicized, colored), and horizontal dividers

## 2. Image Converter
- **Input:** Any image file (PNG, JPG, WebP, BMP, ICO, TIFF, GIF, and more)
- **Output formats:** PNG, JPG/JPEG, WebP, BMP, ICO, TIFF/TIF, GIF
- **Quality control:** Adjustable quality slider (1–100) for JPG and WebP
- **Resize:** Optional width and height inputs with aspect-ratio preservation (one dimension auto-calculated)
- **ICO generation:** Multi-size ICO files (16×16 to 256×256)
- **Transparency handling:** RGBA-to-RGB compositing on white background for JPG output
- **Format-specific optimization:** PNG optimize flag, JPG optimize flag

## 3. Audio Converter
- **Input:** Any audio file (MP3, WAV, AAC, FLAC, OGG, M4A, WMA, and more)
- **Output formats:** MP3, WAV, AAC, FLAC, OGG, M4A, WMA
- **Bitrate control:** 128 kbps, 192 kbps (default), 256 kbps, 320 kbps
- **Engine:** pydub + bundled ffmpeg (imageio_ffmpeg) for cross-platform support
- **MIME types:** Correct Content-Type headers for all formats

## 4. Video to GIF Converter
- **Input:** Video files (MP4, AVI, MOV, MKV, WebM, and more)
- **Output:** Animated GIF
- **FPS control:** Adjustable frames per second (1–30, default: 8)
- **Width control:** Output width in pixels (default: 480px, auto-scaled from source)
- **Trimming:** Start time (seconds) and duration (seconds) for clipping segments
- **Size optimization:** GIF palette optimization enabled, auto-downscale for large videos (>480px width)
- **Engine:** MoviePy + bundled ffmpeg with explicit ffmpeg binary path configuration

## 5. Spreadsheet Converter
- **Input:** XLSX, XLS, CSV, TSV, JSON
- **Output formats:** CSV, TSV, JSON, Excel (.xlsx), HTML, Markdown
- **Engine:** pandas for reading/writing, openpyxl for Excel output
- **Presetation:** Markdown tables with proper alignment, HTML tables with structure

## 6. Document Converter
- **Input:** DOCX, HTML/HTM, Markdown (.md), TXT
- **Output formats:** PDF, HTML
- **DOCX support:** Preserves headings, paragraphs, and tables with styling
- **Markdown rendering:** Tables, fenced code blocks, and standard markdown extensions
- **HTML support:** Direct HTML-to-PDF conversion
- **TXT support:** Plain text with pre-wrap formatting to PDF/HTML
- **Engine:** xhtml2pdf for PDF generation, python-docx for DOCX parsing, markdown library for MD rendering

---

## UI/UX Features
- **Dark theme:** GitHub-inspired dark color scheme (#0f1117 background)
- **Tab navigation:** 6 converter tabs with smooth switching (PDF, Image, Audio, Video, Spreadsheet, Document)
- **Drag-and-drop:** File drop zones with visual dragover feedback on all converters
- **Click-to-browse:** Click any dropzone to open file picker
- **File info display:** Shows selected filename and file size (MB) after selection
- **Loading spinner:** Animated spinner during conversion
- **File size display:** Shows output file size (KB) after successful conversion
- **Download link:** Clickable download link after conversion (not auto-download)
- **Error handling:** Clear red error messages for invalid files, unsupported formats, and server errors
- **Input validation:** PDF tab rejects non-PDF files; format-specific accept attributes on file inputs
- **Disabled buttons:** Convert buttons disabled until a file is selected

## Support/Donation Features
- **"Buy me a coffee" modal:** Shown after each successful conversion, before download
- **Donation link:** https://selar.com/showlove/tetadigitals?currency=USD
- **Skip option:** "Skip, download now" button to bypass the modal and download immediately
- **Coffee link redirect:** Clicking "Buy me a coffee" in the modal opens the donation page, then auto-downloads after 500ms
- **Footer links:** "Powered by TetaDigitals" branding + persistent "Buy me a coffee" link in footer

## Technical Features
- **FastAPI backend:** Async Python web server with uvicorn
- **RESTful API:** POST endpoints for each converter (`/convert`, `/convert-image`, `/convert-audio`, `/video-to-gif`, `/convert-spreadsheet`, `/convert-document`)
- **Health check:** `GET /health` endpoint returns `{"status": "ok"}`
- **Temp file cleanup:** Automatic cleanup of uploaded and generated files after each request
- **Error responses:** Structured JSON error responses with descriptive messages
- **MIME type headers:** Correct Content-Type and Content-Disposition headers for all downloads
- **Bundled ffmpeg:** Uses imageio_ffmpeg's bundled ffmpeg binary — no system ffmpeg installation required
- **Cross-platform:** Works on Windows, macOS, and Linux
- **Auto ffmpeg discovery:** Falls back through system PATH → imageio_ffmpeg bundle → error

## Deployment
- **Local development:** `python web/server.py` starts on http://localhost:8000
- **Dockerfile:** Python 3.11-slim + JDK + Maven + ffmpeg for containerized deployment
- **Railway:** One-click deploy via Dockerfile
- **CyberPanel:** Upload via File Manager, run via Cron Jobs GUI (no SSH required)
