import json
import sys
from difflib import SequenceMatcher


def detect_bumps(old_signatures, new_signatures):
    len_new_signatures = len(new_signatures)

    for old_index in range(0, len(old_signatures)):
        old_signature = old_signatures[old_index]

        old_sig_str = json.dumps(old_signature["Signature"])

        # Start off at the old index since things will most likely be ahead
        upper_limit = ((old_index + 20) if (old_index + 20) < len_new_signatures else len_new_signatures)
        for new_index in range(old_index, upper_limit):
            new_sig = new_signatures[new_index]
            new_sig_str = json.dumps(new_sig["Signature"])

            likeness = SequenceMatcher(None, old_sig_str, new_sig_str).ratio()

            if "Matches" not in new_sig:
                new_sig["Matches"] = list()

            new_sig["Matches"].append({"Likeness": likeness, "Signature": old_signature})

    enums_taken = {}
    bump = 0
    for signature in new_signatures:
        new_id = signature["Id"]
        enum_name = f'Unknown{new_id}'
        if "Matches" in signature:
            signature["Matches"].sort(key=lambda match: (match["Likeness"], match["Signature"]["Id"]), reverse=True)

            old_signature = None
            for old_sig in signature["Matches"]:
                if old_sig["Signature"]["Id"] + bump > new_id:
                    continue
                else:
                    old_signature = old_sig
                    break

            if old_signature:
                likeness = old_signature["Likeness"]
                old_signature = old_signature["Signature"]
                old_id = old_signature["Id"]
                if likeness < 1.0:
                    # Get difference, if too far throw it away
                    if new_id - (old_id + bump) < 3:
                        bump += new_id - old_id - bump
                        enum_name = old_signature["Name"]
                else:
                    if bump > 0:
                        if old_id + bump <= new_id:
                            bump += new_id - old_id - bump
                            enum_name = old_signature["Name"]
                    else:
                        bump += new_id - old_id - bump
                        enum_name = old_signature["Name"]

        if enum_name in enums_taken:
            # Is this signature closer to the previous one?
            prev_sig_id = enums_taken[enum_name]["Id"]
            cur_sig_id = signature["Id"]
            old_id = signature["Matches"][0]["Signature"]["Id"]
            if abs(cur_sig_id-old_id) < abs(prev_sig_id-old_id):
                enums_taken[enum_name] = signature
            else:
                enum_name = f'Unknown{signature["Id"]}'
        else:
            enums_taken[enum_name] = signature
        print(f'{enum_name}={signature["Id"]}')

    return new_signatures


if __name__ == "__main__":
    old_file_path = sys.argv[1]
    new_file_path = sys.argv[2]
    output_file_path = sys.argv[3]

    with open(old_file_path, 'r') as old_fh:
        old_signatures = json.load(old_fh)

    with open(new_file_path, 'r') as old_fh:
        new_signatures = json.load(old_fh)

    matches = detect_bumps(old_signatures, new_signatures)

    with open(output_file_path, 'w') as output_fh:
        json.dump(matches, output_fh, indent=4)
