"""
Script: lang_learner_app.py
Description: Main entry point for streamlit language learner app.

Author: Terry Dolan
Date Created: 31st March 2025
Date Last Modified: 12th May 2025

ToDo:
- Replace Google Sheets with simple cloud database (e.g. MongoDB) allowing insertion and
update of single rows
- Enhance remove user to also remove user's scores
- Consider admin function to tidy scores e.g. keep only top n scores for each user
- Add method for a user to report a word pair error
- Make solution fully language agnostic (when second language file available); includes
giving the user the ability to select / change the source and target language pair
- Fix pylint warning:
Use lazy % formatting in logging functions (...) [logging-fstring-interpolation]
"""
import logging
import streamlit as st
from pathlib import Path
from pages.account import login, change_nickname, remove_user, logout

# set streamlit page config, must be the first streamlit command
st.set_page_config(page_title="Language Learner App",
                   layout='wide',
                   page_icon=":material/language:")
# setup logger
# logger level can be set from set_log_level group in the streamlit secrets.toml
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s')
# preferred format for print statements for DEBUG datetime.now().strftime('%Y-%m-%d %H:%M:%S')
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)

# ------------------------------------------------------------------------------
# functions
# ------------------------------------------------------------------------------


def sel_lang_pair():
    """Return selected source and target language."""
    logger.debug("call: sel_lang_pair()")
    # initially pair is fixed to English and French so simply return these
    source_lang = "French"
    target_lang = "English"
    logger.debug(f"return: {source_lang=}, {target_lang=}")
    return source_lang, target_lang


def main():
    """Main program logic for language learner app."""
    logger.debug(f"call: start Lang Learner app {st.user.is_logged_in=} {'='*50}")

    # login
    login()

    if "login_complete" in st.session_state:
        # login complete (user authenticated and nickname set)

        # select source and target language pair
        if "source_language" not in st.session_state and "target_language" not in st.session_state:
            st.session_state.source_language, st.session_state.target_language = sel_lang_pair()
            logger.debug(f"{st.session_state.source_language=}, "
                         f"{st.session_state.target_language=}")

        # define app pages
        # account pages
        change_nickname_page = st.Page(
            change_nickname,
            title="Change Your Nickname", icon=":material/manage_accounts:")
        remove_user_page = st.Page(
            remove_user,
            title="Remove Your User", icon=":material/person_remove:")
        logout_page = st.Page(
            logout,
            title="Log Out", icon=":material/logout:")

        # admin pages
        admin_enter_scores = st.Page(
            "pages/admin_enter_scores.py",
            title="Manual Entry of Scores", icon=":material/build_circle:")
        admin_display_nicknames = st.Page(
            "pages/admin_display_nicknames.py",
            title="Display Nicknames Gsheet", icon=":material/build_circle:")
        admin_display_scores = st.Page(
            "pages/admin_display_scores.py",
            title="Display Scores Gsheet", icon=":material/build_circle:")

        # in-development pages
        gender_match_page = st.Page(
            "pages/gender_match.py",
            title="Gender Match", icon=":material/group:")
        prototype_page = st.Page(
            "pages/prototype.py",
            title="Prototype", icon=":material/group:")

        # mini-app pages
        word_match_page = st.Page(
            "pages/word_match.py",
            title="Word Match", icon=":material/match_word:", default=True)
        scores_page = st.Page(
            "pages/scores.py",
            title="Scores", icon=":material/scoreboard:")

        # configure app pages
        if st.session_state.user_id in st.secrets.admin.admin_user_ids:
            # special page navigation with admin
            pg = st.navigation(
                {
                    "Account": [change_nickname_page, remove_user_page, logout_page],
                    "Admin": [admin_enter_scores, admin_display_nicknames, admin_display_scores],
                    "In-development": [gender_match_page, prototype_page],
                    "Mini-apps": [word_match_page, scores_page]
                }
            )
        else:
            # standard page navigation
            pg = st.navigation(
                {
                    "Account": [change_nickname_page, remove_user_page, logout_page],
                    "Mini-apps": [word_match_page, scores_page]
                }
            )

        # go!
        pg.run()


if __name__ == "__main__":
    main()
