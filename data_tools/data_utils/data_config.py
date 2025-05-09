"""
Module: data_tools/data_utils/data_config.py
Description: Defines useful data tools config values for project e.g. key folder location.
"""
import os

# Get the absolute path to the directory containing this config file
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# Get the absolute path to the data_tools root (one level up from data_utils)
DATA_TOOLS_ROOT = os.path.dirname(CONFIG_DIR)

# Define the path to the main language data work in progress (wip) directory
DATA_TOOLS_DATA_DIR_PATH = os.path.join(DATA_TOOLS_ROOT, "data_wip")

# Define the path to the test language data directory
DATA_TOOLS_TEST_DATA_DIR_PATH = os.path.join(DATA_TOOLS_ROOT, "data_test")

# Define paths to specific data files
# French to English files for all words
FRENCH_ENGLISH_WORDS_CSV = os.path.join(
    DATA_TOOLS_DATA_DIR_PATH, "fr_en_words_v1.csv")
FRENCH_ENGLISH_WORDS_FEA = os.path.join(
    DATA_TOOLS_DATA_DIR_PATH, "fr_en_words_v1.fea")
FRENCH_ENGLISH_WORDS_TLCHK_FEA = os.path.join(
    DATA_TOOLS_DATA_DIR_PATH, "fr_en_words_tlchk_v1.fea")