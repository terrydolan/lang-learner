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

def main():
    """Main for prototype."""
    st.subheader("Prototype")
    logger.debug(f"call: start Prototype mini-app {'-'*50}")

    # prototype display of buttons on mobile
    st.write("Aim: check button behaviour on mobile devices")
    col_proto1, col_proto2, _col_proto3 = st.columns([.25, 0.25, 0.5], gap='small')
    for i in range(1, 5+1):
        with col_proto1:
            # st.button(f"twelve_lft_{i}", use_container_width=True)
            # st.button(f"eight_l{i}", use_container_width=True)
            st.button(f"4_l{i}", use_container_width=True)
        with col_proto2:
            # st.button(f"twelve_rgt_{i}", use_container_width=True)
            # st.button(f"eight_r{i}", use_container_width=True)
            st.button(f"4_r{i}", use_container_width=True)


if __name__ == "__main__":
    main()
