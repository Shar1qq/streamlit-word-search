import streamlit as st
import time
import re

# Add custom CSS for styling
st.markdown("""
    <style>
    .stButton>button {
        font-size: 18px;
        padding: 8px 20px;
        margin: 5px;
    }
    .result-container {
        border: 1px solid #ddd;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        background-color: #f9f9f9;
        font-size: 16px;
    }
    .highlight {
        color: red;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state variables for navigation
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
    st.session_state.results = []
    st.session_state.matched_word_index = 0
    st.session_state.show_summary = True  # To control summary visibility

# Function to highlight search term in red
def highlight_term(sentence, term):
    highlighted_sentence = re.sub(f"({term})", r"<span class='highlight'>\1</span>", sentence, flags=re.IGNORECASE)
    return highlighted_sentence

# Brute Force Search
def brute_force_search(content, term, whole_word=False, case_sensitive=False):
    results = {}
    for line_num, line in enumerate(content):
        line_to_check = line if case_sensitive else line.lower()
        term_to_check = term if case_sensitive else term.lower()

        if whole_word:
            # Using regex to match whole words
            if re.search(r'\b' + re.escape(term_to_check) + r'\b', line_to_check):
                results[line] = line_num + 1
        else:
            if term_to_check in line_to_check:
                results[line] = line_num + 1
    return results

# KMP Search Algorithm
def kmp_search(content, term, whole_word=False, case_sensitive=False):
    results = {}
    term_len = len(term)

    def build_kmp_table(term):
        table = [0] * term_len
        j = 0
        for i in range(1, term_len):
            while j > 0 and term[i] != term[j]:
                j = table[j - 1]
            if term[i] == term[j]:
                j += 1
                table[i] = j
        return table

    def search_kmp(line, term, table):
        line_len = len(line)
        j = 0
        for i in range(line_len):
            while j > 0 and line[i] != term[j]:
                j = table[j - 1]
            if line[i] == term[j]:
                j += 1
            if j == term_len:
                return i - term_len + 1
        return -1

    for line_num, line in enumerate(content):
        line_to_check = line if case_sensitive else line.lower()
        term_to_check = term if case_sensitive else term.lower()
        table = build_kmp_table(term_to_check)

        # Perform whole word match using regex if needed
        if whole_word:
            if re.search(r'\b' + re.escape(term_to_check) + r'\b', line_to_check):
                results[line] = line_num + 1
        else:
            col_position = search_kmp(line_to_check, term_to_check, table)
            if col_position != -1:
                results[line] = line_num + 1

    return results

# Streamlit GUI
st.title("Word Search Application")
st.write("Search for a specific word across multiple text files using both Brute Force and KMP algorithms.")

uploaded_files = st.file_uploader("Upload Text Files", accept_multiple_files=True, type=["txt"])
search_term = st.text_input("Enter search term")
whole_word = st.checkbox("Whole Word Match")
case_sensitive = st.checkbox("Case Sensitive Match")

if st.button("Search"):
    if not uploaded_files or not search_term:
        st.error("Please upload at least one file and enter a search term.")
    else:
        # Reset the session state for new search
        st.session_state.current_index = 0
        st.session_state.results = []
        st.session_state.matched_word_index = 0
        st.session_state.show_summary = True  # Show summary initially

        brute_force_time = 0
        kmp_time = 0
        unified_results = {}

        # Search each file and collect results
        for file in uploaded_files:
            content = file.read().decode("utf-8").splitlines()

            # Brute Force Search
            start_time = time.time()
            brute_force_results = brute_force_search(content, search_term, whole_word, case_sensitive)
            brute_force_time += time.time() - start_time

            # KMP Search
            start_time = time.time()
            kmp_results = kmp_search(content, search_term, whole_word, case_sensitive)
            kmp_time += time.time() - start_time

            # Combine Brute Force and KMP results, avoiding duplicate sentences
            for line, line_num in {**brute_force_results, **kmp_results}.items():
                if line not in unified_results:
                    unified_results[line] = {"file": file.name, "line": line_num, "algorithms": []}
                if line in brute_force_results:
                    unified_results[line]["algorithms"].append("Brute Force")
                if line in kmp_results:
                    unified_results[line]["algorithms"].append("KMP")

        # Convert unified results into a sorted list
        st.session_state.results = sorted(unified_results.items(), key=lambda x: (x[1]["file"], x[1]["line"]))

        # Calculate total matches found
        total_matches = len(st.session_state.results)

        # Store the summary for future display
        st.session_state.search_summary = {
            "search_term": search_term,
            "whole_word": whole_word,
            "case_sensitive": case_sensitive,
            "total_matches": total_matches,
            "brute_force_time": brute_force_time,
            "kmp_time": kmp_time
        }

# Display the original summary
if hasattr(st.session_state, "search_summary"):
    if st.session_state.show_summary:
        summary = st.session_state.search_summary
        st.write("## Results Summary")
        st.write(f"Search Term: **{summary['search_term']}**")
        st.write(f"Whole Word Match: **{summary['whole_word']}**, Case Sensitive: **{summary['case_sensitive']}**")
        st.write(f"Total Matches Found: **{summary['total_matches']}**")
        st.write(f"Total Brute Force Time: **{summary['brute_force_time']:.4f} seconds**")
        st.write(f"Total KMP Time: **{summary['kmp_time']:.4f} seconds**")
        if st.button("Hide Summary"):
            st.session_state.show_summary = False
    else:
        if st.button("Show Summary"):
            st.session_state.show_summary = True

# Display current search result with navigation
if st.session_state.results:
    try:
        current_index = st.session_state.current_index
        matched_word_index = st.session_state.matched_word_index

        # Ensure we retrieve the correct result before displaying it
        sentence, result_info = st.session_state.results[current_index]
        highlighted_sentence = highlight_term(sentence, search_term)

        # Display the result in a formatted box
        algorithms_used = ", ".join(result_info["algorithms"])
        st.markdown(
            f"""
            <div class="result-container">
                <strong>Matched Word: {matched_word_index + 1} of {len(st.session_state.results)}</strong><br>
                <strong>Algorithms Used: {algorithms_used}</strong><br>
                File: {result_info['file']}<br>
                Line: {result_info['line']}<br>
                Sentence: {highlighted_sentence}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])

        if col1.button("Previous", disabled=current_index == 0):
            st.session_state.current_index -= 1
            st.session_state.matched_word_index -= 1  # Decrement matched word index
            
        if col3.button("Next", disabled=current_index == len(st.session_state.results) - 1):
            st.session_state.current_index += 1
            st.session_state.matched_word_index += 1  # Increment matched word index

    except IndexError:
        st.error("No more results available.")
else:
    st.write("No results found.")
