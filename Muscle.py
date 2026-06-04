import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# ================= 版面與全局設定 =================
st.set_page_config(page_title="科學化肌力訓練", layout="wide")

# 🟢 你的 Google Apps Script URL (已串通)
GAS_URL = "https://script.google.com/macros/s/AKfycbxqXjzLRtEECiIVtySb6gQiOiCpy91WkihbKB-ynio_pnfDoL94VszMePjo5T7P-OdWIw/exec"

st.markdown("""
    <style>
    .big-font { font-size:22px !important; font-weight: bold; color: #38BDF8; }
    .coach-card { background-color: #F3F4F6; color: #0F172A !important; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; margin-bottom: 10px; }
    .alert-card { background-color: #FEF2F2; color: #7F1D1D !important; padding: 20px; border-radius: 10px; border-left: 5px solid #EF4444; margin-bottom: 10px; }
    .gold-card { background-color: #FFFBEB; color: #78350F !important; padding: 20px; border-radius: 10px; border-left: 5px solid #F59E0B; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏋️‍♂️ 個人科學化肌力紀錄")


# ================= 資料讀取函數 =================
@st.cache_data(ttl=5) 
def load_data():
    try:
        response = requests.get(GAS_URL)
        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                st.error("⚠️ 資料格式錯誤！請檢查 Apps Script 部署權限。")
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            if not df.empty and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
                numeric_cols = ['Weight_kg', 'Reps', 'Sets', 'RPE', 'Intensity_Pct', 'Volume', 'Est_1RM']
                existing_cols = [col for col in numeric_cols if col in df.columns]
                df[existing_cols] = df[existing_cols].apply(pd.to_numeric, errors='coerce')
            return df
        else:
            st.error(f"⚠️ 伺服器連線異常，狀態碼：{response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ 無法連線至資料庫：{e}")
        return pd.DataFrame()

# ================= 側邊欄：訓練登錄表單 =================
with st.sidebar:
    st.markdown('<p class="big-font">📝 登錄今日訓練</p>', unsafe_allow_html=True)
    with st.form("workout_form", clear_on_submit=True):
        date = st.date_input("日期", datetime.today())
        
        phase = st.selectbox("當前訓練週期", [
            "適應期 (Adaptation)", "肌肥大期 (Hypertrophy)", 
            "最大肌力期 (Max Strength)", "減量期 (Deload)", "PR 測試 (Peaking)"
        ])
        
        muscle = st.selectbox("目標肌群", ["胸 (Chest)", "背 (Back)", "腿 (Legs)", "肩 (Shoulders)", "核心 (Core)"])
        exercise = st.text_input("動作名稱 (如：槓鈴臥推)")
        
        st.markdown("---")
        intensity = st.number_input("目標強度 (% 1RM)", min_value=0.0, max_value=120.0, value=75.0, step=2.5)
        
        col1, col2 = st.columns(2)
        with col1:
            weight = st.number_input("重量 (kg)", min_value=0.0, step=2.5)
            sets = st.number_input("組數 (Sets)", min_value=1, step=1)
        with col2:
            reps = st.number_input("次數 (Reps)", min_value=1, step=1)
            rpe = st.slider("RPE (疲勞度)", min_value=1, max_value=10, value=8)
            
        notes = st.text_area("備註 (狀況、感受等)")
        submit_btn = st.form_submit_button("🚀 送出紀錄")
        
        if submit_btn:
            if exercise and weight > 0:
                volume = weight * reps * sets
                est_1rm = round(weight * (1 + (reps / 30)), 1)
                
                unique_id = f"ID_{int(time.time() * 1000)}"
                
                payload = {
                    "action": "add", "Date": str(date), "Phase": phase, "Muscle_Group": muscle, 
                    "Exercise": exercise, "Weight_kg": weight, "Reps": reps, 
                    "Sets": sets, "RPE": rpe, "Intensity_Pct": intensity, 
                    "Volume": volume, "Est_1RM": est_1rm, "Notes": notes, "ID": unique_id
                }
                
                with st.spinner("寫入雲端資料庫中..."):
                    res = requests.post(GAS_URL, json=payload)
                    if res.status_code == 200:
                        st.success("紀錄成功！")
                        st.cache_data.clear() 
                        st.rerun() 
            else:
                st.warning("請填寫動作名稱與有效重量！")

# ================= 主畫面：數據儀表板 =================
df = load_data()

if df.empty:
    st.info("目前尚無訓練紀錄，請從左側登錄你的第一筆菜單！")
else:
    st.subheader("💡 近期訓練指標")
    recent_volume = df['Volume'].sum()
    current_phase = df.iloc[-1]['Phase'] if 'Phase' in df.columns else "未知"
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="目前所處週期", value=str(current_phase).split(" ")[0])
    kpi2.metric(label="總搬運重量 (Total Volume)", value=f"{recent_volume:,.0f} kg")
    kpi3.metric(label="累計訓練筆數", value=f"{len(df)} 筆")
    
    st.markdown("---")
    
    # 🌟 重大更新：四大科學分頁
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 專屬教練建議", "📈 疲勞與體能預測", "📊 數據視覺化圖表", "📋 歷史清單與刪除"])
    
    # ----------------- TAB 1: 專屬教練建議 -----------------
    with tab1:
        st.markdown("### 🔍 基於近期數據的戰術分析")
        recent_df = df.sort_values('Date', ascending=False).head(5)
        
        avg_rpe = recent_df['RPE'].mean()
        if avg_rpe >= 9:
            st.markdown(f"""<div class="alert-card"><b>🚨 疲勞過度警告 (RPE 過高)</b><br>近期平均 RPE 達到了 {avg_rpe:.1f}！這表示你幾乎每組都練到力竭。<br><b>建議：</b> 中樞神經可能已經疲乏，建議下週切換至 <b>「減量期 (Deload)」</b>，讓身體超補償恢復。</div>""", unsafe_allow_html=True)
        elif avg_rpe <= 6 and "減量" not in str(current_phase):
            st.markdown(f"""<div class="coach-card"><b>💪 強度提升空間</b><br>近期平均 RPE 只有 {avg_rpe:.1f}，保留次數偏多。<br><b>建議：</b> 你的身體已經適應目前的重量，下一次訓練可以嘗試增加 2.5kg - 5kg，給肌肉新的刺激。</div>""", unsafe_allow_html=True)

        latest_workout = recent_df.iloc[0]
        reps = latest_workout['Reps']
        phase = str(latest_workout['Phase'])
        intensity_pct = latest_workout.get('Intensity_Pct', 0)
        
        if "肌肥大" in phase and (reps < 6 or intensity_pct > 85):
            st.markdown(f"""<div class="alert-card"><b>⚠️ 週期目標偏移 (肌肥大期)</b><br>你目前處於肌肥大期，但設定的強度高達 {intensity_pct}% 或是次數過低 ({reps} 下)，這更偏向神經徵召。<br><b>建議：</b> 稍微降重至 <b>65%-80% 1RM</b>，將次數拉高至 <b>8-12 下</b>，以達到最佳的代謝壓力。</div>""", unsafe_allow_html=True)
        elif "最大肌力" in phase and (reps > 6 or intensity_pct < 80):
            st.markdown(f"""<div class="alert-card"><b>⚠️ 週期目標偏移 (最大肌力期)</b><br>你目前處於最大肌力期，但訓練強度偏低 ({intensity_pct}%) 或是次數過多 ({reps} 下)。<br><b>建議：</b> 勇敢加重！請將重量提升至 <b>85%-95% 1RM</b>，次數控制在 <b>1-5 下</b>，專注神經系統徵召。</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="coach-card"><b>🎯 週期執行精準</b><br>你目前的訓練強度 ({intensity_pct}% 1RM) 與次數 ({reps} 下) 非常符合 <b>{phase.split(" ")[0]}</b> 的課表設計，請繼續保持這個紀律！</div>""", unsafe_allow_html=True)

    # ----------------- 🟢 TAB 2: 疲勞與體能預測 (Banister 脈衝回應模型) -----------------
    with tab2:
        st.markdown("### 🧬 體能超補償動態預測 (Banister Model)")
        st.markdown("系統自動將你的 `訓練量 × RPE` 計算為**身體疲勞積累**與**長期體能適應**，藉此精準捕捉你何時達到超越極限的超補償狀態。")
        
        # 按日期排序並統計每日總訓練負荷
        daily_df = df.sort_values('Date').copy()
        daily_df['Load'] = daily_df['Volume'] * (daily_df['RPE'] / 10.0)
        daily_summary = daily_df.groupby('Date')['Load'].sum().reset_index()
        
        # 補足日期空缺，以便進行衰減演算法
        idx = pd.date_range(start=daily_summary['Date'].min(), end=daily_summary['Date'].max())
        daily_summary.set_index('Date', inplace=True)
        daily_summary = daily_summary.reindex(idx, fill_value=0).reset_index().rename(columns={'index': 'Date'})
        
        # 運動科學半衰期權重：體能衰減慢(45天)，疲勞衰減快(15天)
        fitness, fatigue, readiness = [], [], []
        fit_curr, fat_curr = 0, 0
        
        for index, row in daily_summary.iterrows():
            load = row['Load']
            # 衰減公式
            fit_curr = fit_curr * 0.95 + load * 0.1
            fat_curr = fat_curr * 0.85 + load * 0.3
            
            fitness.append(fit_curr)
            fatigue.append(fat_curr)
            readiness.append(fit_curr - fat_curr)
            
        daily_summary['體能指數 (Fitness)'] = fitness
        daily_summary['疲勞指數 (Fatigue)'] = fatigue
        daily_summary['準備度/超補償 (Readiness)'] = readiness
        
        # 繪製動態流速圖
        fig_banister = go.Figure()
        fig_banister.add_trace(go.Scatter(x=daily_summary['Date'], y=daily_summary['體能指數 (Fitness)'], name='📈 體能累積 (長期效果)', line=dict(color='#10B981', width=2)))
        fig_banister.add_trace(go.Scatter(x=daily_summary['Date'], y=daily_summary['疲勞指數 (Fatigue)'], name='📉 疲勞蓄積 (神經壓力)', line=dict(color='#EF4444', width=2, dash='dot')))
        fig_banister.add_trace(go.Scatter(x=daily_summary['Date'], y=daily_summary['準備度/超補償 (Readiness)'], name='🔥 競技準備度 (超補償值)', fill='tozeroy', fillcolor='rgba(245, 158, 11, 0.2)', line=dict(color='#F59E0B', width=3)))
        
        fig_banister.update_layout(title="身體動態超補償預測圖表", xaxis_title="日期", yaxis_title="科學權重指數", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_banister, use_container_width=True)
        
        # 計算黃金減量調整 (Tapering) 指引
        latest_readiness = readiness[-1]
        with st.expander("🗣️ 科學化 Tapering 備戰策略演算法判讀"):
            if latest_readiness > max(readiness) * 0.7 and "減量" in str(current_phase):
                st.markdown(f"""<div class="gold-card"><b>🏆 進入黃金超補償窗口！</b><br>數據顯示你目前的準備度高達 {latest_readiness:.1f}，且疲勞已大幅衰減。<br><b>測驗指引：</b> 這是衝擊 <b>1RM 生涯新紀錄 (PR)</b> 的絕佳完美時機！本週請保持高神經興奮度，直接進行最大強度測試。</div>""", unsafe_allow_html=True)
            elif latest_readiness < 0:
                st.markdown(f"""<div class="alert-card"><b>🚨 處於「機能低迷期」</b><br>當前你的疲勞值大於體能適應（準備度：{latest_readiness:.1f}）。<br><b>調整指引：</b> 此時強行測驗只會增加受傷機率。若兩週後有重要賽事，請立刻開始進行 <b>減量調整 (Tapering)</b>：維持原本訓練強度的 85%，但將總組數（Volume）砍掉 50%，讓疲勞在賽前歸零！</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="coach-card"><b>💪 穩健體能堆疊期</b><br>目前的準備度狀態平穩 ({latest_readiness:.1f})，身體正在適應當前訓練總量。<br><b>調整指引：</b> 請繼續按照原有週期（肌肥大期或最大肌力期）穩步推進，累積足夠的體能底蘊。</div>""", unsafe_allow_html=True)

    # ----------------- 🟢 TAB 3: 數據視覺化圖表 -----------------
    with tab3:
        st.markdown("### 📊 多維度重訓數據視覺化矩陣")
        
        col_chart1, col_chart2 = st.columns([1, 1.2])
        
        # 1. 1RM 生涯極限突破曲線 (動態折線圖)
        with col_chart1:
            if 'Exercise' in df.columns:
                selected_ex = st.selectbox("選擇動作動作查看 1RM 突破軌跡", df['Exercise'].dropna().unique())
                ex_df = df[df['Exercise'] == selected_ex].sort_values('Date')
                
                if not ex_df.empty:
                    max_1rm = ex_df['Est_1RM'].max()
                    latest_1rm = ex_df.iloc[-1]['Est_1RM']
                    st.metric("🎯 預估 1RM 最高紀錄 / 當前狀態", f"{max_1rm} kg", f"當前: {latest_1rm} kg")
                    
                    fig_line = px.line(ex_df, x='Date', y='Est_1RM', markers=True, title=f"{selected_ex} - 漸進性超負荷曲線")
                    fig_line.update_traces(line_color='#F59E0B', marker=dict(size=8))
                    st.plotly_chart(fig_line, use_container_width=True)

        # 2. 肌群與動作容量矩陣樹狀圖 (Treemap)
        with col_chart2:
            if 'Muscle_Group' in df.columns and 'Volume' in df.columns:
                tree_df = df.groupby(['Muscle_Group', 'Exercise'])['Volume'].sum().reset_index()
                tree_df = tree_df[tree_df['Volume'] > 0]
                
                if not tree_df.empty:
                    fig_tree = px.treemap(tree_df, path=['Muscle_Group', 'Exercise'], values='Volume',
                                          title="重訓容量幾何分佈矩陣 (點擊區塊可放大探索細節動作)",
                                          color='Muscle_Group', color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_tree, use_container_width=True)
                else:
                    st.info("尚無動作數據")

    # ----------------- TAB 4: 歷史清單與刪除 -----------------
    with tab4:
        st.markdown("### 🗑 * 刪除錯誤紀錄")
        if 'ID' in df.columns and not df[df['ID'].notna() & (df['ID'] != "")].empty:
            del_df = df[df['ID'].notna() & (df['ID'] != "")].copy()
            del_df['Display'] = del_df['Date'].astype(str) + " ｜ " + del_df['Exercise'] + " (" + del_df['Weight_kg'].astype(str) + "kg x " + del_df['Reps'].astype(str) + "下)"
            
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                selected_to_delete = st.selectbox("請選擇要刪除的紀錄：", del_df['Display'].tolist())
            with col_del2:
                st.markdown("<br>", unsafe_allow_html=True) 
                if st.button("🗑️ 確定刪除", type="primary"):
                    del_id = del_df[del_df['Display'] == selected_to_delete]['ID'].values[0]
                    del_payload = {"action": "delete", "ID": str(del_id)}
                    
                    with st.spinner("刪除中..."):
                        res = requests.post(GAS_URL, json=del_payload)
                        if res.status_code == 200:
                            st.success("成功刪除紀錄！")
                            st.cache_data.clear()
                            st.rerun()
            
            st.markdown("---")
            st.dataframe(df.drop(columns=['ID', 'Display'], errors='ignore').sort_values('Date', ascending=False), use_container_width=True)
        else:
            st.info("💡 刪除功能已經準備就緒。新紀錄若填錯即可在這裡刪除！")
            st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True)