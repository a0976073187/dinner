import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
import urllib.request
import urllib.parse
import json

# ========================================== 網頁 Logo 與主題設定 ==========================================
LOGO_IMAGE = "logo.webp"
has_logo = os.path.exists(LOGO_IMAGE)

st.set_page_config(
    page_title="學生晚餐費用",
    page_icon=LOGO_IMAGE if has_logo else "🍱",
    layout="centered"
)

st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# 您的 Google 試算表公開共用網址（請確保已在 Google 雲端設定為「知道連結的人皆可檢視」）
GSHEETS_URL = "https://google.com"

# ========================================== 學生名單與年級設定區 ==========================================
STUDENT_LIST = {
    "曾以恩": "三年級", "許家恆": "六年級", "陳觀題": "六年級", "杜翔安": "六年級",
    "陳佑典": "四年級", "陳奕勳": "四年級", "曾以利": "五年級", "黃承賢": "五年級",
    "呂韋樂": "五年級", "蘇珈媃": "五年級", "蘇倢羽": "五年級", "王竑詰": "五年級",
    "許玗琁": "五年級", "黃琪珊": "三年級", "李星呈": "六年級", "林育瑄": "二年級",
    "陳晞": "五年級", "嚴昕嬡": "二年級", "嚴竤翔": "四年級", "蔣采宣": "四年級",
    "許奕晨": "二年級", "魏靖芸": "六年級", "林柏翰": "三年級", "魏宇杉": "五年級",
    "魏宇成": "三年級", "魏嫣": "五年級"
}

GRADE_ORDER = {
    "一年級": 1, "二年級": 2, "三年級": 3, "四年級": 4, "五年級": 5, "六年級": 6, "未知年級": 7
}

sorted_students_info = sorted(STUDENT_LIST.items(), key=lambda x: (GRADE_ORDER.get(x, 99), x))
name_list_by_grade = ["請選擇學生..."] + [f"[{grade}] {name}" for name, grade in sorted_students_info]

# ========================================== 內建讀取函數 (完全免裝外部套件) ==========================================
def load_cloud_data():
    try:
        # 將 edit 網址轉換為標準的 CSV 匯出網址，指向第一個分頁 gid=0
        base_url = GSHEETS_URL.split("/edit")
        csv_url = f"{base_url}/export?format=csv&gid=0"
        
        # 使用 Python 內建的 urllib 進行網路下載
        req = urllib.request.Request(csv_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            csv_data = response.read()
            df = pd.read_csv(io.BytesIO(csv_data))
            
            if df is not None and not df.empty:
                df.columns = df.columns.str.strip()
                df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
                df["金額"] = pd.to_numeric(df["金額"], errors='coerce').fillna(0)
                df["月份"] = df["日期"].dt.strftime("%Y-%m").fillna(datetime.now().strftime("%Y-%m"))
                df["年級"] = df["姓名"].map(STUDENT_LIST).fillna("未知年級")
                return df
    except Exception as e:
        st.error(f"雲端資料庫讀取失敗：{e}")
    return pd.DataFrame(columns=["日期", "姓名", "年級", "金額", "備註", "月份"])

# 載入最新雲端資料
df = load_cloud_data()

# ========================================== 側邊欄導覽選單 ==========================================
st.sidebar.title("系統選單")
if has_logo:
    st.sidebar.image(LOGO_IMAGE, use_container_width=True)

page = st.sidebar.radio("請選擇功能：", ["📝 填寫晚餐紀錄", "📊 每月費用彙整", "⚙️ 管理歷史紀錄"])

# ========================================== 頁面 1：填寫紀錄 ==========================================
if page == "📝 填寫晚餐紀錄":
    if has_logo:
        col1, col2, col3 = st.columns(3)
        with col2:
            st.image(LOGO_IMAGE, width=200)
            
    st.session_state["last_date"] = datetime.now()
    if "last_note" not in st.session_state:
        st.session_state["last_note"] = ""
        
    date = st.date_input("選擇日期", st.session_state["last_date"])
    selected_display = st.selectbox("請選擇學生姓名 (依年級排序)", name_list_by_grade)
    price = st.number_input("晚餐金額", min_value=0, step=1)
    note = st.text_input("備註 (晚餐類型，例如：麥當勞、便當)", st.session_state["last_note"])
    
    confirm = st.checkbox("勾選此處，確認資料無誤")
    submit = st.button("📥 送出紀錄", disabled=not confirm)
    
    # 彈出確認對話框
    @st.dialog("⚠️ 請確認晚餐紀錄資料")
    def confirm_submit_dialog(d, name, p, n):
        st.warning("請核對下方資料是否完全正確：")
        st.write(f"📅 **紀錄日期**：{d.strftime('%Y-%m-%d')}")
        st.write(f"👤 **學生姓名**：{name}")
        st.write(f"💰 **晚餐金額**：${int(p)} 元")
        st.write(f"💬 **備註內容**：{n if n else '無'}")
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        if c1.button("❌ 點此取消", use_container_width=True):
            st.rerun()
            
        if c2.button("✅ 確定送出", type="primary", use_container_width=True):
            # 💡 終極修復的 Google 表單發送，直接補正網址代號
            form_url = "https://google.com"
            form_data = {
                "entry.396279679": d.strftime('%Y-%m-%d'),
                "entry.1784386595": name,
                "entry.1788176734": str(int(p)),
                "entry.1731490716": n
            }
            try:
                data_encoded = urllib.parse.urlencode(form_data).encode('utf-8')
                req = urllib.request.Request(form_url, data=data_encoded, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    pass
                st.session_state["submit_success"] = True
                st.session_state["last_note"] = n
                st.rerun()
            except Exception as e:
                st.error(f"雲端同步寫入失敗: {e}")

    if submit:
        if selected_display == "請選擇學生...":
            st.error("❌ 請先選擇一位學生姓名！")
        else:
            pure_name = selected_display.split("] ") if "] " in selected_display else selected_display
            confirm_submit_dialog(date, pure_name, price, note)

    if st.session_state.get("submit_success", False):
        st.success("🎉 紀錄已成功儲存並同步至雲端系統！不同電腦已完全互通！")
        st.balloons()
        st.session_state["submit_success"] = False

# ========================================== 頁面 2：每月費用彙整 ==========================================
elif page == "📊 每月費用彙整":
    st.title("📊 每月費用彙整")
    
    if not df.empty and "月份" in df.columns and "姓名" in df.columns and "金額" in df.columns:
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
        st.info("💡 目前雲端內還沒有任何完整紀錄。請切換至『填寫晚餐紀錄』送出第一筆吧！")

# ========================================== 頁面 3：管理歷史紀錄 ==========================================
elif page == "⚙️ 管理歷史紀錄":
    st.title("⚙️ 管理歷史紀錄 (修改 / 刪除)")
    st.info("💡 因本地環境限制，雲端刪除功能目前請直接前往 Google 試算表後台整列選取並按右鍵刪除，所有電腦將會同步即時更新！")
    
    if not df.empty:
        display_df = df.copy()
        display_df["顯示日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
        display_df = display_df.sort_values(by="日期", ascending=False)
        
        for idx, row in display_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                col1.write(f"📅 {row['顯示日期']}")
                col2.write(f"👤 {row['姓名']} ({row['年級']})")
                col3.write(f"💰 ${int(row['金額'])}")
                col4.write(f"💬 {row['備註'] if pd.notna(row['備註']) else ''}")
            st.markdown("<hr style='margin:0.5rem 0; border-top: 1px dashed #ccc;'/>", unsafe_allow_html=True)
    else:
        st.info("💡 目前雲端尚無任何歷史明細可供管理。")
