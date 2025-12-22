# Dataset Corrections (v1.2)

## Overview

This document describes corrections made to the free text sections of the MIMIC Clinical Decision Making (MIMIC-CDM) Dataset, specifically for the History of Present Illness and Physical Examination fields. These corrections address extraction errors, formatting issues, and cases with ambiguous or incomplete information.

The corrected data is available in
- `history_of_present_illness.csv`
- `physical_examination.csv`

after running [create_corrections.py](create_corrections.py).

## Main Changes

### 1. Removed Cases with Limited/Ambiguous Information

Two cases were excluded due to insufficient or ambiguous clinical information:
- **24004035**: No information in patient history and incorrect information in physical exam section
- **23169808**: Ambiguous clinical data with additional history in physical exam section

### 2. History of Present Illness Corrections

**Formatting fixes:**
- Standardized concatenation of past medical history (appended to HPI with header `\n\nPast Medical History:\n`)
- Removed irrelevant section headers
- Fixed duplicate headers
- Examples: 20694289, 20760817

**Content corrections:**
- Removed physical examination text that was incorrectly included in history section
- Affected cases: 23305064, 24775589, 29255851

### 3. Physical Examination Corrections

**Wrong exam type extracted:**
- Cases where discharge physical exam was extracted instead of admission exam: 23305064, 24775589, 29255851

**Incomplete extractions:**
- Multiple cases with incomplete physical exams due to overly aggressive "discharge" keyword matching
- Examples: 20521700, 20639685, 20861414

**Multiple/duplicate exams:**
- Cases containing multiple physical exams, e.g., 21902794, 26322243, 26765568
- Complex multi-exam cases (redacted exams, misspelled headers, etc.), e.g., 23627544, 24819782, 22944548

**Out-of-scope content:**
- Cases containing labs and imaging data (should not be in physical exam), e.g., 21948836, 24188879, 25033877
- Cases with labs + diagnostics: 24797227
- Cases with labs + family history: 26339780

**Other issues:**
- Minor formatting issues (unnecessary headers like "Physical Exam" or "PE" in end of text): Many cases including 20007881, 20045412, 20287524, 20117610, and many more
- Removed unnecessary delimiters at text boundaries (e.g., sequences of "=" or "\_" characters, "\_\_\_:" patterns)

### 4. General Formatting Cleanup
- Removed html tags and replaced unicode, and hex characters, e.g., 21392013, 21966843, 23008526
- Removed lines with only dots
- Improved section extraction by first splitting discharge summary into all available sections and then selecting the needed ones