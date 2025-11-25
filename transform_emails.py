import os
import json
from collections import defaultdict
from datetime import datetime

# Jeffrey Epstein identifiers
JE_EMAILS = {
    'jeevacation@gmail.com',
    'jeeitunes@gmail.com',
    'e:jeeitunes@gmail.com'
}

JE_NAMES = {
    'jeffrey epstein',
    'jeffrey e.',
    'jeffrey e',
    'je'
}

# Name mapping for consolidation
NAME_MAPPING = {
  "Al Seckel": ["al seckel"],
  "Alan Dershowitz": ["Alan M. Dershowitz"],
  "Alireza Ittihadieh": ["Alireza ITTIHADIEH"],
  "Anas Alrasheed": ["anasalrasheed"],
  "Anil Ambani": ["anil.ambani", "Anil.Ambani"],
  "Barbro C. Ehnbom": ["Barbro C Ehnbo", "Barbro C Ehnbom", "BARBRO EHNBOM", "Barbro Ehnbom"],
  "Barry J. Cohen": ["Barry"],
  "Boris Nikolic": ["boris", "Boris Nikolic (bgC3)"],
  "Brad S Karp": ["Karp, Brad S"],
  "Darren K. Indyke": ["Darren Indyke"],
  "David Schoen": ["David I. Schoen", "DAVID SCHOEN"],
  "Deepak Chopra": ["drsra"],
  "Ehud Barak": ["ehbarak", "ehud barak"],
  "Faith Kates": ["Faith Kate"],
  "Gerald G. Barton": ["Gerald Barton"],
  "Ghislaine Maxwell": ["G Maxwell", "GMAX", "Gmax", "gmax"],
  "Gwendolyn Beck": ["Gwendolyn"],
  "Alan S. Halperin": ["Halperin, Alan S", "Dlugash, Alan"],
  "Heather Mann": ["Heather"],
  "Jack Lang": ["Jack LANG"],
  "Jean Huguen": ["jean", "jean.huguen"],
  "Jeffrey Epstein": ["Jeffrey", "jeffrey E.", "jeffrey epstein", "Jeffrey epstein", "jeffrey Epstein", "Jeff", "jeffreyepsteinorg@gmail.com"],
  "Jeannine Jeskewitz": ["Jeskewitz, Jeannine"],
  "Joichi Ito": ["Joi Ito", "Joi"],
  "Jonathan Farkas": ["JONATHAN FARKAS"],
  "Joscha Bach": ["Joscha"],
  "Kathy Ruemmler": ["Kathy Ruemmle", "Kathryn H. Ruemmler", "Kathy"],
  "Ken Starr": ["ken", "Ken", "Starr, Ken"],
  "Kirsty MacKenzie": ["Kirsty Mackenzie"],
  "Landon Thomas Jr.": ["Landon Thomas, Jr.", "Landon Thomas", "Thomas Jr., Landon", "Thomas Jr.", "Landon"],
  "Larry Summers": ["Lawrence H. Summers", "Lawrence Summers", "LHS", "Larry"],
  "Larry Visoski": ["Lawrance Visoski"],
  "Lawrence M. Krauss": ["Lawrence Krauss"],
  "Leon Black": ["leon black", "Leon"],
  "Leslie Wexner": ["Les Wexner"],
  "Lilly Ann Sanchez": ["Lilly Sanchez"],
  "Linda Pinto": ["Linda PINTO"],
  "Mark L. Epstein": ["Based on the email thread, the recipient is Mark L. Epstein."],
  "Martin G. Weinberg": ["Martin Weinberg", "Martin weinberg", "Martin Weinberg Esq"],
  "Masha Drokova": ["masha"],
  "Melanie Walker": ["Melanie Walker, MD", "Melanie"],
  "Michael Miller": ["Miller, Michael"],
  "Miroslav Lajčák": ["Lajcak Miroslav/MINISTER/MZV"],
  "Mohamed Waheed Hassan": ["Mohamed Waheed", "Mohammed Waheed Hassan", "Waheed"],
  "Nadia Marcinkova": ["Nadia"],
  "Nav Gupta": ["Nav"],
  "Neal Kassell": ["Neal"],
  "Nicholas Ribis": ["nicholas.ribis"],
  "Noam Chomsky": ["Noam"],
  "OLIVIER COLOM": ["COLOM, Olivier"],
  "Paul Morris": ["Morris, Paul V"],
  "Peggy Siegal": ["Peggy"],
  "Peter Mandelson": ["PETER MANDELSON", "Peter Mandelson BT", "Peter Mandelson, BT"],
  "Redacted": ["[Redacted]", "[REDACTED]", "REDACTED", "redacted"],
  "Reid Hoffman": ["Reid"],
  "Renata Bolotova": ["Renata B"],
  "Robert Lawrence Kuhn": ["Robert Kuhn", "Robert L. Kuhn"],
  "Soon-Yi Previn": ["Soon-Yi", "soon yi previn", "Soon-Yi Previn or Woody Allen"],
  "Stephen Hanson": ["Steve Hanson"],
  "Caroline Lang": ["Lang, Caroline"],
  "Amanda Ens": ["Ens, Amanda"],
  "Tom Pritzker": ["Pritzker, Tom"],
  "Reid Weingarten": ["Weingarten, Reid", "Weingarten"],
  "Martin A. Nowak": ["Nowak, Martin A.", "Martin Nowak"],
  "David Haig": ["Haig, David"],
  "Alex Yablon": ["Yablon, Alex"],
  "Ed Boyden": ["Ed"],
  "Flipboard": ["Flipboard 10 for Today", "Flipboard Photo Desk", "Flipboard Week in Review", "Flipboard, Inc."]
}

