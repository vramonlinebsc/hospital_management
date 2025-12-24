#!/usr/bin/env python3
"""
Hospital Management System - Submission ZIP Creator
====================================================

This script creates a properly structured ZIP file for project submission.

Features:
- Excludes unnecessary files (__pycache__, .pyc, venv, .git, hospital.db)
- Maintains correct folder structure as per submission guidelines
- Validates ZIP contents before finalizing
- Creates ZIP with roll number in filename

Usage:
    python create_submission_zip.py

Author: Generated for MAD-1 Project
Date: November 2025
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """Print script header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}")
    print("   Hospital Management System - Submission ZIP Creator")
    print(f"{'='*70}{Colors.END}\n")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def get_roll_number():
    """Get roll number from user"""
    print(f"{Colors.BOLD}Enter your roll number (e.g., 2K24XXXXX):{Colors.END}")
    roll_number = input("Roll Number: ").strip()
    
    if not roll_number:
        print_warning("No roll number provided. Using default: 2KXXXX")
        return "2KXXXX"
    
    return roll_number

def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent.absolute()

def should_exclude(path, excludes):
    """Check if a path should be excluded from ZIP"""
    path_str = str(path)
    
    # Exclude specific files and folders
    for exclude in excludes:
        if exclude in path_str:
            return True
    
    # Exclude hidden files (starting with .)
    if path.name.startswith('.') and path.name not in ['.gitignore']:
        return True
    
    # Exclude Python cache files
    if path.suffix in ['.pyc', '.pyo']:
        return True
    
    # Exclude large files
    if path.is_file() and path.stat().st_size > 50 * 1024 * 1024:  # 50 MB
        print_warning(f"Excluding large file: {path.name} ({path.stat().st_size / (1024*1024):.2f} MB)")
        return True
    
    return False

def copy_project_files(source_dir, dest_dir, excludes):
    """Copy project files to temporary directory, excluding unnecessary files"""
    print_info("Copying project files...")
    
    files_copied = 0
    files_excluded = 0
    
    for root, dirs, files in os.walk(source_dir):
        # Remove excluded directories from traversal
        dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d, excludes)]
        
        for file in files:
            source_path = Path(root) / file
            
            if should_exclude(source_path, excludes):
                files_excluded += 1
                continue
            
            # Calculate relative path
            relative_path = source_path.relative_to(source_dir)
            dest_path = dest_dir / relative_path
            
            # Create destination directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            try:
                shutil.copy2(source_path, dest_path)
                files_copied += 1
                
                # Show progress for every 10 files
                if files_copied % 10 == 0:
                    print(f"   Copied {files_copied} files...", end='\r')
            except Exception as e:
                print_warning(f"Failed to copy {relative_path}: {e}")
    
    print(f"   Copied {files_copied} files...{' ' * 20}")  # Clear line
    print_success(f"Copied {files_copied} files (excluded {files_excluded} files)")
    
    return files_copied

def validate_required_files(project_dir):
    """Validate that required files are present"""
    print_info("Validating required files...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'README.md',
    ]
    
    required_dirs = [
        'templates',
        'static',
        'models',
        'routes',
    ]
    
    missing_files = []
    missing_dirs = []
    
    # Check required files
    for file in required_files:
        if not (project_dir / file).exists():
            missing_files.append(file)
    
    # Check required directories
    for dir_name in required_dirs:
        if not (project_dir / dir_name).exists():
            missing_dirs.append(dir_name)
    
    if missing_files or missing_dirs:
        print_error("Missing required files/directories:")
        for file in missing_files:
            print(f"   ❌ {file}")
        for dir_name in missing_dirs:
            print(f"   ❌ {dir_name}/")
        return False
    
    print_success("All required files present")
    return True

def check_project_report(project_dir):
    """Check if Project_Report.pdf exists"""
    report_files = list(project_dir.glob('Project_Report.pdf'))
    
    if not report_files:
        print_warning("Project_Report.pdf not found!")
        print_info("Make sure to add your Project_Report.pdf before submission")
        return False
    
    print_success("Project_Report.pdf found")
    return True

def create_zip_file(source_dir, zip_path, project_folder_name):
    """Create ZIP file with proper structure"""
    print_info(f"Creating ZIP file: {zip_path.name}")
    
    files_added = 0
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                
                # Calculate archive path (inside project folder)
                relative_path = file_path.relative_to(source_dir)
                archive_path = f"{project_folder_name}/{relative_path}"
                
                # Add to ZIP
                zipf.write(file_path, archive_path)
                files_added += 1
                
                # Show progress
                if files_added % 10 == 0:
                    print(f"   Added {files_added} files to ZIP...", end='\r')
    
    print(f"   Added {files_added} files to ZIP...{' ' * 20}")  # Clear line
    print_success(f"ZIP file created with {files_added} files")
    
    return files_added

def validate_zip_structure(zip_path, project_folder_name):
    """Validate ZIP file structure"""
    print_info("Validating ZIP structure...")
    
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        file_list = zipf.namelist()
        
        # Check if all files are inside project folder
        if not all(f.startswith(f"{project_folder_name}/") for f in file_list):
            print_error("ZIP structure incorrect! Some files are not inside project folder")
            return False
        
        # Check if main file exists
        if f"{project_folder_name}/app.py" not in file_list:
            print_error("app.py not found in ZIP!")
            return False
        
        # Check if requirements.txt exists
        if f"{project_folder_name}/requirements.txt" not in file_list:
            print_error("requirements.txt not found in ZIP!")
            return False
        
        print_success("ZIP structure is correct")
        
        # Show some sample files
        print(f"\n{Colors.CYAN}Sample ZIP structure:{Colors.END}")
        sample_files = file_list[:10]
        for file in sample_files:
            print(f"   📄 {file}")
        if len(file_list) > 10:
            print(f"   ... and {len(file_list) - 10} more files")
    
    return True

