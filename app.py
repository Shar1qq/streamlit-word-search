import streamlit as st
import time
import re
import mysql.connector

# Database connection parameters
DB_HOST = 'sql12.freesqldatabase.com'
DB_NAME = 'sql12741043'
DB_USER = 'sql12741043'
DB_PASS = 'NLzNvI2xMP'
DB_PORT = 3306

# Add custom CSS for styling
st.markdown("""<style>
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
    background-color: #f4f4f4;
    font-size: 16px;
}
.highlight {
    color: #e74c3c;
    font-weight: bold;
}
.info-container {
    font-size: 16px;
    margin-bottom: 10px;
}
</style>""", unsafe_allow_html=True)

# Initialize session state variables for navigation
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
    st.session_state.results = []
    st.session_state.matched_word_index = 0
    st.session_state.show_summary = True  # To control summary visibility

# Function to highlight search term
def highlight_term(sentence, term, whole_word=False):
    if whole_word:
        pattern = rf"\b(?:{re.escape(term)})\b"
    else:
        pattern = rf"({re.escape(term)})"
    
    highlighted_sentence = re.sub(pattern, r"<span class='highlight'>\g<0></span>", sentence, flags=re.IGNORECASE)
    return highlighted_sentence

# Brute Force Search
def brute_force_search(content, term, whole_word=False, case_sensitive=False):
    results = {}
    for line_num, line in enumerate(content):
        line_to_check = line if case_sensitive else line.lower()
        term_to_check = term if case_sensitive else term.lower()
        
        if whole_word:
            matches = re.findall(r'\b' + re.escape(term_to_check) + r'\b', line_to_check)
            match_count = len(matches)
        else:
            match_count = line_to_check.count(term_to_check)

        if match_count > 0:
            results[line] = {"line_num": line_num + 1, "match_count": match_count}
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
        count = 0
        i = 0
        while i < line_len:
            if line[i] == term[j]:
                i += 1
                j += 1
            if j == term_len:
                count += 1
                j = table[j - 1]  # reset j using KMP table to find next match
            elif i < line_len and line[i] != term[j]:
                if j != 0:
                    j = table[j - 1]
                else:
                    i += 1
        return count

    for line_num, line in enumerate(content):
        line_to_check = line if case_sensitive else line.lower()
        term_to_check = term if case_sensitive else term.lower()
        table = build_kmp_table(term_to_check)

        if whole_word:
            matches = re.findall(r'\b' + re.escape(term_to_check) + r'\b', line_to_check)
            match_count = len(matches)
        else:
            match_count = search_kmp(line_to_check, term_to_check, table)

        if match_count > 0:
            results[line] = {"line_num": line_num + 1, "match_count": match_count}
    return results

# Connect to the database and fetch content
def fetch_database_content():
    conn = mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM documents")
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1]) for row in rows]

# Streamlit GUI
st.title("Word Search Application")
st.write("Search for a specific word across multiple text files or within stored database entries.")

uploaded_files = st.file_uploader("Upload Text Files", accept_multiple_files=True, type=["txt"])
use_database = st.checkbox("Use Database Content")
search_term = st.text_input("Enter search term")
whole_word = st.checkbox("Whole Word Match")
case_sensitive = st.checkbox("Case Sensitive Match")

# Initialization before search
brute_force_time = 0
kmp_time = 0
total_matched_words = 0
unified_results = {}

