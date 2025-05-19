"""
Module: word_match.py
Description: Contains logic for the Word Match miniapp page.

Outline Design:
- Parse the cleansed language dataframe to obtain the source and target languages and to return a
list of shuffled word pairs; the dataframe is prepared by the data tools
- Initially the target language is English and the source language is French
- The user clicks the start button to start the countdown timer
- Display the time remaining in seconds, together with a count of the hits and misses
- A hit is a successful word match, a miss is an unsuccessful word match
- Make a page slice of the shuffled word pairs for display, a list of words_left (English words) and
words_right (French words) e.g. [man, dog, woman, ...] and [homme, chien, femme, ...]
- Shuffle the words_right and provide a shuffle_map; the shuffle map explains how the words were shuffled
- Take the page slice of word pairs and display them in a grid of buttons, English words
in the left column and the shuffled French words in the right column
- The user selects a pair of words, one from the left column and one from the right
- Only one button can be selected at a time for each column
- The user can select the left word first or the right word first
- By default all the buttons are displayed initially with the button's 'secondary' colour
- A selected button is highlighted with the button's 'primary' colour, or toggled back to the
secondary colour, if selected a second time (or another button in the same column is selected)
- If a button is selected in the left and right columns then check for a word match
- If there is a successful word pair match then disable the pair of buttons, otherwise reset
buttons ready for selection again
- If all pairs are matched on the page then generate a new page of words and repeat
- When the countdown timer reaches zero the matching is complete and all the buttons are disabled
- Finally the user's score is summarised and saved in the scores sheet
- The user is given the option of trying again or jumping to the scores page
- The user can also review their misses

ToDo:
- remove fix_mobile_columns() and its 2 column limitation, also re-introduce display of
miss metric as this requires 3 columns; dependent on streamlit release of Flex layout #10895
https://github.com/streamlit/streamlit/issues/10895

Nice-to-have:
- set a temporary highlight colour or a glow when there is a successful or
unsuccessful word match e.g. green for hit and red for miss
- mis-matched words could be stored and used as a preference for future runs or as part of a
practice app
- give option to report word pair data errors; could be saved to an errors file?

"""
import logging
import os
import pandas as pd
import streamlit as st
import utils.config as config
from dataclasses import dataclass
from random import shuffle
from pathlib import Path
from utils.gsheet_utils import save_score_to_gsheet
from utils.st_countdown import st_countdown
from utils.page_utils import save_page
from utils.gsheet_utils import read_scores_as_df_from_gsheet
from data_tools.data_utils.data_schema import load_report_data_df_from_feather

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)

# define global constants to control dynamic behaviour
COUNTDOWN_FROM = 120  # total seconds to countdown from to match word pairs
COL_TOT = 2  # total number of columns, 2 columns for display of word pairs
ROW_TOT = 5  # total number of rows (word pairs) per page
LEFT = 0  # left column has index=0
RIGHT = 1  # right column has index=1
ICON_HIT = "🟢"  # indicates a correct word pair match (hit)
ICON_MISS = "🔴"  # indicates an incorrect word pair match (miss)
MINIAPP_WORD_MATCH = "word_match"  # name of this miniapp in Scores Google sheet
MAX_WORD_LEN_FOR_MOBILE = 14  # max word length for mobile to avoid button wrap on small displays
DEBUG_SHOW_STATS = False  # True if progress stats should not be shown (normal is False)
DEBUG_NO_LOG_SCORES = False  # True if scores should not be logged to scores google sheet (normal is False)
DEBUG_NO_COUNTDOWN = False  # True if countdown is not to run (normal is False)
DEBUG_NO_COUNTDOWN_PAGE_LIMIT = 2  # Stop word match at this page limit, if DEBUG_NO_COUNTDOWN is True

# define html strings to hide and restore Streamlit's status info (running man)
# ref: https://discuss.streamlit.io/t/remove-hide-running-man-animation-on-top-of-page/21773/3
HIDE_STREAMLIT_STATUS = """
    <style>
        div[data-testid="stStatusWidget"] {
        visibility: hidden;
        
        height: 0%;
        position: fixed;
    }
    </style>
"""
RESTORE_STREAMLIT_STATUS = """
    <style>
        div[data-testid="stStatusWidget"] {
        visibility: visible;
        height: 0%;
        position: fixed;
    }
    </style>
"""

# ------------------------------------------------------------------------------
# classes
# ------------------------------------------------------------------------------


