import streamlit as st
import pandas as pd
import difflib
import re
from pathlib import Path

# Directories
NEW_DIR = "/home/kiki/MIMIC-Clinical-Decision-Making-Dataset"
ORIGINAL_DIR = "/srv/mimic/cdm_v1"

# File options
FILE_OPTIONS = {
    "History of Present Illness": "history_of_present_illness.csv",
    "Physical Examination": "physical_examination.csv"
}


def load_csv_files(file_name):
    """Load CSV files from both directories."""
    new_path = Path(NEW_DIR) / file_name
    original_path = Path(ORIGINAL_DIR) / file_name

    try:
        new_df = pd.read_csv(new_path)
        original_df = pd.read_csv(original_path)
        return new_df, original_df
    except FileNotFoundError as e:
        st.error(f"Error loading files: {e}")
        return None, None


def normalize_pmh_header(text):
    """Normalize 'Past Medical History' header formatting for consistent comparison."""
    # Replace various formats of "Past Medical History:" with consistent format
    # Handles variations like:
    # - "\nPast Medical History:\n"
    # - "\n\nPast Medical History:\n"
    # - "\nPast Medical History: "
    # - " Past Medical History:\n"
    # etc.
    pattern = r'\s*Past Medical History:\s*'
    normalized = re.sub(pattern, '\n\nPast Medical History:\n', text)
    return normalized


def calculate_overlap_score(text1, text2, normalize_pmh=False):
    """Calculate similarity score between two texts."""
    if pd.isna(text1) and pd.isna(text2):
        return 1.0
    if pd.isna(text1) or pd.isna(text2):
        return 0.0

    text1 = str(text1)
    text2 = str(text2)

    # Normalize Past Medical History header if requested
    if normalize_pmh:
        text1 = normalize_pmh_header(text1)
        text2 = normalize_pmh_header(text2)

    matcher = difflib.SequenceMatcher(None, text1, text2)
    return matcher.ratio()


def highlight_diff(text1, text2, normalize_pmh=False):
    """Generate HTML with highlighted differences between two texts."""
    if pd.isna(text1):
        text1 = ""
    if pd.isna(text2):
        text2 = ""

    text1 = str(text1)
    text2 = str(text2)

    # Normalize Past Medical History header if requested
    if normalize_pmh:
        text1 = normalize_pmh_header(text1)
        text2 = normalize_pmh_header(text2)

    matcher = difflib.SequenceMatcher(None, text1, text2)

    def generate_html(text, opcodes, is_first):
        html = []
        for tag, i1, i2, j1, j2 in opcodes:
            if is_first:
                chunk = text[i1:i2]
                idx_start, idx_end = i1, i2
            else:
                chunk = text[j1:j2]
                idx_start, idx_end = j1, j2

            if tag == 'equal':
                html.append(f'<span class="match-text">{chunk}</span>')
            elif tag == 'replace':
                if is_first:
                    html.append(f'<span class="removed-text">{chunk}</span>')
                else:
                    html.append(f'<span class="added-text">{chunk}</span>')
            elif tag == 'delete':
                if is_first:
                    html.append(f'<span class="removed-text">{chunk}</span>')
            elif tag == 'insert':
                if not is_first:
                    html.append(f'<span class="added-text">{chunk}</span>')

        return ''.join(html)

    opcodes = matcher.get_opcodes()
    html1 = generate_html(text1, opcodes, True)
    html2 = generate_html(text2, opcodes, False)

    return html1, html2


def compare_dataframes(new_df, original_df, normalize_pmh=False):
    """Compare dataframes and return comparison results."""
    # Assuming first column is hadm_id and second column is text
    hadm_id_col = new_df.columns[0]
    text_col = new_df.columns[1]

    # Merge on hadm_id
    merged = pd.merge(
        new_df[[hadm_id_col, text_col]],
        original_df[[hadm_id_col, text_col]],
        on=hadm_id_col,
        how='outer',
        suffixes=('_new', '_original')
    )

    # Calculate overlap scores
    merged['overlap_score'] = merged.apply(
        lambda row: calculate_overlap_score(
            row[f'{text_col}_new'],
            row[f'{text_col}_original'],
            normalize_pmh=normalize_pmh
        ),
        axis=1
    )

    # Add difference flag
    merged['has_difference'] = merged['overlap_score'] < 1.0

    return merged, hadm_id_col, text_col


