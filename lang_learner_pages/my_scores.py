"""
Module: my_scores.py
Description: Contains logic for the My Scores miniapp page.
"""
import logging
import streamlit as st
from pathlib import Path
from utils.gsheet_utils import read_scores_as_df_from_gsheet
from utils.page_utils import save_page

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)

# define constants
if st.session_state.user_id in st.secrets.admin.admin_user_ids:
    MINIAPPS_WITH_SCORES = ['word_match', 'gender_match', 'other']
else:
    MINIAPPS_WITH_SCORES = ['word_match']


# cache data for 1 minute
@st.cache_data(show_spinner="Reading app data and building the table...", ttl=60*1)
def build_my_scores_table(user_id, miniapp):
    """Return the sorted scores (highest first) for the given user and miniapp
    """
    logger.debug(f"call: build_my_scores_table({user_id=}, {miniapp=})")

    # read the scores data into a dataframe
    df_scores = read_scores_as_df_from_gsheet()

    # filter the scores dataframe for the user and miniapp, sorted by
    # Score (highest) and Timestamp (earliest)
    df_scores = df_scores[(df_scores.User_id == user_id) &
                          (df_scores.Miniapp == miniapp)][["Score", "Timestamp"]] \
        .sort_values(by=["Score", "Timestamp"], ascending=(False, True), ignore_index=True)

    logger.debug(f"return: {df_scores=}")
    return df_scores


def main():
    st.header("My Scores")
    logger.debug(f"call: start my scores miniapp")
    # save page
    _calling_page = save_page('my_scores')

    # create a dictionary to map from a miniapp friendly name to the miniapp name
    miniapp_map = {m.replace('_', ' ').title(): m for m in MINIAPPS_WITH_SCORES}

    # select the miniapp
    mini_app_friendly_names = list(miniapp_map.keys())
    selection = st.radio(label="Selected Mini-app", options=mini_app_friendly_names, horizontal=True)
    st.info(f"My scores for {selection}")
    logger.debug(f"user selected my scores for {selection=}")

    # build the my scores table (with nickname) for the selection
    df_user_scores = build_my_scores_table(st.session_state.user_id, miniapp_map[selection])

    # display the table
    if not df_user_scores.empty:
        logger.debug(f"display {df_user_scores=}")
        # display
        st.dataframe(df_user_scores, hide_index=False)

    else:
        logger.debug(f"No scores saved yet for miniapp")
        st.write("No scores saved yet, try again later after using the mini-app.")


if __name__ == "__main__":
    main()
