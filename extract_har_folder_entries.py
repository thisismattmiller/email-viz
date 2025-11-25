#!/usr/bin/env python3
"""
Extract JSON responses from Dropbox list_shared_link_folder_entries requests in HAR files.
"""

import json
import os
import glob

def extract_folder_entries():
    """Load all .har files from data/dropbox and extract list_shared_link_folder_entries responses."""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    har_dir = os.path.join(script_dir, "data", "dropbox")
    output_dir = os.path.join(script_dir, "data", "dropbox_json")

    os.makedirs(output_dir, exist_ok=True)

    har_files = glob.glob(os.path.join(har_dir, "*.har"))

    if not har_files:
        print(f"No .har files found in {har_dir}")
        return

    for har_file in har_files:
        print(f"Processing: {har_file}")

        with open(har_file, 'r', encoding='utf-8') as f:
            har_data = json.load(f)

        entries = har_data.get('log', {}).get('entries', [])
        all_entries = []

        for entry in entries:
            request = entry.get('request', {})
            url = request.get('url', '')

            if 'list_shared_link_folder_entries' in url:
                response = entry.get('response', {})
                content = response.get('content', {})
                text = content.get('text', '')

                if text:
                    try:
                        json_response = json.loads(text)
                        all_entries.append({
                            'url': url,
                            'response': json_response
                        })
                        print(f"  Found response with {len(json_response.get('entries', []))} entries")
                    except json.JSONDecodeError as e:
                        print(f"  Failed to parse JSON: {e}")

        # Save with same name as .har but .json extension
        har_basename = os.path.basename(har_file)
        json_filename = os.path.splitext(har_basename)[0] + ".json"
        output_file = os.path.join(output_dir, json_filename)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_entries, f, indent=2)

        # Count total files
        total_files = sum(len(e.get('response', {}).get('entries', [])) for e in all_entries)
        print(f"  Saved {len(all_entries)} responses ({total_files} file entries) to: {output_file}")


if __name__ == "__main__":
    extract_folder_entries()
