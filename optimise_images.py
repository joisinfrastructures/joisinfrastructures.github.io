#!/usr/bin/env python3
"""
Project Image Optimizer for Architecture Portfolio
===================================================
Place this script in your website root folder (same level as index.html)

Structure:
your-website/
├── images/projects/Adhvaita/, images/projects/Akhilesh/, etc.
├── optimize_images.py  ← THIS FILE
└── projects.json       ← GENERATED

Usage:
    python optimize_images.py
"""

import os
import sys
import json
import base64
import shutil
from pathlib import Path
from PIL import Image
import io
from datetime import datetime

# ============= CONFIGURATION =============
CONFIG = {
    # Input: where your original project folders are
    'input_folder': 'images/projects',
    
    # Output: where to save optimized images (inside each project folder)
    'output_structure': {
        'thumbnails': 'images/projects/thumbnails',
        'covers': 'images/projects/covers',
        'blur': 'images/projects/blur',
    },
    
    # Image sizes
    'sizes': {
        'thumbnail': (400, 500),   # For gallery grid
        'cover': (800, 1000),      # For expanded view
        'blur': (20, 25),          # For blur placeholder
    },
    
    # Quality settings (1-100)
    'quality': {
        'thumbnail': 75,
        'cover': 82,
        'blur': 20,
    },
    
    # Supported image formats
    'image_extensions': {'.jpg', '.jpeg', '.png', '.webp', '.gif'},
    
    # Output format
    'output_format': 'webp',  # 'webp' or 'jpg'
    
    # Generate JPEG fallback for older browsers
    'generate_jpg_fallback': False,
    
    # Projects JSON output path
    'json_output': 'projects.json',
    
    # Default metadata (will be used if not specified in metadata.json)
    'default_category': 'Residential',
    'default_location': 'Shivamogga',
}

# Optional: Project-specific metadata
# You can create a metadata.json file or define here
PROJECT_METADATA = {
    'Adhvaita': {
        'name': 'Adhvaita Residency',
        'location': 'Navanagara, Shivamogga',
        'category': 'Residential',
        'cover': 'Advaitha 2.jpeg'
    },
    'Akhilesh': {
        'name': 'Akhilesh Residency',
        'location': 'Chalukya Nagara, Shivamogga',
        'category': 'Residential',
    },
    'Brindavana': {
        'name': 'Brindavana Residency',
        'location': 'Urgadur, Shivamogga',
        'category': 'Residential',
    },
    'Elu Koti': {
        'name': 'Elu Koti Residency',
        'location': 'Urgadur, Shivamogga',
        'category': 'Residential',
        'cover': 'sridevi 12 - Photo_6 - Photo.jpg'
    },
    'Keshava': {
        'name': 'Keshava Residency',
        'location': 'Urgadur, Shivamogga',
        'category': 'Residential',
    },
    'Manjunath': {
        'name': 'Manjunath Residency',
        'location': 'Taralabalu Layout, Shivamogga',
        'category': 'Residential',
    },
    'Mathareeshwa': {
        'name': 'Mathareeshwa Residency',
        'location': 'Gandhi Bazar, Shivamogga',
        'category': 'Residential',
    },
    'Mathrushree': {
        'name': 'Mathrushree Residency',
        'location': 'Urgadur, Shivamogga',
        'category': 'Residential',
    },
    # Add more projects as needed...
}


