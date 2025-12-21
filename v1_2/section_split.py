"""NOTE: Removed empty sections (by initial_formatting):

--- Removed top part because always redacted ---
# -------------------------
# "Name": ["Name:"],
# "Unit No": ["Unit No:", "Unit ___:", "___ No:"],
# "Admission Date": ["Admission Date:"],
# "Discharge Date": ["Discharge Date:"],
# "Date of Birth": ["Date of Birth:"],
# -------------------------

--- Between Allergies and Chief Complaint ---
# "Attending": ["Attending:"]

--- Between Discharge Disposition and Discharge Diagnosis ---
# "Facility": ["Facility:"]

--- Removed bottom part because always redacted ---
# "Followup Instructions": [
#    "Followup Instructions:",
#    "Follow-up Instructions:",
# ]  # Can also be ___ Instructions:
"""

import re

# Section headers start with a word followed by a colon.
HEADER_REGEX = r"^([^:\n]+):"

DISCHARGE_SECTIONS = {
    "Sex": {"order_id": 0, "synonyms": ["Sex:"], "key": "gender", "length_limit": None},
    "Service": {
        "order_id": 1,
        "synonyms": ["Service:"],
        "key": "service",
        "length_limit": None,
    },
    "Allergies": {
        "order_id": 2,
        "synonyms": ["Allergies:"],
        "key": "allergies",
        "length_limit": None,
    },
    "Chief Complaint": {
        "order_id": 3,
        "synonyms": ["Chief Complaint:", "___ Complaint:"],
        "key": "chief_complaint",
        "length_limit": 200,
    },
    "Major Surgical or Invasive Procedure": {
        "order_id": 4,
        "synonyms": [
            "Major Surgical or Invasive Procedure:",
            "___ Surgical or Invasive Procedure:",
            "Major ___ or Invasive Procedure:",
            "___ or Invasive Procedure:",
            "Major Surgical ___ Invasive Procedure:",
        ],
        "key": "major_procedure",
        "length_limit": 500,
    },
    "History of Present Illness": {
        "order_id": 5,
        "synonyms": [
            "History of Present Illness:",
            "___ of Present Illness:",
            "History ___ Present Illness:",
            "History of Present ___:",
        ],
        "key": "history_of_present_illness",
        "length_limit": 5000,
    },
    "Past Medical History": {
        "order_id": 6,
        "synonyms": [
            "Past Medical History:",
            "Past medical history:",
            "___ Medical History:",
            "Past ___ History:",
        ],
        "key": "past_medical_history",
        "length_limit": 3000,
    },
    "Physical Exam": {
        "order_id": 7,
        "synonyms": [
            "Physical Exam:",
            "PHYSICAL EXAM:",
            "Physical ___:",
            "___ Exam:",
            "Physical ___ Physical Exam:",
            "Physical ___ Exam:",
            "Physical ___ PE:",
        ],
        "key": "physical_examination",
        "length_limit": 3000,
    },
    "Pertinent Results": {
        "order_id": 8,
        "synonyms": ["Pertinent Results:", "Pertinent ___:", "___ Results:"],
        "key": "pertinent_results",
        "length_limit": 9500,
    },
    "Brief Hospital Course": {
        "order_id": 9,
        "synonyms": [
            "Brief Hospital Course:",
            "___ Hospital Course:",
            "Brief ___ Course:",
            "Brief Hospital ___:",
        ],
        "key": "brief_hospital_course",
        "length_limit": 9000,
    },
    "Medications on Admission": {
        "order_id": 10,
        "synonyms": [
            "Medications on Admission:",
            "Medications ___ Admission:",
            "Medications on ___:",
            "___ on Admission:",
        ],
        "key": "medications_on_admission",
        "length_limit": 3000,
    },
    # "Discharge ___:" was labeled manually for most cases
    "Discharge Medications": {
        "order_id": 11,
        "synonyms": ["Discharge Medications:", "___ Medications:"],
        "key": "discharge_medications",
        "length_limit": 3000,
    },
    "Discharge Disposition": {
        "order_id": 12,
        "synonyms": ["Discharge Disposition:", "___ Disposition:"],
        "key": "discharge_disposition",
        "length_limit": None,
    },
    "Discharge Diagnosis": {
        "order_id": 13,
        "synonyms": ["Discharge Diagnosis:", "___ Diagnosis:", "ischarge Diagnosis:"],
        "key": "discharge_diagnosis",
        "length_limit": 600,
    },
    "Discharge Condition": {
        "order_id": 14,
        "synonyms": ["Discharge Condition:", "___ Condition:"],
        "key": "discharge_condition",
        "length_limit": 800,
    },
    "Discharge Instructions": {
        "order_id": 15,
        "synonyms": ["Discharge Instructions:", "___ Instructions:"],
        "key": "discharge_instructions",
        "length_limit": None,
    },
}


def get_section_order():
    return sorted(
        DISCHARGE_SECTIONS.keys(), key=lambda x: DISCHARGE_SECTIONS[x]["order_id"]
    )


def get_section_synonyms():
    return {section: data["synonyms"] for section, data in DISCHARGE_SECTIONS.items()}


