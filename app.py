from datetime import datetime, time
import pandas as pd
import streamlit as st
from parser import build_ics_content, process_pdf_file

# =============================================================================
# Page Config
# =============================================================================
st.set_page_config(
    page_title="ShiftSync - PDF Roster to Calendar",
    page_icon="⛳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Force Bright / Clean Light Theme CSS
st.markdown(
    """
    <style>
        /* Force clean light theme */
        .stApp {
            background-color: #F8FAFC;
            color: #0F172A;
        }

        /* Make the drag & drop area significantly taller and easier to hit */
        section[data-testid="stFileUploadDropzone"] {
            min-height: 240px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            padding: 2.5rem 1.5rem !important;
            background-color: #FFFFFF !important;
            border: 2px dashed #94A3B8 !important;
            border-radius: 0.85rem !important;
            transition: border-color 0.2s ease, background-color 0.2s ease;
        }
        section[data-testid="stFileUploadDropzone"]:hover {
            border-color: #0EA5E9 !important;
            background-color: #F0F9FF !important;
        }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 1rem 1.25rem;
            border-radius: 0.75rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        /* Primary action button */
        .stDownloadButton > button {
            background-color: #0EA5E9 !important;
            color: white !important;
            border-radius: 0.5rem;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# 메인 UI 레이아웃
# =============================================================================
st.title("⛳ ShiftSync")
st.info("Drag and drop your PDF shift schedule files to convert them into an **.ics Calendar file**.")

# =============================================================================
# TOP: TALL DRAG & DROP PDF UPLOADER
# =============================================================================
# _, center_col, _ = st.columns([1, 2.2, 1])

# with center_col: 
with st.container(border=True):
    st.subheader("Upload Your PDF Schedule Files")
    # 다중 파일 업로더 (드래그 앤 드롭 기본 지원)
    uploaded_files = st.file_uploader(
        "Upload PDF schedule files (Drag & Drop or click to browse) - multiple files supported",
        type=["pdf"],
        accept_multiple_files=True
    )

st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

# =============================================================================
# BELOW UPLOADER: FIXED-WIDTH DETAILS CONTAINER
# =============================================================================

# Centering columns to prevent inputs from stretching across ultra-wide monitors
with st.container(border=True):
    st.subheader("⚙️ Staff & Shift Details")
    
    target_name = st.text_input(
        "Staff Name * (Required)",
        placeholder="e.g. Mary",
        help="Enter your name exactly or partially as it appears on the roster."
    )

    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        selected_year = st.number_input(
            "Roster Year",
            value=datetime.now().year,
            step=1
        )
    with sub_col2:
        timezone_str = st.selectbox(
            "Timezone",
            ["America/Edmonton", "America/Vancouver", "America/Toronto", "Asia/Seoul"],
            index=0
        )

    with st.expander("Advanced Settings (Close Shift Time)", expanded=False):
        close_hour = st.slider(
            "Closing Shift End Hour",
            min_value=18,
            max_value=24,
            value=23,
            format="%d:00"
        )
        close_time = time(close_hour if close_hour < 24 else 23, 59 if close_hour == 24 else 0)

# =============================================================================
# SHIFT PROCESSING & PREVIEW GATE
# =============================================================================
clean_name = target_name.strip().lower()

if uploaded_files:
    # Validation Gate: Name is strictly required
    if not clean_name:
        st.warning("⚠️ **Name required**: Please enter your name in the input box above to extract and preview your shifts.")
    else:
        all_shifts_dict = {}  # 중복 방지를 위한 딕셔너리 (키: (시작시각, 종료시각))
    
        with st.spinner(f"Extracting shifts for '{target_name}' from {len(uploaded_files)} uploaded files..."):
            for uploaded_file in uploaded_files:
                file_bytes = uploaded_file.read()
                shifts = process_pdf_file(file_bytes, target_name, selected_year, timezone_str, close_time)
                for s in shifts:
                    key = (s["start"], s["end"], s["location"])
                    all_shifts_dict[key] = s

        deduped_shifts = sorted(all_shifts_dict.values(), key=lambda x: x["start"])

        if not deduped_shifts:
            st.warning(f"Couldn't find any shifts for '{target_name}' in the uploaded PDF file(s). Please check the name in the sidebar.")
        else:
            # 상단 요약 지표 카드
            total_hours = sum((s["end"] - s["start"]).total_seconds() / 3600 for s in deduped_shifts)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Number of Uploaded Files", f"{len(uploaded_files)}")
            col2.metric("Total Shifts", f"{len(deduped_shifts)} Days")
            col3.metric("Total Hours", f"{total_hours:.1f} Hours")

            st.subheader("📋 List of Extracted Shifts")
            
            # 미리보기 데이터프레임 구성
            preview_data = []
            for s in deduped_shifts:
                hours = (s["end"] - s["start"]).total_seconds() / 3600
                preview_data.append({
                    "Date": s["start"].strftime("%Y-%m-%d (%a)"),
                    "Start Time": s["start"].strftime("%H:%M"),
                    "End Time": s["end"].strftime("%H:%M"),
                    "Work Hours": f"{hours:.1f}h",
                    "Location": s["location"]
                })
            
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True)

            # .ics 다운로드 버튼
            ics_bytes = build_ics_content(deduped_shifts, timezone_str)
            st.download_button(
                label="📅 Download the iCalendar files (.ics) - open it to import the schedule into your calendar",
                data=ics_bytes,
                file_name=f"{target_name}_schedule.ics",
                mime="text/calendar",
                type="primary"
            )
else:
    st.info("👆 Drag & Drop your PDF schedule files above.")