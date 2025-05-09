"""
Module: scores.py
Description: Contains logic for the Scores miniapp page.

ToDo:
- remove miniapp filter if only one value
"""
import logging
import streamlit as st
import pandas as pd

from utils.gsheet_utils import read_nicknames_as_df_from_gsheet, read_scores_as_df_from_gsheet

# setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# define constants
if st.session_state.user_id in st.secrets.admin.admin_user_ids:
    MINIAPPS_WITH_SCORES = ['word_match', 'gender_match', 'other']
else:
    MINIAPPS_WITH_SCORES = ['word_match']


# cache data for 1 minutes
@st.cache_data(show_spinner="Reading app data and building the table...", ttl=60*1)
def build_scores_table(miniapp):
    """Return the sorted scores table (highest first) for the given miniapp
    """
    logger.debug(f"call: build_scores_table({miniapp=})")

    # read the scores data into a dataframe
    df_scores = read_scores_as_df_from_gsheet()

    # filter the scores dataframe for the miniapp, sorted by
    # Score (highest), Timestamp (earliest) and User_id (alphabetical)
    df_miniapp_scores = df_scores[(df_scores.Miniapp == miniapp)][["User_id", "Score", "Timestamp"]] \
        .sort_values(by=["Score", "Timestamp", "User_id"], ascending=(False, True, True), ignore_index=True)

    # select each user's best score
    df_miniapp_scores = df_miniapp_scores.loc[df_miniapp_scores.groupby('User_id')['Score'].idxmax()] \
        .sort_values(by=["Score", "Timestamp", "User_id"], ascending=(False, True, True), ignore_index=True)
    logger.debug(f"{df_miniapp_scores=}")

    # read the nicknames and join the best scores with the user nicknames so that
    # the user-friendly nickname can be displayed instead of the user_id
    df_nicknames = read_nicknames_as_df_from_gsheet()
    logger.debug(f"{df_nicknames=}")
    # include only scores that have an active user_id and nickname
    df_table = df_miniapp_scores.merge(df_nicknames, on=['User_id'], how='inner')
    df_table = df_table[["Nickname", "Score", "Timestamp"]]
    # add Position to the table, starting at 1 to create a league table
    df_table.index += 1
    df_table = df_table.reset_index(names=['Position'])
    # rename 'Score' column to 'Best Score'
    df_table = df_table.rename(columns={"Score": "Best Score"})

    logger.debug(f"return: {df_table=}")
    return df_table


def highlight_row_with_this_user_nickname(row: pd.Series):
    """Return all items in row highlighted if row has this user's nickname."""
    if ('Nickname' in row.index and
            row.Nickname == st.session_state.user_nickname):
        # ToDo: add bold styling when (if) supported by st.dataframe in future st.release
        # return ['background-color: lightyellow; font-weight: bold'] * len(row)
        return ['background-color: lightyellow'] * len(row)
    else:
        return [''] * len(row)


# # Note: streamlit does not support display of index styling in st.dataframe() so
# # alternative (and simpler!) solution is to promote the index to a Position column
# def highlight_index_with_this_user_nickname(idx: pd.Series, df: pd.DataFrame):
#     """Return all items in index idx highlighted if df.iloc[idx] has this user's nickname.
#
#     example call:
#     st.dataframe(df.apply_index(highlight_index_with_this_user_nickname, df=df))
#     """
#     colour_l = []
#     for i in idx:
#         # search Nickname for this user
#         # note that idx starts at 1 so use loc
#         if st.session_state.user_nickname in df.loc[i]['Nickname']:
#             colour_l.append('background-color: lightyellow')
#         else:
#             colour_l.append('')
#
#     return colour_l


def main():
    st.header("Scores")
    logger.debug(f"call: start scores miniapp")

    # create a dictionary to map from a miniapp friendly name to the miniapp name
    miniapp_map = {m.replace('_', ' ').title(): m for m in MINIAPPS_WITH_SCORES}

    # select the miniapp
    mini_app_friendly_names = list(miniapp_map.keys())
    selection = st.radio(label="Select Mini-app", options=mini_app_friendly_names, horizontal=True)
    st.info(f"Best score for {selection}")
    logger.debug(f"user selected scores for {selection=}")

    # build the scores table (with nickname) for the selection
    df_scores_table = build_scores_table(miniapp_map[selection])

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