# Build reverse lookup
NAME_REVERSE_LOOKUP = {}
for canonical, aliases in NAME_MAPPING.items():
    for alias in aliases:
        NAME_REVERSE_LOOKUP[alias.lower()] = canonical

def normalize_name(name):
    """Normalize a name using the mapping."""
    if not name:
        return name
    name_lower = name.lower().strip()
    return NAME_REVERSE_LOOKUP.get(name_lower, name)

def is_jeffrey_epstein(name, email):
    """Check if the sender/receiver is Jeffrey Epstein."""
    if email:
        if isinstance(email, (list, dict)):
            email = str(email)
        email_lower = email.lower().strip()
        if email_lower in JE_EMAILS:
            return True
    if name:
        if isinstance(name, (list, dict)):
            name = str(name)
        name_lower = name.lower().strip()
        if name_lower in JE_NAMES:
            return True
        if 'epstein' in name_lower and 'jeffrey' in name_lower:
            return True
    return False

def parse_date_to_timestamp(date_str):
    """Parse date string in yyyy-mm-dd-hh-mm format to Unix timestamp."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d-%H-%M")
        return int(dt.timestamp())
    except (ValueError, TypeError):
        return None

def get_name_key(name, email):
    """Create a consistent key for the other party."""
    if name:
        # Clean up name
        name = str(name).strip()
        if isinstance(name, dict):
            name = str(name)
        return name
    if email:
        return email
    return 'Unknown'

def normalize_to_list(value):
    """Convert value to a list, handling strings that look like lists."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # Check if it's a string representation of a list
        stripped = value.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            try:
                import ast
                parsed = ast.literal_eval(stripped)
                if isinstance(parsed, list):
                    return parsed
            except:
                pass
        return [value] if value else []
    return [value]

def extract_name_from_value(value):
    """Extract a clean name from various value types including dicts."""
    if value is None:
        return None
    if isinstance(value, dict):
        # Try to get name from dict
        return value.get('name') or value.get('email') or str(value)
    if isinstance(value, str):
        # Check if it's a string representation of a dict
        stripped = value.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                import ast
                parsed = ast.literal_eval(stripped)
                if isinstance(parsed, dict):
                    return parsed.get('name') or parsed.get('email') or str(parsed)
            except:
                pass
        return value
    return str(value)

