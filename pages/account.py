"""
Module: account.py
Description: Contains logic for the account page covering login,
change_nickname, remove_user and logout.
"""
import logging
import streamlit as st
from pathlib import Path
from utils.gsheet_utils import (load_nicknames_dict_from_gsheet, save_nickname_to_gsheet,
                                read_nicknames_as_df_from_gsheet, save_nicknames_df_to_gsheet)

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)

# ------------------------------------------------------------------------------
# Account login page functions
# ------------------------------------------------------------------------------


def login():
    """Log the user in and set the user's nickname."""
    logger.debug(f"call: login")
    if not st.user.is_logged_in:
        # user not yet logged in
        logger.debug(f"not logged in")
        st.write("Please login to use the app.\n")
        if st.button("Log in with Google", on_click=st.login):
            st.rerun()
        st.stop()
    else:
        # login authenticated, auth info is in st.user
        # logger.debug(f"log in authenticated, {st.user.to_dict()=}")

        # define key user data from auth data and save to session state
        if "user_id" not in st.session_state:
            user_dict = st.user.to_dict()
            st.session_state.user_id = user_dict['email'].strip()
            st.session_state.user_given_name = user_dict['given_name'].strip()
            logger.debug(f"Logged in with User id: '{st.session_state.user_id}'")

        # set the user's nickname to complete the login
        # the user's user_id and user_nickname are stored in the nicknames google sheet
        if "user_nickname" not in st.session_state:
            # load the nicknames into a dict from the nicknames google sheet
            if "nicknames_dict" not in st.session_state:
                st.session_state.nicknames_dict = load_nicknames_dict_from_gsheet()

            logger.debug(f"{st.session_state.nicknames_dict=}")
            if st.session_state.user_id in st.session_state.nicknames_dict:
                # user already has a nickname
                logger.debug(f"User_id already has nickname: "
                             f"'{st.session_state.nicknames_dict[st.session_state.user_id]}'")
                st.session_state.user_nickname = st.session_state.nicknames_dict[st.session_state.user_id]
                logger.debug(f"Logged in with nickname: '{st.session_state.user_nickname}'")
                st.session_state.login_popup = f"Welcome back {st.session_state.user_nickname}"
                st.session_state.login_complete = True
                st.rerun()
            elif st.session_state.user_given_name not in st.session_state.nicknames_dict.values():
                # set the user's given name (from their auth data) as their nickname
                logger.debug(f"Set user's given name '{st.session_state.user_given_name}' as their nickname")
                save_nickname_to_gsheet(st.session_state.user_id, st.session_state.user_given_name)
                st.session_state.user_nickname = st.session_state.user_given_name
                logger.debug(f"Logged in with new nickname: '{st.session_state.user_nickname}'")
                st.session_state.login_popup = (
                    f"Welcome, your nickname is set to '{st.session_state.user_nickname}'. "
                    f"You can change your nickname on the *Manage* page in the sidebar.")
                st.session_state.login_complete = True
                st.rerun()
            else:
                # user must set a new unique nickname
                logger.debug(f"User {st.session_state.user_id=} must set a new unique nickname")
                new_nickname = ui_set_unique_nickname(st.session_state.nicknames_dict)
                if new_nickname:
                    logger.debug(f"User set newly selected unique nickname '{new_nickname}' as their nickname")
                    save_nickname_to_gsheet(st.session_state.user_id, new_nickname)
                    st.session_state.user_nickname = new_nickname
                    logger.debug(f"Logged in with new nickname: '{st.session_state.user_nickname}'")
                    st.session_state.login_popup = (
                        f"Welcome, your nickname is set to '{st.session_state.user_nickname}'. "
                        f"You can change your nickname on the *Manage* page in the sidebar."
                    )
                    st.session_state.login_complete = True
                    st.rerun()
        else:
            # nickname set and user logged in

            # display logged-in user
            logger.debug(f"Logged in as: {st.session_state.user_nickname} ({st.session_state.user_id})")
            st.sidebar.write(f"Logged in as: {st.session_state.user_nickname} ({st.session_state.user_id})")

            # display initial login popup message and then clear the message
            if "login_popup" in st.session_state:
                logger.debug(f"display login_popup")
                st.sidebar.info(st.session_state.login_popup, icon=":material/info:")
                del st.session_state.login_popup


