"""
Script: check_lang_df_translation.py

Performs translation and gender checks on a language dataframe.

This script loads a LanguageDataFrame from a Feather file and checks the
translation accuracy of each source phrase and, if the phrase is a noun,
the given gender correctness.

It uses the TranslationCheckerFactory and its associated language translation
services for the source and target languages.

The script adds additional columns to the dataframe that act as a validation
report and stores the dataframe as a feather file.

The report highlights those source phrases that require manual review due to
potential translation mismatches or gender errors.

This report is intended to facilitate the iterative refinement of the language
data and, once the issues have been resolved, for 'publication' and use in
the language learning applications.
"""
import logging
import pandas as pd
import data_tools.data_utils.data_config as data_config

from tqdm import tqdm
from typing import List
from data_tools.data_utils.data_schema import (ValidationReportDataSchema,
                                               validate_report_dataframe_schema,
                                               load_report_data_df_from_feather)
from data_tools.data_utils.translation import TranslationCheckerFactory
from data_tools.scripts.convert_lang_csv_to_df import \
    load_language_data_df_from_feather

# setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s')
logger.setLevel(logging.WARNING)

# define key constants
FUZZY_RATIO_THRESHOLD = 85

# ------------------------------------------------------------------------------
# functions
# ------------------------------------------------------------------------------


def analyse_errors(translation_error, fuzzy_ratio,
                   is_source_noun, gender_error, is_gender_match, lexical_gender):
    """Analyse errors and return a summary review dictionary.

    Review reasons:
    'TE': Unexpected translation error
    'NNF': Noun not found
    'GNF': Gender not found
    'GM': Gender mismatch

    Return:
    return_dict = {'is_needs_review': boolean, 'review_reason': str, 'review_detail': str}
        'is_needs_review': True if review is needed
        'review_reason': String containing the summary review reasons, separated by a ';'
        'review_detail': String containing the detailed review reasons, separated by a ';'
    """
    is_needs_review = False
    review_reason = []
    review_detail = []

    if not translation_error and fuzzy_ratio < FUZZY_RATIO_THRESHOLD:
        is_needs_review = True
        reason = 'TM'  # translation mismatch, fuzzy ratio below threshold
        review_reason.append(reason)
        review_detail.append(f"{reason}: Translation Mismatch (fuzzy ratio "
                             f"< threshold) - {fuzzy_ratio}")

    if translation_error:
        is_needs_review = True
        reason = 'TE'  # unexpected translation error
        review_reason.append(reason)
        review_detail.append(f"{reason}: {translation_error}")

    if (is_source_noun and gender_error
            and is_gender_match is None and lexical_gender is None):
        is_needs_review = True
        reason = 'NNF'  # Noun not found
        review_reason.append(reason)
        review_detail.append(f"{reason}: {gender_error}")

    if (is_source_noun and gender_error
            and is_gender_match is None and lexical_gender):
        is_needs_review = True
        reason = 'GNF'  # Gender not found
        review_reason.append(reason)
        review_detail.append(f"{reason}: {gender_error}")

    if (is_source_noun and gender_error
            and is_gender_match is False):
        is_needs_review = True
        reason = 'GM'  # Gender mismatch
        review_reason.append(reason)
        review_detail.append(f"{reason}: {gender_error}")

    return {
        'is_needs_review': is_needs_review,
        'review_reason': '; '.join(review_reason),  # convert list to ; separated string
        'review_detail': '; '.join(review_detail)  # convert list to ; separated string
    }