class ImageOptimizer:
    """Main image optimization class"""
    
    def __init__(self, config):
        self.config = config
        self.input_path = Path(config['input_folder'])
        self.projects_data = []
        self.stats = {
            'total_projects': 0,
            'total_images': 0,
            'original_size': 0,
            'optimized_size': 0,
        }
        
    def setup_output_directories(self):
        """Create output directory structure"""
        print("\n📁 Setting up output directories...")
        
        for dir_name, dir_path in self.config['output_structure'].items():
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            print(f"   ✓ {dir_path}")
    
    def get_project_folders(self):
        """Get all project folders"""
        if not self.input_path.exists():
            print(f"❌ Input folder not found: {self.input_path}")
            print(f"   Make sure you're running the script from your website root folder")
            sys.exit(1)
        
        # Exclude output directories
        exclude = {'thumbnails', 'covers', 'blur', '.DS_Store', '__pycache__'}
        
        folders = [
            f for f in self.input_path.iterdir()
            if f.is_dir() and f.name not in exclude and not f.name.startswith('.')
        ]
        
        return sorted(folders, key=lambda x: x.name.lower())
    
    def get_images_from_folder(self, folder_path):
        """Get all image files from a project folder"""
        images = []
        
        for file in folder_path.iterdir():
            if file.is_file() and file.suffix.lower() in self.config['image_extensions']:
                images.append(file)
        
        # Sort by name
        return sorted(images, key=lambda x: x.name.lower())
    
    def slugify(self, text):
        """Convert text to URL-friendly slug"""
        import re
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text
    
    def optimize_image(self, input_path, output_path, size, quality):
        """Optimize and resize a single image"""
        try:
            with Image.open(input_path) as img:
                # Track original size
                original_size = input_path.stat().st_size
                self.stats['original_size'] += original_size
                
                # Handle different color modes
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        # Paste with alpha mask
                        alpha = img.split()[-1] if img.mode == 'RGBA' else img.split()[1]
                        background.paste(img, mask=alpha)
                        img = background
                    else:
                        img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate dimensions for cover crop
                target_w, target_h = size
                img_w, img_h = img.size
                
                img_ratio = img_w / img_h
                target_ratio = target_w / target_h
                
                if img_ratio > target_ratio:
                    # Image is wider - fit height, crop width
                    new_h = target_h
                    new_w = int(new_h * img_ratio)
                else:
                    # Image is taller - fit width, crop height
                    new_w = target_w
                    new_h = int(new_w / img_ratio)
                
                # Resize with high quality
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Center crop to exact target size
                left = (new_w - target_w) // 2
                top = (new_h - target_h) // 2
                img_cropped = img_resized.crop((left, top, left + target_w, top + target_h))
                
                # Save as WebP
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                if self.config['output_format'] == 'webp':
                    img_cropped.save(
                        output_path,
                        'WEBP',
                        quality=quality,
                        method=6
                    )
                else:
                    img_cropped.save(
                        output_path,
                        'JPEG',
                        quality=quality,
                        optimize=True,
                        progressive=True
                    )
                
                # Track optimized size
                optimized_size = output_path.stat().st_size
                self.stats['optimized_size'] += optimized_size
                
                return True
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return False
    
    def generate_blur_data_url(self, input_path):
        """Generate tiny blur placeholder as base64 data URL"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB
                if img.mode != 'RGB':
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
                
                # Tiny resize
                size = self.config['sizes']['blur']
                img_ratio = img.width / img.height
                target_ratio = size[0] / size[1]
                
                if img_ratio > target_ratio:
                    new_h = size[1]
                    new_w = int(new_h * img_ratio)
                else:
                    new_w = size[0]
                    new_h = int(new_w / img_ratio)
                
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Center crop
                left = (new_w - size[0]) // 2
                top = (new_h - size[1]) // 2
                img_cropped = img_resized.crop((left, top, left + size[0], top + size[1]))
                
                # Save to bytes
                buffer = io.BytesIO()
                img_cropped.save(buffer, 'WEBP', quality=self.config['quality']['blur'])
                buffer.seek(0)
                
                # Convert to base64
                b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return f"data:image/webp;base64,{b64}"
                
        except Exception as e:
            print(f"      ⚠️  Blur generation failed: {e}")
            return None
    
    def get_dominant_color(self, input_path):
        """Extract dominant color from image"""
        try:
            with Image.open(input_path) as img:
                # Resize for speed
                img_small = img.resize((50, 50), Image.Resampling.LANCZOS)
                if img_small.mode != 'RGB':
                    img_small = img_small.convert('RGB')
                
                # Get pixels
                pixels = list(img_small.getdata())
                
                # Calculate average
                r = sum(p[0] for p in pixels) // len(pixels)
                g = sum(p[1] for p in pixels) // len(pixels)
                b = sum(p[2] for p in pixels) // len(pixels)
                
                return f"#{r:02x}{g:02x}{b:02x}"
                
        except:
            return "#8B7765"  # Default warm neutral
    
    def format_size(self, size_bytes):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def process_project(self, folder_path):
        """Process a single project folder"""
        folder_name = folder_path.name
        project_id = self.slugify(folder_name)
        
        # Get images
        images = self.get_images_from_folder(folder_path)
        
        if not images:
            print(f"   ⚠️  No images found, skipping")
            return None
        
        print(f"   Found {len(images)} images")
        
        # Get metadata
        metadata = PROJECT_METADATA.get(folder_name, {})
        project_name = metadata.get('name', f"{folder_name} Residency")
        location = metadata.get('location', self.config['default_location'])
        category = metadata.get('category', self.config['default_category'])
        
        # Use specified cover image or fallback to first image
        cover_filename = metadata.get('cover')
        cover_image = images[0]
        if cover_filename:
            for img in images:
                if img.name == cover_filename:
                    cover_image = img
                    break
                    
        cover_path = str(cover_image.relative_to(Path('.'))).replace('\\', '/')
        
        # Build media array (original paths - YOUR EXISTING FORMAT)
        media = []
        for img in images:
            img_path = str(img.relative_to(Path('.'))).replace('\\', '/')
            media.append({
                "type": "image",
                "src": img_path
            })
        
        # Generate optimized versions
        ext = '.webp' if self.config['output_format'] == 'webp' else '.jpg'
        
        # Thumbnail
        thumb_path = Path(self.config['output_structure']['thumbnails']) / f"{project_id}{ext}"
        print(f"   → Generating thumbnail...")
        self.optimize_image(
            cover_image,
            thumb_path,
            self.config['sizes']['thumbnail'],
            self.config['quality']['thumbnail']
        )
        
        # Cover
        cover_opt_path = Path(self.config['output_structure']['covers']) / f"{project_id}{ext}"
        print(f"   → Generating cover...")
        self.optimize_image(
            cover_image,
            cover_opt_path,
            self.config['sizes']['cover'],
            self.config['quality']['cover']
        )
        
        # Blur placeholder
        print(f"   → Generating blur placeholder...")
        blur_data_url = self.generate_blur_data_url(cover_image)
        
        # Save blur file too
        blur_path = Path(self.config['output_structure']['blur']) / f"{project_id}{ext}"
        with Image.open(cover_image) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_small = img.resize(self.config['sizes']['blur'], Image.Resampling.LANCZOS)
            img_small.save(blur_path, 'WEBP', quality=self.config['quality']['blur'])
        
        # Dominant color
        dominant_color = self.get_dominant_color(cover_image)
        
        # Build project data (YOUR EXACT FORMAT + optimized paths)
        project_data = {
            "id": project_id,
            "name": project_name,
            "location": location,
            "category": category,
            "cover": cover_path,  # Original cover path
            "thumbnail": str(thumb_path).replace('\\', '/'),  # Optimized thumbnail
            "coverOptimized": str(cover_opt_path).replace('\\', '/'),  # Optimized cover
            "blurDataUrl": blur_data_url,
            "dominantColor": dominant_color,
            "media": media  # All original images
        }
        
        self.stats['total_images'] += len(images)
        
        print(f"   ✓ Processed successfully")
        
        return project_data
    
    def run(self):
        """Main execution"""
        print("\n" + "=" * 60)
        print("🎨 ARCHITECTURE PORTFOLIO IMAGE OPTIMIZER")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Input: {self.input_path}")
        
        # Setup
        self.setup_output_directories()
        
        # Get projects
        folders = self.get_project_folders()
        
        if not folders:
            print(f"\n❌ No project folders found in '{self.input_path}'")
            print("   Expected structure: images/projects/ProjectName/image.jpg")
            return
        
        print(f"\n📋 Found {len(folders)} project folders:")
        for f in folders:
            print(f"   • {f.name}")
        
        # Process each project
        print("\n" + "-" * 60)
        print("🔄 PROCESSING PROJECTS")
        print("-" * 60)
        
        for folder in folders:
            self.stats['total_projects'] += 1
            print(f"\n📁 [{self.stats['total_projects']}/{len(folders)}] {folder.name}")
            
            project_data = self.process_project(folder)
            
            if project_data:
                self.projects_data.append(project_data)
        
        # Generate JSON
        if self.projects_data:
            self.generate_json()
        
        # Print summary
        self.print_summary()
    
    def generate_json(self):
        """Generate projects.json file"""
        json_path = Path(self.config['json_output'])
        
        # Format for YOUR exact structure
        output_data = []
        for p in self.projects_data:
            output_data.append({
                "id": p["id"],
                "name": p["name"],
                "location": p["location"],
                "category": p["category"],
                "cover": p["cover"],
                "thumbnail": p["thumbnail"],
                "coverOptimized": p["coverOptimized"],
                "blurDataUrl": p["blurDataUrl"],
                "dominantColor": p["dominantColor"],
                "media": p["media"]
            })
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ Generated: {json_path}")
    
    def print_summary(self):
        """Print optimization summary"""
        print("\n" + "=" * 60)
        print("📊 OPTIMIZATION SUMMARY")
        print("=" * 60)
        
        print(f"   Projects processed: {self.stats['total_projects']}")
        print(f"   Total images: {self.stats['total_images']}")
        
        if self.stats['original_size'] > 0:
            savings = self.stats['original_size'] - self.stats['optimized_size']
            savings_percent = (savings / self.stats['original_size']) * 100
            
            print(f"\n   Original size: {self.format_size(self.stats['original_size'])}")
            print(f"   Optimized size: {self.format_size(self.stats['optimized_size'])}")
            print(f"   💾 Saved: {self.format_size(savings)} ({savings_percent:.1f}%)")
        
        print("\n" + "=" * 60)
        print("✨ OPTIMIZATION COMPLETE!")
        print("=" * 60)
        
        # Output file locations
        print("\n📁 Generated files:")
        print(f"   • {self.config['json_output']}")
        print(f"   • {self.config['output_structure']['thumbnails']}/")
        print(f"   • {self.config['output_structure']['covers']}/")
        print(f"   • {self.config['output_structure']['blur']}/")


def main():
    """Entry point"""
    # Check if Pillow is installed
    try:
        from PIL import Image
    except ImportError:
        print("❌ Pillow not installed!")
        print("   Run: pip install Pillow")
        sys.exit(1)
    
    # Check we're in the right directory
    if not Path('images/projects').exists():
        print("⚠️  Warning: 'images/projects' folder not found!")
        print("   Make sure you're running from your website root folder.")
        print("\n   Expected structure:")
        print("   your-website/")
        print("   ├── images/projects/Adhvaita/...")
        print("   ├── images/projects/Akhilesh/...")
        print("   ├── index.html")
        print("   └── optimize_images.py  ← Run from here")
        
        response = input("\n   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    optimizer = ImageOptimizer(CONFIG)
    
    try:
        optimizer.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()