if st.button("Search"):
    if (not uploaded_files and not use_database) or not search_term:
        st.error("Please upload files or use the database content and enter a search term.")
    else:
        st.session_state.current_index = 0
        st.session_state.matched_word_index = 0
        st.session_state.results = []
        
        # Initialize timing variables here
        brute_force_time = 0
        kmp_time = 0
        total_matched_words = 0
        unified_results = {}

        # Search in uploaded files if provided
        if uploaded_files:
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

                for line, details in {**brute_force_results, **kmp_results}.items():
                    if line not in unified_results:
                        unified_results[line] = {
                            "file": file.name,
                            "line": details["line_num"],
                            "match_count": details["match_count"],
                            "algorithms": []
                        }
                    if line in brute_force_results:
                        unified_results[line]["algorithms"].append("Brute Force")
                    if line in kmp_results:
                        unified_results[line]["algorithms"].append("KMP")
                    total_matched_words += details["match_count"]

        # Search in database content if selected
        if use_database:
            database_content = fetch_database_content()
            for title, content in database_content:
                content_lines = content.splitlines()

                # Brute Force Search
                start_time = time.time()
                brute_force_results = brute_force_search(content_lines, search_term, whole_word, case_sensitive)
                brute_force_time += time.time() - start_time

                # KMP Search
                start_time = time.time()
                kmp_results = kmp_search(content_lines, search_term, whole_word, case_sensitive)
                kmp_time += time.time() - start_time

                for line, details in {**brute_force_results, **kmp_results}.items():
                    if line not in unified_results:
                        unified_results[line] = {
                            "file": title,
                            "line": details["line_num"],
                            "match_count": details["match_count"],
                            "algorithms": []
                        }
                    if line in brute_force_results:
                        unified_results[line]["algorithms"].append("Brute Force")
                    if line in kmp_results:
                        unified_results[line]["algorithms"].append("KMP")
                    total_matched_words += details["match_count"]

        st.session_state.results = sorted(
            [
                (line, details)
                for line, details in unified_results.items()
            ],
            key=lambda x: (x[1]["file"], x[1]["line"])
        )

        # Store the summary for future display
        st.session_state.search_summary = {
            "search_term": search_term,
            "whole_word": whole_word,
            "case_sensitive": case_sensitive,
            "total_matches": total_matched_words,
            "brute_force_time": brute_force_time,
            "kmp_time": kmp_time
        }

# Display the summary at all times with a button to hide it
if st.session_state.show_summary:
    summary = st.session_state.search_summary
    st.markdown(f"**Search Term:** {summary['search_term']}")
    st.markdown(f"Whole Word Match: **{summary['whole_word']}**")
    st.markdown(f"Case Sensitive Match: **{summary['case_sensitive']}**")
    st.markdown(f"Total Matches: **{summary['total_matches']}**")
    st.markdown(f"Total Brute Force Time: **{summary['brute_force_time']:.4f} seconds**")
    st.markdown(f"Total KMP Time: **{summary['kmp_time']:.4f} seconds**")
    if st.button("Hide Summary"):
        st.session_state.show_summary = False
else:
    if st.button("Show Summary"):
        st.session_state.show_summary = True

# Display the results
if st.session_state.results:
    matched_lines = st.session_state.results
    if st.session_state.current_index < len(matched_lines):
        line, details = matched_lines[st.session_state.current_index]
        highlighted_line = highlight_term(line, search_term, whole_word)

        # Display file title and current matched word number
        current_word_number = st.session_state.current_index + 1
        total_matched = len(matched_lines)

        # Display the match info above the sentence box
        st.markdown(f"""
        <div class='info-container'>
            Current Match: <strong>{current_word_number}/{total_matched}</strong><br>
            Title: <strong>{details['file']}</strong><br>
            Line No: <strong>{details['line']}</strong>
        </div>
        """, unsafe_allow_html=True)

        # Well formatted box containing the sentence
        st.markdown(f"""
        <div class='result-container'>
            {highlighted_line}
        </div>
        """, unsafe_allow_html=True)

        # Navigation buttons in a single row
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.session_state.current_index > 0:
                if st.button("Previous"):
                    st.session_state.current_index -= 1
            else:
                st.button("Previous", disabled=True)  # Disable if at the first result

        with col2:
            if st.session_state.current_index < len(matched_lines) - 1:
                if st.button("Next"):
                    st.session_state.current_index += 1
            else:
                st.button("Next", disabled=True)  # Disable if at the last result
    else:
        st.write("No more results.")
