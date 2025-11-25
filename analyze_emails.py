import os
import json
from collections import defaultdict
from datetime import datetime

def parse_date(date_str):
    """Parse date string in yyyy-mm-dd-hh-mm format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d-%H-%M")
    except (ValueError, TypeError):
        return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, 'data', 'email_extracted')
    output_file = os.path.join(script_dir, 'data', 'emails_analysis.json')

    if not os.path.exists(input_dir):
        print(f"Error: Directory not found: {input_dir}")
        return

    # Data structures for analysis
    senders = defaultdict(lambda: {'count': 0, 'dates': []})
    receivers = defaultdict(lambda: {'count': 0, 'dates': []})
    all_dates = []

    # Stats
    total_files = 0
    valid_files = 0
    invalid_files = 0
    total_emails = 0
    files_with_errors = []
    not_email_count = 0

    # Process all JSON files
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    total_files = len(json_files)

    print(f"Processing {total_files} files from {input_dir}")

    for filename in json_files:
        filepath = os.path.join(input_dir, filename)

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            invalid_files += 1
            files_with_errors.append({'file': filename, 'error': 'JSONDecodeError'})
            continue

        # Get parsed_response from the file structure
        parsed = data.get('parsed_response')

        if not parsed:
            invalid_files += 1
            files_with_errors.append({'file': filename, 'error': 'No parsed_response'})
            continue

        # Check for notEmail marker
        if isinstance(parsed, dict) and parsed.get('notEmail'):
            not_email_count += 1
            continue

        # Ensure it's a list
        if isinstance(parsed, dict):
            parsed = [parsed]

        if not isinstance(parsed, list):
            invalid_files += 1
            files_with_errors.append({'file': filename, 'error': 'parsed_response is not a list or dict'})
            continue

        valid_files += 1

        for email in parsed:
            if not isinstance(email, dict):
                continue

            total_emails += 1

            # Extract sender info
            sender = email.get('sender') or email.get('senderGuess') or 'Unknown'
            sender_email = email.get('senderEmail')

            # Handle various types for sender
            if isinstance(sender, dict):
                sender = str(sender)
            elif isinstance(sender, list):
                sender = ', '.join(str(s) for s in sender)

            if sender_email:
                if isinstance(sender_email, list):
                    sender_email = ', '.join(str(e) for e in sender_email)
                sender = f"{sender} <{sender_email}>"

            # Extract receiver info
            receiver = email.get('receiver') or email.get('receiverGuess') or 'Unknown'
            receiver_email = email.get('receiverEmail')

            # Handle various types for receiver
            if isinstance(receiver, dict):
                receiver = str(receiver)
            elif isinstance(receiver, list):
                receiver = ', '.join(str(r) for r in receiver)

            if receiver_email:
                if isinstance(receiver_email, list):
                    receiver_email = ', '.join(str(e) for e in receiver_email)
                receiver = f"{receiver} <{receiver_email}>"

            # Parse date
            date_str = email.get('date')
            date_obj = parse_date(date_str)

            # Update sender stats
            senders[sender]['count'] += 1
            if date_obj:
                senders[sender]['dates'].append(date_obj)
                all_dates.append(date_obj)

            # Update receiver stats
            receivers[receiver]['count'] += 1
            if date_obj:
                receivers[receiver]['dates'].append(date_obj)

    # Calculate date ranges
    def get_date_range(dates):
        if not dates:
            return None, None
        return min(dates).strftime("%Y-%m-%d-%H-%M"), max(dates).strftime("%Y-%m-%d-%H-%M")

    # Build sender summary
    sender_summary = []
    for name, data in sorted(senders.items(), key=lambda x: x[1]['count'], reverse=True):
        min_date, max_date = get_date_range(data['dates'])
        sender_summary.append({
            'name': name,
            'count': data['count'],
            'date_range': {'min': min_date, 'max': max_date} if min_date else None
        })

    # Build receiver summary
    receiver_summary = []
    for name, data in sorted(receivers.items(), key=lambda x: x[1]['count'], reverse=True):
        min_date, max_date = get_date_range(data['dates'])
        receiver_summary.append({
            'name': name,
            'count': data['count'],
            'date_range': {'min': min_date, 'max': max_date} if min_date else None
        })

    # Overall date range
    overall_min, overall_max = get_date_range(all_dates)

    # Build final analysis
    analysis = {
        'stats': {
            'total_files': total_files,
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'not_email_files': not_email_count,
            'total_emails': total_emails,
            'unique_senders': len(senders),
            'unique_receivers': len(receivers)
        },
        'overall_date_range': {
            'min': overall_min,
            'max': overall_max
        },
        'senders': sender_summary,
        'receivers': receiver_summary,
        'errors': files_with_errors[:50]  # Limit errors to first 50
    }

    # Write output
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"\nAnalysis complete!")
    print(f"Total files: {total_files}")
    print(f"Valid files: {valid_files}")
    print(f"Invalid files: {invalid_files}")
    print(f"Not email files: {not_email_count}")
    print(f"Total emails: {total_emails}")
    print(f"Unique senders: {len(senders)}")
    print(f"Unique receivers: {len(receivers)}")
    print(f"Date range: {overall_min} to {overall_max}")
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
