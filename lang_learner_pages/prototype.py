"""
Module: prototype.py
Description: Contains logic to prototype mini-app logic for cloud deployment.
"""
import logging
import streamlit as st
from pathlib import Path
from contextlib import contextmanager
from utils.page_utils import save_page

# setup logger
logger = logging.getLogger(__name__)
this_file_stem = Path(__file__).stem
if this_file_stem in st.secrets.set_log_level:
    logger.setLevel(st.secrets.set_log_level[this_file_stem])
else:
    logger.setLevel(logging.WARNING)


# def fix_mobile_columns():
#     """ Define two flex columns for mobile.
#
#     Initial simple solution based on:
#     https://github.com/streamlit/streamlit/issues/6592
#     """
#     logger.debug(f"call: fix_mobile_columns()")
#     st.write('''<style>
#     [data-testid="stColumn"] {
#         width: calc(50.0% - 1rem) !important;
#         flex: 1 1 calc(50.0% - 1rem) !important;
#         min-width: calc(50.0% - 1rem) !important;
#     }
#     </style>''', unsafe_allow_html=True)

# HORIZONTAL_STYLE = """
# <style class="hide-element">
#     /* Hides the style container and removes the extra spacing */
#     .element-container:has(.hide-element) {
#         display: none;
#     }
#     /*
#         The selector for >.element-container is necessary to avoid selecting the whole
#         body of the streamlit app, which is also a stVerticalBlock.
#     */
#     div[data-testid="stVerticalBlock"]:has(> .element-container .horizontal-marker) {
#         display: flex;
#         flex-direction: row !important;
#         flex-wrap: wrap;
#         /* gap: 0.5rem; */
#         align-items: baseline;
#     }
#     /* Buttons and their parent container all have a width of 704px, which we need to override */
#     div[data-testid="stVerticalBlock"]:has(> .element-container .horizontal-marker) div {
#         / * width: max-content !important; */
#         width: calc(50.0% - 1rem) !important;
#         flex: 1 1 calc(50.0% - 1rem) !important;
#         min-width: calc(50.0% - 1rem) !important;
#     }
#     /* Just an example of how you would style buttons, if desired */
#     div[data-testid="stVerticalBlock"]:has(> .element-container .horizontal-marker) button {
#         border-color: green;
#     }
# </style>
# """
#
#
# @contextmanager
# def st_horizontal():
#     st.markdown(HORIZONTAL_STYLE, unsafe_allow_html=True)
#     with st.container():
#         st.markdown('<span class="hide-element horizontal-marker"></span>', unsafe_allow_html=True)
#         yield


@contextmanager
def st_columns_horizontal_fix_mobile(n=2):
    """ Define n flex columns for mobile.

    Inputs:
    n: int, number of columns (defaults to 2)

    Addresses issue on mobile where mobile solution for st.columns does not support two (or three)
    buttons side-by-side horizontally, even though display is wide enough.

    Streamlit have fix for this on the way: Flex layout #10895

    ToDo: replace st_columns_horizontal_fix_mobile() when flex container available with horizontal support.
    Based on:
    https://gist.github.com/ddorn/decf8f21421728b02b447589e7ec7235

    """
    logger.debug(f"call: st_columns_horizontal_fix_mobile({n=})")
    assert n > 0, f"Number of columns must be >0, given {n=}"
    ratio_pcnt = f"{100/n:.3f}"
    logger.debug(f"{ratio_pcnt=}")

    # define style to n flex cols (with a percentage of ratio_pcnt) for mobile
    horizontal_style = """
<style class="hide-element">
    /* Hides the style container and removes the extra spacing */
    .element-container:has(.hide-element) {
        display: none;
    }
    /*
        The selector for >.element-container is necessary to avoid selecting the whole
        body of the streamlit app, which is also a stVerticalBlock.
    */
    div[data-testid="stVerticalBlock"]:has(> .element-container .horizontal-marker) {
        display: flex;
        flex-direction: row !important;
        flex-wrap: wrap;
        /* gap: 0.5rem; */
        align-items: baseline;
    }
    /* Buttons and their parent container all have a width of 704px, which we need to override */
    div[data-testid="stVerticalBlock"]:has(> .element-container .horizontal-marker) div {
        / * width: max-content !important; */
        width: calc({ratio_pcnt}% - 1rem) !important;
        flex: 1 1 calc({ratio_pcnt}% - 1rem) !important;
        min-width: calc({ratio_pcnt}% - 1rem) !important;
        margin-top: auto;  /* fix equivalent of vertical_alignment="bottom" */
    }
    /* Just an example of how you would style buttons, if desired */
    div[data-testid="stVerticalBlock"]:has(> .element-container .horizontal-marker) button {
        border-color: green;
    }
</style>
"""
    # replace the actual ratio_pcnt in the html
    horizontal_style = horizontal_style.replace("{ratio_pcnt}", str(ratio_pcnt))
    logger.debug(f"{horizontal_style=}")

    # apply the style and yield the horizontal marker
    st.markdown(horizontal_style, unsafe_allow_html=True)
    with st.container():
        st.markdown('<span class="hide-element horizontal-marker"></span>',
                    unsafe_allow_html=True)
        yield


