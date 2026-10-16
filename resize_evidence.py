#!/usr/bin/env python3
# /// script
# dependencies = [
#     "Pillow",
# ]
# ///
"""
Author: ADO Security
Description: Resizes individual image files or bulk directories of PNG/JPG images 
             to exactly 800px wide while scaling height proportionately. 
             Includes robust path resolution and safe in-place editing.
"""

import os
import sys
import tempfile
from PIL import Image

TARGET_WIDTH = 800
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg')

def resize_single_image(input_path, output_path):
    try:
        real_input = os.path.realpath(input_path)
        
        # If output exists, check if input and output are the same file
        is_same_file = False
        if os.path.exists(output_path):
            if os.path.isfile(output_path):
                try:
                    if os.path.samefile(input_path, output_path):
                        is_same_file = True
                except Exception:
                    is_same_file = (real_input == os.path.realpath(output_path))
            elif os.path.isdir(output_path):
                # If output is a directory, redirect output path inside it
                output_path = os.path.join(output_path, os.path.basename(input_path))

        with Image.open(input_path) as img:
            orig_width, orig_height = img.size
            new_height = int((TARGET_WIDTH / float(orig_width)) * orig_height)
            
            resized_img = img.resize((TARGET_WIDTH, new_height), Image.Resampling.LANCZOS)
            
            if is_same_file:
                # Safe in-place write via temp file
                dir_name = os.path.dirname(real_input)
                with tempfile.NamedTemporaryFile(dir=dir_name, delete=False, suffix=os.path.splitext(input_path)[1]) as temp_file:
                    temp_output = temp_file.name
                
                resized_img.save(temp_output)
                os.replace(temp_output, input_path)
                print(f"[OK] {os.path.basename(input_path)} (In-Place): {orig_width}x{orig_height} -> {TARGET_WIDTH}x{new_height}")
            else:
                output_dir = os.path.dirname(output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # Prevent saving a file over a directory
                if os.path.isdir(output_path):
                    print(f"[ERROR] Output path '{output_path}' is a directory. Please specify a file destination.")
                    return
                    
                resized_img.save(output_path)
                print(f"[OK] {os.path.basename(input_path)} -> {output_path} ({orig_width}x{orig_height} -> {TARGET_WIDTH}x{new_height})")
                
    except Exception as e:
        print(f"[ERROR] Failed to process {input_path}: {e}")

def resize_images(input_path, output_path):
    if os.path.isfile(input_path):
        if not input_path.lower().endswith(SUPPORTED_EXTENSIONS):
            print(f"[-] Error: Input file '{input_path}' is not a supported image format.")
            sys.exit(1)
            
        resize_single_image(input_path, output_path)
        print("[+] Single file resizing complete.")

    elif os.path.isdir(input_path):
        if os.path.exists(output_path) and os.path.isfile(output_path):
            print(f"[-] Error: Input is a directory, but output path '{output_path}' is an existing file.")
            sys.exit(1)
            
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            print(f"[+] Created output directory: {output_path}")

        files = [f for f in os.listdir(input_path) if f.lower().endswith(SUPPORTED_EXTENSIONS)]
        
        if not files:
            print(f"[-] No supported images found in {input_path}")
            return

        print(f"[+] Processing {len(files)} images...")
        
        for filename in files:
            src_file = os.path.join(input_path, filename)
            dst_file = os.path.join(output_path, filename)
            resize_single_image(src_file, dst_file)

        print("[+] Bulk resizing complete.")
    else:
        print(f"[-] Error: Input path '{input_path}' does not exist or is invalid.")
        sys.exit(1)

if __name__ == '__main__':
    source = sys.argv[1] if len(sys.argv) > 1 else "./screenshots"
    destination = sys.argv[2] if len(sys.argv) > 2 else "./resized_screenshots"
    
    resize_images(source, destination)
