# Short 'Quote' Video Generator

Generate automated quote videos for short-form platforms (TikTok, YouTube Shorts, Instagram Reels). The script pulls vertical nature videos from Pexels, adds voiceover narration via Google Text-to-Speech (gTTS), renders animated text overlays with ImageMagick and MoviePy, and mixes in background music.

---

## Preview
![Preview](https://i.imgur.com/CkJYmLg.png)

- **Example video with intro**: [YouTube Shorts](https://www.youtube.com/shorts/JCElumu8KZ8)
- **Example video without intro**: [YouTube Shorts](https://youtube.com/shorts/j-xkH3DrD9k)

---

## Features
- **Automated Video Generation**: Batch generate short videos ready for upload.
- **Dynamic Backgrounds**: Automatically searches and downloads portrait HD nature videos from Pexels.
- **TTS Narration**: Text-to-speech audio generated for each quote.
- **Royalty-Free Music**: Background music included from YouTube's commercial-use library.
- **4500+ Quotes**: Pre-loaded motivational quotes included in `quotes/motivational.txt`.

---

## Prerequisites

1. **Python 3.10+**: Make sure Python is installed and added to your `PATH`.
2. **ImageMagick**: Required by MoviePy for rendering text clips.
   - **Windows**: Download and install from [ImageMagick.org](https://imagemagick.org/script/download.php) (or use the installer in `./imageMagicksInstaller`).
   - *Important during installation*: Check the box for **"Add application directory to your system path"**.
3. **Pexels API Key**: A free API key from [Pexels API](https://www.pexels.com/api/).

---

## Installation & Setup

### 1. Clone or Open the Repository
```bash
cd videoGenerator-master
```

### 2. Create and Activate a Virtual Environment
**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key and Settings
Open `config.json` and add your Pexels API key:
```json
{
    "amountOfVideosToMake": "1",
    "pexelsAPIKey": "YOUR_PEXELS_API_KEY_HERE"
}
```
*(You can also update these values directly from the interactive CLI menu.)*

---

## How to Run

### Option A: Interactive CLI Menu
```bash
python main.py
```
This opens the interactive menu:
```text
Current configurations:
 Pexels API key: <your_key>
 Videos to create: 1

Options:
1) Change number of videos
2) Change API key
3) Start generating videos
4) Check ImageMagick
5) Exit
```

### Option B: Direct Generation (Non-Interactive)
Run generation directly with the `--generate` flag:
```bash
python main.py --generate
```

Output videos are saved in the project root as `VID_0.mp4`, `VID_1.mp4`, etc.

---

## Project Structure

```text
├── config.json          # Configuration for video count and Pexels API key
├── main.py              # Main generator script
├── requirements.txt     # Python dependencies
├── intro_clip/          # Video clips used for the intro hook
├── quotes/
│   ├── motivational.txt # Unused quotes (one quote per line: "Quote - Author")
│   └── usedQuotes.txt   # History of quotes already generated
├── sad_music/           # Royalty-free background music tracks (.mp3)
├── tempFiles/           # Temporary download and audio cache (cleaned automatically)
└── VID_0.mp4            # Generated output video(s)
```

---

## Troubleshooting

- **ImageMagick Not Found**:
  Make sure ImageMagick is installed. You can verify ImageMagick by running option `4` in the CLI menu or by checking `magick --version` in your terminal.
- **PermissionError on Temp Files**:
  On Windows, background media player apps or preview panes can occasionally lock temporary files. The script automatically catches and handles locked files without interrupting video creation.
