"""공무원용 승인/반려 대시보드 (Step 4). social_impact 백엔드의 /cases, /elders API를 호출.

팀원이 만든 yai_hackathon_silverbridge의 officer_dashboard(HTML/JS)를 참고해서 카드 레이아웃,
접이식 서류 보기, 반려 사유 입력 흐름을 그대로 옮겼다 -- 다만 그쪽 백엔드는 케이스 하나에
추천 여러 건 + 신청서 여러 건이 달리는 구조라 그 부분은 안 맞아서 뺐다. social_impact의 Case는
정책 하나당 초안 하나뿐이라 승인/반려도 케이스 단위로 한 번씩만 한다."""
import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="실버브릿지 승인 대시보드", layout="wide")
st.title("실버브릿지 — 복지 신청 승인 대시보드")
st.caption(
    "시민이 전화 상담을 마치면 이 화면에 사례가 자동으로 나타나요. "
    "신청서 내용을 확인하고 승인 또는 반려를 결정해 주세요."
)

if st.button("사례 새로고침"):
    st.rerun()


@st.cache_data(ttl=30)
def _elder_name(elder_id: int) -> str:
    resp = requests.get(f"{API_BASE_URL}/elders/{elder_id}")
    if not resp.ok:
        return f"어르신 #{elder_id}"
    return resp.json().get("full_name", f"어르신 #{elder_id}")


response = requests.get(f"{API_BASE_URL}/cases/pending")
response.raise_for_status()
cases = response.json()

if not cases:
    st.info("아직 승인 대기 중인 신청이 없어요. 시민이 통화를 마치면 여기에 나타나요.")

for case in cases:
    reject_open_key = f"reject-open-{case['id']}"

    with st.container(border=True):
        st.subheader(f"{_elder_name(case['elder_id'])} — {case['policy_title']}")
        st.caption(f"통화 ID: {case['call_id']} · 신청일: {case['created_at'][:10]}")

        with st.expander("AI 작성 서류 초안 보기"):
            st.text(case["draft_content"])

        approve_col, reject_col = st.columns(2)
        with approve_col:
            if st.button("승인", key=f"approve-{case['id']}", type="primary", use_container_width=True):
                requests.post(f"{API_BASE_URL}/cases/{case['id']}/approve").raise_for_status()
                st.success("승인 완료. 어르신께 자동으로 콜백이 발신됩니다.")
                st.rerun()
        with reject_col:
            if st.button("반려", key=f"reject-btn-{case['id']}", use_container_width=True):
                st.session_state[reject_open_key] = True

        if st.session_state.get(reject_open_key):
            reason = st.text_input("반려 사유", key=f"reject-reason-{case['id']}")
            if st.button("반려 확정", key=f"reject-confirm-{case['id']}"):
                if not reason.strip():
                    st.warning("반려 사유를 입력해 주세요.")
                else:
                    requests.post(
                        f"{API_BASE_URL}/cases/{case['id']}/reject",
                        json={"reason": reason},
                    ).raise_for_status()
                    st.success("반려 처리되었고, 어르신께 자동으로 콜백이 발신됩니다.")
                    del st.session_state[reject_open_key]
                    st.rerun()