def get_section_key_map():
    return {section: data["key"] for section, data in DISCHARGE_SECTIONS.items()}


def get_section_keys():
    """Get the keys for each section."""
    return {data["key"] for _, data in DISCHARGE_SECTIONS.items()}


def get_section_length_limits():
    """Get the length limits for each section."""
    return {
        data["key"]: data["length_limit"]
        for section, data in DISCHARGE_SECTIONS.items()
    }


SECTION_KEYS = get_section_keys()
EXPECTED_SECTION_ORDER = get_section_order()
SECTION_HEADERS = get_section_synonyms()
SECTION_TO_KEY_MAP = get_section_key_map()
KEY_LENGTH_LIMITS = get_section_length_limits()


def remove_sec_facility(disch_smry: str) -> str:
    r"""Remove the Facility section which is always redacted in various formats.

    Handles patterns like:
    - Facility: ___
    - Facility:\n___
    - Facility:\n.___
    - Facility:\n(___)
    - etc.

    Regex Breakdown:
    - ^Facility:\s*          - Start with "Facility:" and optional whitespace
    - (?:\n\s*)?             - Optional newline with optional whitespace (non-capturing)
    - (?:[._:\-()]|___)*     - Any combination of redaction characters (non-capturing)
    - \.?                    - Optional period at the end
    - \s*\n?                 - Optional trailing whitespace and newline
    """

    pattern = r"^Facility:\s*(?:\n\s*)?(?:[._:\-()]|___)*\.?\s*\n?"

    return re.sub(pattern, "", disch_smry, flags=re.MULTILINE)


def remove_sec_attending(disch_smry: str) -> str:
    """Attending section is always redacted, so we remove it.

    Inspection revealed the following:
    - Possible values: "Attending: ___", Attending: ___.", "___", or "___."
    - Last two lines can be detected as either "Chief Complaint:" or "___ Complaint:" follows
    """
    original_text = disch_smry

    # Remove: "Attending: ___." (with period)
    disch_smry = re.sub(r"Attending:\s*___\.\s*\n?", "", disch_smry)
    # Remove: "Attending: ___" (without period)
    disch_smry = re.sub(r"Attending:\s*___\s*\n?", "", disch_smry)

    if disch_smry == original_text:
        # No explicit "Attending:" patterns were found, so look for standalone patterns that appear before Chief Complaint section
        # Pattern 3: "___." immediately before Chief Complaint (with optional whitespace between)
        disch_smry = re.sub(
            r"^___\.\s*$(\s*)(Chief Complaint:|___ Complaint:)",
            r"\1\2",
            disch_smry,
            flags=re.MULTILINE,
        )

        # Pattern 4: "___" immediately before Chief Complaint (with optional whitespace between)
        disch_smry = re.sub(
            r"^___\s*$(\s*)(Chief Complaint:|___ Complaint:)",
            r"\1\2",
            disch_smry,
            flags=re.MULTILINE,
        )

    return disch_smry


def remove_sec_followup(disch_smry: str) -> str:
    """Remove everything after follow-up section as it's always redacted

    Inspection revealed the following:
    - Possible values: "Followup Instructions: ___", "Follow-up Instructions: ___", "___ Instructions: ___", or "___: ___".
    """
    follow_up_match = re.search(
        r"Followup Instructions:|Follow-up Instructions:", disch_smry
    )
    if follow_up_match:
        if len(disch_smry) - follow_up_match.start() > 40:
            raise ValueError(
                f"Implementation error: Follow-up might not be last section in the discharge summary. {disch_smry[follow_up_match.start() :]}"
            )
        disch_smry = disch_smry[: follow_up_match.start()].strip(" \n")
    else:
        # Section might be redacted as "___ Instructions:\n___" or "___:\n___"
        endings = ["___ Instructions:\n___", "___:\n___"]
        for end in endings:
            if disch_smry.endswith(end):
                disch_smry = disch_smry[: -len(end)].strip(" \n")

    return disch_smry


def remove_empty_sections(disch_smry: str) -> str:
    """Removes specific sections from discharge summaries."""
    # Remove everything before "Sex:" as it's redacted
    sex_match = re.search(r"Sex:", disch_smry)
    if sex_match:
        disch_smry = disch_smry[sex_match.start() :].strip(" \n")

    disch_smry = remove_sec_followup(disch_smry)
    disch_smry = remove_sec_attending(disch_smry)
    disch_smry = remove_sec_facility(disch_smry)

    return disch_smry


