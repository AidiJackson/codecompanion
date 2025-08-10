#!/usr/bin/env python3
"""
Temporary script to help clear OpenAI API key from environment
This will help reset the key so a fresh one can be added
"""
import os
import sys

def main():
    print("🔍 Checking current OpenAI API key status...")
    
    # Check if key exists
    current_key = os.getenv('OPENAI_API_KEY')
    if current_key:
        print(f"Found key: {current_key[:8]}...{current_key[-4:]} (length: {len(current_key)})")
        print("The key exists but appears to be invalid based on API testing.")
        print("\n📝 To fix this:")
        print("1. Go to Replit project settings")
        print("2. Click on 'Secrets' tab")
        print("3. Find OPENAI_API_KEY entry")
        print("4. Click the trash/delete icon to remove it")
        print("5. Add a fresh key from platform.openai.com")
        print("\nAlternatively, click the pencil/edit icon and overwrite the value.")
    else:
        print("✅ No OpenAI API key found - ready for fresh key!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())