@dataclass
class ClickedButton:
    """Clicked Button of pair.

    If button is on left col == LEFT
    If button is on right col == RIGHT

    First clicked button on left has row=LEFT, col=LEFT
    Last clicked button on right has row=ROW_TOT-1, col=RIGHT

    The words always contains ROW_TOT words.
    For the LEFT column the value is the same as words[words_index] and row==words_index.
    For the RIGHT column the value is the same as words[words_index].

    Examples, for a page of 6 rows, for a pair of matching buttons:
    b2 = ClickedButton(val="girl", row=3, col=LEFT,
                       words=["man", "woman", "girl", "cat", "dog", "boy"])
    b1 = ClickedButton(val="fille", row=0, col=RIGHT,
                       words=["fille", "homme", "garçon", "femme", "chat", "chien"])
    ClickedButton(b2, b1) returns True
    """
    val: str  # button value
    row: int  # button row position (0 to ROW_TOT-1)
    col: int  # button column position (0 or 1 for a button pair)
    words: list  # list of original unshuffled button words for the page column
    words_index: int  # index of this word in the original unshuffled list of words

    def __post_init__(self):
        """Carry out integrity checks and derive key data."""
        # check rows and columns and derive is_on_left and is_on_right
        if self.col not in [0, 1]:
            raise ValueError("Invalid value for 'col'. Expected 0 or 1.")
        if self.row not in range(ROW_TOT):
            raise ValueError(f"Invalid value for 'row'. Expected value from 0 to {ROW_TOT-1}")
        self.is_on_left = True if self.col == LEFT else False  # True if button is on left
        self.is_on_right = True if self.col == RIGHT else False  # True if button is on right

        # check words
        if len(self.words) != ROW_TOT:
            raise ValueError(f"There should be ROW_TOT '{ROW_TOT}' items in the words list: {self.words}")
        if self.words[self.words_index] != self.val:
            raise ValueError(f"The button value '{self.val}' should be the words_index "
                             f"item '{self.words_index}' in the column words list: {self.words}")
        if self.is_on_left and self.row != self.words_index:
            raise ValueError(f"The left words are not shuffled, so the row value should equal the "
                             f"words_index value, here row={self.row} and words_index={self.words_index}")

    def toggle_button_colour(self):
        """Toggle highlight colour (primary or secondary) on selected button."""
        logger.debug(f"call: ClickedButton: toggle_button_colour({self.row=}, {self.col=})")
        st.session_state.btn_colour[(self.row, self.col)] = 'secondary' \
            if st.session_state.btn_colour[(self.row, self.col)] == 'primary' \
            else 'primary'

    def toggle_button_disable(self):
        """Toggle disable state (True or False) on selected button."""
        logger.debug(f"call: toggle_button_disable({self.row=}, {self.col=})")
        st.session_state.btn_disabled[(self.row, self.col)] = \
            not st.session_state.btn_disabled[(self.row, self.col)]

    def check_word_match(self, button2):
        """Return True if left word value matches the original unshuffled right word value."""
        button1 = self
        logger.debug(f"call: check_word_match({button1=}, {button2=})")

        # find which button is on the left
        assert button1.is_on_left or button2.is_on_left, "unexpected error, neither buttons on left!"
        if button1.is_on_left:
            # button1 is on left
            logger.debug("button1 is left word")
            left_btn = button1
            right_btn = button2
        else:
            # button2 is left
            logger.debug("button2 is left word")
            left_btn = button2
            right_btn = button1

        logger.debug(f"target_language (left columns words): "
                     f"{left_btn.words=}, {left_btn.words_index=}")
        logger.debug(f"source_language (right columns words): "
                     f"{right_btn.words=}, {left_btn.words_index=}")

        # check for word match, for a match the left button's words_index should
        # equal the right button's words_index should
        is_word_match = left_btn.words_index == right_btn.words_index

        logger.debug(f"return: {is_word_match=}, "
                     f"logic, True if: {left_btn.words_index=} == {right_btn.words_index=}")
        return is_word_match

    def get_correct_words_for_miss(self, button2):
        """Return dictionary of correct words for given buttons.

        Returns:
        miss_dict = {
            'miss_lword': <miss_lword>, 'miss_rword': <miss_rword>,
            'correct_lword': <correct_lword>, 'correct_rword': <correct_rword>
            }

        So the correct matching pairs as tuples are:
            (<miss_lword>, <correct_rword>)
            (<correct_lword>, <miss_rword>)
        """
        button1 = self
        logger.debug(f"call: get_correct_words_for_miss({button1=}, {button2=})")

        # find which button is on the left
        assert button1.is_on_left or button2.is_on_left, "unexpected error, neither buttons on left!"
        if button1.is_on_left:
            # button1 is on left
            logger.debug("button1 is left word")
            left_btn = button1
            right_btn = button2
        else:
            # button2 is left
            logger.debug("button2 is left word")
            left_btn = button2
            right_btn = button1

        # lookup correct words
        correct_rword = right_btn.words[left_btn.words_index]
        correct_lword = left_btn.words[right_btn.words_index]

        # prepare dictionary
        miss_dict = {
            'miss_lword': left_btn.val, 'miss_rword': right_btn.val,
            'correct_lword': correct_lword, 'correct_rword': correct_rword
            }

        logger.debug(f"return: {miss_dict=}")
        return miss_dict

# ------------------------------------------------------------------------------
# functions
# ------------------------------------------------------------------------------


