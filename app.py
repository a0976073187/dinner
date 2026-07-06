import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# ==================== 🎨 網頁 Logo 與主題設定 ====================
LOGO_IMAGE = "logo.webp"
has_logo = os.path.exists(LOGO_IMAGE)

st.set_page_config(
    page_title="學生晚餐費用",
    page_icon=LOGO_IMAGE if has_logo else "🍽️",
    layout="centered"
)
# ================================================================

# 設定檔案名稱
DB_FILE = "dinner_records.csv"

# ==================== 🎒 學生名單與年級設定區 ====================
STUDENT_LIST = {
    "曾以恩": "三年級",
    "許睿恆": "六年級",
    "陳靚恩": "六年級",
    "杜祤安": "六年級",
    "陳佑典": "四年級",
    "陳奕勳": "四年級",
    "曾以利": "五年級",
    "黃家賢": "五年級",
    "呂孝樂": "五年級",
    "蘇唯榛": "五年級",
    "蘇婕羽": "五年級",
    "王竑喆": "五年級",
    "許芷昀": "五年級",
    "黃琪蓁": "三年級",
    "李星呈": "六年級",
    "林宥瑄": "二年級",
    "陳晞": "五年級",
    "嚴珩瑀": "二年級",
    "嚴珩栩": "四年級",
    "蔣采霓": "四年級",
    "許奕晟": "二年級",
    "魏靖芸": "六年級",
    "林祐緯": "三年級",
    "魏宇杉": "五年級",
    "魏宇成": "三年級",
    "魏媽": "五年級",
    "蔣采霓": "四年級",
}

# 定義年級的自訂排序權重
GRADE_ORDER = {
    "一年級": 1,
    "二年級": 2,
    "三年級": 3,
    "四年級": 4,
    "五年級": 5,
    "六年級": 6,
    "未知名級": 7
}

# 產生按照年級排序的下拉選單名單
sorted_students_info = sorted(
    STUDENT_LIST.items(), 
    key=lambda x: (GRADE_ORDER.get(x[1], 99), x[0])
)
name_list_by_grade = [f"[{grade}] {name}" for name, grade in sorted_students_info]
# ================================================================

# 載入資料
if os.path.exists(DB_FILE):
    try:
        df = pd.read_csv(DB_FILE)
    except:
        df = pd.DataFrame(columns=["日期", "姓名", "年級", "金額", "備註"])
else:
    df = pd.DataFrame(columns=["日期", "姓名", "年級", "金額", "備註"])

# --- 側邊欄導覽選單 ---
st.sidebar.title("系統選單")

if has_logo:
    st.sidebar.image(LOGO_IMAGE, use_container_width=True)

page = st.sidebar.radio("請選擇功能：", ["📝 填寫晚餐紀錄", "📊 每月費用彙整", "⚙️ 管理歷史紀錄"])

# 確保日期格式正確
if not df.empty:
    df["日期"] = pd.to_datetime(df["日期"], format='mixed')
    df["月份"] = df["日期"].dt.strftime("%Y-%m")

# ==================== 頁面 1：填寫紀錄 ====================
if page == "📝 填寫晚餐紀錄":
    if has_logo:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(LOGO_IMAGE, width=200)
            
    # 💡 修正點：移除含有 HTML 的 st.markdown 語法，改用最新標準原生標題
    st.title("📝 學生晚餐紀錄系統")
    st.write("請在下方輸入今日的訂餐資訊：")
    
    if "last_date" not in st.session_state:
        st.session_state["last_date"] = datetime.now()
    if "last_note" not in st.session_state:
        st.session_state["last_note"] = ""

    date = st.date_input("選擇日期", st.session_state["last_date"])
    
    selected_display = st.selectbox("選擇點餐學生姓名（依年級排序）", ["請選擇學生..."] + name_list_by_grade)
    
    price = st.number_input("晚餐金額", min_value=0, step=1)
    note = st.text_input("備註（晚餐類型，例如：麥當勞、便當）", st.session_state["last_note"])
    
    confirm = st.checkbox("勾選此處，確認資料無誤")
    submit = st.button("🚀 送出紀錄", disabled=not confirm)
    if submit:
        if selected_display == "請選擇學生...":
            st.error("❌ 請先選擇一位學生！")
        elif price <= 0:
            st.error("❌ 金額必須大於 0 元！")
        else:
            st.session_state["last_date"] = date
            st.session_state["last_note"] = note
            
            pure_name = selected_display.split("] ")[1]
            grade = STUDENT_LIST.get(pure_name, "未知名級")
            
            new_data = pd.DataFrame([[date.strftime("%Y-%m-%d"), pure_name, grade, price, note]], columns=["日期", "姓名", "年級", "金額", "備註"])
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.success(f"✅ 已成功記錄：【{grade}】{pure_name} 吃了 {price} 元！")
            st.rerun()
            st.success("🎉 紀錄已成功送出！")

