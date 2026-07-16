import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# ============================== 網頁 Logo 與主題設定 ==============================
LOGO_IMAGE = "logo.webp"
has_logo = os.path.exists(LOGO_IMAGE)

st.set_page_config(
    page_title="學生晚餐費用",
    page_icon=LOGO_IMAGE if has_logo else "🍱",
    layout="centered"
)

st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

GSHEETS_URL = "https://docs.google.com/spreadsheets/d/1dZf3ua1q_FQkOhA8b_7__R_qWHZNsz2ror37OfUnILc/edit?resourcekey=&gid=1227634028#gid=1227634028"

# ============================== 學生名單與年級設定區 ==============================
STUDENT_LIST = {
    "曾以恩": "三年級", "許睿恆": "六年級", "陳靚恩": "六年級", "杜祤安": "六年級",
    "陳佑典": "四年級", "陳奕勳": "四年級", "曾以利": "五年級", "黃家賢": "五年級",
    "呂幸樂": "五年級", "蘇唯榛": "五年級", "蘇婕羽": "五年級", "王竑喆": "五年級",
    "許芷昀": "五年級", "黃琪蓁": "三年級", "李星呈": "六年級", "林宥瑄": "二年級",
    "陳晞": "五年級", "嚴珩瑀": "二年級", "嚴珩栩": "四年級", "蔣采霓": "四年級",
    "許奕晟": "二年級", "魏靖芸": "六年級", "林祐緯": "三年級", "魏宇杉": "五年級",
    "魏宇成": "三年級", "魏媽": "五年級"
}

GRADE_ORDER = {
    "一年級": 1, "二年級": 2, "三年級": 3, "四年級": 4, "五年級": 5, "六年級": 6, "未知名級": 7
}

sorted_students_info = sorted(STUDENT_LIST.items(), key=lambda x: (GRADE_ORDER.get(x[1], 99), x[0]))
name_list_by_grade = ["請選擇學生..."] + [f"[{grade}] {name}" for name, grade in sorted_students_info]


# ============================== 統一從 Google 試算表載入資料 ==============================
try:
    clean_url = GSHEETS_URL.split("/edit")[0]  + "/edit"
        
    base_url = GSHEETS_URL.split("/edit")[0]
    csv_url = f"{base_url}/export?format=csv&gid=0"


    raw_df = pd.read_csv(csv_url)
    
    if raw_df is not None and not raw_df.empty:
        raw_df.columns = raw_df.columns.str.strip()
        df = pd.DataFrame()
    
        if "時間戳記" in raw_df.columns or raw_df.shape[1] >= 5:
            df["日期"] = raw_df.iloc[:, 1]  # 第 2 欄是日期
            df["姓名"] = raw_df.iloc[:, 2]  # 第 3 欄是學生姓名
            df["金額"] = raw_df.iloc[:, 3]  # 第 4 欄是晚餐金額
            df["備註"] = raw_df.iloc[:, 4] if raw_df.shape[1] > 4 else ""  # 第 5 欄是備註
        else:
            df["日期"] = raw_df.iloc[:, 0] if raw_df.shape[1] > 0 else ""
            df["姓名"] = raw_df.iloc[:, 1] if raw_df.shape[1] > 1 else ""
            df["金額"] = raw_df.iloc[:, 2] if raw_df.shape[1] > 2 else ""
            df["備註"] = raw_df.iloc[:, 3] if raw_df.shape[1] > 3 else ""

        # 格式清理
        df["姓名"] = df["姓名"].astype(str).str.strip().str.replace(r"^\[.*\]\s*", "", regex=True)
        df["金額"] = pd.to_numeric(df["金額"], errors='coerce').fillna(0)
        df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
        df["月份"] = df["日期"].dt.strftime("%Y-%m").fillna(datetime.now().strftime("%Y-%m"))
        df["年級"] = df["姓名"].map(STUDENT_LIST).fillna("未知名級")
    else:
        df = pd.DataFrame(columns=["日期", "姓名", "年級", "金額", "備註", "月份"])
            
except Exception as e:
    st.error(f"雲端資料庫讀取失敗: {e}")
    df = pd.DataFrame(columns=["日期", "姓名", "年級", "金額", "備註", "月份"])


# --- 側邊欄導覽選單 ---
st.sidebar.title("系統選單")
if has_logo:
    st.sidebar.image(LOGO_IMAGE, use_container_width=True)

