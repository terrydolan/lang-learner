"""
Script: convert_lang_csv_to_df.py

Converts a CSV file of language pairs into a Pandas dataframe.

This script focuses on the data ingestion and structuring phase of the
language processing pipeline.

The CSV file is a simple text file with the source language phrase separated from
the target language phrase with a ':'. The header marker '>' at the top of file
defines the langauges. If the word is a noun it contains the gender in between
brackets: (m) for a masculine word and (f) for a feminine word. The target phrase
may also contain additional information that explains the word, this is usually
preceded by e.g. or within round brackets. The line may also be terminated with
meta-data inserted by other scripts in the data pipeline e.g. '# ignore translation error'.

The script parses the CSV file and extracts the source and target language
header (defining the source and target languages) and the source and target
phrases and stores the data in the dataframe.

The script then parses the source phrases and derives key data (like the nouns
and their genders) and then stores the dataframe in Feather format for efficient
access and further processing. Duplicates are removed.

The script also includes schema validation to ensure that the created dataframe
conforms to the defined LanguageDataSchema, thereby helping to maintain data integrity
between the different parts of the langauge processing pipeline.

Example CSV:
>French: English
à: to, at, in # ignore translation error
absent, absente: absent
accord (m): agreement
acheter: to buy
addition (f): bill, addition e.g. l’addition et la soustraction: addition and subtraction
adolescent, adolescente, ado: teenager, adolescent
adresse (f): address
âge (m): age
agréable: pleasant
ail (m): garlic
aimable: nice, kind
air (m): look, air, tune e.g. Elle a l’air fatiguée: she looks tired
aire (f): area (e.g. service area near a motorway)
...
"""
import logging
import re
import os
import pandas as pd
import shutil
import unidecode
import data_tools.data_utils.data_config as data_config

from datetime import datetime
from pathlib import Path
from data_tools.data_utils.data_schema import LanguageDataFrameType, validate_language_dataframe_schema

# setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s')
logger.setLevel(logging.WARNING)

# ------------------------------------------------------------------------------
# functions
# ------------------------------------------------------------------------------


def extract_between_brackets(phrase: str):
    """Return what is between round brackets in given phrase."""

    # capture what is between the brackets
    regex_pattern = re.compile(r'.+?\((.*)\)')
    between_brackets = regex_pattern.match(phrase)

    return between_brackets


def extract_noun(source_phrase):
    """Return noun and gender from given source phrase."""
    source_is_noun = False
    source_noun = None
    source_noun_gender = None

    # capture noun and gender using a regex
    regex_gender = re.compile(r'^(?P<source_noun>.+?)\s*\((?P<source_noun_gender>[mf])\)')
    regex_match_gender = regex_gender.match(source_phrase)

    # extract the noun and gender (if present)
    if regex_match_gender:
        source_is_noun = True
        source_noun = regex_match_gender.group('source_noun')
        source_noun_gender = regex_match_gender.group('source_noun_gender')

    return source_is_noun, source_noun, source_noun_gender


def get_phrase_short(s, comment_marker='#', special_comment='# special comment'):
    """Return tuple with shortened version of s and is_special_comment flag.

    Return short_s, where short_s is s up to the comment_marker, stripped
    of whitespace

    If special_comment string found at end of s then set
    is_special_comment to True, otherwise False

    Assume that special_comment starts with the comment_marker, if not then
    raise assertion error."""
    # print(f"get_phrase_short({s=}, {comment_marker=}, {special_comment})")
    assert special_comment.startswith(comment_marker), (
        f"the special_comment '{special_comment}' should start "
        f"with the comment_marker '{comment_marker}'"
    )

    is_special_comment = False
    if s.find(comment_marker) != -1:
        # print('found comment')
        s_short = s.split(comment_marker)[0].strip()
    else:
        # print('no comment')
        s_short = s

    len_special_comment = len(special_comment)
    if s[-len_special_comment:] == special_comment:
        # print(f"found special comment {special_comment} at end of line")
        is_special_comment = True

    # print(f"ruturn ({s_short=}, {is_special_comment=})")
    return s_short, is_special_comment


