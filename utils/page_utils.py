"""
Module: uils/page_utils.py
Description: Contains utilities for use in Streamlit pages.
"""

import logging
import streamlit as st
from pathlib import Path

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)


def save_page(page_name):
    """Save page_name to session_state.page_name and return previous value.

    Return:
        previous_page_name: str | None, name of previous session_state.page_name
        Note: Return None if page_name not set
    """
    logger.debug(f"call: log_page({page_name=})")
    if "page_name" in st.session_state:
        previous_page_name = st.session_state.page_name
        st.session_state.page_name = page_name
    else:
        previous_page_name = None
        st.session_state.page_name = page_name

    logger.debug(f"return: {previous_page_name=}")
    return previous_page_name
