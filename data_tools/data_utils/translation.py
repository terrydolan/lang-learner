"""
Module: data_tools/data_utils/translation.py
Translation classes.

"""
import logging
from typing import Optional
from deep_translator import GoogleTranslator  # type: ignore
from fuzzywuzzy import fuzz  # type: ignore
from pylexique import Lexique383  # French language lexicon

# setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# ------------------------------------------------------------------------------
# classes
# ------------------------------------------------------------------------------


class TranslationCheckerFactory:
    """Factory class to get the appropriate TranslationChecker."""
    @staticmethod
    def get_checker(source_language: str, target_language: str):
        """Returns a TranslationChecker instance based on language pair.

        Currently, only French-English is handled specifically.
        Defaults to GenericTranslationChecker for other language pairs.

        Args:
            source_language (str): Source language code (e.g., 'French').
            target_language (str): Target language code (e.g., 'English').

        Returns:
            GenericTranslationChecker: An instance of a TranslationChecker
                                         (or a language-specific subclass).
        """
        logger.debug(f"{source_language=}, {target_language=}")
        if source_language.lower() == 'french' and target_language.lower() == 'english':
            return FrenchEnglishChecker()
        else:
            return GenericTranslationChecker(source_language, target_language)


class GenericTranslationChecker:
    """Base class for translation checkers providing generic functionality."""

    def __init__(self, source_language: str, target_language: str):
        """Initialises GenericTranslationChecker.

        Sets source and target languages.
        Sets translator and fuzzy string matchiner functions.

        Args:
            source_language (str): Source language code (e.g., 'French').
            target_language (str): Target language code (e.g., 'English').
        """
        self.source_language = source_language.lower()
        self.target_language = target_language.lower()
        self.translator = GoogleTranslator  # selected translator function
        self.fuzzer = fuzz.token_set_ratio  # selected fuzzy string matcher function
        logger.debug(f"{self.source_language=}, {self.target_language=}")

    def check_translation(self, source_text: str,
                          provided_target_translation: str) -> dict:
        """Checks translation using translator.

        Compares the provided target translation against the API translation
        for exact match, substring match, word presence, and fuzzy ratio.

        Args:
            source_text (str): Phrase in the source language.
            provided_target_translation (str): Provided target translation for given source.

        Returns:
            dict: Dictionary containing translation check results:
                'api_translation' (str): Translation from Google Translate API.
                'is_exact_match' (bool): True if provided translation is an exact match.
                'is_substring_match' (bool): True if provided is a substring of API or vice-versa.
                'is_word_in_api_translation' (bool): True if any word from provided is in API translation.
                'fuzzy_ratio' (float): Fuzzy string matching ratio (0-100).
                'error' (Optional[str]): Error message if API call fails, else None.
        """
        logger.debug(f"check_translation({source_text=}, {provided_target_translation=}")
        try:
            translation_result = self.translator(source=self.source_language,
                                                 target=self.target_language).translate(source_text)
            logger.info(f"{translation_result=}")
            # api_translation = translation_result.lower().strip()
            # provided_translation_lower = provided_target_translation.lower().strip()
            # is_exact_match = (api_translation == provided_translation_lower)
            # is_substring_match = (provided_translation_lower in api_translation) or (
            #             api_translation in provided_translation_lower)
            # is_word_in_api_translation = False
            # provided_words = set(provided_translation_lower.split())
            # api_words = set(api_translation.split())
            # if provided_words.intersection(api_words):
            #     is_word_in_api_translation = True

            # check match using fuzzy string matcher
            fuzzy_ratio = self.fuzzer(translation_result, provided_target_translation)

            # return result
            return {
                'translation': translation_result,
                'fuzzy_ratio': fuzzy_ratio,
                'translation_error': None
            }
        except Exception as e:
            return {
                'translation': None,
                'fuzzy_ratio': None,
                'translation_error': str(e)
            }

    def validate_gender(self, source_noun: str, provided_gender: Optional[str]) -> dict:
        """Validates gender of a source noun.

        Note: Gender validation is not implemented in the Generic Checker.
        This method should be overridden in language-specific checkers.

        Args:
            source_noun (str): Source noun to validate gender for.
            provided_gender (Optional[str]): Provided gender ('m', 'f', or None).

        Returns:
            dict: Dictionary with gender validation results:
                'is_gender_match' (Optional[bool]): Always None in Generic Checker.
                'lexical_gender' (Optional[Literal['m', 'f']]): Always None in Generic Checker.
                'gender_error' (Optional[str]): Error message indicating lack of implementation.
        """
        return {'is_gender_match': None,
                'lexical_gender': None,
                'gender_error': "Gender validation not implemented for this language pair."}


