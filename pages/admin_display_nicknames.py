"""
Module: admin_display_nicknames.py
Description: Contains logic for the Admin page to display the Nicknames gsheet.
"""
import logging
import streamlit as st

from utils.gsheet_utils import read_nicknames_as_df_from_gsheet

# setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def main():
    logger.debug(f"call: started admin display nicknames")
    st.header("Admin: Display Nicknames gsheet")

    df_nicknames = read_nicknames_as_df_from_gsheet()
    logger.debug(f"display {df_nicknames=}")
    st.dataframe(df_nicknames)


if __name__ == "__main__":
    main()
