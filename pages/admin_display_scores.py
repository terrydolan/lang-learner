"""
Module: admin_display_scores.py
Description: Contains logic for the Admin page to display the Scores gsheet.
"""
import logging
import streamlit as st

from utils.gsheet_utils import read_scores_as_df_from_gsheet

# setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def main():
    logger.debug(f"call: started admin display scores")
    st.header("Admin: Display Scores gsheet")

    df_scores = read_scores_as_df_from_gsheet()

    # calculate required height to display required number of rows (default is 10)
    # https://discuss.streamlit.io/t/st-dataframe-controlling-the-height-threshold-for-scolling/31769/5
    num_rows_to_display = 20
    reqd_height = (num_rows_to_display + 1) * 35 + 3
    logger.debug(f"{reqd_height=}")

    # show the dataframe
    logger.debug(f"display {df_scores=}")
    st.dataframe(df_scores, height=reqd_height)


if __name__ == "__main__":
    main()