def remove_str_in_brackets(s):
    """Remove string(s) in round brackets from s and return updated s.

     Also remove trailing whitespace after brackets removed.

     Return s if no brackets found.
     """
    num_brackets = s.count('(')
    for _i in range(num_brackets, 0, -1):
        s = re.sub(r'\([^()]*\)', '', s).strip()

    return s


def clean(s):
    """Return a clean s, without extraneous information.

    Extraneous information is defined as:
    1. sub-strings between (and including) round brackets '('
    2. sub-strings after (and including) 'e.g'

    Return clean_s, where clean_s is s without the extraneous
    information, stripped of whitespace.

    e.g.
    s = 'basic string (containing extraneous information in brackets) e.g. and with extraneous info in example'
    clean(s) -> 'basic string'
    """
    # remove sub-string(s) between round brackets, including brackets (if any)
    s_clean = remove_str_in_brackets(s)

    # remove sub-strings after and including 'e.g' (if any)
    s_clean = s_clean.split('e.g')[0].strip()

    return s_clean


def remove_diacritic(s):
    """
    Return given string s with diacritics removed.

    E.g.
    remove_diacritic('être') -> 'etre'

    Ref: based on https://realpython.com/python-sort-unicode-strings/
    """
    return unidecode.unidecode(s)


def sort_and_remove_duplicates(df, words_csv, key_comment):
    """Sort and remove duplicates from given dataframe and words_csv."""
    logger.debug(f"started: sort_and_remove_duplicates()")
    # sort dataframe, by ascending source phrase (ignoring diacritics)
    df_sorted = df.sort_values(by=['source_phrase_no_diacritic'], ascending=True)\
        .reset_index(drop=True)

    # check if original dataframe is sorted
    is_original_sorted = all(df.source_phrase_no_diacritic ==
                             df_sorted.source_phrase_no_diacritic)
    logger.debug(f"{is_original_sorted=}")

    # check if original dataframe has duplicates
    duplicated_count = df.duplicated().sum()
    is_original_has_duplicates = False if duplicated_count == 0 else True
    logger.debug(f"{is_original_has_duplicates=}")

    # set-up file information
    # parse words_csv and extract file name and extension and define timestamp
    words_csv_fname, words_csv_fext = os.path.splitext(words_csv)
    timestamp = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")

    # remove duplicates from the dataframe, if any
    if is_original_has_duplicates:
        # save duplicate source_phrase and target_phrase with count to csv
        logger.debug("removing duplicates and saving record")
        df_dups = df_sorted[['source_phrase', 'target_phrase']]
        df_dups = df_dups[df_dups.duplicated()].groupby(df_dups.columns.tolist(),
                                                        as_index=True).size()
        words_csv_dup_marker = "_duplicates"
        words_dups_csv = f"{words_csv_fname}{words_csv_dup_marker}{words_csv_fext}"
        with open(file=words_dups_csv, mode='a', encoding='utf-8') as f:
            file_info = f"# Duplicates from '{words_csv}' written at {timestamp}: \n"
            f.write(file_info)
        df_dups.to_csv(path_or_buf=words_dups_csv, mode='a', header=False)

        # drop the duplicates from the dataframe
        df_sorted = df_sorted.drop_duplicates(ignore_index=True)
        print(f"Removed {duplicated_count} duplicates and "
              f"saved record of duplicated to '{words_dups_csv}'")

    # update original csv if it has duplicates or needs sorting
    if is_original_has_duplicates or (not is_original_sorted):
        logger.debug("update original")
        # determine the update reason
        if is_original_has_duplicates and is_original_sorted:
            update_reason = "remove duplicates"
        elif (not is_original_has_duplicates) and (not is_original_sorted):
            update_reason = "sort"
        elif is_original_has_duplicates and (not is_original_sorted):
            update_reason = "remove duplicates and sort"
        else:
            raise ValueError(f"unexpected update reason, "
                             f"{is_original_has_duplicates=}, {is_original_sorted=}")
        logger.debug(f"{update_reason=}")

        # update words_csv to remove the duplicates and/or sort (and save the original)
        words_csv_temp_marker = "_tmp"
        words_temp_csv = f"{words_csv_fname}{words_csv_temp_marker}{words_csv_fext}"
        words_csv_save_marker = f"_saved_{timestamp}"
        words_save_csv = f"{words_csv_fname}{words_csv_save_marker}{words_csv_fext}"
        # print(f"{words_csv=}, {words_temp_csv=}, {words_save_csv=}")
        with (open(file=words_temp_csv, mode='w', encoding='utf-8') as f):
            # write the key comment from original csv
            for line in key_comment:
                # print(f"{line=}\n")
                f.write(f"{line}\n")

            # write the sorted source_phrase and target phrase from the dataframe
            for _idx, (source_phrase, target_phrase) in \
                    df_sorted[['source_phrase', 'target_phrase']].iterrows():
                # print(f"{source_phrase}: {target_phrase}")
                f.write(f"{source_phrase}: {target_phrase}\n")

        # manage the files
        shutil.move(words_csv, words_save_csv)  # save original
        Path(words_save_csv).touch()  # touch the save file to capture the date moved
        shutil.move(words_temp_csv, words_csv)  # replace original with sorted csv, duplicates removed
        print(f"Updated '{words_csv}' to {update_reason}, original saved as '{words_save_csv}'")

    # return sorted dataframe with no duplicates
    logger.debug(f"ended: sort_and_remove_duplicates()")
    return df_sorted


