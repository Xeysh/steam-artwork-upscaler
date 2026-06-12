# Steam Artwork Upscaler

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Framework](https://img.shields.io/badge/Engine-Real--ESRGAN-orange.svg)](https://github.com/xinntao/Real-ESRGAN)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A brief project to upscale Steam artwork (`.gif` files) using **Real-ESRGAN**. 

> **Default Model Note:** This project uses **`realesrgan-x4plus-anime`** by default.

## Prerequisites & Installation

### Step 1: Download FFmpeg & FFprobe

1. Go to the official binaries repository: **[ffbinaries.com/downloads](https://ffbinaries.com/downloads)**
2. Download the appropriate versions for your operating system:
   * `ffmpeg.exe`
   * `ffprobe.exe`

### Step 2: Project Structure Setup

1. Move the downloaded `ffmpeg.exe` and `ffprobe.exe` files into the **`realesrgan`** folder.
2. Place your target `.gif` file (e.g., `input.gif`) directly into the **root (main) directory** of the project.

Your repository layout must look exactly like this before running the script:
```text
📁 Real-ESRGAN-GIF-Upscaler/
│
├── 📄 run.py                     # Main execution script
├── 🖼️ input.gif                  # Your target GIF file (Main Directory)
│
└── 📁 realesrgan/                # Core engine directory
    ├── 📄 ffmpeg.exe             # Placed here
    ├── 📄 ffprobe.exe            # Placed here
    └── 📄 ... (Other files)
```
## License

MIT License - Use this for educational and research purposes.