def get_shuffled_word_pairs(source_language, target_language, max_word_len=None):
    """Return shuffled word pairs as list of lists for the given source and target languages.
    Inputs:
    source_language: str, source language e.g. French
    target_language: str, target language e.g. English
    max_word_len: int, maximum word length for returned word pairs (optional)

    Return:
    word_pairs: list, shuffled list of lists, with each inner list containing a matching pair of
    words [word_target, word_source] e.g.
        word_pairs = [['man', 'homme', ['woman', 'femme'], ...]
    """
    logger.debug(f"call: get_shuffled_word_pairs({source_language=}, {target_language=}, {max_word_len=})")

    # load the French English all words translation report feather file into a pandas dataframe
    word_match_all_words_file = config.lang_pair_to_all_words[(source_language, target_language)]
    logger.debug(f"{word_match_all_words_file=}")
    dfrpt_all = load_report_data_df_from_feather(word_match_all_words_file)

    # create a shuffled list of target words mapped to source words,
    # the target language (e.g. English) is left, source language (e.g. French) is right

    # determine if any restrictions on word length
    if not max_word_len:
        # no restriction
        max_word_len = float('inf')  # set to infinity i.e. allow all values

    # select nouns
    word_pairs_nouns_list = dfrpt_all[(
        (dfrpt_all['is_source_noun'] == True) & (dfrpt_all['is_ok_to_display'] == True) &
        ((dfrpt_all.source_noun.str.len() <= max_word_len) &
         (dfrpt_all.target_phrase_short.str.len() <= max_word_len))
        )][['target_phrase_short', 'source_noun']].sample(frac=1).values.tolist()
    # select others
    word_pairs_others_list = dfrpt_all[(
        (dfrpt_all['is_source_noun'] == False) & (dfrpt_all['is_ok_to_display'] == True) &
        ((dfrpt_all.source_phrase.str.len() <= max_word_len) &
         (dfrpt_all.target_phrase_short.str.len() <= max_word_len))
        )][['target_phrase_short', 'source_phrase']].sample(frac=1).values.tolist()
    # combine nouns and others
    word_pairs = word_pairs_nouns_list + word_pairs_others_list

    # shuffle in place
    shuffle(word_pairs)

    logger.debug(f"return: shuffled word_pairs from df, total of {len(word_pairs)} pairs loaded")
    lt = max((t for t, _s in word_pairs), key=len)
    ls = max((s for _t, s in word_pairs), key=len)
    logger.debug(f"longest target is '{lt}', length={len(lt)}")
    logger.debug(f"longest source is '{ls}', length={len(ls)}")
    # logger.debug(f"return: First 36 word pairs\n: {word_pairs[0:36]=}")
    return word_pairs


@st.cache_data  # cached, run when pg_start_index changes
def get_page_of_word_pairs(word_pairs, pg_start_index, pg_words_tot):
    """Return a page slice of size pg_words_tot of the word_pairs starting at pg_start_index.

    Inputs:
    word_pairs: list, list of lists with inner list containing matched pair of
    [target word, source_word]
    pg_start_index: int, the index from which to start the page slice in the word lists
    pg_words_tot: int, the number of words in the page slice

    Returns:
    lwords_page: list, page slice of lwords
    rwords_page: list, page slice of rwords
    rwords_page_shuffled: list, shuffled rwords_page
    page_indices_shuffled: list, shuffled page indices in range(pg_words_tot) (as used to
    shuffle the rwords_page)
    """
    logger.debug(f"call: get_page_of_word_pairs("
                 f"{word_pairs[0:36]=}, {pg_start_index=}, {pg_words_tot=})")

    # split word_pairs into a list of lwords (left words, corresponding to target)
    # and a list of rwords (right words, corresponding to source)
    lwords, rwords = zip(*word_pairs)

    # take a page slice of those lists
    lwords_page = lwords[pg_start_index:pg_start_index + pg_words_tot]
    rwords_page = rwords[pg_start_index:pg_start_index + pg_words_tot]

    # shuffle the rwords_page slice
    page_indices_shuffled = list(range(pg_words_tot))
    shuffle(page_indices_shuffled)
    rwords_page_shuffled = [rwords_page[idx] for idx in page_indices_shuffled]

    logger.debug(f"return: {lwords_page=}, {rwords_page=}, "
                 f"{rwords_page_shuffled=}, {page_indices_shuffled=}")
    return lwords_page, rwords_page, rwords_page_shuffled, page_indices_shuffled


def disable_buttons():
    """Set the disable state of all buttons in the grid to True."""
    logger.debug("call: disable_buttons()")
    for row in range(ROW_TOT):
        for col in range(COL_TOT):
            st.session_state.btn_disabled[(row, col)] = True


def reset_buttons():
    """Reset the session state of all buttons in the grid."""
    logger.debug("call: reset_buttons()")
    # reset the currently selected buttons
    st.session_state.btn_value = None
    st.session_state.btn_row = None
    st.session_state.btn_col = None
    st.session_state.btn_count = 0
    st.session_state.btn1 = None
    st.session_state.btn2 = None

    # reset the default colour of all buttons in the grid
    for row in range(ROW_TOT):
        for col in range(COL_TOT):
            st.session_state.btn_colour[(row, col)] = 'secondary'

    # reset the default disabled stae of all buttons in the grid
    for row in range(ROW_TOT):
        for col in range(COL_TOT):
            st.session_state.btn_disabled[(row, col)] = False