def main():
    """Main for prototype."""
    st.header("Prototype")
    logger.debug(f"call: start Prototype mini-app {'-'*50}")
    # save page
    _calling_page = save_page('scores')

    # prototype display of buttons on mobile
    st.write("Aim: support two horizontal button on mobile devices")

    st.subheader("Start by display 3 items in 3 standard columns")
    col0_1, col0_2, col0_3 = st.columns(3, gap='small', vertical_alignment="bottom")
    col0_1.button("CNT 2:00 DN")
    col0_2.metric("Hit", value=36)
    col0_3.metric("Miss", value=2)

    st.write("and 2 standard word match columns")
    col1, col2 = st.columns(2, gap='small')
    for i in range(1, 2+1):
        with col1:
            st.button(f"Fifteen chars l{i}", use_container_width=True)
        with col2:
            st.button(f"Fifteen chars r{i}", use_container_width=True)

    st.write("---")
    # custom CSS
    st.subheader("Proto1: Basic Demo Custom CSS, 15 chars")
    with st_columns_horizontal_fix_mobile(2):
        st.button("15fteen charsl1", use_container_width=True)

        st.button("15fteen charsr1", use_container_width=True)

    st.write("---")
    st.subheader("Proto2: Demo Custom CSS Width (4 chars)")
    for i in range(1, 2+1):
        with st_columns_horizontal_fix_mobile(2):
            st.button(f"4 l{i}", use_container_width=True)
            st.button(f"4 r{i}", use_container_width=True)

    st.write("---")
    st.subheader("Proto3: Use Container Width (8 chars)")
    for i in range(1, 2+1):
        with st_columns_horizontal_fix_mobile(2):
            st.button(f"eight l{i}", use_container_width=True)
            st.button(f"eight r{i}", use_container_width=True)

    st.write("---")
    st.subheader("Proto4: Use Container Width (16 chars)")
    for i in range(1, 2+1):
        with st_columns_horizontal_fix_mobile(2):
            st.button(f"sixteen chr lft{i}", use_container_width=True)
            st.button(f"sixteen chr rgt{i}", use_container_width=True)

    st.write("---")
    st.subheader("Proto6: Use Container Width (32 chars)")
    for i in range(1, 2+1):
        with st_columns_horizontal_fix_mobile(2):
            st.button(f"thirtytwo32 thirtytwo chars lft{i}", use_container_width=True)
            st.button(f"thirtytwo32 thirtytwo chars rgt{i}", use_container_width=True)

    st.write("---")
    st.subheader("Proto7: Use Container Width (31 chars)")
    for i in range(1, 2+1):
        with st_columns_horizontal_fix_mobile(2):
            st.button(f"thirtyone_ thirtyone chars lft{i}", use_container_width=True)
            st.button(f"thirtyone_ thirtyone chars rgt{i}", use_container_width=True)

    st.write("---")
    st.subheader("Proto8: Use Container Width 3 cols (may need vertical alignment?)")
    with st_columns_horizontal_fix_mobile(3):
        st.button("CNT 2:01 DN")
        st.metric("H1t", value=36)
        st.metric("M1ss", value=2)

    st.write("---")
    st.subheader("Proto8: Use Container Width 3 cols (may need vertical alignment?)")
    with st_columns_horizontal_fix_mobile(3):
        st.button("CNT 2:02 DN")
        st.write(f"Hit: :green[35]")
        st.write(f"Miss: :red[3]")

    # # prototype display of buttons on mobile
    # st.write("Aim: support two horizontal button on mobile devices")
    #
    # st.subheader("Start by display 3 items in 3 columns")
    # col0_1, col0_2, col0_3 = st.columns(3, gap='small', vertical_alignment="bottom")
    # col0_1.button("Countdown")
    # col0_2.metric("Hit", value=6)
    # col0_3.metric("Miss", value=2)
    #
    # st.write("---")
    # st.subheader("Proto1: Basic")
    # fix_mobile_columns()
    # col1, col2 = st.container(2, gap='small')
    # for i in range(1, 2+1):
    #     with col1:
    #         # st.button(f"twelve_lft_{i}", use_container_width=True)
    #         # st.button(f"eight_l{i}", use_container_width=True)
    #         # st.button(f"4_l{i}", use_container_width=True)
    #         st.button(f"s4l{i}")
    #     with col2:
    #         # st.button(f"twelve_rgt_{i}", use_container_width=True)
    #         # st.button(f"eight_r{i}", use_container_width=True)
    #         # st.button(f"4_r{i}", use_container_width=True)
    #         st.button(f"s4r{i}")

    # st.write("---")
    # st.subheader("Proto2: Use Container Width (4 chars)")
    # fix_mobile_columns()
    # col2_1, col2_2 = st.columns(2, gap='small')
    # for i in range(1, 2+1):
    #     with col2_1:
    #         # st.button(f"twelve_lft_{i}", use_container_width=True)
    #         # st.button(f"eight_l{i}", use_container_width=True)
    #         st.button(f"4_l{i}", use_container_width=True)
    #         # st.button(f"s4l{i}")
    #     with col2_2:
    #         # st.button(f"twelve_rgt_{i}", use_container_width=True)
    #         # st.button(f"eight_r{i}", use_container_width=True)
    #         st.button(f"4_r{i}", use_container_width=True)
    #         # st.button(f"s4r{i}")
    #
    # st.write("---")
    # st.subheader("Proto3: Use Container Width (8 chars)")
    # fix_mobile_columns()
    # col3_1, col3_2 = st.columns(2, gap='small')
    # for i in range(1, 2+1):
    #     with col3_1:
    #         # st.button(f"twelve_lft_{i}", use_container_width=True)
    #         st.button(f"eight_l{i}", use_container_width=True)
    #         # st.button(f"4_l{i}", use_container_width=True)
    #         # st.button(f"s4l{i}")
    #     with col3_2:
    #         # st.button(f"twelve_rgt_{i}", use_container_width=True)
    #         st.button(f"eight_r{i}", use_container_width=True)
    #         # st.button(f"4_r{i}", use_container_width=True)
    #         # st.button(f"s4r{i}")
    #
    # st.write("---")
    # st.subheader("Proto4: Use Container Width (16 chars)")
    # fix_mobile_columns()
    # col4_1, col4_2 = st.columns(2, gap='small')
    # for i in range(1, 2+1):
    #     with col4_1:
    #         st.button(f"sixteen_chr_lft{i}", use_container_width=True)
    #         # st.button(f"twelve_lft_{i}", use_container_width=True)
    #         # st.button(f"eight_l{i}", use_container_width=True)
    #         # st.button(f"4_l{i}", use_container_width=True)
    #         # st.button(f"s4l{i}")
    #     with col4_2:
    #         st.button(f"sixteen_chr_rgt{i}", use_container_width=True)
    #         # st.button(f"twelve_rgt_{i}", use_container_width=True)
    #         # st.button(f"eight_r{i}", use_container_width=True)
    #         # st.button(f"4_r{i}", use_container_width=True)
    #         # st.button(f"s4r{i}")
    #
    # st.write("---")
    # st.subheader("Proto5: Use Container Width (16 chars, valign on bottom)")
    # fix_mobile_columns()
    # col5_1, col5_2 = st.columns(2, gap='small', vertical_alignment="bottom")
    # for i in range(1, 2+1):
    #     with col5_1:
    #         st.button(f"sixteen_ch _lft{i}", use_container_width=True)
    #         # st.button(f"twelve_lft_{i}", use_container_width=True)
    #         # st.button(f"eight_l{i}", use_container_width=True)
    #         # st.button(f"4_l{i}", use_container_width=True)
    #         # st.button(f"s4l{i}")
    #     with col5_2:
    #         st.button(f"sixteen_ch _rgt{i}", use_container_width=True)
    #         # st.button(f"twelve_rgt_{i}", use_container_width=True)
    #         # st.button(f"eight_r{i}", use_container_width=True)
    #         # st.button(f"4_r{i}", use_container_width=True)
    #         # st.button(f"s4r{i}")
    #
    # st.write("---")
    # st.subheader("Proto6: Use Container Width (32 chars, valign on bottom)")
    # fix_mobile_columns()
    # col6_1, col6_2 = st.columns(2, gap='small', vertical_alignment="bottom")
    # for i in range(1, 2+1):
    #     with col6_1:
    #         st.button(f"thirtytwo32 thirtytwo chars lft{i}", use_container_width=True)
    #         # st.button(f"sixteen_chr_lft{i}", use_container_width=True)
    #         # st.button(f"twelve_lft_{i}", use_container_width=True)
    #         # st.button(f"eight_l{i}", use_container_width=True)
    #         # st.button(f"4_l{i}", use_container_width=True)
    #         # st.button(f"s4l{i}")
    #     with col6_2:
    #         st.button(f"thirtytwo32 thirtytwo chars rgt{i}", use_container_width=True)
    #         # st.button(f"sixteen_chr_rgt{i}", use_container_width=True)
    #         # st.button(f"twelve_rgt_{i}", use_container_width=True)
    #         # st.button(f"eight_r{i}", use_container_width=True)
    #         # st.button(f"4_r{i}", use_container_width=True)
    #         # st.button(f"s4r{i}")
    #
    # st.write("---")
    # st.subheader("Proto7: Use Container Width (31 chars, valign on bottom)")
    # fix_mobile_columns()
    # col7_1, col7_2 = st.columns(2, gap='small', vertical_alignment="bottom")
    # for i in range(1, 2+1):
    #     with col7_1:
    #         st.button(f"thirtytwo_ thirtytwo chars lft{i}", use_container_width=True)
    #         # st.button(f"thirtytwo32 thirtytwo chars lft{i}", use_container_width=True)
    #         # st.button(f"sixteen_chr_lft{i}", use_container_width=True)
    #         # st.button(f"twelve_lft_{i}", use_container_width=True)
    #         # st.button(f"eight_l{i}", use_container_width=True)
    #         # st.button(f"4_l{i}", use_container_width=True)
    #         # st.button(f"s4l{i}")
    #     with col7_2:
    #         st.button(f"thirtytwo_ thirtytwo chars rgt{i}", use_container_width=True)
    #         # st.button(f"thirtytwo32 thirtytwo chars rgt{i}", use_container_width=True)
    #         # st.button(f"sixteen_chr_rgt{i}", use_container_width=True)
    #         # st.button(f"twelve_rgt_{i}", use_container_width=True)
    #         # st.button(f"eight_r{i}", use_container_width=True)
    #         # st.button(f"4_r{i}", use_container_width=True)
    #         # st.button(f"s4r{i}")


if __name__ == "__main__":
    main()
