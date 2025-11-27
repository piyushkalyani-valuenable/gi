"""
Gemini Storage Cleanup Script
Fetches all files from Google Gemini storage and deletes them.
Shows storage stats before cleanup.

Usage:
    python server/cleanup.py          # Show stats and cleanup
    python server/cleanup.py --dry    # Show stats only, don't delete
"""
import sys
import os
from pathlib import Path

# Add server directory to path so imports work from any location
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

# Load .env from server directory
from dotenv import load_dotenv
load_dotenv(server_dir / ".env")

from google import genai

# Get API key directly from env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found!")
    print(f"   Make sure it's set in: {server_dir / '.env'}")
    sys.exit(1)


def format_bytes(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def cleanup_gemini_storage(dry_run: bool = False):
    """
    List and delete all files from Gemini storage
    
    Args:
        dry_run: If True, only show stats without deleting
    """
    print("=" * 60)
    print("🔍 GEMINI STORAGE CLEANUP")
    print("=" * 60)
    
    # Initialize client
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Fetch all files
    print("\n📂 Fetching files from Gemini storage...")
    
    try:
        files_list = list(client.files.list())
    except Exception as e:
        print(f"❌ Failed to fetch files: {e}")
        return
    
    if not files_list:
        print("✅ No files found in storage. Nothing to clean up!")
        return
    
    # Calculate stats
    total_files = len(files_list)
    total_bytes = 0
    
    print(f"\n📊 STORAGE STATS:")
    print("-" * 100)
    print(f"{'File Name':<35} {'Size':<12} {'State':<10} {'Created':<20} {'Expires'}")
    print("-" * 100)
    
    for file in files_list:
        file_size = getattr(file, 'size_bytes', 0) or 0
        total_bytes += file_size
        state = getattr(file, 'state', 'unknown')
        
        # Get timestamps
        create_time = getattr(file, 'create_time', None)
        expiration_time = getattr(file, 'expiration_time', None)
        
        # Format timestamps
        created_str = create_time.strftime("%Y-%m-%d %H:%M") if create_time else "N/A"
        expires_str = expiration_time.strftime("%Y-%m-%d %H:%M") if expiration_time else "N/A"
        
        # Truncate long names
        display_name = file.name[:32] + "..." if len(file.name) > 35 else file.name
        print(f"{display_name:<35} {format_bytes(file_size):<12} {state:<10} {created_str:<20} {expires_str}")
    
    print("-" * 100)
    print(f"{'TOTAL':<35} {format_bytes(total_bytes):<12} {total_files} files")
    print()
    
    # Token estimation note:
    # - Images: ~258-768 tokens per image (fixed, not based on size)
    # - PDFs: ~258-768 tokens per page
    # - Text: ~1 token per 4 bytes
    # Since most files here are images/PDFs, estimate ~500 tokens per file
    estimated_tokens = total_files * 500
    print(f"📈 Estimated tokens: ~{estimated_tokens:,} tokens ({total_files} files × ~500 tokens/file)")
    print(f"   Note: Images/PDFs use fixed tokens per file/page, not based on file size")
    print()
    
    if dry_run:
        print("🔒 DRY RUN - No files deleted")
        print("   Run without --dry flag to delete files")
        return
    
    # Confirm deletion
    print(f"⚠️  About to delete {total_files} files ({format_bytes(total_bytes)})")
    confirm = input("   Type 'yes' to confirm: ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Cancelled. No files deleted.")
        return
    
    # Delete files
    print("\n🗑️  Deleting files...")
    deleted = 0
    failed = 0
    
    for file in files_list:
        try:
            client.files.delete(name=file.name)
            print(f"   ✓ Deleted: {file.name}")
            deleted += 1
        except Exception as e:
            print(f"   ✗ Failed: {file.name} - {e}")
            failed += 1
    
    # Summary
    print()
    print("=" * 60)
    print("📋 CLEANUP SUMMARY")
    print("=" * 60)
    print(f"   ✅ Deleted: {deleted} files")
    print(f"   ❌ Failed:  {failed} files")
    print(f"   💾 Freed:   {format_bytes(total_bytes)}")
    print("=" * 60)


if __name__ == "__main__":
    dry_run = "--dry" in sys.argv
    cleanup_gemini_storage(dry_run=dry_run)
