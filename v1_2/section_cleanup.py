import re


def clean_section(text: str):
    # Remove lines that only contain a "."
    text = "\n".join(line for line in text.split("\n") if line.strip() != ".")
    # Replace unicode "times" symbol
    text = text.replace("×", "x")

    # Remove HTML tags: <h3>, </h3>, <I></I>, and <br>
    text = re.sub(r"</?[hH]3>|</?[iI]>|<br>", "", text, flags=re.IGNORECASE)

    # Replace special characters
    text = text.replace("\x85", "...")
    text = text.replace("\x95", "- ")  # Bullet
    text = text.replace("\x93", '"')  # Left quote
    text = text.replace("\x94", '"')  # Right quote
    text = text.replace("\x96", "-")  # En dash
    text = text.replace("\x97", "-")  # Em dash
    text = text.replace("\x91", "'")  # Single quotes
    text = text.replace("\x92", "'")  # Single quotes

    return text


def clean_physical_exam(text: str):
    """Clean physical examination text by removing discharge information and duplicate sections.

    Args:
        text: Raw physical examination text from clinical notes

    Returns:
        Cleaned physical examination text with discharge info and duplicates removed
    """
    # Redact ground truth procedure
    text = re.sub(r"cholecystostomy", "___", text, flags=re.IGNORECASE)

    # Remove family history section
    # Pattern matches: Family History: ___: none
    family_history_pattern = re.compile(
        r"Family History:\s*_+:\s*none", re.IGNORECASE | re.DOTALL
    )
    fh_match = family_history_pattern.search(text)
    if fh_match:
        text = text[: fh_match.start()].strip()

    # Remove text after discharge-related phrases, but avoid discharge in normal sentences
    # For "on/upon/at/in discharge" or "on/upon/at/in day of discharge" or "day of discharge" (optionally preceded by exam-related headers)
    # Handles common misspellings: Physical, Phsyical, Physcial
    text = re.sub(
        r"(?:\b(?:(?:Physical|Phsyical|Physcial)\s+Exam(?:ination)?|Exam(?:ination)?|PE|Patient\s+examined)\s+)?\b(?:(?:on|upon|at|in)\s+(?:(day|time)\s+of\s+)?|day\s+of\s+)discharge\b.*",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

    # Handle "discharge vs" case
    text = re.sub(
        r"\bdischarge\s+vs\b.*", "", text, flags=re.IGNORECASE | re.DOTALL
    ).strip()

    # Handle "discharge physical" case, also catch typos like "phsycial"
    text = re.sub(
        r"\bdischarge\s+ph[sy]+[sy]?[iyc]+a?l\b.*",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

    # Handle specific discharge-related "Physical:" patterns (including literal "___")
    # Also removes "ACS Discharge Physical Exam ___:"
    text = re.sub(
        r"(?:\b(?:ACS\s+)?(?:Discharge|Transfer|D/C)\s+(?:Physical\s+Exam\s+)?|___\s*)Physical\s*:.*",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

    # Handle "at [prefix]ischarge Exam" pattern (corrupted discharge text)
    text = re.sub(
        r"\bat\s+.{0,3}ischarge\s+exam\b.*", "", text, flags=re.IGNORECASE | re.DOTALL
    ).strip()

    # Handle "Discharge" as a standalone section header (at start of line)
    text = re.sub(
        r"(?:^|\n)\s*Discharge\b.*", "", text, flags=re.IGNORECASE | re.DOTALL
    ).strip()

    # Handle "--DISCHARGE--" pattern
    text = re.sub(r"--DISCHARGE--.*", "", text, flags=re.IGNORECASE | re.DOTALL).strip()

    # Handle standalone all-caps "DISCHARGE"
    text = re.sub(r"\bDISCHARGE\b.*", "", text, flags=re.DOTALL).strip()

    # Then handle "discharge" with colon, colon optional for "discharge exam"/"discharge pe"
    # Also removes "Prior Discharge:" and "On D/C:"
    discharge_pattern = re.compile(
        r"\b(?:Prior\s+discharge\s*:|discharge\s*:|discharge\s+exam|discharge\s+pe|discharge\s+labs|on\s+discharged\s*:|On\s+D/C\s*:|Time\s+of\s+Discharge\s*:|D/C\s*:|DISPO).*",
        re.IGNORECASE | re.DOTALL,
    )
    text = discharge_pattern.sub("", text).strip()

    # Remove labs, imaging, and diagnostics sections (but keep ADMISSION LABS)
    text = re.sub(
        r"(?<!ADMISSION\s)\b(?:Labs and imaging|Labs|Laboratory|Imaging|Diagnostics)\s*:.*",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

    # Pattern matches major section headers for additional physical exam sections:
    # Excludes "Scrotal exam:" and "Pelvic exam:" from being matched
    physical_exam_pattern = re.compile(
        r"(?:^|\n.{0,15})(?:PHYSICAL\s+EXAM:?|TRANSFER\s+EXAM:|EXAMINATION:|(?<!Scrotal\s)(?<!Pelvic\s)EXAM:|P/E:|PE:|VS:|Vital\s+signs:|AMA:)",
        re.IGNORECASE,
    )
    matches = list(physical_exam_pattern.finditer(text))

    # Find any additional physical exam section that appears after the first ~200 characters and remove
    # Trial and error with the comparison script resulted in 200 character cutoff
    # If "Gen:" appears shortly after the header, keep it (it's likely a continuation)
    for match in matches:
        if match.start() > 200:
            # Check if "Gen:" or "HEENT:" appears within 22 (cutoff to avoid false positives but get all false negatives) characters after this header
            # Very specific to catch only the few false positives following this pattern
            remaining_text = text[match.start() :]
            if not re.search(
                r"\b(?:Gen|HEENT)\s*:", remaining_text[:22], re.IGNORECASE
            ):
                text = text[: match.start()].strip()
                break

    # Special case for one case with only AMA exam
    text = text.replace("Prior to leaving AMA...", "").strip()

    # False negatives that miss the above patterns
    # Remove duplicate HEENT sections (keep only first occurrence)
    heent_pattern = re.compile(r"\bHEENT\s*:", re.IGNORECASE)
    heent_matches = list(heent_pattern.finditer(text))
    if len(heent_matches) > 1:
        # Remove everything from the second HEENT onwards
        text = text[: heent_matches[1].start()].strip()

    # Remove duplicate exam starting with vital signs pattern
    # This catches exams that don't have a header but start with temperature later in the text
    duplicate_vitals_pattern = re.compile(
        r"\s+T\d+\.?\d*\s+HR\s+\d+\s+BP\s+\d+/\d+", re.IGNORECASE
    )
    vitals_match = duplicate_vitals_pattern.search(text)
    if vitals_match and vitals_match.start() > 200:
        text = text[: vitals_match.start()].strip()

    # Remove lab values that appear without header
    # Pattern matches common lab value format: WBC followed by number
    lab_values_pattern = re.compile(r"\s+WBC\s+\d+\.?\d*,?\s+", re.IGNORECASE)
    lab_match = lab_values_pattern.search(text)
    if lab_match:
        text = text[: lab_match.start()].strip()

    # Remove section headers that may appear in the text
    text = re.sub(
        r"\b(?:PE|Physical\s+Exam|Physical\s+Examination)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # Remove specific string about 10 system review
    text = text.replace(
        "10 system review negative, except as stated above in HPI.", ""
    ).strip()

    # Replace sequences of more than 4 "x" characters with "___"
    text = re.sub(r"x{5,}", "___", text, flags=re.IGNORECASE).strip()

    # Remove multiple "=", "_" symbols (more than 1) at the beginning and end of text
    text = re.sub(r"^=={2,}", "", text).strip()
    text = re.sub(r"=={2,}$", "", text).strip()
    text = re.sub(r"^__{4,}", "", text).strip()
    text = re.sub(r"__{4,}$", "", text).strip()

    # Remove "___:" pattern from beginning and end
    text = re.sub(r"^___:", "", text).strip()
    text = re.sub(r"___:$", "", text).strip()

    # Remove section headers that may appear in the text
    text = re.sub(
        r"\b(?:PE|Physical\s+Exam|Physical\s+Examination)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    return text