# --- FRENCH-ENGLISH CHECKER ---
class FrenchEnglishChecker(GenericTranslationChecker):
    """Language checker specialised for French to English language pairs.

    Used to validate gender of given French noun."""

    def __init__(self):
        """Initializes FrenchEnglishChecker."""
        super().__init__("French", "English")

        # Instantiate selected pylexique lexical analyser object
        self.lex383 = Lexique383()
        self.verbose = False

    def get_pylexique_cgram_genre_pairs(self, word, verbose=False):
        """Return pylexique list of (cgram, genre) pairs for given word.

        Args:
            word (str): target word
            verbose (boolean): flag indicating if function should be show details (defaults to false)

        Returns:
            list of tuples containing cgram and genre pairs.

        Note:
            return None if word not found in pylexique (Lexique383) dictionary.

        Examples:
            get_pylexique_cgram_genre_pairs('homme') -> [('NOM', 'm')]
            get_pylexique_cgram_genre_pairs('souris') -> [('VER', ''), ('ADJ', 'm'), ('NOM', '')]
            get_pylexique_cgram_genre_pairs('xxx') -> None
        """
        if verbose:
            print(f"get_pylexique_cgram_genre_pairs({word=}, {verbose=})")

        if word not in self.lex383.lexique:
            # word not found
            if verbose:
                print(f"{word=} not in lex383 dictionary")
            return None

        cg_gn_pairs = []
        lex383_res = self.lex383.lexique[word]
        if not isinstance(lex383_res, list):
            # single item
            lex_item = lex383_res
            if verbose:
                print(f"single item: {lex_item=}, {lex_item.cgram=}, {lex_item.genre=}")
            cg_gn_pairs.append((lex_item.cgram, lex_item.genre))
        else:
            for lex_item in lex383_res:
                if verbose:
                    print(f"multiple item: {lex_item=}, {lex_item.cgram=}, {lex_item.genre=}")
                cg_gn_pairs.append((lex_item.cgram, lex_item.genre))

        if verbose:
            print(f"return cgram genre pair list: {cg_gn_pairs}")
        return cg_gn_pairs

    @staticmethod
    def get_pylexique_gender_from_cgram_genre_pair_list(cgram_genre_pairs, verbose=False):
        """Return gender from given list of cgram_genre_pairs.

        Args:
            cgram_genre_pairs (list of tuples or None): list of pylexique (cgram, genre) pairs
            verbose (boolean): flag indicating if function should be show details (defaults to false)

        Returns:
            gender (str or None): gender is 'm' (male) or 'f' female

        Note:
            return None gender cannot be determined.

        Examples:
            # using output from: get_pylexique_cgram_genre_pairs('homme')
            get_pylexique_gender_from_cgram_genre_pair_list([('NOM', 'm')], verbose=True) -> 'm'

            # using output from: get_pylexique_cgram_genre_pairs('souris')
            get_pylexique_gender_from_cgram_genre_pair_list([('VER', ''), ('ADJ', 'm'), ('NOM', '')]) -> 'm'

            # using output from: get_pylexique_cgram_genre_pairs('xxx')
            get_pylexique_gender_from_cgram_genre_pair_list(None, verbose=True) -> None
        """
        if verbose:
            print(f"get_pylexique_gender_from_cgram_genre_pair_list({cgram_genre_pairs=}, {verbose=}): ")

        if cgram_genre_pairs is None:
            if verbose:
                print(f"gender could not be determined - input is None")
            return None

        # extract unique genders from list of (cgram, genre)  pairs
        unique_genders = set(g for _c, g in cgram_genre_pairs if g != '')
        if verbose:
            print(f"{unique_genders=}")

        # parse the unique genders
        if len(unique_genders) == 0:
            if verbose:
                print(f"gender could not be determined - no gender found")
            return None
        elif len(unique_genders) == 1:
            gender = unique_genders.pop()
            if verbose:
                print(f"gender found: {gender}")
            return gender
        else:
            if verbose:
                print(f"gender could not be determined - multiple values found")
            return None

    def validate_gender(self, french_noun: str, provided_gender: Optional[str]) -> dict:
        """Validates gender of a French noun using Lexique3 database.

        Checks if the provided gender matches the gender from the Lexique3
        database for the given French noun.

        Args:
            french_noun (str): French noun (without gender marker) to validate.
            provided_gender (Optional[str]): Provided gender ('m', 'f').

        Returns:
            dict: Dictionary with gender validation results:
                'is_gender_match' (Optional[bool]): True if lexical gender of french_noun matched provided_gender.
                'lexical_gender' (Optional[Literal['m', 'f']]): Gender from Lexique3 if found, else None.
                'gender_error' (Optional[str]): Error message if validation fails, else None.
        """
        # get list of (cgram, genre) pairs for given french_noun
        cgram_genre_pair_list = self.get_pylexique_cgram_genre_pairs(french_noun, self.verbose)
        if not cgram_genre_pair_list:
            return {
                'is_gender_match': None,
                'lexical_gender': None,
                'gender_error': f"noun '{french_noun}' not in lexical database, check for diacritics"
            }

        # get gender from the (cgram, genre) pair list
        lexique_gender = self.get_pylexique_gender_from_cgram_genre_pair_list(cgram_genre_pair_list, self.verbose)
        if not lexique_gender:
            return {
                'is_gender_match': None,
                'lexical_gender': lexique_gender,
                'gender_error': f"'gender could not be determined)"
            }

        if lexique_gender == provided_gender:
            return {
                'is_gender_match': True,
                'lexical_gender': lexique_gender,
                'gender_error': None
            }
        else:
            return {
                'is_gender_match': False,
                'lexical_gender': lexique_gender,
                'gender_error': (
                    f"gender mismatch: laxical gender '{lexique_gender}' "
                    f"does not match provided gender '{provided_gender}'")
            }
