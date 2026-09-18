import os
import shutil
import glob
import sys

# Tell MoviePy where ImageMagick is
magick_path = shutil.which("magick")
if not magick_path:
    candidates = glob.glob(r"C:\Program Files\ImageMagick-*\magick.exe")
    if candidates:
        magick_path = candidates[0]
if magick_path:
    os.environ["IMAGEMAGICK_BINARY"] = magick_path

# Monkey-patch PIL for ANTIALIAS (removed in Pillow 10)
from PIL import Image
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = getattr(Image, "Resampling", Image).LANCZOS

import requests
import json
import gtts
import random
import subprocess
from tqdm.auto import tqdm
from moviepy.editor import *
import glob
from mutagen.mp3 import MP3

# Robust download from a direct video URL with retry logic
def downloadVideo(url, save_path="tempFiles/vid.mp4", retries=3) -> str:
    """Downloads video from the given direct MP4 URL, retrying on network hiccups."""
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, stream=True, timeout=15)
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            with open(save_path, "wb") as f, tqdm(total=total, unit="iB", unit_scale=True) as pbar:
                for chunk in resp.iter_content(1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            return save_path
        except (requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException) as e:
            print(f"Download error (attempt {attempt}/{retries}): {e}")
            if attempt == retries:
                return None
            print("Retrying…")
    return None

# Fetch Pexels search results
def scrapeVideos(api_key: str):
    """Fetches portrait-nature video results from Pexels API."""
    if not api_key or api_key.strip() in ("", "YOUR_PEXELS_API_KEY_HERE"):
        print("Pexels API key is not configured.")
        return None
    params = {'query': 'nature', 'orientation': 'portrait'}
    headers = {'Authorization': api_key.strip()}
    try:
        resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15)
    except requests.exceptions.RequestException as e:
        print(f"Network error connecting to Pexels: {e}")
        return None
    if resp.status_code == 401:
        print("Pexels API error 401: Unauthorized. Please check that your Pexels API key is valid.")
        return None
    elif resp.status_code != 200:
        print(f"Pexels API error {resp.status_code}: {resp.text}")
        return None
    data = resp.json()
    if data.get('total_results', 0) < 1 or not data.get('videos'):
        print("No videos found for your query.")
        return None
    return data

# Select and download a random video file
def getBackgroundVideo(api_key: str, video_index: int = 0) -> str:
    """Selects a random Pexels video, grabs its highest-res file, and downloads it."""
    data = scrapeVideos(api_key)
    if not data or not data.get('videos'):
        return None
    video_obj = random.choice(data['videos'])
    mp4_files = [f for f in video_obj.get('video_files', []) if f.get('link')]
    if not mp4_files:
        print("No valid video files found in Pexels result.")
        return None
    files = sorted(mp4_files, key=lambda v: v.get('width', 0), reverse=True)
    video_url = files[0]['link']
    print("Downloading video from:", video_url)
    return downloadVideo(video_url, save_path=f"tempFiles/vid_{video_index}.mp4")

# Move used quote to a separate file
def usedQuoteToDifferentFile():
    if not os.path.exists('quotes/motivational.txt'):
        return
    with open('quotes/motivational.txt', 'r+', encoding='utf8') as f:
        lines = f.readlines()
        if not lines:
            return
        quote = lines[0]
        f.seek(0)
        f.truncate()
        f.writelines(lines[1:])
    with open('quotes/usedQuotes.txt', 'a', encoding='utf8') as f:
        f.write(quote)

# Read one quote from the text file
def getQuote():
    if not os.path.exists('quotes/motivational.txt'):
        print("quotes/motivational.txt not found!")
        return None
    with open('quotes/motivational.txt', 'r', encoding='utf8') as file:
        line = file.readline().strip()
        if not line:
            return None
        line = line.replace("-", "\n -")
        print("Quote:", line)
        return line

# Create the intro clip with animated text
def videoIntro(introText, videoNumber) -> CompositeVideoClip:
    selected_intro = introText[videoNumber % len(introText)]
    text_clip = TextClip(
        txt=selected_intro, fontsize=70,
        size=(800,0), font="Roboto-Regular",
        color="white", method="caption"
    ).set_position('center')
    w, h = text_clip.size
    bg = ColorClip((w+100, h+50), color=(0,0,0)).set_opacity(0.6)
    intro_clip = VideoFileClip("intro_clip/2_hands_up.mp4").resize((1080,1920))
    duration = 6
    overlay = CompositeVideoClip([bg, text_clip]).set_position(lambda t: ('center', 200+t)).set_duration(duration)
    return CompositeVideoClip([intro_clip, overlay]).set_duration(duration)