# ------------------------------------------------------------------------------
# Account logout page functions
# ------------------------------------------------------------------------------
def logout():
    """Log user out and clear session state."""
    logger.debug(f"call: logout()")
    st.write("Log out from the app, all your information will be saved")
    if st.button("Log out"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.logout()
        st.rerun()


# ------------------------------------------------------------------------------
# Account change user's nickname page functions
# ------------------------------------------------------------------------------
def ui_set_unique_nickname(nicknames_dict):
    """Prompt user to set a new unique nickname, validate and return."""
    logger.debug(f"call: ui_set_unique_nickname({nicknames_dict=})")
    st.write("Please select a nickname to use the app.")
    new_nickname = st.text_input("Nickname:")
    if st.button("Confirm selection"):
        new_nickname = new_nickname.strip()
        if not new_nickname:
            logger.debug(f"Error {new_nickname=}: The nickname cannot be blank. Please choose another.")
            st.error("The nickname cannot be blank. Please choose another.")
        elif len(new_nickname) == 1:
            logger.debug(f"Error {new_nickname=}: The nickname must have at least 2 characters. "
                         f"Please choose another.")
            st.error("The nickname must have at least 2 characters. Please choose another.")
        elif new_nickname.lower() in [nname.lower() for nname in nicknames_dict.values()]:
            logger.debug(f"Error {new_nickname=}: This nickname is already taken. Please choose another.")
            st.error("This nickname is already taken. Please choose another.")
        else:
            logger.debug(f"Success: {new_nickname} is valid.")
            return new_nickname

    return None


def ui_change_unique_nickname(current_nickname, nicknames_dict):
    """Prompt user to set a new unique replacement nickname, validate and return."""
    logger.debug(f"call: ui_change_unique_nickname({current_nickname=}, {nicknames_dict=})")

    st.write("Please select a new nickname.")
    st.info(f"Your current nickname is: {current_nickname}")
    new_nickname = st.text_input("New nickname:")
    if st.button("Confirm selection"):
        new_nickname = new_nickname.strip()
        if not new_nickname:
            logger.debug(f"Error {new_nickname=}: The new nickname cannot be blank. Please choose another.")
            st.error("The new nickname cannot be blank. Please choose another.")
        elif len(new_nickname) == 1:
            logger.debug(f"Error {new_nickname=}: The new nickname must have at least 2 characters. "
                         f"Please choose another.")
            st.error("The new nickname must have at least 2 characters. Please choose another.")
        elif new_nickname == current_nickname:
            logger.debug(f"Error {new_nickname=}: The new nickname must have at least 2 characters. "
                         f"Please choose another.")
            st.error("The new nickname must not be the same as your current nickname. Please choose another.")
        elif new_nickname.lower() in [nname.lower() for nname in nicknames_dict.values()]:
            logger.debug(f"Error {new_nickname=}: This nickname is already taken. Please choose another.")
            st.error("This nickname is already taken. Please choose another.")
        else:
            logger.debug(f"Success: {new_nickname} is valid.")
            return new_nickname

    return None


def change_nickname():
    """Change user's existing nickname in the nicknames gsheet."""
    logger.debug(f"call: change_nickname()")
    # refresh the nicknames_dict with existing nicknames
    st.session_state.nicknames_dict = load_nicknames_dict_from_gsheet()

    # prompt user to set a new unique nickname to replace current one
    logger.debug(f"User {st.session_state.user_id=} must set a new unique nickname, "
                 f"current nickname {st.session_state.user_nickname}")
    new_nickname = ui_change_unique_nickname(st.session_state.user_nickname,
                                             st.session_state.nicknames_dict)
    if new_nickname:
        logger.debug(f"User set new unique nickname '{new_nickname}' "
                     f"to replace their their current nickname")
        # save changed nickname
        save_nickname_to_gsheet(st.session_state.user_id, new_nickname)
        st.session_state.user_nickname = new_nickname
        logger.debug(f"Logged in as: {st.session_state.user_nickname} "
                     f"({st.session_state.user_id})")
        st.info(f"Your new nickname is set to '{st.session_state.user_nickname}'. "
                f"You can change your nickname on the *Manage* page in the sidebar.")
        if st.button("Acknowledge"):
            st.rerun()

# ------------------------------------------------------------------------------
# Account remove user page functions
# ------------------------------------------------------------------------------


def remove_user():
    """Remove user from nicknames and log user out."""
    logger.debug(f"call: remove_user()")
    st.info(f"You are logged in as: {st.session_state.user_nickname} ({st.session_state.user_id})")
    st.write("Remove your user / nickname from the app and logout")
    if st.button("Remove"):
        # get the latest nicknames as a dataframe
        df_nicknames = read_nicknames_as_df_from_gsheet()
        logger.debug(f"{df_nicknames=}")

        # create an updated dataframe with the current user removed
        df_updated = df_nicknames[df_nicknames["User_id"] != st.session_state.user_id]

        # carry out a few integrity checks before updating the gsheet
        assert not df_updated.duplicated().any(), f"should not be any duplicate rows in the dataframe! {df_updated=}"
        assert not df_updated.User_id.duplicated().any(), f"should not be any duplicated User_ids! {df_updated=}"
        assert not df_updated.Nickname.duplicated().any(), f"should not be any duplicated Nicknames! {df_updated=}"
        assert df_updated.notnull().values.all(), f"should not be any empty values! {df_updated=}"

        # save the updated dataframe
        save_nicknames_df_to_gsheet(df_updated)

        # remove session_state keys and log out
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.logout()
        st.rerun()
