"""
Module: uils/gsheet_utils.py
Description: Contains utilities handling interface to Google sheet files.
"""
import logging
import pandas as pd
import streamlit as st
from pathlib import Path
from streamlit_gsheets import GSheetsConnection

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)

# ------------------------------------------------------------------------------
# Functions related to nickname gsheet
# ------------------------------------------------------------------------------


@st.cache_data(show_spinner="Reading app data...", ttl=0)  # replace unfriendly gsheet spinner
# @st.cache_data(show_spinner="Reading nicknames data...")
# @st.cache_data(show_spinner=False)
def read_nicknames_as_df_from_gsheet():
    """Return the nicknames from the gsheet as a dataframe."""
    logger.debug(f"call: read_nicknames_as_df_from_gsheet()")
    conn = st.connection("gsheets-nicknames", type=GSheetsConnection)
    try:
        df = conn.read(worksheet="Sheet1", ttl=0, usecols=["User_id", "Nickname"])
        # logger.debug(f"return: ({df=})")
        return df
    except Exception as e:
        logger.error(f"Exception: Error loading nicknames from Google Sheet as df: {e}, report to app admin")
        st.error("")
        st.error(f"Error loading nicknames from Google Sheet: {e}, report to app admin")
        st.stop()


@st.cache_data(show_spinner="Saving app data...", ttl=0)  # replace unfriendly gsheet spinner
def save_nicknames_df_to_gsheet(df):
    """Save the given dataframe to the nicknames gsheet."""
    logger.debug(f"call: save_nicknames_df_to_gsheet({df=})")
    conn = st.connection("gsheets-nicknames", type=GSheetsConnection)
    conn.clear(worksheet="Sheet1")

    try:
        conn.update(worksheet="Sheet1", data=df)
    except Exception as e:
        logger.error(f"Exception: Error saving nicknames to Google Sheet as df: {e}, report to app admin")
        st.error("")
        st.error(f"Error saving nicknames from Google Sheet: {e}, report to app admin")
        st.stop()


def load_nicknames_dict_from_gsheet():
    """Return nicknames as a dictionary."""
    logger.debug(f"call: load_nicknames_dict_from_gsheet()")
    # read the nicknames as a dataframe
    nicknames_df = read_nicknames_as_df_from_gsheet()

    # convert pandas dataframe to pandas series and then to dict
    nicknames_dict = nicknames_df.set_index("User_id")["Nickname"].to_dict()
    logger.debug(f"return: {nicknames_dict=}")
    return nicknames_dict


def save_nickname_to_gsheet(user_id, nickname):
    """Save given user_id and nickname to nicknames gsheet."""
    logger.debug(f"call: save_nickname_to_gsheet({user_id=}, {nickname=})")
    assert user_id and nickname, f"error: both user_id and nickname should not be null, {user_id=} and {nickname=}"
    # read the existing nicknames as a dataframe
    df_nicknames = read_nicknames_as_df_from_gsheet()  # read latest data
    df_nicknames = df_nicknames[df_nicknames["User_id"] != user_id]  # exclude existing user_id (if present)

    # produce a new dataframe that includes a new row containing the given user_id and nickname
    # noinspection PyUnreachableCode
    df_updated = pd.concat([
        df_nicknames,
        pd.DataFrame([{"User_id": user_id, "Nickname": nickname}])],
        ignore_index=True)
    df_updated = df_updated.sort_values(by=['User_id', 'Nickname'], ascending=(True, True), ignore_index=True)

    # carry out a few integrity checks before updating the gsheet
    assert not df_updated.duplicated().any(), f"should not be any duplicate rows in the dataframe! {df_updated=}"
    assert not df_updated.User_id.duplicated().any(), f"should not be any duplicated User_ids! {df_updated=}"
    assert not df_updated.Nickname.duplicated().any(), f"should not be any duplicated Nicknames! {df_updated=}"
    assert df_updated.notnull().values.all(), f"should not be any empty values! {df_updated=}"

    # save the updated dataframe to nicknames
    save_nicknames_df_to_gsheet(df_updated)