def convert_csv_to_dataframe(words_csv, deliminator=': ', encoding='utf-8'):
    """Convert given words_csv file to pandas dataframe.

    The language source_phrases and target_phrase are written to the dataframe
    split by the given deliminator.

    The header is on a row beginning with a '>'. The header is used to define
    the names of the source and target languages.

    Lines beginning with '#' and blank lines are ignored

    Return: pandas dataframe
    With two columns, one for source phrases and one for the target phrases.
    The source and target language column names are defined by the header.

    Raises:
        ValueError: missing header
        ValueError: more than one header
        ValueError: empty source or target phrase
    """
    logger.debug(f"convert_csv_to_dataframe({words_csv=}, {deliminator=}, {encoding=}")
    src_phrase_l = []  # source phrase list
    tgt_phrase_l = []  # target phrase list
    src_hdr = None  # source phrase header
    tgt_hdr = None  # target phrase header
    key_comment = []  # key comment at top of the file
    comment = []  # any comment or blank line in the file
    regex_pattern = re.compile(r'.+?\((.*)\)')  # pattern to match items between round brackets

    with open(words_csv, 'r', encoding=encoding) as file:
        for idx, line in enumerate(file):
            if line.startswith('#') or not line.strip():
                # save comments and empty lines at top of file, otherwise ignore
                comment.append(line.rstrip('\n'))

                continue

            if line.startswith('>'):  # header
                if src_hdr:
                    # header already set
                    raise ValueError(f"header already set, "
                                     f"didn't expect another at line number {idx}!")

                # parse the header
                comment.append(line.rstrip('\n'))
                line = line.rstrip().partition(deliminator)
                src_hdr = line[0][1:]  # ignore header marker
                tgt_hdr = line[2]

                # save key_comment
                key_comment = comment.copy()
                continue

            # parse the phrase
            line = line.rstrip().partition(deliminator)
            # print(line)
            if not line[0] or not line[2]:
                raise ValueError(f"unexpected empty source or target value at line number {idx}: {line}!")

            src_phrase, tgt_phrase = line[0], line[2]

            # check for invalid gender value
            between_brackets = regex_pattern.findall(src_phrase)
            if between_brackets and 'm' not in between_brackets and 'f' not in between_brackets:
                raise ValueError(f"invalid source phrase at line number {idx}, only the gender "
                                 f"values 'm' or 'f' are allowed between the brackets: {src_phrase}")

            # remove any caps at beginning of the source phrase
            src_phrase = src_phrase[0].lower() + src_phrase[1:]

            src_phrase_l.append(src_phrase)
            tgt_phrase_l.append(tgt_phrase)

    # check integrity
    if not src_hdr or not tgt_hdr:
        raise ValueError("no header found in file!")

    # report on number of phrases parsed
    print(f"Parsed {len(src_phrase_l)} phrases")

    # create the dataframe with source and target phrases
    df = pd.DataFrame(zip(src_phrase_l, tgt_phrase_l),
                      columns=['source_phrase', 'target_phrase'])

    # add the languages to the dataframe
    df['source_language'] = src_hdr
    df['target_language'] = tgt_hdr

    # add derived data to the dataframe

    # parse the source phrase to add the noun and gender information
    df[['is_source_noun', 'source_noun', 'source_noun_gender']] = \
        list(df.source_phrase.apply(extract_noun))

    # parse the target phrase to add the initial shortened phrase
    # and the is_ignore_translation_error flag
    df[['target_phrase_short', 'is_ignore_translation_error']] = \
        list(df.target_phrase.apply(get_phrase_short,
                                    comment_marker='#',
                                    special_comment='# ignore translation error'))

    # clean the shortened target phrase to remove extraneous info
    df['target_phrase_short'] = df.target_phrase_short.apply(clean)

    # add new column, the source_phrase with any diacritic removed
    df['source_phrase_no_diacritic'] = df.source_phrase.apply(remove_diacritic)

    # set the data type of new boolean columns to bool
    df.is_source_noun = df.is_source_noun.astype(bool)
    df.is_ignore_translation_error = df.is_ignore_translation_error.astype(bool)

    # sort and remove duplicates from the dataframe and words_csv
    df = sort_and_remove_duplicates(df, words_csv, key_comment)

    # validate the dataframe schema against the LanguageDataSchema
    validate_language_dataframe_schema(df)

    return df