page = st.sidebar.radio("請選擇功能：", ["📝 填寫晚餐紀錄", "📊 每月費用彙整", "⚙️ 管理歷史紀錄"])

# ============================== 頁面 1：填寫紀錄 ==============================
if page == "📝 填寫晚餐紀錄":
    if has_logo:
        coll, col2, col3 = st.columns(3)
        with col2:
            st.image(LOGO_IMAGE, width=200)
            
    st.session_state["last_date"] = datetime.now()
    if "last_note" not in st.session_state:
        st.session_state["last_note"] = ""
        
    date = st.date_input("選擇日期", st.session_state["last_date"])
    selected_display = st.selectbox("請選擇學生姓名 (依年級排序)", ["請選擇學生..."] + name_list_by_grade)
    price = st.number_input("晚餐金額", min_value=0, step=1)
    note = st.text_input("備註 (晚餐類型，例如：麥當勞、便當)", st.session_state["last_note"])
    
    confirm = st.checkbox("勾選此處，確認資料無誤")
    submit = st.button("🚀 送出紀錄", disabled=not confirm)
    
    if submit:
        if selected_display == "請選擇學生...":
            st.error("❌ 請先選擇一位學生姓名！")
        else:
            try:
                import requests
                
                pure_name = selected_display.split("] ")[1] if "] " in selected_display else selected_display
                
                form_url = "https://docs.google.com/forms/d/1F_jL39Vf3IL8rdUVvybRuJt54NRy4SyfRdv_m_T9rzg/formResponse"
                
                form_data = {
                   "entry.396279679": date.strftime('%Y-%m-%d'), # 日期
                   "entry.1784386595": pure_name,                 # 學生姓名
                   "entry.1788176734": str(price),                # 晚餐金額
                   "entry.1731490716": note                       # 備註
                }
                
                response = requests.post(form_url, data=form_data)
                
                if response.status_code == 200:
                    st.success("🎉 紀錄已成功自動送出並同步至 Google 雲端！")
                    st.balloons()
                    st.session_state["last_note"] = note
                else:
                    st.error(f"發送失敗，代碼: {response.status_code}。已為您切換為手動備用方案：")
                    st.markdown(f'➡️ [打開 Google 試算表手動登記]({GSHEETS_URL})')
                    
            except Exception as e:
                st.error(f"系統自動寫入失敗: {e}")

# ============================== 頁面 2：每月費用彙整 ==============================
elif page == "📊 每月費用彙整":
    st.title("📊 每月應繳費用彙整")
    if not df.empty and "月份" in df.columns and "姓名" in df.columns:
        student_summary = df.groupby(["月份", "年級", "姓名"])["金額"].sum().reset_index()
        student_summary["年級權重"] = student_summary["年級"].map(GRADE_ORDER)
        student_summary = student_summary.sort_values(by=["月份", "年級權重", "姓名"]).drop(columns=["年級權重"])
        
        st.subheader("👥 學生個人每月帳單")
        st.dataframe(student_summary, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📥 匯出 Excel 資料")
        
        display_df = df.copy()
        display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
        available_cols = [c for c in ["日期", "年級", "姓名", "金額", "備註"] if c in display_df.columns]
        history_df = display_df[available_cols]
        if "日期" in history_df.columns:
            history_df = history_df.sort_values(by="日期", ascending=False)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            student_summary.to_excel(writer, sheet_name='學生個人彙整', index=False)
            history_df.to_excel(writer, sheet_name='歷史詳細明細', index=False)
            
        st.download_button(
            label="📥 下載 Excel 報表",
            data=buffer.getvalue(),
            file_name=f"學生晚餐費用統計表_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown("---")
        st.subheader("📜 歷史明細詳細紀錄")
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("目前雲端試算表還沒有任何紀錄，請先前往 Google 試算表填寫第一筆紀錄吧！")

# ============================== 頁面 3：管理歷史紀錄 ==============================
elif page == "⚙️ 管理歷史紀錄":
    st.title("⚙️ 管理歷史紀錄 (修改 / 刪除)")
    st.info("💡 為了確保資料安全，如需修改或刪除歷史明細，請直接點擊下方連結前往 Google 雲端試算表手動編輯。")
    st.markdown(f'➡️ [點此開啟 Google 試算表進行修改/刪除]({GSHEETS_URL})')
