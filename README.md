# Language Learner

## Introduction
The *Language Learner App* contains 'mini-apps' to help learn a language.

The app is designed to be language agnostic.

Initially the app uses a single word file with the source and target 
languages fixed at French and English.

The miniapps and the account utilities are available from the sidebar. 

The first miniapp is a simple word match challenge.

## Word Match
Match as many English and French words as you can before the timer runs out.

## Top Scores
Check your top score and see how you compare to others.

## My Scores
Check all your scores.

## Search
Search the words.

## Language Dataset and Pipeline
The app uses a hand-crafted list of paired French and English words and phrases.

Before using the language data in the app, the phrases are loaded into a 
dataframe and the translation is validated using the data tools.

The phrases will *not* be error free.

## Key Project Files
The 'lang_learner_app.py' is the main python streamlit app implementation.

The associated app pages are in the './lang_learner_pages' folder.

The associated app utilities are in the './utils' folder.

The latest dataframe containing the validated source and target language 
phrases is in the './data' folder.

The data tools are in the './data_tools' folder.

## Cloud Deployment
The app is deployed on the Streamlit Comminity Cloud at
[lang-learner](https://terrydolan-lang-learner.streamlit.app/). Try it!

Note that the app is run on demand, so you may have to wait for it to load.


Terry Dolan  
May 2025