import re


def clean_physical_exam(text: str):
    """Clean physical examination text by removing discharge information and duplicate sections.

    Args:
        text: Raw physical examination text from clinical notes

    Returns:
        Cleaned physical examination text with discharge info and duplicates removed
    """
    # Remove text after discharge-related phrases
    text = re.sub(
        r"\b(?:on|upon|at|day\s+of)\s+discharge\b.*",
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

    # Handle standalone all-caps "DISCHARGE"
    text = re.sub(r"\bDISCHARGE\b.*", "", text, flags=re.DOTALL).strip()

    # Then handle "discharge" with colon, colon optional for "discharge exam"/"discharge pe"
    discharge_pattern = re.compile(
        r"\b(?:discharge\s*:|discharge\s+exam|discharge\s+pe|discharge\s+labs|D/C\s*:|DISPO).*",
        re.IGNORECASE | re.DOTALL,
    )
    text = discharge_pattern.sub("", text).strip()

    # Remove labs, imaging, and diagnostics sections (but keep ADMISSION LABS)
    text = re.sub(
        r"(?<!ADMISSION\s)\b(?:Labs|Laboratory|Imaging|Diagnostics)\s*:.*",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

    # Pattern matches major section headers for additional physical exam sections:
    physical_exam_pattern = re.compile(
        r"(?:^|\n.{0,15})(?:PHYSICAL\s+EXAM:?|TRANSFER\s+EXAM:|EXAMINATION:|EXAM:|P/E:|PE:|VS:|Vital\s+signs:|AMA:)",
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

    return text
