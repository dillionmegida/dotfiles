#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_bottom, box_line, box_top


FORMATS = {
    'mp4': ('libx264', 'aac'),
    'mov': ('libx264', 'aac'),
    'mkv': ('libx264', 'aac'),
    'webm': ('libvpx-vp9', 'libopus'),
}
ALIASES = {
    'q': '--quality',
    'e': '--extension',
    'o': '--output',
}


def fail(message):
    box_top()
    box_line(message)
    box_bottom()
    raise SystemExit(1)


def normalize_args(args):
    normalized = []
    for arg in args:
        key, separator, value = arg.partition('=')
        alias = ALIASES.get(key.lstrip('-'))
        if separator and alias:
            normalized.append(f'{alias}={value}')
        else:
            normalized.append(arg)
    return normalized


def parse_args(args):
    parser = argparse.ArgumentParser(
        description='Convert video with safe FFmpeg defaults',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  convert video.mov q=80
  convert video.mov q=80 e=mp4
  convert video.mov q=80 o=compressed.mp4
  convert video.mov q=80 e=mp4 -f
        ''',
    )
    parser.add_argument('source', help='Source video file')
    parser.add_argument('-q', '--quality', type=int, help='Output quality from 1 to 100')
    parser.add_argument('-e', '--extension', choices=FORMATS, help='Output extension')
    parser.add_argument('-o', '--output', help='Output path')
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite the destination')
    parsed = parser.parse_args(normalize_args(args))
    if parsed.quality is None and parsed.extension is None and parsed.output is None:
        fail('Pass options, e.g. q=80')
    if parsed.quality is not None and not 1 <= parsed.quality <= 100:
        fail('Quality must be between 1 and 100')
    return parsed


def next_output(source, suffix):
    number = 1
    while True:
        output = source.with_name(f'{source.stem}_{number}{suffix}')
        if not output.exists():
            return output
        number += 1


def output_path(source, output, extension, force):
    suffix = f'.{extension}' if extension else source.suffix.lower()
    if suffix.lstrip('.') not in FORMATS:
        fail(f"Unsupported format: {suffix.lstrip('.') or 'none'}")

    if output:
        destination = Path(output).expanduser()
        if destination.is_dir():
            destination = destination / f'{source.stem}{suffix}'
        elif extension:
            destination = destination.with_suffix(suffix)
        elif not destination.suffix:
            destination = destination.with_suffix(suffix)
        destination = destination.resolve()
    elif force:
        destination = source.with_suffix(suffix)
    else:
        destination = next_output(source, suffix)

    if not destination.parent.exists():
        fail(f"Output directory does not exist: {destination.parent}")
    if destination == source and not force:
        fail('Use -f to overwrite the source')
    if destination.exists() and not force:
        fail(f"Output already exists: {destination}")
    return destination


def crf_for_quality(quality, codec):
    if codec == 'libvpx-vp9':
        return round(50 - (quality - 1) * 35 / 99)
    return round(51 - (quality - 1) * 33 / 99)


def ffmpeg_command(source, destination, quality, force):
    extension = destination.suffix.lower().lstrip('.')
    video_codec, audio_codec = FORMATS[extension]
    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(source),
        '-map', '0:v:0', '-map', '0:a?', '-map_metadata', '0',
        '-c:v', video_codec, '-crf', str(crf_for_quality(quality, video_codec)),
    ]
    if video_codec == 'libvpx-vp9':
        command.extend(['-b:v', '0', '-c:a', audio_codec, '-b:a', '192k'])
    else:
        command.extend(['-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', audio_codec, '-b:a', '192k'])
        if extension in ('mp4', 'mov'):
            command.extend(['-movflags', '+faststart'])
    command.extend(['-y' if force else '-n', str(destination)])
    return command


def convert(args):
    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        fail(f"Source file does not exist: {args.source}")
    if not shutil.which('ffmpeg'):
        fail("'ffmpeg' not found. Install it with: brew install ffmpeg")

    destination = output_path(source, args.output, args.extension, args.force)
    quality = args.quality if args.quality is not None else 80

    box_top()
    box_line(f'Source: {source}')
    box_line(f'Output: {destination}')
    box_line(f'Quality: {quality}')
    box_bottom()

    conversion_output = destination
    replace_destination = args.force and destination.exists()
    if replace_destination:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f'.{destination.stem}-', suffix=destination.suffix, dir=destination.parent
        )
        os.close(file_descriptor)
        conversion_output = Path(temporary_name)

    try:
        subprocess.run(
            ffmpeg_command(source, conversion_output, quality, args.force),
            check=True,
        )
        if replace_destination:
            os.replace(conversion_output, destination)
    except subprocess.CalledProcessError:
        fail('Conversion failed')
    finally:
        if conversion_output != destination and conversion_output.exists():
            conversion_output.unlink()

    size_mb = destination.stat().st_size / (1024 * 1024)
    box_top()
    box_line(f'Created: {destination}')
    box_line(f'Size: {size_mb:.2f} MB')
    box_bottom()


def main():
    convert(parse_args(sys.argv[1:]))


if __name__ == '__main__':
    main()
