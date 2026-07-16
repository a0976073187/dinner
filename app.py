import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# ========================================== 網頁 Logo 與主題設定 ==========================================
LOGO_IMAGE = "logo.webp"
has_logo = os.path.exists(LOGO_IMAGE)

st.set_page_config(
    page_title="學生晚餐費用",
    page_icon=LOGO_IMAGE if has_logo else "🍱",
    layout="centered"
)

st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# 為了保留您原本的雲端連結備查（本機版已不需要它來運作儲存）
GSHEETS_URL = "https://google.com"

# ========================================== 學生名單與年級設定區 ==========================================
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
    "一年級": 1, "二年級": 2, "三年級": 3, "四年級": 4, "五年級": 5, "六年級": 6, "未知年級": 7
}

sorted_students_info = sorted(STUDENT_LIST.items(), key=lambda x: (GRADE_ORDER.get(x[1], 99), x[0]))
name_list_by_grade = ["請選擇學生..."] + [f"[{grade}] {name}" for name, grade in sorted_students_info]

# ========================================== 本機 CSV 檔案初始化 ==========================================
DB_FILE = "dinner_records.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # 確保欄位格式正確
            if not df.empty:
                df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
                df["金額"] = pd.to_numeric(df["金額"], errors='coerce').fillna(0)
                df["月份"] = df["日期"].dt.strftime("%Y-%m").fillna(datetime.now().strftime("%Y-%m"))
                df["年級"] = df["姓名"].map(STUDENT_LIST).fillna("未知年級")
            return df
        except:
            pass
    # 若檔案不存在或毀損，回傳空的標準結構
    return pd.DataFrame(columns=["日期", "姓名", "年級", "金額", "備註", "月份"])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# 載入目前所有的歷史資料
df = load_data()

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
    
    # ⭐ 新增：二次確認對話框功能
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
            try:
                # 建立新的一筆資料並直接使用外部讀好的 df 變數
                new_row = pd.DataFrame([{
                    "日期": pd.to_datetime(d),
                    "姓名": name,
                    "年級": STUDENT_LIST.get(name, "未知年級"),
                    "金額": float(p),
                    "備註": n,
                    "月份": d.strftime("%Y-%m")
                }])
                
                # 這裡調用全域資料並儲存
                global df
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                
                # 透過 session_state 把成功訊息帶到外層，避免對話框關閉時訊息被重置
                st.session_state["submit_success"] = True
                st.session_state["last_note"] = n
                st.rerun()
            except Exception as e:
                st.error(f"系統自動寫入失敗: {e}")

    # 當點擊最外層的「送出紀錄」按鈕時
    if submit:
        if selected_display == "請選擇學生...":
            st.error("❌ 請先選擇一位學生姓名！")
        else:
            pure_name = selected_display.split("] ")[1] if "] " in selected_display else selected_display
            # 💡 觸發彈出視窗
            confirm_submit_dialog(date, pure_name, price, note)

    # 顯示成功訊息與噴氣球（當對話框按下確定重新整理網頁後執行）
    if st.session_state.get("submit_success", False):
        st.success("🎉 紀錄已成功儲存至本機系統！")
        st.balloons()
        # 清除旗標，避免下次進網頁重複噴氣球
        st.session_state["submit_success"] = False

# ========================================== 頁面 2：每月費用彙整 ==========================================
elif page == "📊 每月費用彙整":
    st.title("📊 每月費用彙整")
    
    if not df.empty and "月份" in df.columns and "姓名" in df.columns:
        # 計算學生個人每月帳單
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
        st.info("💡 目前系統內還沒有任何紀錄，請切換至『填寫晚餐紀錄』頁面新增第一筆資料吧！")

# ========================================== 頁面 3：管理歷史紀錄 ==========================================
elif page == "⚙️ 管理歷史紀錄":
    st.title("⚙️ 管理歷史紀錄 (修改 / 刪除)")
    st.info("💡 這裡可以直接查看您存在這台電腦裡的所有歷史明細。您可以一鍵刪除任何寫錯的資料。")
    
    if not df.empty:
        # 複製一份用來顯示的資料，並將日期轉換成好看的字串格式
        display_df = df.copy()
        display_df["顯示日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
        # 依日期由新到舊排序
        display_df = display_df.sort_values(by="日期", ascending=False)
        
        # 顯示歷史明細清單（這裡的 idx 就是該筆資料在原本 df 裡的真實編號）
        for idx, row in display_df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 3, 1]) # 調配欄位寬度讓畫面更好看
                col1.write(f"📅 {row['顯示日期']}")
                col2.write(f"👤 {row['姓名']} ({row['年級']})")
                col3.write(f"💰 ${int(row['金額'])}")
                col4.write(f"💬 {row['備註'] if pd.notna(row['備註']) else ''}")
                
                # 🗑️ 直接利用原資料的真實編號 idx 進行刪除
                if col5.button("🗑️ 刪除", key=f"del_{idx}"):
                    df = df.drop(idx) # ⭐ 直接秒殺這行編號的資料！
                    save_data(df)     # 儲存回本機 CSV
                    st.success("紀錄已成功刪除！")
                    st.rerun()        # 重新整理網頁
            st.markdown("<hr style='margin:0.5rem 0; border-top: 1px dashed #ccc;'/>", unsafe_allow_html=True)
    else:
        st.info("💡 目前尚無任何歷史明細可供管理。")