def get_other_parties(sender_names, sender_emails, receiver_names, receiver_emails, je_is_sender):
    """Get list of other party identifiers (name or email)."""
    parties = []

    if je_is_sender:
        # JE is sender, so receivers are the other parties
        names = normalize_to_list(receiver_names)
        emails = normalize_to_list(receiver_emails)
    else:
        # JE is receiver, so senders are the other parties
        names = normalize_to_list(sender_names)
        emails = normalize_to_list(sender_emails)

    # Match names with emails if possible
    if names:
        for i, name in enumerate(names):
            if name:
                extracted = extract_name_from_value(name)
                if extracted:
                    parties.append(str(extracted).strip())
            elif i < len(emails) and emails[i]:
                extracted = extract_name_from_value(emails[i])
                if extracted:
                    parties.append(str(extracted).strip())
    elif emails:
        for email in emails:
            if email:
                extracted = extract_name_from_value(email)
                if extracted:
                    parties.append(str(extracted).strip())

    if not parties:
        parties = ['Unknown']

    return parties

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, 'data', 'email_extracted')
    output_file = os.path.join(script_dir, 'data', 'all_emails.json')

    if not os.path.exists(input_dir):
        print(f"Error: Directory not found: {input_dir}")
        return

    # Dictionary to hold emails by other party
    emails_by_person = defaultdict(list)
    confidentiality_emails = []

    # Stats
    total_files = 0
    total_emails = 0
    je_emails = 0
    skipped = 0

    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    total_files = len(json_files)

    print(f"Processing {total_files} files from {input_dir}")

    for filename in json_files:
        filepath = os.path.join(input_dir, filename)

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            continue

        parsed = data.get('parsed_response')

        if not parsed:
            continue

        # Check for notEmail marker
        if isinstance(parsed, dict) and parsed.get('notEmail'):
            continue

        # Ensure it's a list
        if isinstance(parsed, dict):
            parsed = [parsed]

        if not isinstance(parsed, list):
            continue

        for email in parsed:
            if not isinstance(email, dict):
                continue

            total_emails += 1

            # Get sender info (keep original values for checking)
            sender_name_raw = email.get('sender') or email.get('senderGuess') or ''
            sender_email_raw = email.get('senderEmail') or ''

            # Get receiver info (keep original values for checking)
            receiver_name_raw = email.get('receiver') or email.get('receiverGuess') or ''
            receiver_email_raw = email.get('receiverEmail') or ''

            # Normalize to lists for checking
            sender_names = normalize_to_list(sender_name_raw)
            sender_emails = normalize_to_list(sender_email_raw)
            receiver_names = normalize_to_list(receiver_name_raw)
            receiver_emails = normalize_to_list(receiver_email_raw)

            # Check if JE is involved
            je_is_sender = any(is_jeffrey_epstein(n, e) for n, e in zip(sender_names + [''], sender_emails + ['']))
            je_is_receiver = any(is_jeffrey_epstein(n, e) for n, e in zip(receiver_names + [''], receiver_emails + ['']))

            # Also check single values
            if not je_is_sender:
                je_is_sender = is_jeffrey_epstein(sender_name_raw if isinstance(sender_name_raw, str) else '',
                                                   sender_email_raw if isinstance(sender_email_raw, str) else '')
            if not je_is_receiver:
                je_is_receiver = is_jeffrey_epstein(receiver_name_raw if isinstance(receiver_name_raw, str) else '',
                                                    receiver_email_raw if isinstance(receiver_email_raw, str) else '')

            if not (je_is_sender or je_is_receiver):
                skipped += 1
                continue

            je_emails += 1

            # Get all other parties
            other_parties = get_other_parties(sender_name_raw, sender_email_raw,
                                               receiver_name_raw, receiver_email_raw,
                                               je_is_sender)

            # Parse date to timestamp
            date_str = email.get('date')
            timestamp = parse_date_to_timestamp(date_str)

            # Build email record
            email_record = {
                'sender': sender_name_raw,
                'senderEmail': sender_email_raw if sender_email_raw else None,
                'receiver': receiver_name_raw,
                'receiverEmail': receiver_email_raw if receiver_email_raw else None,
                'date': date_str,
                'timestamp': timestamp,
                'subject': email.get('subject'),
                'summary': email.get('summary'),
                'messageType': email.get('messageType'),
                'source_file': filename
            }

            # Add optional fields if present
            if email.get('senderGuess'):
                email_record['senderGuess'] = email.get('senderGuess')
            if email.get('receiverGuess'):
                email_record['receiverGuess'] = email.get('receiverGuess')
            if email.get('senderRelationship'):
                email_record['senderRelationship'] = email.get('senderRelationship')
            if email.get('receiverRelationship'):
                email_record['receiverRelationship'] = email.get('receiverRelationship')

            # Add email to each other party's list
            for other_name in other_parties:
                # Normalize the name using mapping
                normalized_name = normalize_name(other_name)

                # Check if going to Unknown and has confidentiality in summary
                if normalized_name == 'Unknown':
                    summary = email.get('summary', '') or ''
                    if isinstance(summary, str) and 'confidentiality' in summary.lower():
                        confidentiality_emails.append(email_record.copy())
                        continue
                emails_by_person[normalized_name].append(email_record.copy())

    # Sort emails for each person chronologically
    for person in emails_by_person:
        emails_by_person[person].sort(key=lambda x: x['timestamp'] if x['timestamp'] else 0)

    # Build final output structure
    output = {}
    for person in sorted(emails_by_person.keys(), key=lambda x: x.lower()):
        output[person] = {
            'count': len(emails_by_person[person]),
            'emails': emails_by_person[person]
        }

    # Write output
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    # Create summary file with just names and counts (sorted alphabetically)
    summary_file = os.path.join(script_dir, 'data', 'contacts_summary.json')
    summary = {}
    for person in sorted(output.keys(), key=lambda x: x.lower()):
        summary[person] = output[person]['count']

    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Write confidentiality emails
    confidentiality_file = os.path.join(script_dir, 'data', 'confidentiality_email_blank_email_check.json')
    with open(confidentiality_file, 'w') as f:
        json.dump(confidentiality_emails, f, indent=2)

    print(f"\nTransformation complete!")
    print(f"Total files: {total_files}")
    print(f"Total emails: {total_emails}")
    print(f"Emails involving JE: {je_emails}")
    print(f"Skipped (not JE): {skipped}")
    print(f"Unique contacts: {len(output)}")
    print(f"Confidentiality emails: {len(confidentiality_emails)}")
    print(f"\nResults saved to: {output_file}")
    print(f"Summary saved to: {summary_file}")
    print(f"Confidentiality emails saved to: {confidentiality_file}")

if __name__ == "__main__":
    main()