def get_zip_size(zip_path):
    """Get ZIP file size in human-readable format"""
    size_bytes = zip_path.stat().st_size
    
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def main():
    """Main function"""
    print_header()
    
    # Get project root directory
    project_root = get_project_root()
    project_name = project_root.name
    
    print_info(f"Project directory: {project_root}")
    print_info(f"Project name: {project_name}\n")
    
    # Get roll number
    roll_number = get_roll_number()
    print()
    
    # Define paths
    temp_dir = project_root / 'temp_submission'
    project_folder_name = f"{project_name}"
    zip_filename = f"{project_name}_{roll_number}.zip"
    zip_path = project_root / zip_filename
    
    # Files and folders to exclude
    excludes = [
        '__pycache__',
        '.pyc',
        '.pyo',
        'venv',
        'env',
        '.env',
        '.git',
        '.gitignore',
        'hospital.db',
        'temp_submission',
        zip_filename,
        '.DS_Store',
        'Thumbs.db',
        '*.log',
        'core',  # core dump file
        '.vscode',
        '.idea',
        'node_modules',
        'DEPLOYMENT_GUIDE.pdf',
        'TESTING_CHECKLIST.pdf',
        'TROUBLESHOOTING.pdf',
        'create_submission_zip.py',  # Exclude this script itself (optional)
    ]
    
    try:
        # Clean up old temp directory if exists
        if temp_dir.exists():
            print_info("Cleaning up old temporary files...")
            shutil.rmtree(temp_dir)
        
        # Create temporary directory
        temp_dir.mkdir(parents=True)
        project_temp_dir = temp_dir / project_folder_name
        project_temp_dir.mkdir(parents=True)
        
        # Copy project files
        files_copied = copy_project_files(project_root, project_temp_dir, excludes)
        print()
        
        if files_copied == 0:
            print_error("No files were copied! Something went wrong.")
            return
        
        # Validate required files
        if not validate_required_files(project_temp_dir):
            print_error("Validation failed! Please ensure all required files are present.")
            return
        
        # Check for project report
        has_report = check_project_report(project_temp_dir)
        print()
        
        # Delete old ZIP if exists
        if zip_path.exists():
            print_info(f"Deleting old ZIP file: {zip_filename}")
            zip_path.unlink()
            print()
        
        # Create ZIP file
        files_added = create_zip_file(temp_dir, zip_path, project_folder_name)
        print()
        
        # Validate ZIP structure
        if not validate_zip_structure(zip_path, project_folder_name):
            print_error("ZIP validation failed!")
            return
        
        # Get ZIP size
        zip_size = get_zip_size(zip_path)
        
        # Success message
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*70}")
        print("   ✅ SUCCESS! Submission ZIP created successfully!")
        print(f"{'='*70}{Colors.END}\n")
        
        print(f"{Colors.BOLD}ZIP File Details:{Colors.END}")
        print(f"   📦 Filename: {Colors.CYAN}{zip_filename}{Colors.END}")
        print(f"   📍 Location: {Colors.CYAN}{zip_path}{Colors.END}")
        print(f"   💾 Size: {Colors.CYAN}{zip_size}{Colors.END}")
        print(f"   📄 Files: {Colors.CYAN}{files_added}{Colors.END}")
        print()
        
        # Warnings
        if not has_report:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  IMPORTANT:{Colors.END}")
            print(f"{Colors.YELLOW}   Add Project_Report.pdf and run this script again!{Colors.END}")
            print()
        
        # Check ZIP size
        if zip_path.stat().st_size > 100 * 1024 * 1024:  # 100 MB
            print_warning(f"ZIP file is quite large ({zip_size})")
            print_info("Consider removing unnecessary files or large assets")
            print()
        
        # Next steps
        print(f"{Colors.BOLD}Next Steps:{Colors.END}")
        print(f"   1. Verify ZIP structure by extracting and testing")
        print(f"   2. Use validation Google form (link in submission portal)")
        print(f"   3. Submit ZIP file to project submission portal")
        print(f"   4. Check your email for validation confirmation")
        print()
        
        # Testing instructions
        print(f"{Colors.BOLD}To test your submission:{Colors.END}")
        print(f"   {Colors.CYAN}# Extract ZIP file{Colors.END}")
        print(f"   unzip {zip_filename}")
        print()
        print(f"   {Colors.CYAN}# Navigate to project directory{Colors.END}")
        print(f"   cd {project_folder_name}")
        print()
        print(f"   {Colors.CYAN}# Create virtual environment and install{Colors.END}")
        print(f"   python -m venv venv")
        print(f"   source venv/bin/activate  # or venv\\Scripts\\activate on Windows")
        print(f"   pip install -r requirements.txt")
        print()
        print(f"   {Colors.CYAN}# Run the application{Colors.END}")
        print(f"   python app.py")
        print()
        
        print(f"{Colors.GREEN}Good luck with your submission! 🚀{Colors.END}\n")
        
    except Exception as e:
        print_error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            print_info("Cleaning up temporary files...")
            try:
                shutil.rmtree(temp_dir)
                print_success("Cleanup complete")
            except Exception as e:
                print_warning(f"Could not clean up temporary files: {e}")
                print_info(f"Please manually delete: {temp_dir}")

if __name__ == "__main__":
    main()
