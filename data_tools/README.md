# Language Learner Data Tools

## Key Folders
- *data_wip*: the 'work in progress' data folder; contains the .csv 
file(s) with the pairs of word phrases for the source and target languages 
and the associated dataframes produced by the data pipeline scripts. 
- *scripts*: contains the scripts that manage the data pipeline.
- *data_test*: contains test data files to check the data pipleline.
- *data_utils*: contains utilities used by the scripts and notebooks.
- *notebooks*: contains the notebooks used to explore the data pipeline.

## Data Pipeline
Run the following from scripts:
1. *convert_lang_csv_to_df.py*: convert language csv to dataframe e.g.  
**Input**: data_wip/fr_en_words_v1.csv  
**Output**: data_wip/fr_en_words_v1.fea  
The dataframe output from the conversion identifies the source and target 
languages. 
It also identifies if the source phrase is a noun and, if so, the 
noun's gender.
Note that *fr_en_words_v1.csv* is version 1 of the *csv* file containing the 
list of *French* and *English* words.


2. *check_lang_df_translation.py*: check translation of dataframe e.g.    
**Input**: data_wip/fr_en_words_v1.fea  
**Output**: data_wip/fr_en_words_tlchk_v1.fea  
The dataframe output from the translation check includes a translation
confidence value - a 'fuzzy ratio' - and an indication if the source 
and target phrase translation needs a review.
If a review is required, a review reason is given to help identify 
the issue. 
Typically a resolution requires an update to the starter file and a 
re-running of the pipeline.

Note that the key folders and filenames are defined in 
*data_utils/data_config.py*.

See the pipeline scripts for a more detailed description of the
process.

## Publish Validated Data File
Once the translation issues have been resolved the pipleline output 
dataframe, e.g. *data_wip/fr_en_words_tlchk_v1.fea*, is copied to 
the project data folder, ready to be used by the apps.