"""
Module: search.py
Description: Contains logic for the Search miniapp page.
"""
import logging
import streamlit as st
import re
from pathlib import Path
from utils.page_utils import save_page

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)


def main():
    """Main for gender match."""
    st.subheader("Search Words")
    logger.debug(f"call: start Search Words mini-app {'-'*50}")
    # save page
    _calling_page = save_page('scores')

    # assign key vars from session state
    target_language = st.session_state.target_language
    source_language = st.session_state.source_language
    df_words = st.session_state.df_words

    # determine what language to search (sidebar)
    what_lang = st.sidebar.radio(label="Select *what* to search:",
                                 options=[f"{target_language} phrases",
                                          f"{source_language} phrases",
                                          f"{source_language} phrases (without diacritics)"],
                                 horizontal=False)

    # determine type of search (sidebar)
    search_type = st.sidebar.radio(label="Select *type* of search:",
                                   options=["Simple (starts with)",
                                            "Advanced match (using regex)"],
                                   horizontal=False)

    # determine what cols to display (sidebar)
    if st.session_state.user_id in st.secrets.admin.admin_user_ids:
        # admin user has option to see All cols
        display_cols = st.sidebar.radio(label="Select columns to display in results:",
                                        options=['Key', 'All'],
                                        horizontal=True)
    else:
        # other users see only 'key' columns, displayed in a friendly way
        display_cols = 'Key'

    with st.container(border=True):
        # user decides on search string
        search_str = st.text_input(label=f"Enter search string for {what_lang}:",
                                   placeholder="<Search string>",
                                   help="Use the sidebar to change *what* is searched and the *type* of search.")

        # user decides when to search
        do_search = st.button(label="Search")

    if do_search:
        logger.debug(f"prepare search with inputs: {what_lang=}, {display_cols=}")
        # determine what columns to search in dataframe
        if target_language in what_lang:
            what_col = 'target_phrase_short'
        elif 'diacritic' in what_lang:
            what_col = 'source_phrase_no_diacritic'
        else:
            what_col = 'source_phrase'

        # select dataframe columns to display
        if display_cols == 'Key':
            # display only key cols
            sel_cols = ['source_phrase', 'target_phrase_short']
            sel_cols_map = {'source_phrase': source_language,
                            'target_phrase_short': target_language}
        else:
            # display all cols
            sel_cols = df_words.columns.tolist()
            sel_cols_map = {c: c for c in sel_cols}

        # search
        try:
            logger.debug(f"search df_words using: {search_type=}, {what_col=}, {search_str=}, {sel_cols=}")

            # search words dataframe (based on search type)
            if 'Simple' in search_type:
                df_srch = df_words[(df_words[what_col].str.startswith(pat=search_str))]\
                    [sel_cols].reset_index(drop=True)
            else:
                df_srch = df_words[(df_words[what_col].str.contains(pat=search_str, regex=True))]\
                    [sel_cols].reset_index(drop=True)

            st.write("Results:")
            logger.debug(f"display df_srch using: {sel_cols_map=}")
            st.dataframe(
                df_srch,
                column_config=sel_cols_map)

            logger.debug(f"report found {len(df_srch)} items in {what_lang}")
            st.write(f"Found {len(df_srch)} items in {what_lang}")
        except re.error as e:
            logger.debug(f"exception re.error triggered: error in regular expression: {e}")
            st.error(f"error in regular expression: {e}")


if __name__ == "__main__":
    main()
