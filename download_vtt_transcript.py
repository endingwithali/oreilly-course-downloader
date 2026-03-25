"""
Download and parse VTT subtitle file from ON24
"""

import requests
from pathlib import Path
import re

VTT_URL = "https://event.on24.com/event/52/06/56/7/rt/1/vtt/mediaplayer/5206567_English_B107E6F0585580F6734D37482203CA1D.vtt"
DOWNLOAD_DIR = Path("downloads/Claude_Code_and_Large_Context_Reasoning")

def download_vtt(url):
    """Download VTT file"""
    print(f"📥 Downloading VTT file...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f"   ✅ Downloaded {len(response.content)} bytes")
        return response.text
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def parse_vtt(vtt_content):
    """Parse VTT file and extract transcript"""
    print("\n📝 Parsing VTT file...")
    
    lines = vtt_content.split('\n')
    captions = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for timestamp lines (format: 00:00:00.000 --> 00:00:00.000)
        if '-->' in line:
            timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})', line)
            if timestamp_match:
                start_time = timestamp_match.group(1)
                end_time = timestamp_match.group(2)
                
                # Next lines are the caption text
                caption_text = []
                i += 1
                while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                    text = lines[i].strip()
                    # Remove VTT formatting tags
                    text = re.sub(r'<[^>]+>', '', text)
                    if text:
                        caption_text.append(text)
                    i += 1
                
                if caption_text:
                    captions.append({
                        'start': start_time[:8],  # HH:MM:SS
                        'end': end_time[:8],
                        'text': ' '.join(caption_text)
                    })
        
        i += 1
    
    print(f"   ✅ Parsed {len(captions)} caption entries")
    return captions

def format_transcript(captions):
    """Format captions into readable transcript"""
    print("\n📄 Formatting transcript...")
    
    transcript = f"""Claude Code and Large-Context Reasoning
O'Reilly Live Event - Video Transcript
Source: ON24 VTT Captions
Total Captions: {len(captions)}
{'=' * 80}

"""
    
    for caption in captions:
        transcript += f"[{caption['start']}] {caption['text']}\n\n"
    
    print(f"   ✅ Formatted {len(transcript)} characters")
    return transcript

def save_transcript(transcript):
    """Save transcript to file"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    output_file = DOWNLOAD_DIR / "full_transcript.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(transcript)
    
    print(f"\n✅ Transcript saved to: {output_file}")
    print(f"   Size: {len(transcript)} characters")
    return output_file

def main():
    print("=" * 80)
    print("🎓 ON24 VTT TRANSCRIPT DOWNLOADER")
    print("=" * 80)
    print("\n📚 Event: Claude Code and Large-Context Reasoning")
    
    # Download VTT file
    vtt_content = download_vtt(VTT_URL)
    
    if not vtt_content:
        print("\n❌ Failed to download VTT file")
        return
    
    # Parse VTT
    captions = parse_vtt(vtt_content)
    
    if not captions:
        print("\n❌ No captions found in VTT file")
        return
    
    # Format transcript
    transcript = format_transcript(captions)
    
    # Save to file
    output_file = save_transcript(transcript)
    
    print("\n" + "=" * 80)
    print("✅ SUCCESS - TRANSCRIPT EXTRACTED")
    print("=" * 80)
    print(f"\n📁 File: {output_file}")
    print(f"📊 Captions: {len(captions)}")
    print(f"📏 Size: {len(transcript):,} characters")
    
    # Show preview
    print("\n📖 Preview (first 500 characters):")
    print("-" * 80)
    print(transcript[transcript.find('['):transcript.find('[') + 500] + "...")
    print("-" * 80)

if __name__ == "__main__":
    main()
