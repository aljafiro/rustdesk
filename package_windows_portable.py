#!/usr/bin/env python3
"""
RustDesk Windows Portable Packager using Enigma Virtual Box.
This script automatically generates the .evb configuration file for Enigma Virtual Box
by recursively scanning the compiled Release directory, then compiles it into a single EXE.
"""

import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Default Paths (Adjust these if your build directory is different)
POSSIBLE_RELEASE_DIRS = [
    r"flutter\build\windows\x64\runner\Release",
    r"flutter\build\windows\runner\Release",
    r"build\windows\x64\runner\Release",
]
DEFAULT_RELEASE_DIR = POSSIBLE_RELEASE_DIRS[0]
for d in POSSIBLE_RELEASE_DIRS:
    if os.path.exists(d):
        DEFAULT_RELEASE_DIR = d
        break

OUTPUT_EVB_FILE = "soporte_deputacion.evb"
FINAL_EXE_NAME = "Soporte_Deputacion.exe"

def indent_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def add_files_recursively(parent_xml_element, folder_path, base_path):
    """Recursively scan a directory and map its files/folders to EVB XML format."""
    files_node = ET.SubElement(parent_xml_element, "Files")
    
    # Process files in the current folder
    for entry in os.scandir(folder_path):
        if entry.is_file():
            file_node = ET.SubElement(files_node, "File")
            ET.SubElement(file_node, "Type").text = "2"  # Type 2 = External file virtualized
            ET.SubElement(file_node, "Name").text = entry.name
            # Relative path to the original file
            rel_path = os.path.relpath(entry.path, base_path)
            ET.SubElement(file_node, "File").text = rel_path
            ET.SubElement(file_node, "Active").text = "true"
            
        elif entry.is_dir():
            folder_node = ET.SubElement(files_node, "Folder")
            ET.SubElement(folder_node, "Name").text = entry.name
            # Recursively scan subfolders
            add_files_recursively(folder_node, entry.path, base_path)

def generate_evb(release_dir, evb_output_path, final_exe):
    print(f"[*] Scanning release directory: {release_dir}")
    if not os.path.exists(release_dir):
        print(f"[!] Error: Release directory '{release_dir}' not found!")
        print("Please compile the Windows project first using flutter build windows.")
        return False
        
    main_exe = os.path.join(release_dir, "rustdesk.exe")
    if not os.path.exists(main_exe):
        # Fallback to general compiled .exe name
        exes = [f for f in os.listdir(release_dir) if f.endswith(".exe")]
        if exes:
            main_exe = os.path.join(release_dir, exes[0])
        else:
            print(f"[!] Error: Main executable not found in '{release_dir}'!")
            return False

    # Create EVB Root element
    root = ET.Element("Virtual_Box", {"version": "windows-1251"})
    
    # Global Settings
    ET.SubElement(root, "Input_File").text = os.path.abspath(main_exe)
    ET.SubElement(root, "Output_File").text = os.path.abspath(final_exe)
    ET.SubElement(root, "Compression").text = "true"
    ET.SubElement(root, "Share_Virtual_System").text = "true"
    ET.SubElement(root, "Map_Executables").text = "false"
    
    # Files Node
    files_root = ET.SubElement(root, "Files")
    ET.SubElement(files_root, "Enabled").text = "true"
    
    # Default Folder node represents the virtual directory where files are placed
    default_folder = ET.SubElement(files_root, "Folder")
    ET.SubElement(default_folder, "Name").text = "%DEFAULT FOLDER%"
    
    # Scan everything in the Release folder EXCEPT the main executable itself
    files_node = ET.SubElement(default_folder, "Files")
    for entry in os.scandir(release_dir):
        if entry.is_file() and entry.path != main_exe:
            file_node = ET.SubElement(files_node, "File")
            ET.SubElement(file_node, "Type").text = "2"
            ET.SubElement(file_node, "Name").text = entry.name
            ET.SubElement(file_node, "File").text = os.path.relpath(entry.path, ".")
            ET.SubElement(file_node, "Active").text = "true"
            
        elif entry.is_dir():
            folder_node = ET.SubElement(files_node, "Folder")
            ET.SubElement(folder_node, "Name").text = entry.name
            add_files_recursively(folder_node, entry.path, ".")

    # Write EVB file
    xml_str = indent_xml(root)
    with open(evb_output_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
        
    print(f"[+] Successfully generated EVB project file: '{evb_output_path}'")
    return True

def main():
    print("====================================================")
    print("  RustDesk Windows Portable Packager Generator      ")
    print("====================================================")
    
    release_dir = DEFAULT_RELEASE_DIR
    if len(sys.argv) > 1:
        release_dir = sys.argv[1]
        
    success = generate_evb(release_dir, OUTPUT_EVB_FILE, FINAL_EXE_NAME)
    if success:
        print("\n--- NEXT STEPS TO BUILD & SIGN ON WINDOWS ---")
        print("1. Install Enigma Virtual Box (from: https://enigmaprotector.com/en/aboutvb.html)")
        print(f"2. Run Enigma Virtual Box via Command Line to pack the app:")
        print(f"   \"C:\\Program Files (x86)\\Enigma Virtual Box\\enigmavbox.exe\" {OUTPUT_EVB_FILE}")
        print(f"3. Sign the resulting single executable using your certificate:")
        print(f"   signtool sign /f \"YourCertificate.pfx\" /p \"YourPassword\" /tr http://timestamp.digicert.com /td sha256 /fd sha256 {FINAL_EXE_NAME}")
        print("\nYour client will then be fully compiled, packaged, signed, and ready for AppLocker distribution!")

if __name__ == "__main__":
    main()
