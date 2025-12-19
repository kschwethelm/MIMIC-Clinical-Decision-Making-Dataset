import re

import spacy

nlp = spacy.load("en_core_sci_lg")

###
# Collection of functions for natural language processing utility
###


# Abbreviations (i.e. short names) are often given in parantheses after long name. Extract both short and long name
def extract_short_and_long_name(test: str):
    match = re.search("\((.*)\)", test)
    if match:
        short_name = match.group(1).strip()
        long_name = test.replace(match.group(0), "").strip()
        long_name = long_name.replace("  ", " ")
        long_name = long_name.replace(" ,", ",")
        return short_name, long_name
    else:
        return test, test


# Text parses differently if done line by line and as a whole. This function extracts the first diagnosis from the text by checking both
def extract_primary_diagnosis(text):
    earliest_keyword_index = len(text)

    # Do parsing of entire text and check for earliest possible diagnosis
    doc = nlp(text)
    diag = check_ents_for_diagnosis_noun_chunks(doc)
    if diag:
        earliest_keyword_index = min(earliest_keyword_index, text.find(diag))
    diag = check_ents_for_diagnosis_entities(doc)
    if diag:
        earliest_keyword_index = min(earliest_keyword_index, text.find(diag))

    # Do parsing of each line and check for earliest possible diagnosis
    for line in text.split("\n"):
        doc = nlp(line)
        diag = check_ents_for_diagnosis_noun_chunks(doc)
        if diag:
            earliest_keyword_index = min(earliest_keyword_index, text.find(diag))
            break
        diag = check_ents_for_diagnosis_entities(doc)
        if diag:
            earliest_keyword_index = min(earliest_keyword_index, text.find(diag))
            break

    # Extract line with diagnosis and make sure we only return the first diagnosis if multiple given on one line
    prim_diag = text[earliest_keyword_index:]
    prim_diag = prim_diag.split("\n")[0]
    prim_diag = prim_diag.split(",")[0]
    # We can split on 'and' here because we are just looking for the general pathology, not a specific subtype i.e. "diverticulitis with perforation and stricture and abscess"
    prim_diag = re.split(r"\band\b", prim_diag)[0]
    prim_diag = re.split(r"\bor\b", prim_diag)[0]
    prim_diag = re.split(r"\bvs[.]?\b", prim_diag)[0]
    return prim_diag.strip()


def check_ents_for_diagnosis_entities(doc):
    for e in doc.ents:
        d = e.text.lower()
        if (
            "primary" not in d
            and "diagnosis" not in d
            and "diagnoses" not in d
            and "dx" not in d
            and d != "active"
            and d != "acute"
        ):
            return e.text
    return None


def check_ents_for_diagnosis_noun_chunks(doc):
    for chunk in doc.noun_chunks:
        d = chunk.text.lower()
        # Remove initial characters to first letter
        d = re.sub(r"^[^a-zA-Z]+", "", d)
        if (
            "primary" not in d
            and "diagnosis" not in d
            and "diagnoses" not in d
            and "dx" not in d
            and d != "active"
            and d != "acute"
        ):
            return d.strip()
    return None
