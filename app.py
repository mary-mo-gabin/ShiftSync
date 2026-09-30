from datetime import datetime, time
import pandas as pd
import streamlit as st
from parser import build_ics_content, process_pdf_file

# =============================================================================
# 페이지 기본 설정
# =============================================================================
st.set_page_config(
    page_title="PDF Roster to Calendar",
    page_icon="⛳",
    layout="wide"
)

# =============================================================================
# 사이드바 설정 (사용자 정의 옵션)
# =============================================================================
st.sidebar.header("⚙️ Settings")
target_name = st.sidebar.text_input("Employee Name", placeholder="e.g., Mary")
selected_year = st.sidebar.number_input("Year", value=datetime.now().year, step=1)
timezone_str = st.sidebar.selectbox(
    "Timezone",
    ["America/Edmonton", "America/Vancouver", "America/Toronto", "Asia/Seoul"],
    index=0
)
close_hour = st.sidebar.slider("Close Hour", min_value=18, max_value=24, value=23)
close_time = time(close_hour if close_hour < 24 else 23, 59 if close_hour == 24 else 0)


# =============================================================================
# 메인 UI 레이아웃
# =============================================================================
st.title("⛳ Screen Golf Shift to Calendar")
st.markdown("Drag and drop your PDF shift schedule files to convert them into an **.ics Calendar file**.")

# 다중 파일 업로더 (드래그 앤 드롭 기본 지원)
uploaded_files = st.file_uploader(
    "Upload PDF schedule files (Drag & Drop or click to browse)",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
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
        col1.metric("Number of Uploaded Files", f"{len(uploaded_files)}개")
        col2.metric("Total Shifts", f"{len(deduped_shifts)}회")
        col3.metric("Total Hours", f"{total_hours:.1f} 시간")

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