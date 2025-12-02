# app_case_manager.py （完整可直接覆蓋版本）
import streamlit as st
import pandas as pd
import datetime
import json
from pathlib import Path

# ====================== 頁面設定 ======================
st.set_page_config(
    page_title="個管師後台 - 運動處方箋系統",
    page_icon="doctor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== 模擬資料 ======================
if "patients" not in st.session_state:
    st.session_state.patients = {
        "001": {"name": "陳小美", "gender": "女", "age": 72, "phone": "0912-345-678"},
        "002": {"name": "溫實初", "gender": "男", "age": 78, "phone": "0933-456-789"},
        "003": {"name": "安陵容", "gender": "女", "age": 81, "phone": "0921-567-890"},
        "004": {"name": "余鶯兒", "gender": "女", "age": 75, "phone": "0987-654-321"},
        "005": {"name": "蘇培盛", "gender": "男", "age": 69, "phone": "0918-123-456"},
    }

# 處方箋檔案
PRESCRIPTION_FILE = Path("prescriptions.json")
if PRESCRIPTION_FILE.exists():
    st.session_state.prescriptions = json.loads(PRESCRIPTION_FILE.read_text(encoding="utf-8"))
else:
    st.session_state.prescriptions = {}

# ====================== 左側選單 ======================
with st.sidebar:
    st.title("個管師後台")
    st.write(f"歡迎，**王小明 個管師**")
    st.divider()

    btn1 = st.button("病人列表", use_container_width=True,
                     type="primary" if st.session_state.get("page", "病人列表") == "病人列表" else "secondary")
    btn2 = st.button("開立／編輯處方箋", use_container_width=True,
                     type="primary" if st.session_state.get("page", "病人列表") == "處方箋管理" else "secondary")

    if btn1:
        st.session_state.page = "病人列表"
        st.rerun()
    if btn2:
        st.session_state.page = "處方箋管理"
        st.rerun()

if "page" not in st.session_state:
    st.session_state.page = "病人列表"

# ====================== 主畫面 ======================
if st.session_state.page == "病人列表":
    st.header("病人列表")
    df = pd.DataFrame.from_dict(st.session_state.patients, orient="index")
    df = df.reset_index().rename(columns={"index": "病歷號"})
    df = df[["病歷號", "name", "gender", "age", "phone"]]

    for idx, row in df.iterrows():
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(f"**{row['name']}** ({row['gender']}, {row['age']}歲)")
                st.write(f"病歷號：{row['病歷號']}　｜　電話：{row['phone']}")
            with col2:
                pid = row['病歷號']
                if pid in st.session_state.prescriptions:
                    history = st.session_state.prescriptions[pid]
                    if isinstance(history, dict):
                        history = [history]
                    latest = history[-1] if history else {}
                    st.success(latest.get("status", "已開立"))
                else:
                    st.warning("尚未開立處方箋")
            with col3:
                if st.button("前往開立／編輯", key=pid, use_container_width=True):
                    st.session_state.selected_patient = pid
                    st.session_state.page = "處方箋管理"
                    st.rerun()

elif st.session_state.page == "處方箋管理":
    st.header("運動處方箋開立／編輯")

    patient_options = {v["name"]: k for k, v in st.session_state.patients.items()}
    default_name = st.session_state.patients[st.session_state.selected_patient]["name"] if "selected_patient" in st.session_state else None

    selected_name = st.selectbox("選擇長輩", options=list(patient_options.keys()),
                                index=list(patient_options.keys()).index(default_name) if default_name else 0)
    patient_id = patient_options[selected_name]
    patient = st.session_state.patients[patient_id]

    st.info(f"目前編輯對象：**{patient['name']}** ({patient['gender']}, {patient['age']}歲)　病歷號：{patient_id}")

    # 確保是 list 格式
    if patient_id not in st.session_state.prescriptions:
        st.session_state.prescriptions[patient_id] = []
    elif isinstance(st.session_state.prescriptions[patient_id], dict):
        st.session_state.prescriptions[patient_id] = [st.session_state.prescriptions[patient_id]]

    history = st.session_state.prescriptions[patient_id]
    latest = history[-1] if history else {
        "開立日期": datetime.date.today().strftime("%Y-%m-%d"),
        "個管師": "王小明 個管師",
        "處方內容": [],
        "備註": "",
        "status": "進行中"
    }

    # 支援「載入舊版本」
    if st.session_state.get(f"load_old_{patient_id}"):
        load_data = st.session_state[f"load_old_{patient_id}"]
        issue_date = datetime.datetime.strptime(load_data["開立日期"], "%Y-%m-%d").date()
        case_manager = load_data["個管師"]
        contents = "\n".join(load_data["處方內容"])
        notes = load_data.get("備註", "")
        status = load_data.get("status", "進行中")
        del st.session_state[f"load_old_{patient_id}"]
    else:
        issue_date = datetime.datetime.strptime(latest["開立日期"], "%Y-%m-%d").date()
        case_manager = latest["個管師"]
        contents = "\n".join(latest["處方內容"])
        notes = latest.get("備註", "")
        status = latest.get("status", "進行中")

    with st.form("處方箋表單"):
        st.subheader("運動處方箋內容")
        col1, col2 = st.columns(2)
        with col1:
            issue_date = st.date_input("開立日期", value=issue_date)
        with col2:
            case_manager = st.text_input("個管師姓名", value=case_manager)

        st.markdown("### 處方內容（每行一條建議）")
        contents = st.text_area("請輸入運動建議（換行分隔）", value=contents, height=200)

        notes = st.text_area("備註或提醒訊息（選填）", value=notes, height=100)

        status = st.selectbox("處方狀態", ["進行中", "已完成", "已暫停"],
                              index=["進行中", "已完成", "已暫停"].index(status))

        submitted = st.form_submit_button("儲存處方箋（新增一筆歷史）", type="primary", use_container_width=True)

        if submitted:
            new_prescription = {
                "開立日期": issue_date.strftime("%Y-%m-%d"),
                "個管師": case_manager,
                "處方內容": [line.strip() for line in contents.split("\n") if line.strip()],
                "備註": notes,
                "status": status,
                "最後更新": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.prescriptions[patient_id].append(new_prescription)
            PRESCRIPTION_FILE.write_text(json.dumps(st.session_state.prescriptions, ensure_ascii=False, indent=2), encoding="utf-8")
            st.success(f"已成功新增一筆處方箋給 {patient['name']}！")
            st.balloons()
            st.rerun()

    # ====================== 歷史處方箋顯示 ======================
    if history:
        st.divider()
        st.subheader("歷史處方箋紀錄（點開可載入舊版）")
        # 由新到舊排序
        for idx, p in enumerate(reversed(history)):
            actual_idx = len(history) - 1 - idx
            with st.expander(f"{p['開立日期']}　｜　{p['個管師']}　｜　{p.get('status', '進行中')}", expanded=(actual_idx == len(history)-1)):
                col1, col2 = st.columns([1, 4])
                with col1:
                    if p.get("status") == "進行中":
                        st.success("進行中")
                    elif p.get("status") == "已完成":
                        st.info("已完成")
                    else:
                        st.warning(p.get("status"))
                with col2:
                    st.caption(f"最後更新：{p.get('最後更新', '無記錄')}")

                st.markdown("### 處方內容")
                for item in p["處方內容"]:
                    st.markdown(f"• {item}")
                if p.get("備註"):
                    st.caption(f"備註：{p['備註']}")

                if st.button("載入此版本進行編輯", key=f"load_{patient_id}_{actual_idx}"):
                    st.session_state[f"load_old_{patient_id}"] = p
                    st.rerun()