# Assemble the full video
def createVideo(quoteText: str, bgMusic: str, bgVideo: str, videoNumber: int, ttsAudio: bool):
    if not bgVideo or not os.path.isfile(bgVideo):
        raise FileNotFoundError(f"Background video file not found or invalid: {bgVideo}")
    introText = [
        'A quote about never giving up on your dreams',
        'A quote about being yourself',
        # ... add more intros if desired
    ]
    selected_intro = introText[videoNumber % len(introText)]
    print(f"Introtext: {selected_intro}")
    intro_clip = videoIntro(introText, videoNumber)

    # Generate TTS audio and text clip
    os.makedirs("tempFiles", exist_ok=True)
    save_mp3 = f"tempFiles/temp_audio_{videoNumber}.mp3"
    tts = gtts.gTTS(quoteText, lang='en')
    tts.save(save_mp3)
    audio = MP3(save_mp3)
    dur = audio.info.length
    print(f"Generated TTS duration: {dur}")

    text_clip = TextClip(
        txt=quoteText, fontsize=70, size=(800,0),
        font="Roboto-Regular", color="white", method="caption"
    ).set_position('center')
    tw, th = text_clip.size
    tc_bg = ColorClip((tw+100, th+50), color=(0,0,0)).set_opacity(0.6)
    combined_text = CompositeVideoClip([tc_bg, text_clip]).set_duration(dur).set_position('center')
    audio_clip = AudioFileClip(save_mp3)
    combined_text.audio = CompositeAudioClip([audio_clip])

    bg_clip = VideoFileClip(bgVideo).resize((1080,1920))
    if bg_clip.duration < dur:
        bg_clip = bg_clip.loop(duration=dur)
    else:
        bg_clip = bg_clip.subclip(0, dur)
    final_text_video = CompositeVideoClip([bg_clip, combined_text])

    bg_music = AudioFileClip(bgMusic)
    total_audio_dur = dur + intro_clip.duration
    if bg_music.duration < total_audio_dur:
        bg_music = bg_music.loop(duration=total_audio_dur)
    else:
        bg_music = bg_music.subclip(0, total_audio_dur)

    if ttsAudio:
        final_audio = CompositeAudioClip([bg_music, audio_clip.set_start(intro_clip.duration)])
    else:
        final_audio = bg_music

    final = concatenate_videoclips([intro_clip, final_text_video])
    final.audio = final_audio
    final.write_videofile(f"VID_{videoNumber}.mp4", threads=12)
    # Close clips to release file handles
    final.close()
    intro_clip.close()
    bg_clip.close()
    audio_clip.close()
    bg_music.close()
    combined_text.close()
    final_text_video.close()

# Audio mixing helper
def audioClip(ttsAudio: bool, backgroundMusic, final_export_video, total_video_time, introDuration: int) -> CompositeAudioClip:
    if ttsAudio:
        return CompositeAudioClip([backgroundMusic, final_export_video.audio.set_start(introDuration)]).subclip(0,total_video_time)
    return CompositeAudioClip([backgroundMusic]).subclip(0,total_video_time)

# Random music picker
def randomBgMusic():
    dir = "sad_music"
    files = [f for f in os.listdir(dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
    if not files:
        files = os.listdir(dir)
    x = random.choice(files)
    print("Random music chosen:", x)
    return os.path.join(dir, x)

# Cleanup helpers
def deleteTempFiles():
    """Deletes downloaded/generated files, ignoring ones still in use."""
    print("Deleting temporary files…")
    for filepath in glob.glob('tempFiles/*'):
        try:
            os.remove(filepath)
            print(f"  Removed {filepath}")
        except PermissionError:
            print(f"  • Skipping {filepath}: still in use.")

def cleanUpAfterVideoFinished():
    usedQuoteToDifferentFile()
    deleteTempFiles()

# Data verification
def verifyData(data) -> bool:
    print("Checking data....")
    try:
        amount = int(data.get('amountOfVideosToMake', 0))
    except (ValueError, TypeError):
        print("Error: Invalid number for 'amountOfVideosToMake'. Please check config.json.")
        return False
    if amount < 1:
        print("Amount of videos to create must be at least 1.")
        return False

    api_key = data.get('pexelsAPIKey', '').strip()
    if not api_key or api_key == "YOUR_PEXELS_API_KEY_HERE":
        print("Error: Pexels API key is not configured! Please enter your key in config.json or choose Option 2.")
        return False

    res = scrapeVideos(api_key)
    if not res:
        print("Data verification failed. Could not fetch videos from Pexels.")
        return False

    print("Everything went well! Starting to create videos now!")
    return True

def generateVideos(data):
    if not verifyData(data):
        return
    for i in range(int(data['amountOfVideosToMake'])):
        bgVideo = getBackgroundVideo(data['pexelsAPIKey'], i)
        if not bgVideo or not os.path.exists(bgVideo):
            print(f"Skipping video {i}: Failed to acquire background video.")
            continue
        quote = getQuote()
        if not quote:
            print("No quotes available in quotes/motivational.txt. Exiting.")
            break
        music = randomBgMusic()
        createVideo(quote, music, bgVideo, i, True)
        cleanUpAfterVideoFinished()
        print(f"Finished video {i}")

# CLI Loop
def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--generate", "-g", "run", "3"):
        with open('config.json', 'r') as f:
            data = json.load(f)
        generateVideos(data)
        print("All videos generated successfully!")
        return

    while True:
        with open('config.json','r') as f:
            data = json.load(f)
        os.system('cls' if os.name=='nt' else 'clear')
        print(f"Current configurations:\n Pexels API key: {data['pexelsAPIKey']}\n Videos to create: {data['amountOfVideosToMake']}")
        print("\nOptions:\n1) Change number of videos\n2) Change API key\n3) Start generating videos\n4) Check ImageMagick\n5) Exit")
        try:
            choice = input("Enter choice: ")
        except (EOFError, KeyboardInterrupt):
            break
        if choice == '1':
            data['amountOfVideosToMake'] = input("Amount of videos: ")
            with open('config.json','w') as f: json.dump(data,f,indent=4)
        elif choice == '2':
            data['pexelsAPIKey'] = input("Pexels API key: ")
            with open('config.json','w') as f: json.dump(data,f,indent=4)
        elif choice == '3':
            generateVideos(data)
            input("Done! Press Enter.")
        elif choice == '4':
            subprocess.run(['magick','identify','--version'])
            input("Press Enter.")
        elif choice == '5':
            quit()
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