def reset_session_state():
    """Reset the session state variables for the application.

    # Note that this excludes st.session_state.session_page_number.
    """
    logger.debug("call: reset_session_state()")
    # reset general state variables
    st.session_state.started = False
    st.session_state.word_pair_matches_per_page = 0
    st.session_state.word_pair_match = 0
    st.session_state.word_pair_mismatch = 0
    st.session_state.page_number = 0
    st.session_state.buttons_disabled = False
    st.session_state.scores_logged = False
    st.session_state.countdown_from = COUNTDOWN_FROM
    st.session_state.miss_list = []
    st.session_state.high_score_checked = False

    # reset button state variables
    reset_buttons()


def initialise_session_state():
    """Initialise the session state variables for the application."""
    logger.debug("call: initialise_session_state()")
    # initialise general state variables
    if 'started' not in st.session_state:
        logger.debug("First run - started not in session state, st.session_state.started set to False")
        st.session_state.started = False  # True when user has clicked start button
    if 'word_pair_matches_per_page' not in st.session_state:
        st.session_state.word_pair_matches_per_page = 0  # successful matches for current page run
    if 'word_pair_match' not in st.session_state:
        st.session_state.word_pair_match = 0  # total word pair matches (hits) per run
    if 'word_pair_mismatch' not in st.session_state:
        st.session_state.word_pair_mismatch = 0  # total word pair mis-matches (misses) per run
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 0  # page number in this mini-app run
    # if 'session_page_number' not in st.session_state:
    #     st.session_state.session_page_number = 0  # page number in this session (all mini-app runs)
    if 'buttons_disabled' not in st.session_state:
        st.session_state.buttons_disabled = False  # True if all buttons disabled
    if 'scores_logged' not in st.session_state:
        st.session_state.scores_logged = False  # True if scores logged
    if 'countdown_from' not in st.session_state:
        st.session_state.countdown_from = COUNTDOWN_FROM  # value of countdown in current run
    if 'miss_list' not in st.session_state:
        st.session_state.miss_list = []  # list of dictionaries of misses and correct word matches
    if 'high_score_checked' not in st.session_state:
        st.session_state.high_score_checked = False  # True if high score checked

    # initialise button session state variables
    if 'btn_value' not in st.session_state:
        st.session_state.btn_value = None  # selected button value
    if 'btn_row' not in st.session_state:
        st.session_state.btn_row = None  # selected button row in grid
    if 'btn_col' not in st.session_state:
        st.session_state.btn_col = None  # selected button column in grid
    if 'btn_count' not in st.session_state:
        st.session_state.btn_count = 0  # total count of buttons selected, has value 0, 1 or 2
    if 'btn1' not in st.session_state:
        st.session_state.btn1 = None  # identifies first button selected of pair
    if 'btn2' not in st.session_state:
        st.session_state.btn2 = None  # identifies second button selected of pair
    if 'btn_colour' not in st.session_state:
        st.session_state.btn_colour = {}
        # initialise the default colour of all buttons in the grid
        for row in range(ROW_TOT):
            for col in range(COL_TOT):
                # set initial colour (type) to 'secondary'
                st.session_state.btn_colour[(row, col)] = 'secondary'  # defines colour (type) of button
    if 'btn_disabled' not in st.session_state:
        st.session_state.btn_disabled = {}
        # initialise the default disabled state of all buttons in the grid
        for row in range(ROW_TOT):
            for col in range(COL_TOT):
                # set initial disabled state to False, thereby allowing button to be selected
                st.session_state.btn_disabled[(row, col)] = False  # defines disabled state of button


def on_select(btn_value, btn_row, btn_col, btn_words, btn_words_index):
    """Button on_click callback: check for word match and manage button state."""
    logger.debug(f"call: on_select({btn_value=}, {btn_row=}, {btn_col=}, {btn_words=}, {btn_words_index=})")
    st.session_state.btn_value = btn_value  # for progress reporting
    st.session_state.btn_row = btn_row  # for progress reporting
    st.session_state.btn_col = btn_col  # for progress reporting

    if st.session_state.btn_count == 0:
        # first button, instantiate button1 and set colour
        st.session_state.btn1 = ClickedButton(val=btn_value, row=btn_row, col=btn_col,
                                              words=btn_words, words_index=btn_words_index)
        st.session_state.btn1.toggle_button_colour()
        st.session_state.btn_count = 1
    elif st.session_state.btn_count == 1:
        # second button
        if btn_col == st.session_state.btn1.col and btn_row == st.session_state.btn1.row:
            # same as button1! toggle button 1 and reset button counter
            st.session_state.btn1.toggle_button_colour()
            st.session_state.btn_count = 0
        elif btn_col == st.session_state.btn1.col:
            # same column, replace button1
            st.session_state.btn1.toggle_button_colour()
            st.session_state.btn1 = ClickedButton(val=btn_value, row=btn_row, col=btn_col,
                                                  words=btn_words, words_index=btn_words_index)
            st.session_state.btn1.toggle_button_colour()
        else:
            # different column, instantiate button2
            st.session_state.btn2 = ClickedButton(val=btn_value, row=btn_row, col=btn_col,
                                                  words=btn_words, words_index=btn_words_index)
            st.session_state.btn2.toggle_button_colour()

            # check two buttons for word match
            if ClickedButton.check_word_match(st.session_state.btn1, st.session_state.btn2):
                # match

                # toggle both buttons off
                st.session_state.btn1.toggle_button_colour()
                st.session_state.btn2.toggle_button_colour()

                # disable buttons
                st.session_state.btn1.toggle_button_disable()
                st.session_state.btn2.toggle_button_disable()

                st.session_state.word_pair_match += 1
                st.session_state.word_pair_matches_per_page +=1
                st.session_state.btn_count = 0
                st.toast("Hit", icon=ICON_HIT)  # alt: icon=":material/thumb_up:"
            else:
                # mis-match

                # get the miss dictionary and save
                miss_dict = ClickedButton.get_correct_words_for_miss(st.session_state.btn1, st.session_state.btn2)
                st.session_state.miss_list.append(miss_dict)

                # toggle buttons off
                st.session_state.btn1.toggle_button_colour()
                st.session_state.btn2.toggle_button_colour()

                st.session_state.word_pair_mismatch += 1
                st.session_state.btn_count = 0
                st.toast("Miss", icon=ICON_MISS)