# ==================== 頁面 2：每月費用彙整 ====================
elif page == "📊 每月費用彙整":
    st.title("📊 每月應繳費用彙整")
    if not df.empty:
        student_summary = df.groupby(["月份", "年級", "姓名"])["金額"].sum().reset_index()
        
        student_summary["年級權重"] = student_summary["年級"].map(GRADE_ORDER)
        student_summary = student_summary.sort_values(by=["月份", "年級權重", "姓名"]).drop(columns=["年級權重"])
        
        st.subheader("👤 學生個人每月帳單")
        st.dataframe(student_summary, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📥 匯出 Excel 資料")
        
        display_df = df.copy()
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
    else:
        st.info("目前還沒有任何紀錄，請先到左側選單填寫紀錄吧！")

# ==================== 頁面 3：管理歷史紀錄 ====================
elif page == "⚙️ 管理歷史紀錄":
    st.title("⚙️ 管理歷史紀錄（修改 / 刪除）")
    if not df.empty:
        display_df = df.copy()
        display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
        
        record_options = [f"編號 {i}: {row['日期']} - [{row['年級']}] {row['姓名']} (${row['金額']}) [{row['備註'] if pd.notna(row['備註']) else ''}]" for i, row in display_df.iterrows()]
        selected_option = st.selectbox("請選擇一筆您想要修改或刪除的紀錄：", record_options)
        
        if selected_option:
            selected_index = int(selected_option.split(":")[0].replace("編號 ", ""))
            current_row = df.loc[selected_index]
            
            st.markdown("---")
            action = st.radio("您想要對這筆紀錄做什麼？", ["修改此筆資料", "刪除此筆資料"])
            
            if action == "修改此筆資料":
                st.subheader("✏️ 修改資料內容")
                edit_date = st.date_input("修改日期", pd.to_datetime(current_row["日期"]))
                
                current_display_name = f"[{current_row['年級']}] {current_row['姓名']}"
                default_idx = name_list_by_grade.index(current_display_name) + 1 if current_display_name in name_list_by_grade else 0
                
                edit_selected = st.selectbox("修改姓名", ["請選擇學生..."] + name_list_by_grade, index=default_idx)
                edit_price = st.number_input("修改金額", min_value=0, value=int(current_row["金額"]), step=1)
                edit_note = st.text_input("修改備註", str(current_row["備註"]) if pd.notna(current_row["備註"]) else "")
                
                if st.button("💾 儲存修改"):
                    if edit_selected == "請選擇學生...":
                        st.error("❌ 請選擇學生姓名！")
                    else:
                        pure_edit_name = edit_selected.split("] ")[1]
                        df.at[selected_index, "日期"] = pd.to_datetime(edit_date)
                        df.at[selected_index, "姓名"] = pure_edit_name
                        df.at[selected_index, "年級"] = STUDENT_LIST.get(pure_edit_name, "未知名級")
                        df.at[selected_index, "金額"] = edit_price
                        df.at[selected_index, "備註"] = edit_note
                        df.to_csv(DB_FILE, index=False)
                        st.success("資料修改成功！")
                        st.rerun()
                    
            elif action == "刪除此筆資料":
                st.subheader("🔴 刪除資料確認")
                st.warning(f"您確定要刪除這筆紀錄嗎？\n\n【 {current_row['日期'].strftime('%Y-%m-%d')} - [{current_row['年級']}] {current_row['姓名']} : {current_row['金額']}元 】")
                if st.button("❌ 確認刪除，無法復原"):
                    df = df.drop(selected_index).reset_index(drop=True)
                    df.to_csv(DB_FILE, index=False)
                    st.success("資料已成功刪除！")
                    st.rerun()
    else:
        st.info("目前沒有任何歷史紀錄可以修改或刪除。")