def remove_duplicate_headers(disch_smry: str) -> str:
    """Remove duplicate headers that appear consecutively in the discharge summary.

    Only considers headers defined in SECTION_HEADERS.
    """
    # Create a set of all possible header variations from SECTION_HEADERS
    all_headers = set()
    for section_variations in SECTION_HEADERS.values():
        all_headers.update(section_variations)

    # Escape special regex characters and create pattern
    escaped_headers = [re.escape(header) for header in all_headers]
    header_pattern = r"^(" + "|".join(escaped_headers) + r")\s*$"

    lines = disch_smry.split("\n")
    cleaned_lines = []
    prev_header = None

    for line in lines:
        stripped_line = line.strip()

        # Check if current line is a header
        header_match = re.match(header_pattern, stripped_line, re.IGNORECASE)

        if header_match:
            current_header = header_match.group(1).lower()

            # Only add if it's different from the previous header
            if current_header != prev_header:
                cleaned_lines.append(line)
                prev_header = current_header
            # If it's a duplicate, skip this line
        else:
            # Not a header line, add it and reset prev_header
            cleaned_lines.append(line)
            prev_header = None

    return "\n".join(cleaned_lines)


def initial_formatting(disch_smry: str) -> str:
    """Initial formatting of the discharge summary text.

    NOTE: If no hadm_id is provided, the redacted header filling will be skipped.
    """
    disch_smry = disch_smry.strip(" \n")
    disch_smry = remove_empty_sections(disch_smry)
    disch_smry = remove_duplicate_headers(disch_smry)

    # Remove leading and trailing whitespace
    disch_smry = disch_smry.strip(" \n")

    return disch_smry


def replace_line_on_nr(text, line_nr: int, old_text: str, new_text: str) -> str:
    """Replace part of a specific line in the text with new text."""
    lines = text.split("\n")
    if 1 <= line_nr <= len(lines):
        if old_text not in lines[line_nr - 1]:
            raise ValueError(
                f"Old text '{old_text}' not found in line {line_nr} of the discharge summary."
            )
        lines[line_nr - 1] = lines[line_nr - 1].replace(old_text, new_text)
    else:
        raise ValueError(
            f"Line number {line_nr} is out of range for the discharge summary."
        )

    return "\n".join(lines)


def fill_redacted_headers(
    disch_smry: str, line_nr: int, redacted_header: str, new_header: str
) -> str:
    """Fill in the redacted header in the discharge summary based on section labels."""
    disch_smry_new = disch_smry

    redacted_header = (
        redacted_header if redacted_header.endswith(":") else redacted_header + ":"
    )
    new_header = new_header if new_header.endswith(":") else new_header + ":"

    disch_smry_new = replace_line_on_nr(
        disch_smry_new, line_nr, redacted_header, new_header
    )

    return disch_smry_new


def map_section_name(header_name: str) -> str:
    """Map the header name to the real section name."""
    header_with_colon = header_name if header_name.endswith(":") else header_name + ":"

    for section_name, variations in SECTION_HEADERS.items():
        if header_with_colon in variations:
            return section_name

    return "Unknown Section"


def extract_header_pos(disch_smry: str) -> list:
    """Extract all section header positions from the discharge summary text.

    Caution: A function in sql_cmds_mimic.py imports this!
    """

    # Get all header matches with positions
    all_matches = [
        (m.group(1).strip(), m.start(), m.end())
        for m in re.finditer(HEADER_REGEX, disch_smry, re.MULTILINE)
    ]

    known_headers = []
    seen_sections = set()

    for i, (header_name, start_pos, end_pos) in enumerate(all_matches):
        if i == 1 and header_name == "___":  # Service special case
            header_name = "Service"

        mapped_header = map_section_name(header_name)
        if mapped_header and mapped_header in SECTION_HEADERS:
            if mapped_header in seen_sections:
                continue  # Skip duplicates

            seen_sections.add(mapped_header)
            known_headers.append((header_name, start_pos, end_pos, mapped_header))

    # Special case: Physical Exam without colon - only if not already found
    if "Physical Exam" not in seen_sections:
        special_pe_regex = r"^Physical ___ Physical Exam$"
        pe_match = re.search(special_pe_regex, disch_smry, re.MULTILINE)
        if pe_match:
            header_name = pe_match.group(0).strip()
            start_pos = pe_match.start()
            end_pos = pe_match.end()
            seen_sections.add("Physical Exam")
            # Insert in correct position based on start_pos
            pe_header = (header_name, start_pos, end_pos, "Physical Exam")
            insert_idx = next(
                (i for i, h in enumerate(known_headers) if h[1] > start_pos),
                len(known_headers),
            )
            known_headers.insert(insert_idx, pe_header)

    return known_headers


def extract_section_content(
    disch_smry: str, expected_section_order: list[str] = EXPECTED_SECTION_ORDER
) -> dict:
    """Extract all sections from the discharge summary text."""

    disch_smry = initial_formatting(disch_smry)
    headers_with_positions = extract_header_pos(disch_smry)

    sections = {}
    for i, (_, _, end_pos, inferred_header) in enumerate(headers_with_positions):
        content_start = end_pos

        # Find start of next header or end of text
        if i < len(headers_with_positions) - 1:
            # Not the last section -> end at start of next header
            next_header_start = headers_with_positions[i + 1][1]
            section_content = disch_smry[content_start:next_header_start]
        else:
            # Last section -> go to end of text
            section_content = disch_smry[content_start:]

        sections[inferred_header] = section_content.strip()

    # Reorder keys to match the defined order and add empty sections if missing
    sections = {sec: sections.get(sec, "") for sec in expected_section_order}

    return sections
