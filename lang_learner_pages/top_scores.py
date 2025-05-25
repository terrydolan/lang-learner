"""
Module: top_scores.py
Description: Contains logic for the Top Scores miniapp page.

ToDo:
- add bold styling when (if) supported by st.dataframe in future st.release.
"""
import logging
import streamlit as st
import pandas as pd
from pathlib import Path
from utils.gsheet_utils import read_nicknames_as_df_from_gsheet, read_scores_as_df_from_gsheet
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
def build_top_scores_table(miniapp):
    """Return the sorted top scores table (highest first) for the given miniapp
    """
    logger.debug(f"call: build_top_scores_table({miniapp=})")

    # read the scores data into a dataframe
    df_scores = read_scores_as_df_from_gsheet()

    # filter the scores dataframe for the miniapp, sorted by
    # Score (highest), Timestamp (earliest) and User_id (alphabetical)
    df_miniapp_scores = df_scores[(df_scores.Miniapp == miniapp)][["User_id", "Score", "Timestamp"]] \
        .sort_values(by=["Score", "Timestamp", "User_id"], ascending=(False, True, True), ignore_index=True)

    # select each user's top score
    df_miniapp_scores = df_miniapp_scores.loc[df_miniapp_scores.groupby('User_id')['Score'].idxmax()] \
        .sort_values(by=["Score", "Timestamp", "User_id"], ascending=(False, True, True), ignore_index=True)
    logger.debug(f"{df_miniapp_scores=}")

    # read the nicknames and join the top scores with the user nicknames so that
    # the user-friendly nickname can be displayed instead of the user_id
    df_nicknames = read_nicknames_as_df_from_gsheet()
    logger.debug(f"{df_nicknames=}")
    # include only scores that have an active user_id and nickname
    df_table = df_miniapp_scores.merge(df_nicknames, on=['User_id'], how='inner')
    df_table = df_table[["Nickname", "Score", "Timestamp"]]
    # add Position to the table, starting at 1 to create a league table
    df_table.index += 1
    df_table = df_table.reset_index(names=['Position'])
    # rename 'Score' column to 'Top Score'
    df_table = df_table.rename(columns={"Score": "Top Score"})

    logger.debug(f"return: {df_table=}")
    return df_table


def highlight_row_with_this_user_nickname(row: pd.Series):
    """Return all items in row highlighted if row has this user's nickname.

    Highlight using Streamlit's backgound colour for row selection in light mode.
    """
    if ('Nickname' in row.index and
            row.Nickname == st.session_state.user_nickname):
        # ToDo: add bold styling when (if) supported by st.dataframe in future st.release
        # return ['background-color: lightyellow; font-weight: bold'] * len(row)
        return ['background-color: rgba(251,233,234,255); color: black'] * len(row)
    else:
        return [''] * len(row)


def main():
    st.header("Top Scores")
    logger.debug(f"call: start top scores miniapp")
    # save page
    _calling_page = save_page('top_scores')

    # create a dictionary to map from a miniapp friendly name to the miniapp name
    miniapp_map = {m.replace('_', ' ').title(): m for m in MINIAPPS_WITH_SCORES}

    # select the miniapp
    mini_app_friendly_names = list(miniapp_map.keys())
    selection = st.radio(label="Selected Mini-app", options=mini_app_friendly_names, horizontal=True)
    st.info(f"Top scores for {selection}")
    logger.debug(f"user selected top scores for {selection=}")

    # build the top scores table (with nickname) for the selection
    df_scores_table = build_top_scores_table(miniapp_map[selection])

    # display the table
    if not df_scores_table.empty:
        logger.debug(f"display {df_scores_table=}")
        # display with this user's row highlighted
        st.dataframe(df_scores_table
                     .style.apply(highlight_row_with_this_user_nickname, axis=1),
                     hide_index=True)

        # party if user is top!
        if df_scores_table.Nickname.values[0] == st.session_state.user_nickname:
            logger.debug(f"user congratulated for being top, {st.session_state.user_nickname=}")
            st.success(f"Congratulations {st.session_state.user_nickname}, you are top!", icon=":material/check:")
            st.balloons()
    else:
        logger.debug(f"No scores saved yet for miniapp")
        st.write("No scores saved yet, try again later after using the mini-app.")


if __name__ == "__main__":
    main()