# ------------------------------------------------------------------------------
# Functions related to scores gsheet
# ------------------------------------------------------------------------------


@st.cache_data(show_spinner="Reading app data...", ttl=0)  # replace unfriendly gsheet spinner
def read_scores_as_df_from_gsheet():
    """Return the scores from the gsheet as a dataframe."""
    logger.debug(f"call: read_scores_as_df_from_gsheet()")
    conn = st.connection("gsheets-scores", type=GSheetsConnection)
    try:
        df = conn.read(worksheet="Sheet1", ttl=0, usecols=["User_id", "Miniapp", "Score", "Timestamp"])
        # logger.debug(f"initial dtypes: ({df.dtypes=})")

        # convert Score to int
        df['Score'] = df.Score.astype(int)

        # convert Timestamp (gsheet 'Date time') to pandas datetime
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True)
        # logger.debug(f"dtypes after conversion: ({df.dtypes=})")

        # logger.debug(f"return: dataframe:\n{df.to_string()}")
        # logger.debug(f"return dataframe: \n{df.to_string()}")
        return df
    except Exception as e:
        logger.error(f"Exception: Error loading scores from Google Sheet as df: {e}, report to app admin")
        st.error("")
        st.error(f"Error loading scores from Google Sheet: {e}, report to app admin")
        st.stop()


@st.cache_data(show_spinner="Saving app data...", ttl=0)  # replace unfriendly gsheet spinner
def save_scores_df_to_gsheet(df):
    """Save the given dataframe to the scores gsheet."""
    logger.debug(f"call: save_scores_df_to_gsheet({df=})")
    conn = st.connection("gsheets-scores", type=GSheetsConnection)
    conn.clear(worksheet="Sheet1")

    try:
        conn.update(worksheet="Sheet1", data=df)
    except Exception as e:
        logger.error(f"call: Exception: Error saving scores to Google Sheet as df: {e}, report to app admin")
        st.error(f"Error saving scores from Google Sheet: {e}, report to app admin")
        st.stop()


def save_score_to_gsheet(user_id, miniapp, score, timestamp):
    """Save given user_id, miniapp, score and timestamp to scores gsheet."""
    logger.debug(f"call: save_score_to_gsheet({user_id=}, {miniapp=}, {score=}, {timestamp=})")
    assert score >= 0, f"unexpected error: score should >= 0, {score=}"
    assert user_id and miniapp and timestamp, (
        f"unexpected error: value should not be null, {user_id=}, {miniapp=}, {timestamp=}")

    # read latest scores data
    df_scores = read_scores_as_df_from_gsheet()

    # raise error if record already in dataframe
    logger.debug(f"check for duplicate: {user_id=}, {miniapp=}, {score=}, {timestamp}")
    if ((df_scores.User_id == user_id) &
            (df_scores.Miniapp == miniapp) &
            (df_scores.Score == score) &
            (df_scores.Timestamp == timestamp)).any():
        logger.debug("raise ValueError detected, this record is already present in scores")
        raise ValueError('this record is already present in scores')

    # create updated dataframe that combines existing scores dataframe with the new record
    # noinspection PyUnreachableCode
    df_updated = pd.concat([
        df_scores,
        pd.DataFrame([{"User_id": user_id, "Miniapp": miniapp, "Score": score, "Timestamp": timestamp}])],
        ignore_index=True)
    df_updated = df_updated.sort_values(by=['User_id', "Miniapp", 'Score', "Timestamp"],
                                        ascending=(True, True, False, True), ignore_index=True)
    df_updated['Timestamp'] = df_updated.Timestamp.dt.strftime('%d/%m/%Y %H:%M:%S')

    # carry out a few integrity checks before updating the gsheet
    assert not df_updated.duplicated().any(), f"should not be any duplicate rows in the dataframe! {df_updated=}"
    assert df_updated.notnull().values.all(), f"should not be any empty values! {df_updated=}"

    save_scores_df_to_gsheet(df_updated)
