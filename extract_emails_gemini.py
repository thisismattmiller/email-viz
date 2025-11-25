import base64
import os
import json
import time
from pathlib import Path
from google import genai
from google.genai import types


def encode_image(image_path):
    """Encode an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_mime_type(image_path):
    """Get MIME type based on file extension."""
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


def extract_email_data(image_path):
    """Send image to Gemini and extract email data."""

    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    prompt = """
This is likely a screenshot of an email. If it is not simply respond with an JSON obj: {"notEmail":true}.
There might be multiple nested emails since the email could be a reply to a thread of emails.
For however many emails there are in the image extract the Sender name and email, Receiver name and email, if possible if no email just the name and the date, subject line, and few sentence summary of the email.
Sometimes the sender or receiver name will be redacted, if this is the case add a new field called senderGuess or receiverGuess that is your best guess based on the context of the document who is the sender or receiver if they are redacted.
If the sender or reciever is redacted and cannot guess try to infer the relationship to the the other and put that in senderRelationship or receiverRelationship.
Try to determin if the email was a orgianl message, a reply or a forward and add a field called "messageType" with the value "Original | Reply | Forward".
Return this a JSON array of objects with the key "sender", "senderEmail", "receiver" "receiverEmail" date, subject, summary. represent dates in the yyyy-mm-dd-hh-mm format, senderGuess or receiverGuess or senderRelationship or receiverRelationship . "jeevacation@gmail.com" is "Jeffrey Epstein"

If there are multiple values for the sender or receiver related fields use an array to represent them.

Return ONLY valid JSON, no other text.
"""

    # Read and encode the image
    with open(image_path, "rb") as f:
        image_data = f.read()

    mime_type = get_mime_type(image_path)

    model = "gemini-3-pro-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
        ),
    ]




    # generate_content_config = types.GenerateContentConfig(
    #   temperature=0,
    #   thinking_config=types.ThinkingConfig(
    #       thinking_level=types.ThinkingLevel.HIGH # Dynamic thinking for high reasoning tasks
    #   ),
    #   response_mime_type="application/json"
    # )
    
    
    model = "gemini-2.5-pro"
    generate_content_config = types.GenerateContentConfig(
      temperature=0,
        thinking_config = types.ThinkingConfig(
            thinking_budget=32768,
        ),

      response_mime_type="application/json"
    )



   
   
    # Collect the full response
    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk and hasattr(chunk, 'text') and chunk.text:
            response_text += chunk.text

    return response_text


def main():
    """Main function to process email documents through Gemini."""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    output_dir = os.path.join(data_dir, 'email_extracted')
    os.makedirs(output_dir, exist_ok=True)

    base_image_dir = '/Volumes/NextGlum/emails/IMAGES/'

    print("=" * 80)
    print("Extracting Email Data with Google Gemini")
    print("=" * 80)
    print(f"Output directory: {output_dir}\n")

    # Get all processed files to skip
    processed_files = set()
    for f in os.listdir(output_dir):
        if f.endswith('.json'):
            processed_files.add(f)

    print(f"Already processed: {len(processed_files)} files\n")

    # Load all results files
    results_files = sorted([f for f in os.listdir(data_dir) if f.endswith('_results.json')])

    # Collect all email documents
    email_documents = []

    for results_file in results_files:
        results_path = os.path.join(data_dir, results_file)
        dir_name = results_file.replace('_results.json', '')

        try:
            with open(results_path, 'r') as f:
                results = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not load {results_file}")
            continue

        for result in results:
            if 'parsed_response' not in result or result['parsed_response'] is None:
                continue

            parsed = result['parsed_response']
            if parsed.get('type') == 'Email':
                filename = result['filename']
                image_path = os.path.join(base_image_dir, dir_name, filename)
                output_filename = f"{dir_name}_{filename}.json"

                if output_filename not in processed_files:
                    email_documents.append({
                        'filename': filename,
                        'dir_name': dir_name,
                        'image_path': image_path,
                        'output_filename': output_filename
                    })

    print(f"Found {len(email_documents)} email documents to process\n")

    if not email_documents:
        print("No email documents to process!")
        return

    # Timing variables
    start_time = time.time()
    processed_count = 0

    # Process each email document
    for i, doc in enumerate(email_documents, 1):
        print(f"[{i}/{len(email_documents)}] Processing {doc['dir_name']}/{doc['filename']}...")

        if not os.path.exists(doc['image_path']):
            print(f"  Warning: Image not found: {doc['image_path']}")
            continue

        try:
            response_text = extract_email_data(doc['image_path'])
            print(response_text)
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
                    print(f"  Warning: Could not parse JSON response: {error}")

            # Save result
            result_entry = {
                'source_dir': doc['dir_name'],
                'filename': doc['filename'],
                'image_path': doc['image_path'],
                'response_text': response_text,
                'parsed_response': parsed_response,
                'error': error
            }

            output_path = os.path.join(output_dir, doc['output_filename'])
            with open(output_path, 'w') as f:
                json.dump(result_entry, f, indent=2)

            processed_count += 1
            print(f"  Saved to {doc['output_filename']}")

            # Calculate and display estimated time remaining
            if processed_count > 0:
                elapsed_time = time.time() - start_time
                avg_time_per_doc = elapsed_time / processed_count
                remaining_docs = len(email_documents) - i
                estimated_remaining_seconds = avg_time_per_doc * remaining_docs

                hours = int(estimated_remaining_seconds // 3600)
                minutes = int((estimated_remaining_seconds % 3600) // 60)

                print(f"  Estimated time remaining: {hours}h {minutes}m (avg {avg_time_per_doc:.1f}s per doc)")

        except Exception as e:
            print(f"  Error: {e}")
            # Save error result
            error_entry = {
                'source_dir': doc['dir_name'],
                'filename': doc['filename'],
                'image_path': doc['image_path'],
                'error': str(e)
            }
            output_path = os.path.join(output_dir, doc['output_filename'])
            with open(output_path, 'w') as f:
                json.dump(error_entry, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Completed! Processed {processed_count} email documents.")
    print("=" * 80)


if __name__ == "__main__":
    main()
