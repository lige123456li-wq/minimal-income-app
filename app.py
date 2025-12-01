import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import calendar

DATA_FILE = "income_records.csv"

# ---------- 数据处理 ----------
def load_records():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8')
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=["timestamp", "amount", "remark"])
    else:
        df = pd.DataFrame(columns=["timestamp", "amount", "remark"])

    # 确保列名完整
    for col in ["timestamp", "amount", "remark"]:
        if col not in df.columns:
            df[col] = ""
    return df

def save_record(amount, remark):
    df = load_records()
    df.loc[len(df)] = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), amount, remark]
    df.to_csv(DATA_FILE, index=False, encoding='utf-8')

def delete_record(index):
    df = load_records()
    df = df.drop(index).reset_index(drop=True)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8')

# ---------- Streamlit 界面 ----------
st.set_page_config(page_title="极简记收入", layout="wide")
st.title("💰 极简记收入")

# 使用 session_state 控制刷新
if 'refresh' not in st.session_state:
    st.session_state.refresh = False

# --- 记录收入 ---
st.header("记录收入")
col1, col2, col3 = st.columns([2,3,1])
with col1:
    amount = st.text_input("金额", "")
with col2:
    remark = st.text_input("备注", "")
with col3:
    if st.button("记录"):
        if amount.strip() == "":
            st.warning("请输入金额")
        else:
            try:
                float(amount)
                save_record(amount, remark)
                st.success("记录成功")
                st.session_state.refresh = not st.session_state.refresh
            except ValueError:
                st.warning("金额格式不正确")

# --- 查看记录列表 ---
st.header("所有记录")
df = load_records()
if not df.empty:
    for idx in reversed(df.index):
        row = df.loc[idx]
        timestamp = row.get("timestamp", "")
        amount_val = row.get("amount", "")
        remark_val = row.get("remark", "")
        col1, col2 = st.columns([6,1])
        with col1:
            st.write(f"{timestamp}  ¥{amount_val}  {remark_val}")
        with col2:
            if st.button("删除", key=f"del{idx}"):
                delete_record(idx)
                st.session_state.refresh = not st.session_state.refresh
else:
    st.write("暂无记录")

# --- 按备注统计 ---
st.header("按备注统计")
if st.button("生成统计"):
    if df.empty:
        st.info("暂无记录")
    else:
        summary = df.groupby(df['remark'].fillna("(空备注)"))['amount'].sum()
        for remark_key, total in summary.items():
            st.write(f"{remark_key}: ¥{total:.2f}")

# --- 按天查看（日历折叠面板） ---
st.header("按天查看")
with st.expander("显示按天查看"):
    today = date.today()
    year = st.selectbox("年份", range(today.year-5, today.year+1), index=5)
    month = st.selectbox("月份", range(1,13), index=today.month-1)

    cal = calendar.Calendar(firstweekday=0)
    dates = cal.monthdayscalendar(year, month)

    # 构建当天记录字典
    day_records = {}
    for idx, row in df.iterrows():
        timestamp = row.get("timestamp", "")
        day = timestamp[:10]
        if day not in day_records:
            day_records[day] = []
        day_records[day].append(f"¥{row.get('amount','')}  {row.get('remark','')}")

    st.write(f"### {year} 年 {month} 月")
    for week in dates:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write(" ")
            else:
                day_str = f"{year}-{month:02d}-{day:02d}"
                amt = sum([float(r.split()[0][1:]) for r in day_records.get(day_str, []) if r]) if day_str in day_records else 0
                display_text = f"{day}\n¥{amt:.2f}" if amt>0 else str(day)
                if cols[i].button(display_text, key=day_str):
                    records_list = day_records.get(day_str, [])
                    if records_list:
                        st.info(f"{day_str} 收入明细:\n" + "\n".join(records_list))
                    else:
                        st.info(f"{day_str} 收入明细: 暂无记录")

# --- 导出 CSV ---
st.header("导出 CSV")
st.download_button("下载所有记录 CSV", data=df.to_csv(index=False).encode('utf-8'), file_name="income_records.csv")
