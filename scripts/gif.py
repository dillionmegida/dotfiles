#!/usr/bin/env python3

import sys
import os
import subprocess
import tempfile
import argparse
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_top, box_bottom, box_line


def check_dependencies():
    missing = [tool for tool in ('ffmpeg', 'ffprobe') if not shutil.which(tool)]
    if missing:
        box_top()
        for tool in missing:
            box_line(f"Error: '{tool}' not found. Install it with: brew install ffmpeg")
        box_bottom()
        sys.exit(1)


def get_video_info(video_path):
    """Get video information using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=avg_frame_rate,r_frame_rate,width,height,display_aspect_ratio',
        '-of', 'default=noprint_wrappers=1',
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()

        info = {}
        for line in output.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                info[key] = value

        return info
    except subprocess.CalledProcessError as e:
        box_top()
        box_line(f"Error getting video info: {e}")
        box_bottom()
        sys.exit(1)


def calculate_fps(frame_rate_str):
    """Calculate FPS from a frame rate string (e.g., '30/1' or '30000/1001')."""
    if not frame_rate_str:
        return 0.0
    if '/' in frame_rate_str:
        num, denom = map(int, frame_rate_str.split('/'))
        if denom == 0:
            return 0.0
        return num / denom
    return float(frame_rate_str)


def determine_fps(video_info):
    """
    Determine a sane FPS to use for conversion.

    avg_frame_rate reflects the actual average playback rate (total frames /
    duration), which is reliable even for variable-frame-rate sources like
    screen recordings (e.g. ReplayKit). r_frame_rate is the stream's timing
    resolution and can be wildly inflated for VFR sources (e.g. reporting
    240fps for a screen recording that actually plays at ~30fps), so it's
    only used as a fallback if avg_frame_rate is missing or zero.
    """
    avg = calculate_fps(video_info.get('avg_frame_rate', '0/1'))
    if avg > 0:
        source_fps = avg
    else:
        source_fps = calculate_fps(video_info.get('r_frame_rate', '24/1'))
        if source_fps <= 0:
            source_fps = 24.0

    # GIFs rarely benefit from very high frame rates (most viewers cap
    # playback well below this anyway), and it keeps file sizes sane.
    MAX_GIF_FPS = 30.0
    return min(source_fps, MAX_GIF_FPS)


def convert_to_gif(source, output=None, fps=None, quality=100):
    """Convert video to GIF using two-pass palette generation."""

    source_path = Path(source).expanduser().resolve()

    if not source_path.exists():
        box_top()
        box_line(f"Error: Source file '{source}' does not exist")
        box_bottom()
        sys.exit(1)

    if output is None:
        output_path = source_path.with_suffix('.gif')
    else:
        output_path = Path(output).expanduser().resolve()
        if output_path.is_dir():
            output_path = output_path / source_path.with_suffix('.gif').name

    video_info = get_video_info(str(source_path))

    if fps is None:
        fps = determine_fps(video_info)

    width = int(video_info.get('width', 0))
    height = int(video_info.get('height', 0))
    
    if quality < 100 and width > 0 and height > 0:
        scale_factor = quality / 100.0
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)
        scale_filter = f'scale={new_width}:{new_height}:flags=lanczos,'
    else:
        scale_filter = ''
        new_width = width
        new_height = height
    
    box_top()
    box_line(f"Converting '{source_path.name}' to GIF...")
    box_line(f"FPS: {fps}")
    box_line(f"Quality: {quality}%")
    box_line(f"Resolution: {video_info.get('width', 'unknown')}x{video_info.get('height', 'unknown')}")
    if quality < 100:
        box_line(f"Output resolution: {new_width}x{new_height}")
    if 'display_aspect_ratio' in video_info:
        box_line(f"Aspect ratio: {video_info['display_aspect_ratio']}")
    box_line(f"Output: {output_path}")
    box_bottom()

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as palette_file:
        palette_path = palette_file.name

    try:
        box_top()
        box_line("Step 1: Generating palette...")
        palette_cmd = [
            'ffmpeg',
            '-i', str(source_path),
            '-vf', f'{scale_filter}fps={fps},palettegen=stats_mode=diff',
            '-y',
            palette_path
        ]

        subprocess.run(palette_cmd, check=True)
        box_bottom()

        box_top()
        box_line("Step 2: Creating GIF...")
        gif_cmd = [
            'ffmpeg',
            '-i', str(source_path),
            '-i', palette_path,
            '-filter_complex', f'{scale_filter}fps={fps},paletteuse=dither=sierra2_4a',
            '-y',
            str(output_path)
        ]

        subprocess.run(gif_cmd, check=True)
        box_bottom()

        file_size = output_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        box_top()
        box_line(f"✓ GIF created: {output_path}")
        box_line(f"File size: {size_mb:.2f} MB")
        box_bottom()

    except subprocess.CalledProcessError as e:
        box_top()
        box_line(f"Error during conversion: {e}")
        box_bottom()
        sys.exit(1)
    finally:
        if os.path.exists(palette_path):
            os.unlink(palette_path)


def main():
    parser = argparse.ArgumentParser(
        description='Convert video to GIF using high-quality two-pass palette generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  gif video.mov                    # Creates video.gif with source FPS (capped at 30)
  gif video.mov -o output.gif      # Specify output filename
  gif video.mov --fps 24           # Use 24 FPS
  gif video.mov -q 80              # 80% quality (reduces resolution to 80%)
  gif video.mov --fps 15 -q 50 -o slow.gif
        '''
    )

    parser.add_argument('source', help='Source video file')
    parser.add_argument('-o', '--output', help='Output GIF file (default: source name with .gif extension)')
    parser.add_argument('--fps', type=float, help='Frame rate for the GIF (default: use source video FPS, capped at 30)')
    parser.add_argument('-q', '--quality', type=int, default=100, help='Quality percentage (1-100, default: 100). Lower values reduce resolution proportionally.')

    args = parser.parse_args()

    if args.quality < 1 or args.quality > 100:
        box_top()
        box_line("Error: Quality must be between 1 and 100")
        box_bottom()
        sys.exit(1)

    check_dependencies()
    convert_to_gif(args.source, args.output, args.fps, args.quality)


if __name__ == '__main__':
    main()
