"""
Module: admin_enter_scores.py
Description: Contains logic for the Admin Scores Entry page.

Limitations:
- Note that the admin enter scores does not check for in progress high scores that may be scored in session
variables. This is not usually a problem as admin enter scores is usually used to enter scores for miniapps
that haven't yet been developed.
"""
import logging
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
from lang_learner_pages.top_scores import MINIAPPS_WITH_SCORES
from utils.gsheet_utils import save_score_to_gsheet
from utils.page_utils import save_page

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)


def main():
    logger.debug(f"call: started admin enter scores")
    st.header("Admin: Manual Entry of Scores for Testing")
    # save page
    _calling_page = save_page('scores')

    sel_score = st.number_input(
        label="Enter the simulated score to write to scores gsheet", min_value=0, max_value=100, value=50, step=5)

    user_id_options = list(st.session_state.nicknames_dict.keys())
    this_user_index = user_id_options.index(st.session_state.user_id)
    sel_user_id = st.selectbox(label="Select user_id for score", options=user_id_options, index=this_user_index)

    sel_miniapp = st.selectbox(label="Select miniapp for score", options=MINIAPPS_WITH_SCORES)

    sel_date = st.date_input("Enter date for score", max_value="today")
    sel_time = st.time_input("Enter time for score").replace(microsecond=0)  # time without microseconds
    sel_timestamp= pd.Timestamp(datetime.combine(sel_date, sel_time))

    if st.button("Submit score"):
        try:
            save_score_to_gsheet(sel_user_id, sel_miniapp, sel_score, sel_timestamp)
            logger.debug("Scores successfully updated")
            st.info("Scores successfully updated")
        except ValueError:
            logger.error("ValueError caught: this record already exists in the scores")
            st.error("this record already exists in the scores, please try again with different values")
            st.stop()


if __name__ == "__main__":
    main()
