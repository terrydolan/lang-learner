"""
Module: admin_display_nicknames.py
Description: Contains logic for the Admin page to display the Nicknames gsheet.
"""
import logging
import streamlit as st
from pathlib import Path
from utils.gsheet_utils import read_nicknames_as_df_from_gsheet

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)


def main():
    logger.debug(f"call: started admin display nicknames")
    st.header("Admin: Display Nicknames gsheet")

    df_nicknames = read_nicknames_as_df_from_gsheet()
    logger.debug(f"display {df_nicknames=}")
    st.dataframe(df_nicknames)


if __name__ == "__main__":
    main()