def friendly_secs(total_seconds):
    """Return friendly phrase giving minutes and seconds for given total_seconds."""
    logger.debug(f"call: friendly_secs({total_seconds=})")
    minutes, seconds = divmod(total_seconds, 60)

    min_phrase = 'minute' if minutes == 1 else 'minutes'
    sec_phrase = 'second' if seconds == 1 else 'seconds'

    if minutes == 0:
        friendly_phrase = f"{seconds} {sec_phrase}"
    elif seconds == 0:
        friendly_phrase = f"{minutes} {min_phrase}"
    else:
        friendly_phrase = f"{minutes} {min_phrase} and {seconds} {sec_phrase}"

    return friendly_phrase


def highlight_cols(_s):
    """Return a selected background colour.

    Highlight using Streamlit's backgound colour for row selection in light mode.
    """
    return "background-color: rgba(251,233,234,255); color: black;"


def display_misses(source_lang, target_lang, word_pair_mismatch, miss_list):
    """Display miss_list containing word_pair_mismatch misses.

    Inputs:
    source_lang: str, source language e.g. French
    target_lang: str, target language e.g. English
    word_pair_mismatch: int, number of word pair mismatches (misses)
    miss_list: list, list of miss_dicts

    Example miss_list:
    [{'miss_lword': 'flower', 'miss_rword': 'végane', 'correct_lword': 'vegan', 'correct_rword': 'fleur'}
    ...]
    where 'miss_lword' is the miss-matched left word (target language) of the word pair
    and 'correct_lword' is the correctly translated left word when paired with the miss_rword
    """
    logger.debug(f"call: display_misses({source_lang=}, {target_lang=}, {word_pair_mismatch=}, {miss_list=})")

    # summarise the number of mis-matches (misses)
    st.write(f"You have {word_pair_mismatch} mis-matched {target_lang} and {source_lang} word "
             f"pairs, :red-background[highlighted] in the table below.")

    # create a dataframe of misses
    df_misses = pd.DataFrame(miss_list)

    # generate a deduped dataframe with count of duplicates and repeats
    # ref: https://stackoverflow.com/questions/35584085/how-to-count-duplicate-rows-in-pandas-dataframe
    is_repeats = False
    df_miss_deduped = df_misses.groupby(df_misses.columns.tolist()) \
        .size().reset_index().rename(columns={0: 'dup_count'})
    df_miss_deduped['Repeat_count'] = df_miss_deduped['dup_count'] - 1
    tot_dups = df_miss_deduped['dup_count'].sum() - df_miss_deduped.shape[0]
    tot_repeats = df_miss_deduped['Repeat_count'].sum()
    if tot_repeats > 0:
        is_repeats = True
    logger.debug(f"{tot_dups=}, {tot_repeats=}, {is_repeats=}")

    # summarise the number of repeats, if any, and prepare the selected dataframe
    if is_repeats:
        # are repeats, add count of repeats to the dataframe
        st.write(f"You made {tot_repeats} repeated mis-matches, that is words pairs that "
                 f"you mis-matched more than once. These repeats are also shown in the table.")
        sel_cols = df_miss_deduped.columns.tolist()
        sel_cols.remove('dup_count')
        df_sel = df_miss_deduped[sel_cols].rename(columns={'Repeat_count': 'Repeat count'})
    else:
        # no repeats, so use the misses dataframe unchanged
        df_sel = df_misses

    # tell the user that the dataframe will be active i.e. user can select a row for more info
    st.write("You can select a row to see more information by clicking in the left-most column.")

    # prepare dataframe for display
    # rename columns to make them more user-friendly and descriptive
    df_misses_display = df_sel.rename(columns={
        'miss_lword': f'Your Mis-matched {target_lang} word',
        'miss_rword': f'Your Mis-matched {source_lang} word',
        'correct_lword': f'Correct {target_lang} match for the {source_lang} word',
        'correct_rword': f'Correct {source_lang} match for the {target_lang} word'})
    # logger.debug(f"df_misses_display:\n {df_misses_display.to_string()}")

    # highlight the miss columns using the pandas styler
    df_misses_styled = df_misses_display.style.map(
        highlight_cols,
        subset=pd.IndexSlice[:, [f'Your Mis-matched {target_lang} word', f'Your Mis-matched {source_lang} word']])

    # allow single row selection
    # selected row will be returned in event.selection
    event = st.dataframe(
        df_misses_styled,
        key="data",
        on_select="rerun",
        selection_mode=["single-row"],
        hide_index=True
    )

    # if row selected show additional info
    if event.selection["rows"]:
        selected_row = event.selection['rows'][0]
        sel_miss_lword = df_misses_display.iloc[[selected_row]] \
            [f'Your Mis-matched {target_lang} word'].values[0]
        sel_miss_rword = df_misses_display.iloc[[selected_row]] \
            [f'Your Mis-matched {source_lang} word'].values[0]
        sel_correct_lword = df_misses_display.iloc[[selected_row]] \
            [f'Correct {target_lang} match for the {source_lang} word'].values[0]
        sel_correct_rword = df_misses_display.iloc[[selected_row]] \
            [f'Correct {source_lang} match for the {target_lang} word'].values[0]
        logger.debug(f"selected row info: {sel_miss_lword=}, {sel_miss_rword=}, "
                     f"{sel_correct_lword=}, {sel_correct_rword=}")
        if is_repeats:
            sel_match_repeat_count = df_misses_display.iloc[[selected_row]]['Repeat count'].values[0]
            logger.debug(f"selected row info: {is_repeats=}, {sel_match_repeat_count=}")
        else:
            sel_match_repeat_count = None

        # show additional info about the mis-match and the corrections
        st.write(
            f"You incorrectly matched the {target_lang} word (or phrase) '{sel_miss_lword}' "
            f"with the {source_lang} word (or phrase) '{sel_miss_rword}'.")
        if is_repeats and sel_match_repeat_count:
            if sel_match_repeat_count == 1:
                repeat_str = "once"
            elif sel_match_repeat_count == 2:
                repeat_str = "twice"
            else:
                repeat_str = f"{sel_match_repeat_count} times"
            st.write(f"You repeated this mis-match {repeat_str}.")
        st.write(
            f"The correct match for the {target_lang} word '{sel_miss_lword}' is "
            f"the {source_lang} word '{sel_correct_rword}'.")
        st.write(
            f"And the correct match for the {source_lang} word '{sel_miss_rword}' is "
            f"the {target_lang} word '{sel_correct_lword}'.")


