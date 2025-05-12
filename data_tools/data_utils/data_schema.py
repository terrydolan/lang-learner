# data_schema.py
"""
Module: data_tools/data_utils/data_schema.py
Defines data schemas using TypedDict for structured data validation in the
language processing pipeline.

This file specifies schemas for:
    - Language data (LanguageDataSchema): Represents the core language pairs
      and related information used in the application and for validation.
    - Validation report data (ValidationReportSchema):  Defines the schema for
      the reports generated after translation and gender validation checks.

It also includes functions for runtime schema validation of Pandas DataFrames
against these defined schemas, ensuring data integrity throughout the process.
"""
from typing import TypedDict, Literal, Optional
import pandas as pd


# Schema for the core language data (for learning apps, etc.)
class LanguageDataSchema(TypedDict):
    """
    Schema for the core language data DataFrame.

    This schema defines the structure for DataFrames containing language
    phrases and related information, suitable for language learning apps
    and input to the translation checker.
    """
    source_phrase: str  # original source phrase, may be a noun with a gender marker e.g. 'homme (m)'
    target_phrase: str  # original target phrase, may contain additional info describing the phrase
    source_language: str  # source language e.g. 'French'
    target_language: str  # target language e.g. 'English'
    is_source_noun: Optional[bool]  # True if shortened source phrase is a noun
    source_noun: str  # source phrase without the gender marker (if source phrase is a noun) e.g. 'homme'
    source_noun_gender: Optional[Literal['m', 'f']]  # source phrase gender (if noun) e.g. 'm'
    target_phrase_short: str  # shortened target phrase, text after additional info removed
    is_ignore_translation_error: bool  # True if special comment present at end of the target phrase
    source_phrase_no_diacritic: str  # source phrase without diacritics e.g. être becomes etre


LanguageDataFrameType = pd.DataFrame  # Type alias for Language DataFrame


class ValidationReportDataSchema(LanguageDataSchema):
    """
    Schema for the validation report DataFrame.

    This schema defines the structure for DataFrames that store translation
    validation results, including API translations, fuzzy ratios, gender checks,
    and review flags.
    """
    translation: str  # translation of source phrase or noun
    fuzzy_ratio: int  # fuzzy ratio comparing source phrase translation to target_phrase_short, range 0-100
    lexical_gender: Optional[Literal['m', 'f']]  # lexical gender of given source_noun
    is_gender_match: bool  # True if lexical gender matches source_noun_gender
    is_needs_review: bool  # True if source and target need review e.g. low fuzzy_ratio or gender mismatch
    review_reason: str  # summary reason for review
    review_detail: str  # detailed reason for review
    is_ok_to_display: bool  # True if language word pair ok to display e.g.
                            # no review needed or because is_ignore_translation_error is True


ValidationReportDataFrameType = pd.DataFrame  # Type alias for Validation Report DataFrame


def validate_dataframe_schema(df: pd.DataFrame, expected_schema: type):
    """Validates DataFrame schema against an expected schema.

    Performs runtime validation to ensure a DataFrame conforms to a
    specified schema, checking for column names and data types.

    Args:
        df (pd.DataFrame): DataFrame to validate.
        expected_schema (type): Expected schema as a TypedDict type.

    Raises:
        ValueError: If DataFrame columns do not match the expected schema.
        TypeError: If DataFrame data types do not match the expected schema.
    """
    expected_columns = sorted(expected_schema.__annotations__.keys())
    # print(f'validate_dataframe_schema() {expected_columns=}')
    actual_columns = sorted(df.columns.tolist())
    # print(f'validate_dataframe_schema() {actual_columns=}')

    if actual_columns != expected_columns:
        raise ValueError(
            f"Data structure mismatch: Expected columns {expected_columns}, "
            f"but got {actual_columns}."
        )

    expected_dtypes = expected_schema.__annotations__
    for col_name, expected_type in expected_dtypes.items():
        actual_dtype_name = str(df[col_name].dtype)
        if (expected_type is str or expected_type is Optional[str]
                or expected_type is Literal['m', 'f']
                or expected_type is Optional[Literal['m', 'f']]):
            expected_dtype_name_check = 'object'
        elif expected_type is bool or expected_type is Optional[bool]:
            expected_dtype_name_check = 'bool'
        elif expected_type is int:
            expected_dtype_name_check = 'int64'
        elif expected_type is float:
            expected_dtype_name_check = 'float64'
        else:
            expected_dtype_name_check = 'object'

        if actual_dtype_name != expected_dtype_name_check:
            raise TypeError(
                f"Data type mismatch for column '{col_name}': "
                f"Expected type compatible with '{expected_dtype_name_check}', "
                f"but got '{actual_dtype_name}'."
            )


def validate_language_dataframe_schema(df: pd.DataFrame):
    """Validates DataFrame against the LanguageDataSchema.

    This is a specific validator for DataFrames intended to conform to the
    LanguageDataSchema. It uses the generic validate_dataframe_schema function.

    Args:
        df (pd.DataFrame): DataFrame to validate as LanguageDataFrameType.

    Raises:
        ValueError: If DataFrame columns do not match LanguageDataSchema.
        TypeError: If DataFrame data types do not match LanguageDataSchema.
    """
    validate_dataframe_schema(df, LanguageDataSchema)


def validate_report_dataframe_schema(df: pd.DataFrame):
    """Validates DataFrame against the ValidationReportDataSchema.

    This is a specific validator for DataFrames intended to conform to the
    LanguageDataSchema. It uses the generic validate_dataframe_schema function.

    Args:
        df (pd.DataFrame): DataFrame to validate as ValidationReportDataSchema.

    Raises:
        ValueError: If DataFrame columns do not match ValidationReportDataSchema.
        TypeError: If DataFrame data types do not match ValidationReportDataSchema.
    """
    validate_dataframe_schema(df, ValidationReportDataSchema)


def load_report_data_df_from_feather(feather_filepath: str) -> ValidationReportDataFrameType:
    """Loads the report dataframe from a Feather file and validates its schema.

    Args:
        feather_filepath (str): Path to the Feather file.

    Returns:
        ReportDataFrameType: The loaded report data dataframe.

    Raises:
        FileNotFoundError: If the Feather file is not found.
        RuntimeError: If there is an error reading the Feather file.
        TypeError: If the loaded DataFrame does not conform to ValidationReportDataSchema.
    """
    try:
        df = pd.read_feather(feather_filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"Feather file not found at {feather_filepath}")
    except Exception as e:
        raise RuntimeError(f"Error reading Feather file: {e}")

    validate_report_dataframe_schema(df)

    return df  # type: ValidationReportDataSchema