def load_language_data_df_from_feather(feather_filepath: str) -> LanguageDataFrameType:
    """Loads the language dataFrame from a Feather file and validates its schema.

    Args:
        feather_filepath (str): Path to the Feather file.

    Returns:
        LanguageDataFrameType: The loaded language data DataFrame.

    Raises:
        FileNotFoundError: If the Feather file is not found.
        RuntimeError: If there is an error reading the Feather file.
        TypeError: If the loaded DataFrame does not conform to LanguageDataSchema.
    """
    try:
        df = pd.read_feather(feather_filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"Feather file not found at {feather_filepath}")
    except Exception as e:
        raise RuntimeError(f"Error reading Feather file: {e}")

    validate_language_dataframe_schema(df)

    return df  # xtype: LanguageDataFrameType


def main(lang_csv_filepath: str, lang_feather_filepath: str = 'language_words.fea'):
    """Main function to convert CSV to dataframe and save as a Feather file.

    Orchestrates the conversion of a language CSV file to a Feather DataFrame.
        1. Creates a LanguageDataFrame from the input CSV file.
        2. Saves the LanguageDataFrame to a Feather file for persistent storage.
        3. Loads the LanguageDataFrame back from the Feather file and validates its schema.

    Args:
        lang_csv_filepath (str): Path to the input CSV file.
        lang_feather_filepath (str, optional): Path to save LanguageDataFrame Feather file.
                                               Defaults to 'language_words.fea'.
    """
    try:
        language_df = convert_csv_to_dataframe(lang_csv_filepath)
        language_df.to_feather(lang_feather_filepath)
        print(f"Language data saved to: {lang_feather_filepath}")

        # Load the dataframe back from feather and re-validate schema
        _loaded_df = load_language_data_df_from_feather(lang_feather_filepath)
        print(f"Language data successfully loaded and schema validated from: "
              f"{lang_feather_filepath}")

    except (FileNotFoundError, RuntimeError, ValueError, TypeError) as e:
        print(f"Error during CSV to DataFrame conversion: {e}")


if __name__ == "__main__":
    # call with defaults for French to English words translation
    main(lang_csv_filepath=data_config.FRENCH_ENGLISH_WORDS_CSV,
         lang_feather_filepath=data_config.FRENCH_ENGLISH_WORDS_FEA)