def get_high_score(user_id, miniapp):
    """Return the user's best scores for the given miniapp.

    Inputs:
    user_id: str, user's id e.g. joebloggs@misc.com
    miniapp: str, miniapp name e.g. word_match

    Return:
    high_score: int, user's high score in miniapp; if no entry for user and miniapp then set to None
    """
    logger.debug(f"call: get_high_score({user_id=}, {miniapp=})")

    # read the scores data into a dataframe
    df_scores = read_scores_as_df_from_gsheet()

    # get the user's best score
    if [user_id, miniapp] in df_scores[(df_scores.User_id == user_id) &
                                       (df_scores.Miniapp == miniapp)]\
            [['User_id', 'Miniapp']].values.tolist():
        high_score = df_scores[(df_scores.User_id == user_id) &
                               (df_scores.Miniapp == miniapp)].Score.max()
    else:
        high_score = None

    logger.debug(f"return: {high_score=}")
    return high_score


def fix_mobile_columns():
    """ define two flex columns for mobile
    https://github.com/streamlit/streamlit/issues/6592

    Limitations:
    - Note that this changes style of all columns thereby restricting display to 2 columns
    - ToDo: remove use of function when streamlit release support for Flex layout #10895
    """
    logger.debug(f"call: fix_mobile_columns()")
    st.write('''<style>
    [data-testid="stColumn"] {
        width: calc(50.0% - 1rem) !important;
        flex: 1 1 calc(50.0% - 1rem) !important;
        min-width: calc(50.0% - 1rem) !important;
    }
    </style>''', unsafe_allow_html=True)


