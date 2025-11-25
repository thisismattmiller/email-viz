import ollama
import base64
import os
import json
import time
from pathlib import Path

def encode_image(image_path):
    """Encode an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def send_image_to_ollama(image_path, host='http://192.168.1.60:11434'):


    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        return None

    # Encode the image
    print(f"Processing image: {image_path}")
    encoded_image = encode_image(image_path)

    # Create Ollama client
    client = ollama.Client(
        host=host,
        headers={'x-some-header': 'some-value'},
        timeout=60
    )

    # Prompt for image description
    # prompt ="""Which of these options best describes the image?
    #     1. An Email, the first page
    #     2. An Email, a later page, a continuation
    #     3. A Other document. (classify type, Web page, Tweet, bank statement, power point presentation, etc.)

    #     The first page of an email typically includes the sender's information, recipient's information, subject line, date, and the beginning of the email body. 
    #     a continuation will be the overflow of text from the previous page.

    #     Return in valid JSON in the format:
    #     {
    #     "type": "Email First Page | Email Continuation | Other Document",
    #     "otherType": "<type if Other Document, else null>",
    #     "explanation": "<brief explanation of why>"
    #     }   

    #     Do not send any other response besides the JSON. 
    # """

    # prompt = """
    # This may be a screenshot of an email. 
    # There might be multiple nested emails since the email could be a reply to a thread of emails. 
    # For however many emails there are in the image extract the Sender name and email, Receiver name and email, if possible if no email just the name and the date, subject line, and few sentence summary of the email. 
    # Return this a JSON array of objects with the key "sender", "senderEmail", "receiver" "receiverEmail" date, subject, summary. represent dates in the yyyy-mm-dd-hh-mm format. "Jeevacation" is "Jeffrey Epstein"
    # If it is not an email return a empty JSON array: []




#     This is a screenshot of an email. 
#     There might be multiple nested emails since the email could be a reply to a thread of emails. 
#     For however many emails there are in the image extract the Sender name and email, Receiver name and email, if possible if no email just the name and the date, subject line, and few sentence summary of the email. 
# Sometimes the sender or receiver name will be redacted, if this is the case add a new field called senderGuess or receiverGuess that is your best guess based on the context of the document who is the sender or receiver if they are redacted.

#  Return this a JSON array of objects with the key "sender", "senderEmail", "receiver" "receiverEmail" date, subject, summary. represent dates in the yyyy-mm-dd-hh-mm format, senderGuess or receiverGuess . "Jeevacation" is "Jeffrey Epstein"
#     If it is not an email return a empty JSON array: []





    # """

    prompt = """
    Return if this image is an email or a different type of document.  
    return in valid JSON format as { "type": "Email | Other Document", "otherType": "<type if Other Document, else null>" }.
    """
    



    try:
        # Send request to Ollama
        response = client.chat(
            model="qwen3-vl:8b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [encoded_image],
                }
            ],
        )

        description = response['message']['content']
        print(f"\nDescription:\n{description}\n")
        print("-" * 80)

        return description

    except Exception as e:
        print(f"Error communicating with Ollama: {e}")
        return None

def process_directory(dir_path, output_dir, ollama_host='http://192.168.1.60:11434'):
    """Process all images in a directory and save results to JSON."""

    dir_name = os.path.basename(dir_path)
    output_file = os.path.join(output_dir, f"{dir_name}_results.json")

    # Load existing results if any
    processed_files = set()
    results = []

    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                results = json.load(f)
                processed_files = {r['filename'] for r in results if 'filename' in r}
            print(f"Loaded {len(processed_files)} already processed files from {output_file}")
        except json.JSONDecodeError:
            print(f"Warning: Could not load {output_file}, starting fresh")

    # Get all image files (excluding TIF/TIFF)
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    image_files = []

    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                image_files.append(file)

    image_files.sort()  # Process in consistent order

    print(f"\nProcessing directory: {dir_path}")
    print(f"Found {len(image_files)} image files")
    print(f"Already processed: {len(processed_files)}")
    print(f"Remaining: {len(image_files) - len(processed_files)}")
    print()

    # Timing variables
    start_time = time.time()
    processed_count = 0

    # Process each image
    for i, filename in enumerate(image_files, 1):
        if filename in processed_files:
            print(f"[{i}/{len(image_files)}] Skipping {filename} (already processed)")
            continue

        print(f"[{i}/{len(image_files)}] Processing {filename}...")

        image_path = os.path.join(dir_path, filename)

        try:
            response_text = send_image_to_ollama(image_path, ollama_host)

            # Try to parse as JSON
            parsed_response = None
            error = None

            if response_text:
                try:
                    # Clean up common JSON formatting issues
                    clean_response = response_text.replace('```json', '').replace('```', '').strip()
                    parsed_response = json.loads(clean_response)
                except json.JSONDecodeError as e:
                    error = f"JSONDecodeError: {str(e)}"
                    print(f"Warning: Could not parse JSON response: {error}")

            # Save result
            result_entry = {
                'filename': filename,
                'response_text': response_text,
                'parsed_response': parsed_response,
                'error': error
            }

            results.append(result_entry)
            processed_count += 1

            # Save after each image (for crash recovery)
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

            print(f"Saved result to {output_file}")

            # Calculate and display estimated time remaining
            if processed_count > 0:
                elapsed_time = time.time() - start_time
                avg_time_per_image = elapsed_time / processed_count
                remaining_images = len(image_files) - len(processed_files) - processed_count
                estimated_remaining_seconds = avg_time_per_image * remaining_images

                hours = int(estimated_remaining_seconds // 3600)
                minutes = int((estimated_remaining_seconds % 3600) // 60)

                print(f"Estimated time remaining for this directory: {hours}h {minutes}m (avg {avg_time_per_image:.1f}s per image)")

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            results.append({
                'filename': filename,
                'error': str(e)
            })
            # Save even on error
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

    print(f"\nCompleted directory {dir_path}")
    print(f"Total processed: {len(results)}")
    return results


def main():
    """Main function to process all directories."""

    base_dir = '/Volumes/NextGlum/emails/IMAGES/'
    ollama_host = 'http://192.168.1.60:11434'

    # Create data directory in script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'data')
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}\n")

    # Find all directories matching pattern 001-012
    directories = []
    for i in range(1, 13):
        dir_name = f"{i:03d}"
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.isdir(dir_path):
            directories.append(dir_path)
        else:
            print(f"Warning: Directory {dir_path} not found")

    print("=" * 80)
    print("Processing Email Images with Ollama")
    print("=" * 80)
    print(f"\nFound {len(directories)} directories to process")
    print()

    # Process each directory
    for dir_idx, dir_path in enumerate(directories, 1):
        print("\n" + "=" * 80)
        print(f"Directory {dir_idx}/{len(directories)}")
        print("=" * 80)
        process_directory(dir_path, output_dir, ollama_host)

    print("\n" + "=" * 80)
    print("All directories processed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