def main():
    st.set_page_config(page_title="CSV Text Comparison Tool", layout="wide")

    # Add custom CSS for automatic dark mode
    st.markdown("""
    <style>
    /* Light mode colors (default) */
    :root {
        --bg-color: #f9f9f9;
        --border-color: #ddd;
        --text-color: #000000;
        --match-color: #90EE90;
        --removed-color: #FFB6C6;
        --added-color: #87CEEB;
    }

    /* Dark mode colors (automatic) */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-color: #1e1e1e;
            --border-color: #444;
            --text-color: #e0e0e0;
            --match-color: #2d5016;
            --removed-color: #5c1a1a;
            --added-color: #1a3a52;
        }
    }

    .comparison-box {
        border: 2px solid var(--border-color);
        padding: 10px;
        border-radius: 5px;
        background-color: var(--bg-color);
        max-height: 600px;
        overflow-y: auto;
        color: var(--text-color);
    }

    .match-text {
        background-color: var(--match-color);
        padding: 0 2px;
    }

    .removed-text {
        background-color: var(--removed-color);
        padding: 0 2px;
    }

    .added-text {
        background-color: var(--added-color);
        padding: 0 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("CSV Text Comparison Tool")
    st.markdown("Compare text differences between CSV files from two directories")

    # File selection dropdown
    selected_file_type = st.selectbox(
        "Select file type to compare:",
        list(FILE_OPTIONS.keys())
    )

    file_name = FILE_OPTIONS[selected_file_type]

    # Determine if we should normalize PMH header (only for HPI files)
    normalize_pmh = (selected_file_type == "History of Present Illness")

    # Load data
    new_df, original_df = load_csv_files(file_name)

    if new_df is None or original_df is None:
        st.stop()

    # Compare dataframes
    comparison_df, hadm_id_col, text_col = compare_dataframes(new_df, original_df, normalize_pmh=normalize_pmh)

    # Filter controls
    st.sidebar.header("Filter Options")

    # Overlap score threshold slider
    overlap_threshold = st.sidebar.slider(
        "Show cases with overlap score ≤",
        min_value=0.0,
        max_value=1.0,
        value=1.0,
        step=0.01,
        help="Filter cases by maximum overlap score. 1.0 shows all cases, lower values show only cases with more differences."
    )

    # Filter data based on overlap threshold
    filtered_df = comparison_df[comparison_df['overlap_score'] <= overlap_threshold].reset_index(drop=True)

    # Display statistics
    st.sidebar.header("Statistics")
    st.sidebar.metric("Total cases", len(comparison_df))
    st.sidebar.metric("Cases with differences", len(comparison_df[comparison_df['has_difference']]))
    st.sidebar.metric("Exact matches", len(comparison_df[~comparison_df['has_difference']]))
    st.sidebar.metric("Filtered cases shown", len(filtered_df))

    if len(filtered_df) == 0:
        st.warning("No cases found matching the filter criteria.")
        st.stop()

    # Navigation
    st.sidebar.header("Navigation")

    # Initialize session state for current index
    if 'current_idx' not in st.session_state:
        st.session_state.current_idx = 0

    # Ensure current index is within bounds
    if st.session_state.current_idx >= len(filtered_df):
        st.session_state.current_idx = 0

    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        if st.button("⬅️ Previous"):
            st.session_state.current_idx = (st.session_state.current_idx - 1) % len(filtered_df)

    with col2:
        st.write(f"{st.session_state.current_idx + 1}/{len(filtered_df)}")

    with col3:
        if st.button("Next ➡️"):
            st.session_state.current_idx = (st.session_state.current_idx + 1) % len(filtered_df)

    # Case selector
    selected_case = st.sidebar.selectbox(
        "Jump to case:",
        range(len(filtered_df)),
        index=st.session_state.current_idx,
        format_func=lambda x: f"Case {x+1} - {filtered_df.iloc[x][hadm_id_col]}"
    )
    st.session_state.current_idx = selected_case

    # Display current comparison
    current_row = filtered_df.iloc[st.session_state.current_idx]

    st.header(f"Case: {current_row[hadm_id_col]}")

    # Display overlap score
    overlap_score = current_row['overlap_score']
    score_color = "green" if overlap_score == 1.0 else ("orange" if overlap_score > 0.5 else "red")
    st.markdown(
        f"**Overlap Score:** <span style='color: {score_color}; font-size: 24px; font-weight: bold;'>{overlap_score:.2%}</span>",
        unsafe_allow_html=True
    )

    # Get texts
    text_new = current_row[f'{text_col}_new']
    text_original = current_row[f'{text_col}_original']

    # Generate highlighted HTML
    html_new, html_original = highlight_diff(text_new, text_original, normalize_pmh=normalize_pmh)

    # Display side by side
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("New Version")
        st.markdown(f"📁 `{NEW_DIR}`")
        st.markdown(
            f'<div class="comparison-box">{html_new}</div>',
            unsafe_allow_html=True
        )

    with col_right:
        st.subheader("Original Version")
        st.markdown(f"📁 `{ORIGINAL_DIR}`")
        st.markdown(
            f'<div class="comparison-box">{html_original}</div>',
            unsafe_allow_html=True
        )

    # Legend
    st.markdown("---")
    st.markdown("**Legend:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<span class="match-text" style="padding: 5px;">Matching text</span>', unsafe_allow_html=True)
    with col2:
        st.markdown('<span class="removed-text" style="padding: 5px;">Removed/Changed (New)</span>', unsafe_allow_html=True)
    with col3:
        st.markdown('<span class="added-text" style="padding: 5px;">Added/Changed (Original)</span>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
