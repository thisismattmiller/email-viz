# email-viz

Visualizing emails on a timeline

**Blog Post:** [https://thisismattmiller.com/post/email-visualization/](https://thisismattmiller.com/post/email-visualization/)

**Live Visualization:** [https://thisismattmiller.github.io/email-viz/viz/dist/](https://thisismattmiller.github.io/email-viz/viz/dist/)

## Scripts

| Script | Description |
|--------|-------------|
| `extract_emails_gemini.py` | Uses Google Gemini API to extract email metadata (sender, receiver, date, subject, etc.) from scanned email images |
| `test_ollama_images.py` | Alternative extraction using local Ollama instance for image processing |
| `analyze_emails.py` | Analyzes extracted email JSON files and generates statistics on senders, receivers, and date distributions |
| `transform_emails.py` | Transforms raw extracted data into the final `all_emails.json` format, consolidates contact names, and organizes emails by contact |
| `extract_har_folder_entries.py` | Extracts Dropbox `list_shared_link_folder_entries` responses from HAR files to get file URLs |
| `add_dropbox_urls.py` | Matches email source files to Dropbox URLs and adds `dropbox_url` field to each email |

## Data Files

| File/Directory | Description |
|----------------|-------------|
| `data/001_results.json` - `data/012_results.json` | Classification of what each document is, by Qwen3-VL 8B |
| `data/email_extracted/` | Individual JSON files for each extracted email image (excluded in the repo) |
| `data/all_emails.json` | Final processed email data organized by contact, used by the visualization |
| `data/emails_analysis.json` | Statistical analysis of emails (sender/receiver counts, date ranges) |
| `data/contacts_summary.json` | Summary of all contacts and their email counts |
| `data/confidentiality_email_blank_email_check.json` | Emails flagged as confidentiality notices or blank, filtering out non-emails |
| `data/dropbox/` | HAR files captured from Dropbox folder browsing |
| `data/dropbox_json/` | Extracted JSON responses from HAR files containing file URLs use to map the files to dropbox urls |