def main():
    """Main for word pair match."""
    logger.debug(f"call: start Word Match mini-app {'-'*50}")

    # set the source and target languages
    source_language = st.session_state.source_language
    target_language = st.session_state.target_language

    # get the list of all the word pairs, shuffled, for the selected source and target language
    if "word_pairs_shuffled" not in st.session_state:
        st.session_state.word_pairs_shuffled = get_shuffled_word_pairs(
            source_language, target_language, max_word_len=MAX_WORD_LEN_FOR_MOBILE)

    # get user's high score for word match
    if "high_score" not in st.session_state:
        st.session_state.high_score = get_high_score(
            user_id=st.session_state.user_id, miniapp=MINIAPP_WORD_MATCH)

    # initialise the page number in this session (and all miniapp runs)
    if "session_page_number" not in st.session_state:
        st.session_state.session_page_number = 0

    # initialise other session state variables
    initialise_session_state()

    # save current page and check the calling page
    calling_page = save_page('word_match')
    if calling_page and calling_page != "word_match":
        # called from other page so reset session_state
        logger.debug("calling page not this page, reset session state and increase page number")
        reset_session_state()
        # increase session_page_number to ensure next set of words is presented
        st.session_state.session_page_number += 1

    # wait until the user clicks the start button
    if not st.session_state.started:
        # show subheader
        st.subheader(f"Match the {target_language} and {source_language} words")

        # not started, warn the user about the countdown
        if not DEBUG_NO_COUNTDOWN:
            st.warning(f"You have {friendly_secs(COUNTDOWN_FROM)} from the button click, good luck!",
                       icon=":material/warning:")
            if st.session_state.high_score is not None:
                st.info(f"Your Word Match high score is {st.session_state.high_score}", icon=":material/info:")
            button_start_label = "Click to start the countdown timer"
        else:
            # countdown disabled (debug mode)
            st.write(f"No timer, word match will stop after {DEBUG_NO_COUNTDOWN_PAGE_LIMIT} pages (debug mode)")
            if st.session_state.high_score is not None:
                st.info(f"Your Word Match high score is {st.session_state.high_score}", icon=":material/info:")
            button_start_label = "Click to start (debug mode)"

        logger.debug("wait for start button!")
        if st.button(button_start_label, icon=":material/timer:",):
            # start!
            logger.debug("start button clicked, session started!")
            st.session_state.started = True
            st.rerun()

    if st.session_state.started:
        # display progress

        # prepare columns to display progress
        # the metrics will be in cols 1 and 2; the countdown timer will be in col4
        # disable display of 3 cols because of streamlit mobile display limitations
        # ToDo: restore miss metric in col3 when flex layout available
        # col1, col2, col3 = st.columns(3, vertical_alignment="bottom")
        col1, col2 = st.columns(2, vertical_alignment="bottom")
        fix_mobile_columns()  # ToDo: remove, note that this mobile fix limits all st.columns to 2
        with col1:
            # run the st_countdown timer and read the seconds remaining

            # hide the running man as this can be distracting when updated every countdown tick
            st.markdown(HIDE_STREAMLIT_STATUS, unsafe_allow_html=True)

            # set the start value for the countdown and run
            if not DEBUG_NO_COUNTDOWN:
                # run the countdown timer
                seconds_remaining = st_countdown(st.session_state.countdown_from)
            else:
                # countdown timer disabled (debug mode)
                seconds_remaining = 10000  # set an arbirary high number
        with col2:
            # display hit metric
            st.metric(label=ICON_HIT+"Hit", value=st.session_state.word_pair_match)
        # disable display of miss metric in col3 as 3 cols disabled because of streamlit mobile display limitations
        # ToDo: restore miss metric in col3 when flex layout available
        # with col3:
        #     # display miss metric
        #     st.metric(label=ICON_MISS+"Miss", value=st.session_state.word_pair_mismatch)

        logger.debug(f"progress metrics: {seconds_remaining=}, {st.session_state.word_pair_match=}, "
                     f"{st.session_state.word_pair_mismatch=}")

        # define word index start (start position for next set of word pairs)
        words_index_start = st.session_state.session_page_number * ROW_TOT
        logger.debug(f"{st.session_state.session_page_number=}, {words_index_start=}")

        # get a page slice (of size ROW_TOT) of left and right words, and a shuffle of those right words
        # the right words are shuffled using the page_indices_shuffled map
        words_left_page, words_right_page, words_right_page_shuffled, page_indices_shuffled = (
            get_page_of_word_pairs(word_pairs=st.session_state.word_pairs_shuffled,
                                   pg_start_index=words_index_start,
                                   pg_words_tot=ROW_TOT))
        logger.debug(f"{words_left_page=}")
        logger.debug(f"{words_right_page=}")
        logger.debug(f"{words_right_page_shuffled=}")
        logger.debug(f"{page_indices_shuffled=}")

        # dynamically generate the button grid of word pairs to match and wait
        # the user to select a word pair
        btn_left, btn_right = st.columns(COL_TOT, gap="small", vertical_alignment="bottom")
        logger.debug("display buttons and wait for user input...")
        for row in range(ROW_TOT):
            # logger.debug(f"main for loop: {row=}, {st.session_state.page_number=}")

            # generate a pair of left and right buttons for each row
            # the button's 'on_click' callback function handles the matching logic
            btn_left.button(
                words_left_page[row],
                use_container_width=True,
                key=f'key_{row},{LEFT}',
                on_click=on_select,
                args=[words_left_page[row], row, LEFT,
                      words_left_page, row],
                type=st.session_state.btn_colour[(row, LEFT)],
                disabled=st.session_state.btn_disabled[(row, LEFT)])
            btn_right.button(
                words_right_page_shuffled[row],
                use_container_width=True, key=f'key_{row},{RIGHT}',
                on_click=on_select,
                args=[words_right_page_shuffled[row], row, RIGHT,
                      words_right_page, page_indices_shuffled[row]],
                type=st.session_state.btn_colour[(row, RIGHT)],
                disabled=st.session_state.btn_disabled[(row, RIGHT)])

        if DEBUG_SHOW_STATS:
            # show progress stats on screen (debug mode)
            info_progress = (
                f"seconds remaining: {seconds_remaining}, "
                f"page number: {st.session_state.page_number}, "
                f"session page number: {st.session_state.session_page_number}, "
                f"word index start: {words_index_start}, "
                f"word matches per page: {st.session_state.word_pair_matches_per_page}, "
                f"total word pair mis-matches: {st.session_state.word_pair_mismatch}, "
                f"miss list: {st.session_state.miss_list}, "
                f"DEBUG flags: {DEBUG_NO_LOG_SCORES=}, {DEBUG_NO_COUNTDOWN=}, {DEBUG_NO_COUNTDOWN_PAGE_LIMIT=}")
            st.info(info_progress)
            if st.session_state.btn_value:
                # button selected, show value and position
                info_sel_button = (
                    f"selected button value: {st.session_state.btn_value}, "
                    f"button position: ({st.session_state.btn_row}, {st.session_state.btn_col})")
                st.sidebar.info(info_sel_button)

        # check if countdown complete
        if (not DEBUG_NO_COUNTDOWN and seconds_remaining > 0) or \
                (DEBUG_NO_COUNTDOWN and (st.session_state.page_number != DEBUG_NO_COUNTDOWN_PAGE_LIMIT)):
            # countdown still in progress, check page status
            if st.session_state.word_pair_matches_per_page == ROW_TOT:
                # all word pair matches complete for this page, get next page
                logger.debug("all word pair matches complete for this page, "
                             "{st.session_state.word_pair_matches_per_page=}, {ROW_TOT=}")
                st.session_state.word_pair_matches_per_page = 0
                st.session_state.page_number += 1
                reset_buttons()
                # increase session_page_number to ensure next set of words is presented
                st.session_state.session_page_number += 1
                st.rerun()
        else:
            # countdown complete
            logger.debug(f"countdown complete, {st.session_state.page_number=}, "
                         f"{st.session_state.session_page_number=}")
            # restore the running man!
            st.markdown(RESTORE_STREAMLIT_STATUS, unsafe_allow_html=True)

            # disable all buttons to prevent further user input
            if not st.session_state.buttons_disabled:
                disable_buttons()
                st.session_state.buttons_disabled = True
                st.rerun()

            # notify the user of completion
            st.info(f"Word match complete! You scored {st.session_state.word_pair_match} hits and "
                    f"{st.session_state.word_pair_mismatch} misses", icon=":material/info:")
            logger.debug(f"Word match complete! {st.session_state.word_pair_match=}, "
                         f"{st.session_state.word_pair_mismatch=}, {st.session_state.high_score=}")
            # check high score
            if not st.session_state.high_score_checked:
                if st.session_state.high_score is None:
                    # no score saved yet, so this becomes high score
                    st.session_state.high_score = st.session_state.word_pair_match
                    logger.debug("high score is None,so high score updated with new score")
                elif st.session_state.word_pair_match == st.session_state.high_score:
                    st.info("You equaled your Word Match high score!", icon=":material/star_half:")
                    logger.debug("You equaled your Word Match high score!")
                elif st.session_state.word_pair_match > st.session_state.high_score:
                    st.info("You achieved a new Word Match high score! Check the *Scores* page "
                            "to see your position in the table",
                            icon=":material/star:")
                    st.session_state.high_score = st.session_state.word_pair_match
                    logger.debug("You equaled your Word Match high score! (high score updated with new score)")
                st.session_state.high_score_checked = True

            # log the number of word pair matches (hits) to scores
            if not DEBUG_NO_LOG_SCORES and not st.session_state.scores_logged:
                this_score = st.session_state.word_pair_match
                this_miniapp = os.path.basename(__file__).split(".")[0]
                this_user_id = st.session_state.user_id
                this_timestamp = pd.Timestamp.now().floor('s')  # timestamp (current tz) with floored seconds

                # submit the score
                try:
                    logger.debug(f"Write record to Scores gsheet: "
                                 f"{this_user_id=}, {this_miniapp=}, {this_score=}, {this_timestamp=}")
                    save_score_to_gsheet(this_user_id, this_miniapp, this_score, this_timestamp)
                    logger.debug("Scores successfully updated")
                    st.sidebar.info("Scores successfully updated", icon=":material/database:")
                    st.session_state.scores_logged = True
                except ValueError:
                    logger.error("ValueError caught: this record already exists in the scores")
                    st.error("unexpected error: this record already exists in the scores")
                    st.stop()

            # give the user the option to try again or see the latest scores
            opt_col1, opt_col2 = st.columns(2, gap="small", vertical_alignment="bottom")
            with opt_col1:
                if st.button('Click to try again!', icon=":material/replay:"):
                    # start again
                    logger.debug("user selected 'Click to try again!'")
                    reset_session_state()
                    # increase session_page_number to ensure next set of words is presented
                    st.session_state.session_page_number += 1
                    st.rerun()  # make it happen!

            with opt_col2:
                if st.button("Click to see scores", icon=":material/scoreboard:"):
                    # go to scores
                    logger.debug("user selected 'Click to see scores'")
                    st.switch_page("lang_learner_pages/scores.py")

            # give the user the option to review misses (if any)
            if st.session_state.word_pair_mismatch > 0:
                # user has misses
                if st.toggle(f"{ICON_MISS} Review your misses"):
                    # display the misses
                    logger.debug("user activated toggle switch 'Review your misses'")
                    display_misses(source_lang=source_language,
                                   target_lang=target_language,
                                   word_pair_mismatch=st.session_state.word_pair_mismatch,
                                   miss_list=st.session_state.miss_list)


if __name__ == "__main__":
    main()
