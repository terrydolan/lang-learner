"""
Module: uils/st_countdown.py
Description: Contains utility to implement a simple streamlit front-end
countdown timer component.

ToDo:
- Rewrite to replace vanilla javascript implemnentation with React
"""
import logging
import os
import streamlit.components.v1 as components

# setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# determine component's directory path
component_dir = os.path.dirname(__file__)
# logger.debug(f"st_countdown.py: {component_dir=})"

# declare the component using the streamlit components module
# note that Streamlit expects the index.html file to be in the path dir
_declare_component = components.declare_component(
    name="st_countdown",
    path=component_dir)


def st_countdown(countdown_from, key="st_countdown"):
    """Display basic streamlit countdown timer, starting from given value.

    key is an optional unique key for this countdown timer."""
    logger.debug(f"call: st_countdown({countdown_from=}, {key=})")

    # initiate timer and return the seconds remaining
    seconds_remaining = _declare_component(
        countdown_from=countdown_from,  # value to countdown from in seconds
        default=countdown_from,  # value returned before the timer has started (avoids None being returned)
        key=key  # unique key for component
    )

    return seconds_remaining