def main(language_feather_filepath='language_words.fea',
         output_filepath='language_words_tlchk.fea',
         word_limit=None):
    """Main function to load language data, check translation, and output report as df.

    Orchestrates the translation and gender checking process:
        1. Loads language data from the specified Feather file using reusable function.
        2. Determines the source and target languages from the loaded data.
        3. Initializes a TranslationChecker based on the language pair.
        4. Iterates through each phrase in the language data DataFrame:
           - Performs translation check using the generic TranslationChecker.
           - Performs gender validation for nouns using the specialised language TranslationChecker.
           - Aggregates validation results and flags phrases needing review.
        5. Creates a ValidationReportDataFrame from the results.
        6. Sorts the report DataFrame to prioritise phrases needing review.
        7. Saves the report ValidationReportDataFrameType to a feather file.

    Args:
        language_feather_filepath (str, optional): Path to the LanguageData Feather file.
                                                   Defaults to 'language_words.fea'.
        output_filepath (str, optional): Path to save the validation report Feather file.
                                         Defaults to 'language_words_tlchk.fea'.
        word_limit (int, optional): Word limit, number of words to process.
                                    If None, process all the words in the language dataframe.
                                    Defaults to None i.e. process all words.
    """
    logger.debug(f"main({language_feather_filepath=}, {output_filepath=}, {word_limit=}")
    if word_limit:
        print(f"Processing phrases in dataframe (limited to {word_limit})...")
    else:
        print("Processing all phrases in dataframe...")

    try:
        language_df = load_language_data_df_from_feather(
            language_feather_filepath)
    except (FileNotFoundError, RuntimeError, ValueError, TypeError) as e:
        print(f"Error loading language data: {e}")
        return

    # get the source and target language from the dataframe
    source_language = language_df['source_language'].iloc[0]
    target_language = language_df['target_language'].iloc[0]
    logger.info(f"{source_language=}, {target_language=}")

    # instantiate the translation_checker for the givem source and target language
    checker_factory = TranslationCheckerFactory()
    translation_checker = checker_factory.get_checker(source_language, target_language)

    # create results list and results dictionary
    validation_results: List[ValidationReportDataSchema] = []

    # iterate through each row of the dataframe, checking the translation and gender
    noun_cnt = 0

    tqdm_tot = word_limit if word_limit else len(language_df)
    idx = None
    for idx, (index, row) in enumerate(tqdm(language_df.iterrows(),
                                            desc="Processing source phrases...",
                                            total=tqdm_tot,
                                            initial=1),
                                       start=1):
        logger.info(f"Processing phrase#: {idx}")
        source_phrase = row['source_phrase']
        target_phrase = row['target_phrase']
        target_phrase_short = row['target_phrase_short']
        is_source_noun = row['is_source_noun']
        source_noun = row['source_noun']
        source_noun_gender = row['source_noun_gender']
        is_ignore_translation_error = row['is_ignore_translation_error']
        source_phrase_no_diacritic = row['source_phrase_no_diacritic']
        gender_res = None

        if is_source_noun:
            noun_cnt += 1
            logger.info(f"Processing noun#: {noun_cnt}")

            translation_res = translation_checker.check_translation(source_noun, target_phrase_short)
            logger.info(f"***Translation Check: {source_noun=}, {target_phrase=}, {translation_res=}")

            gender_res = translation_checker.validate_gender(source_noun, source_noun_gender)
            logger.info(f"***Gender Check: {source_noun=}, {source_noun_gender=}, {gender_res=}")
        else:
            translation_res = translation_checker.check_translation(source_phrase, target_phrase_short)
            logger.info(f"***Translation Check: {source_phrase=}, {target_phrase=}, {translation_res=}")

        # retrieve results from translation check
        translation = translation_res.get('translation')
        fuzzy_ratio = translation_res.get('fuzzy_ratio')
        translation_error = translation_res.get('translation_error')

        # retrieve results from gender check
        if is_source_noun:
            is_gender_match = gender_res.get('is_gender_match')
            lexical_gender = gender_res.get('lexical_gender')
            gender_error = gender_res.get('gender_error')
        else:
            is_gender_match = None
            lexical_gender = None
            gender_error = None

        # prepare error summary for dataframe - summarise and collect detail
        error_res = analyse_errors(translation_error, fuzzy_ratio,
                                   is_source_noun, gender_error, is_gender_match, lexical_gender)
        is_needs_review = error_res.get('is_needs_review')
        review_reason = error_res.get('review_reason')
        review_detail = error_res.get('review_detail')

        # set is_ok_to_display
        is_ok_to_display = True if (not is_needs_review) or is_ignore_translation_error else False

        logger.info(f"{is_needs_review=}, {review_reason=}, {review_detail=}, "
                    f"{is_ignore_translation_error=}, {is_ok_to_display=}")

        validation_results.append({
            'source_phrase': source_phrase,
            'target_phrase': target_phrase,
            'target_phrase_short': target_phrase_short,
            'source_language': source_language,
            'target_language': target_language,
            'is_source_noun': is_source_noun,
            'source_noun': source_noun,
            'source_noun_gender': source_noun_gender,
            'is_ignore_translation_error': is_ignore_translation_error,
            'source_phrase_no_diacritic': source_phrase_no_diacritic,
            'translation': translation,
            'fuzzy_ratio': fuzzy_ratio,
            'is_gender_match': is_gender_match,
            'lexical_gender': lexical_gender,
            'is_needs_review': is_needs_review,
            'review_reason': review_reason,
            'review_detail': review_detail,
            'is_ok_to_display': is_ok_to_display
        })

        # stop processing if word_limit reached
        if word_limit and (idx == word_limit):
            break

    # create the validation results dataframe
    dfv = pd.DataFrame(validation_results)

    # set the data type of new boolean columns to bool
    dfv.is_gender_match = dfv.is_gender_match.astype(bool)
    dfv.is_needs_review = dfv.is_needs_review.astype(bool)
    dfv.is_ok_to_display = dfv.is_ok_to_display.astype(bool)

    # validate the report dataframe schema against the ValidationReportDataSchema
    validate_report_dataframe_schema(dfv)

    try:
        dfv.to_feather(output_filepath)
        print(f"Translation and Language check report saved to: {output_filepath}")

        # Load the dataframe back from feather and re-validate schema
        dfv = load_report_data_df_from_feather(output_filepath)
        print(f"Language data successfully loaded and schema validated from: "
              f"{output_filepath}")

        # Report on number of items that need review
        items_tot = len(dfv)
        items_to_review = dfv[(dfv.is_ok_to_display != True)].source_phrase.count()
        print(f"Processed {items_tot} items, {items_to_review} need review")

    except Exception as e:
        print(f"Error saving dataframe as feather file: {e}")


if __name__ == "__main__":
    language_feather_file = data_config.FRENCH_ENGLISH_WORDS_FEA
    output_file = data_config.FRENCH_ENGLISH_WORDS_TLCHK_FEA
    this_word_limit = None  # 5
    main(language_feather_file, output_file, this_word_limit)
