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

# 💡 強制阻斷 Google 翻譯修改網頁 DOM 節點，徹底防止黃臉 removeChild 崩潰
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# ⚠️ 這是您的 Google 試算表真實網址
GSHEETS_URL = "https://google.com"

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

sorted_students_info = sorted(STUDENT_LIST.items(), key=lambda x: (GRADE_ORDER.get(x, 99), x))
name_list_by_grade = [f"[{grade}] {name}" for name, grade in sorted_students_info]

# ============================== 統一從 Google 試算表載入資料 ==============================
try:
    # 💡 終極修正：直接使用純字串替換，徹底拔除所有可能產生 list 拼接錯誤的隱患
    csv_url = str(GSHEETS_URL).replace("/edit", "/export?format=csv").replace("#", "&")
    raw_df = pd.read_csv(csv_url)
    
    if raw_df is not None and not raw_df.empty:
        raw_df.columns = raw_df.columns.str.strip()
        df = pd.DataFrame()
        
        # 💡 位置防呆：如果第一欄是時間戳記，改用欄位位置強制指定，完全解決 None 與錯位問題
        if "時間戳記" in raw_df.columns or raw_df.shape[1] >= 5:
            df["日期"] = raw_df.iloc[:, 1]  # 第 2 欄是日期
            df["姓名"] = raw_df.iloc[:, 2]  # 第 3 欄是學生姓名
            df["金額"] = raw_df.iloc[:, 3]  # 第 4 欄是晚餐金額
            df["備註"] = raw_df.iloc[:, 4] if raw_df.shape > 4 else ""  # 第 5 欄是備註
        else:
            df["日期"] = raw_df.iloc[:, 0] if raw_df.shape > 0 else ""
            df["姓名"] = raw_df.iloc[:, 1] if raw_df.shape > 1 else ""
            df["金額"] = raw_df.iloc[:, 2] if raw_df.shape > 2 else ""
            df["備註"] = raw_df.iloc[:, 3] if raw_df.shape > 3 else ""

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
                
                # 取得乾淨不含中括號的學生姓名
                pure_name = selected_display.split("] ") if "] " in selected_display else selected_display
                
                form_url = "https://google.com"
                form_data = {"entry.569300600": date.strftime('%Y-%m-%d'), "entry.1017833502": pure_name, "entry.1593397984": str(price), "entry.1203096180": note}
                
                requests.post(form_url, data=form_data)
                st.success("🎉 紀錄已成功自動送出並同步至 Google 雲端！")
                st.balloons()
                st.session_state["last_note"] = note
            except Exception as e:
                st.error(f"系統自動寫入失敗: {e}")

# ============================== 頁面 2：每月費用彙整 ==============================
elif page == "📊 每月費用彙整":
    st.title("📊 每月應繳費用彙整")
    
    # 確保有實質的學生姓名資料才顯示
    valid_df = df[df["姓名"].notna() & (df["姓名"] != "nan") & (df["姓名"] != "")]
    
    if not valid_df.empty:
        try:
            # 1. 學生個人每月帳單加總
            student_summary = valid_df.groupby(["月份", "年級", "姓名"])["金額"].sum().reset_index()
            student_summary["年級權重"] = student_summary["年級"].map(GRADE_ORDER)
            student_summary = student_summary.sort_values(by=["月份", "年級權重", "姓名"]).drop(columns=["年級權重"])
            
            st.subheader("👥 學生個人每月帳單")
            st.dataframe(student_summary, use_container_width=True)
            
            st.markdown("---")
            st.subheader("📥 匯出 Excel 資料")
            
            display_df = valid_df.copy()
            if pd.api.types.is_datetime64_any_dtype(display_df["日期"]):
                display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
                
            history_df = display_df[["日期", "年級", "姓名", "金額", "備註"]].sort_values(by="日期", ascending=False)
            
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
        except Exception as err:
            st.error(f"資料統計分析時發生錯誤: {err}")
    else:
        st.info("目前雲端試算表還沒有任何有效的學生晚餐紀錄，請到首頁登記第一筆紀錄吧！")

# ============================== 頁面 3：管理歷史紀錄 ==============================
elif page == "⚙️ 管理歷史紀錄":
    st.title("⚙️ 管理歷史紀錄 (修改 / 刪除)")
    st.info("💡 為了確保資料安全與相容性，如需修改或刪除歷史明細，請直接點擊下方連結前往 Google 雲端試算表手動編輯。")
    st.markdown(f'➡️ [點此開啟 Google 試算表進行修改/刪除]({GSHEETS_URL})')
