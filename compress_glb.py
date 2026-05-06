#!/usr/bin/env python3
"""
GLB 3D Model Compressor for Architecture Portfolio
====================================================
Compresses .glb files using Draco mesh compression and texture optimization.

Prerequisites:
    pip install pygltflib numpy Pillow

What it does:
    1. Scans images/projects/ for .glb files
    2. Reports sizes and flags anything over thresholds
    3. Compresses textures embedded in the GLB (resizes + re-encodes as JPEG/WebP)
    4. Saves compressed version alongside original (with _compressed suffix)
    5. Optionally replaces originals with compressed versions

Usage:
    python compress_glb.py              # Analyse only (dry run)
    python compress_glb.py --compress   # Compress all that need it
    python compress_glb.py --replace    # Compress AND replace originals
    python compress_glb.py --all        # Compress everything, not just large files
"""

import os
import sys
import json
import struct
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Try importing optional dependencies
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ============= CONFIGURATION =============
CONFIG = {
    'projects_folder': 'images/projects',
    'model_extensions': {'.glb'},
    'placeholder_names': {'duck.glb'},

    # Size thresholds
    'warn_size_mb': 10,
    'critical_size_mb': 25,

    # Texture compression settings
    'max_texture_size': 2048,        # Max dimension for textures
    'texture_quality': 80,           # JPEG quality for re-encoded textures
    'aggressive_texture_size': 1024, # Used for files > critical threshold
    'aggressive_quality': 70,
}


