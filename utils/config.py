"""
Module: data_utils/config.py
Description: Defines useful config values for project e.g. key folder location.
"""
import os

# Get the absolute path to the directory containing this config file
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# Get the absolute path to the project root (one level up from data_utils)
PROJECT_ROOT = os.path.dirname(CONFIG_DIR)

# Define the path to the data directory
DATA_DIR_PATH = os.path.join(PROJECT_ROOT, "data")

# Define paths to specific data files
# French to English feather dataframe with translation checks
FRENCH_ENGLISH_WORDS_TLCHK_FEA = os.path.join(
    DATA_DIR_PATH, "fr_en_words_tlchk_v1.fea")

# Define mapping dict from (source_language, target_language) to
# the *words_tlchk.fea file
lang_pair_to_all_words = {
    ('French', 'English'): FRENCH_ENGLISH_WORDS_TLCHK_FEA}