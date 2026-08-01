"""시민용 신청 상태 조회 페이지. 전화 통화에서 확인했던 것과 같은 이름+생년월일로 조회한다.

담당자 승인 화면(../app.py)과 별도 페이지로 분리 -- 정책명/서류초안/거부사유 같은 상세
정보는 여기서 절대 보여주지 않는다 (social_impact 백엔드의 /cases/status가 애초에
그런 정보를 안 돌려줌, 단계 문구만 옴)."""
import datetime
import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="실버브릿지 신청 상태 조회", layout="centered")
st.title("실버브릿지 — 내 신청 상태 조회")
st.caption("전화 상담 때 말씀하신 성함과 생년월일을 입력하시면 지금 진행 상황을 알려드려요.")

with st.form("status-form"):
    full_name = st.text_input("성함")
    birth_date = st.date_input(
        "생년월일",
        value=None,
        min_value=datetime.date(1920, 1, 1),
        max_value=datetime.date.today(),
        format="YYYY-MM-DD",
    )
    submitted = st.form_submit_button("조회하기")

if submitted:
    if not full_name.strip() or birth_date is None:
        st.warning("성함과 생년월일을 모두 입력해 주세요.")
    else:
        response = requests.get(
            f"{API_BASE_URL}/cases/status",
            params={"full_name": full_name.strip(), "birth_date": birth_date.isoformat()},
        )
        if response.status_code == 404:
            st.info(response.json().get("detail", "일치하는 신청 정보를 찾을 수 없어요."))
        else:
            response.raise_for_status()
            result = response.json()
            st.success(f"현재 상태: **{result['stage']}**")
            if result["decision_ready"]:
                st.caption("결과 안내 전화를 곧 받으실 수 있어요.")
            else:
                st.caption("담당 공무원이 검토 중이에요. 조금만 더 기다려 주세요.")
