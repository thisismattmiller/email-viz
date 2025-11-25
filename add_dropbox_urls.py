#!/usr/bin/env python3
"""
Add Dropbox URLs to all_emails.json by matching source_file with dropbox filenames.
"""

import json
import os
import glob


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dropbox_json_dir = os.path.join(script_dir, "data", "dropbox_json")
    all_emails_path = os.path.join(script_dir, "data", "all_emails.json")

    # Build lookup from filename to href
    filename_to_href = {}

    json_files = glob.glob(os.path.join(dropbox_json_dir, "*.json"))
    print(f"Loading {len(json_files)} dropbox JSON files...")

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for response_entry in data:
            entries = response_entry.get('response', {}).get('entries', [])
            for entry in entries:
                filename = entry.get('filename')
                href = entry.get('href')
                if filename and href:
                    filename_to_href[filename] = href

    print(f"Built lookup with {len(filename_to_href)} filenames")

    # Load all_emails.json
    print(f"Loading {all_emails_path}...")
    with open(all_emails_path, 'r', encoding='utf-8') as f:
        all_emails = json.load(f)

    # Match and add URLs
    matched = 0
    unmatched = 0

    for contact, contact_data in all_emails.items():
        for email in contact_data.get('emails', []):
            source_file = email.get('source_file')
            if source_file:
                # source_file format: "009_HOUSE_OVERSIGHT_027063.jpg.json"
                # dropbox filename format: "HOUSE_OVERSIGHT_027063.jpg"
                # Remove prefix (###_) and .json suffix
                import re
                match = re.match(r'^\d+_(.+)\.json$', source_file)
                if match:
                    dropbox_filename = match.group(1)
                    href = filename_to_href.get(dropbox_filename)
                    if href:
                        email['dropbox_url'] = href
                        matched += 1
                    else:
                        unmatched += 1

    print(f"Matched: {matched}, Unmatched: {unmatched}")

    # Save updated all_emails.json
    with open(all_emails_path, 'w', encoding='utf-8') as f:
        json.dump(all_emails, f, indent=2)

    print(f"Updated {all_emails_path}")


if __name__ == "__main__":
    main()
