"""
Module: prototype.py
Description: Contains logic to prototype mini-app logic for cloud deployment.
"""
import logging
import streamlit as st
from pathlib import Path

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)


def fix_mobile_columns():
    """ define two flex columns for mobile
    https://github.com/streamlit/streamlit/issues/6592
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
    """Main for prototype."""
    st.subheader("Prototype")
    logger.debug(f"call: start Prototype mini-app {'-'*50}")

    # prototype display of buttons on mobile
    st.write("Aim: support two horizontal button on mobile devices")
    st.subheader("Proto1")
    fix_mobile_columns()
    col1, col2 = st.columns(2, gap='small')
    fix_mobile_columns()
    for i in range(1, 5+1):
        with col1:
            # st.button(f"twelve_lft_{i}", use_container_width=True)
            # st.button(f"eight_l{i}", use_container_width=True)
            # st.button(f"4_l{i}", use_container_width=True)
            st.button(f"s4l{i}")
        with col2:
            # st.button(f"twelve_rgt_{i}", use_container_width=True)
            # st.button(f"eight_r{i}", use_container_width=True)
            # st.button(f"4_r{i}", use_container_width=True)
            st.button(f"s4r{i}")

    # st.subheader("Proto2")
    # col_proto1, col_proto2 = st.columns(2, gap='small')
    # fix_mobile_columns()
    # for i in range(1, 5+1):
    #     with col_proto1:
    #         # st.button(f"twelve_lft_{i}", use_container_width=True)
    #         # st.button(f"eight_l{i}", use_container_width=True)
    #         # st.button(f"4_l{i}", use_container_width=True)
    #         st.button(f"4_l{i}")
    #     with col_proto2:
    #         # st.button(f"twelve_rgt_{i}", use_container_width=True)
    #         # st.button(f"eight_r{i}", use_container_width=True)
    #         # st.button(f"4_r{i}", use_container_width=True)
    #         st.button(f"4_r{i}")


if __name__ == "__main__":
    main()
