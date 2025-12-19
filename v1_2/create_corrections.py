import sys
from pathlib import Path
import pandas as pd
from tqdm import tqdm

from section_split import initial_formatting, extract_section_content
from section_cleanup import clean_physical_exam


def main():
    base_mimic_note = Path("/srv/mimic/mimiciv/mimic-iv-note/2.2/note")
    base_new = ""

    # Load hospital admission IDs from file
    hadm_ids_file = Path("v1_2/hadm_ids.txt")
    hadm_ids = []

    with open(hadm_ids_file, "r") as f:
        for line in f:
            hadm_id = int(line)
            hadm_ids.append(hadm_id)

    print(f"Loaded {len(hadm_ids)} hospital admission IDs")

    discharge_reports = pd.read_csv(base_mimic_note / "discharge.csv.gz")
    discharge_reports = discharge_reports[discharge_reports["hadm_id"].isin(hadm_ids)]
    discharge_reports = discharge_reports[["hadm_id", "text"]]
    print(f"Loaded {len(discharge_reports)} discharge reports")

    hpi_records = []
    pe_records = []

    for hadm_id, text in tqdm(
        discharge_reports.values,
        desc="Processing reports",
        total=len(discharge_reports),
    ):
        text = initial_formatting(text)
        sections = extract_section_content(text)

        required_sections = [
            "History of Present Illness",
            "Past Medical History",
            "Physical Exam",
        ]
        if not all(section in sections for section in required_sections):
            raise ValueError(f"{hadm_id} has a missing section...")

        history = (
            sections.get("History of Present Illness").replace("\n", " ").strip()
            + "\n\nPast Medical History:\n"
            + sections.get("Past Medical History").replace("\n", " ").strip()
        )
        pe = sections.get("Physical Exam")
        pe = clean_physical_exam(pe)

        pe_records.append({"hadm_id": hadm_id, "pe": pe.replace("\n", " ")})
        hpi_records.append({"hadm_id": hadm_id, "hpi": history})

    # Create DataFrames and save to CSV files
    hpi_df = pd.DataFrame(hpi_records)
    hpi_path = Path(base_new) / "history_of_present_illness.csv"
    hpi_df.to_csv(hpi_path, index=False)
    print(f"Saved {len(hpi_df)} records to {hpi_path}")

    pe_df = pd.DataFrame(pe_records)
    pe_path = Path(base_new) / "physical_examination.csv"
    pe_df.to_csv(pe_path, index=False)
    print(f"Saved {len(pe_df)} records to {pe_path}")


if __name__ == "__main__":
    main()