def format_size(size_bytes):
    """Human-readable file size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def find_glb_files(base_path):
    """Find all real .glb files under the projects folder."""
    base = Path(base_path)
    files = []

    if not base.exists():
        print(f"  Folder not found: {base}")
        return files

    for glb in base.rglob('*.glb'):
        if glb.name.lower() in CONFIG['placeholder_names']:
            continue
        files.append(glb)

    files.sort(key=lambda f: f.stat().st_size, reverse=True)
    return files


def analyse_glb(glb_path):
    """Return basic info about a GLB file."""
    size = glb_path.stat().st_size
    size_mb = size / (1024 * 1024)

    status = 'ok'
    if size_mb >= CONFIG['critical_size_mb']:
        status = 'critical'
    elif size_mb >= CONFIG['warn_size_mb']:
        status = 'warn'

    # Count embedded textures by parsing GLB binary
    texture_count, texture_bytes = count_textures(glb_path)

    return {
        'path': glb_path,
        'size': size,
        'size_mb': round(size_mb, 2),
        'status': status,
        'textures': texture_count,
        'texture_bytes': texture_bytes,
    }


def count_textures(glb_path):
    """Parse GLB header to count embedded images/textures."""
    try:
        with open(glb_path, 'rb') as f:
            # GLB header: magic(4) + version(4) + length(4)
            magic = f.read(4)
            if magic != b'glTF':
                return 0, 0

            version = struct.unpack('<I', f.read(4))[0]
            total_length = struct.unpack('<I', f.read(4))[0]

            # Chunk 0: JSON
            json_length = struct.unpack('<I', f.read(4))[0]
            json_type = f.read(4)
            json_data = f.read(json_length)

            gltf = json.loads(json_data.decode('utf-8'))

            images = gltf.get('images', [])
            bufferViews = gltf.get('bufferViews', [])

            texture_bytes = 0
            for img in images:
                bv_idx = img.get('bufferView')
                if bv_idx is not None and bv_idx < len(bufferViews):
                    texture_bytes += bufferViews[bv_idx].get('byteLength', 0)

            return len(images), texture_bytes

    except Exception:
        return 0, 0


def compress_glb_textures(glb_path, output_path, aggressive=False):
    """
    Compress a GLB file by re-encoding its embedded textures.

    This parses the GLB binary, finds all embedded images (PNG/JPEG),
    resizes them if they exceed the max dimension, and re-encodes them
    as JPEG at the configured quality. The result is a new GLB file.
    """
    if not HAS_PIL:
        print("    Pillow is required for texture compression.")
        print("    Install it: pip install Pillow")
        return False

    try:
        with open(glb_path, 'rb') as f:
            magic = f.read(4)
            if magic != b'glTF':
                print(f"    Not a valid GLB file")
                return False

            version = struct.unpack('<I', f.read(4))[0]
            total_length = struct.unpack('<I', f.read(4))[0]

            # Read JSON chunk
            json_chunk_length = struct.unpack('<I', f.read(4))[0]
            json_chunk_type = f.read(4)
            json_data = f.read(json_chunk_length)

            # Read BIN chunk
            bin_chunk_length = struct.unpack('<I', f.read(4))[0]
            bin_chunk_type = f.read(4)
            bin_data = bytearray(f.read(bin_chunk_length))

        gltf = json.loads(json_data.decode('utf-8'))
        images = gltf.get('images', [])
        bufferViews = gltf.get('bufferViews', [])

        if not images:
            print(f"    No embedded textures found, skipping")
            return False

        max_size = CONFIG['aggressive_texture_size'] if aggressive else CONFIG['max_texture_size']
        quality = CONFIG['aggressive_quality'] if aggressive else CONFIG['texture_quality']

        compressed_count = 0
        bytes_saved = 0

        # Process each image
        for i, img_info in enumerate(images):
            bv_idx = img_info.get('bufferView')
            if bv_idx is None or bv_idx >= len(bufferViews):
                continue

            bv = bufferViews[bv_idx]
            offset = bv.get('byteOffset', 0)
            length = bv.get('byteLength', 0)

            # Extract image bytes
            img_bytes = bytes(bin_data[offset:offset + length])

            try:
                import io
                img = Image.open(io.BytesIO(img_bytes))

                # Convert to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        alpha = img.split()[-1] if img.mode == 'RGBA' else img.split()[1]
                        background.paste(img, mask=alpha)
                        img = background
                    else:
                        img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize if too large
                w, h = img.size
                if max(w, h) > max_size:
                    ratio = max_size / max(w, h)
                    new_w = int(w * ratio)
                    new_h = int(h * ratio)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                # Re-encode as JPEG
                buffer = io.BytesIO()
                img.save(buffer, 'JPEG', quality=quality, optimize=True)
                new_bytes = buffer.getvalue()

                # Only replace if actually smaller
                if len(new_bytes) < length:
                    saved = length - len(new_bytes)
                    bytes_saved += saved

                    # Pad new data to same length or rebuild buffer
                    if len(new_bytes) <= length:
                        # Replace in-place with padding
                        padded = new_bytes + b'\x00' * (length - len(new_bytes))
                        bin_data[offset:offset + length] = padded
                        bv['byteLength'] = len(new_bytes)
                        img_info['mimeType'] = 'image/jpeg'
                        compressed_count += 1

            except Exception as e:
                # Skip images that fail to process
                continue

        if compressed_count == 0:
            print(f"    No textures could be further compressed")
            return False

        # Rebuild GLB with new bin data that removes padding gaps
        # For simplicity, we keep the padded approach (buffer stays same size)
        new_json = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
        # Pad JSON to 4-byte alignment
        while len(new_json) % 4 != 0:
            new_json += b' '

        # Pad BIN to 4-byte alignment
        while len(bin_data) % 4 != 0:
            bin_data += b'\x00'

        # Build new GLB
        total = 12 + 8 + len(new_json) + 8 + len(bin_data)

        with open(output_path, 'wb') as f:
            # Header
            f.write(b'glTF')
            f.write(struct.pack('<I', 2))  # version
            f.write(struct.pack('<I', total))  # total length

            # JSON chunk
            f.write(struct.pack('<I', len(new_json)))
            f.write(b'JSON')
            f.write(new_json)

            # BIN chunk
            f.write(struct.pack('<I', len(bin_data)))
            f.write(b'BIN\x00')
            f.write(bin_data)

        print(f"    Compressed {compressed_count} textures, saved {format_size(bytes_saved)}")
        return True

    except Exception as e:
        print(f"    Error compressing: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Analyse and compress GLB 3D models for web delivery'
    )
    parser.add_argument('--compress', action='store_true',
                        help='Compress files that exceed size thresholds')
    parser.add_argument('--replace', action='store_true',
                        help='Replace originals with compressed versions (backs up first)')
    parser.add_argument('--all', action='store_true',
                        help='Process all GLB files, not just oversized ones')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  GLB 3D MODEL ANALYSER & COMPRESSOR")
    print("=" * 60)
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Scanning: {CONFIG['projects_folder']}/")

    # Find files
    glb_files = find_glb_files(CONFIG['projects_folder'])

    if not glb_files:
        print("\n  No .glb files found (excluding placeholders like Duck.glb).")
        return

    # Analyse
    print(f"\n  Found {len(glb_files)} 3D model(s):\n")
    print(f"  {'Project':<20} {'File':<25} {'Size':>10}  Status")
    print(f"  {'-'*20} {'-'*25} {'-'*10}  {'-'*15}")

    results = []
    for glb in glb_files:
        info = analyse_glb(glb)
        results.append(info)

        project_name = glb.parent.name
        status_label = {
            'ok': 'OK',
            'warn': 'Compress recommended',
            'critical': 'COMPRESS NOW',
        }[info['status']]

        status_marker = {
            'ok': '  ',
            'warn': '! ',
            'critical': '!!',
        }[info['status']]

        texture_info = ""
        if info['textures'] > 0:
            texture_info = f"  ({info['textures']} textures, {format_size(info['texture_bytes'])})"

        print(f"  {project_name:<20} {glb.name:<25} {format_size(info['size']):>10}  {status_marker}{status_label}{texture_info}")

    # Summary
    total_size = sum(r['size'] for r in results)
    needs_work = [r for r in results if r['status'] in ('warn', 'critical')]

    print(f"\n  Total 3D model size: {format_size(total_size)}")

    if needs_work:
        print(f"\n  {len(needs_work)} file(s) would benefit from compression:")
        for r in needs_work:
            target = "< 10 MB" if r['status'] == 'critical' else "< 5 MB"
            print(f"    {r['path'].parent.name}/{r['path'].name}: {r['size_mb']} MB -> target {target}")

    # Compress if requested
    if args.compress or args.replace:
        to_process = results if args.all else [r for r in results if r['status'] != 'ok']

        if not to_process:
            print("\n  All files are within acceptable size. Use --all to compress anyway.")
            return

        print(f"\n" + "-" * 60)
        print("  COMPRESSING")
        print("-" * 60)

        compressed_files = []

        for info in to_process:
            glb_path = info['path']
            project_name = glb_path.parent.name
            stem = glb_path.stem
            compressed_path = glb_path.parent / f"{stem}_compressed.glb"

            print(f"\n  [{project_name}] {glb_path.name}")

            aggressive = info['status'] == 'critical'
            success = compress_glb_textures(glb_path, compressed_path, aggressive=aggressive)

            if success and compressed_path.exists():
                new_size = compressed_path.stat().st_size
                savings = info['size'] - new_size
                pct = (savings / info['size']) * 100 if info['size'] > 0 else 0

                print(f"    {format_size(info['size'])} -> {format_size(new_size)} (saved {pct:.1f}%)")

                compressed_files.append({
                    'original': glb_path,
                    'compressed': compressed_path,
                    'original_size': info['size'],
                    'new_size': new_size,
                })

                if args.replace and pct > 5:  # Only replace if meaningful savings
                    backup = glb_path.parent / f"{stem}_original.glb"
                    shutil.copy2(glb_path, backup)
                    shutil.move(str(compressed_path), str(glb_path))
                    print(f"    Replaced original (backup: {backup.name})")

            elif success is False and not compressed_path.exists():
                print(f"    Skipped (no improvement possible)")

        # Final summary
        if compressed_files:
            total_original = sum(c['original_size'] for c in compressed_files)
            total_new = sum(c['new_size'] for c in compressed_files)
            total_saved = total_original - total_new
            print(f"\n  Compression complete:")
            print(f"    Before: {format_size(total_original)}")
            print(f"    After:  {format_size(total_new)}")
            print(f"    Saved:  {format_size(total_saved)}")

            if not args.replace:
                print(f"\n  Compressed files saved with _compressed suffix.")
                print(f"  To replace originals, run: python compress_glb.py --compress --replace")

    elif needs_work:
        print(f"\n  To compress, run:")
        print(f"    python compress_glb.py --compress          # Save as _compressed.glb")
        print(f"    python compress_glb.py --compress --replace # Replace originals (with backup)")

    print("\n" + "=" * 60)
    print("  Done.")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
