import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# ================= 版面與全局設定 =================
st.set_page_config(page_title="科學化肌力訓練艙", layout="wide")

# 🟢 你的 Google Apps Script URL (已串通)
GAS_URL = "https://script.google.com/macros/s/AKfycbztfxKApaVJLmG11eO6ZinQ6KXigxZkTm65bVZcN-O7XubE7Sdfjrb-w0P5LNT2Qvlyzw/exec"

st.markdown("""
    <style>
    .big-font { font-size:22px !important; font-weight: bold; color: #38BDF8; }
    .coach-card { background-color: #F3F4F6; color: #0F172A !important; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; margin-bottom: 10px; }
    .alert-card { background-color: #FEF2F2; color: #7F1D1D !important; padding: 20px; border-radius: 10px; border-left: 5px solid #EF4444; margin-bottom: 10px; }
    .gold-card { background-color: #FFFBEB; color: #78350F !important; padding: 20px; border-radius: 10px; border-left: 5px solid #F59E0B; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏋️‍♂️ 個人化肌力")

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
        
        train_type = st.radio("🎯 動作定位", ["👑 主項 (Main Lift)", "🛠️ 輔助補強 (Accessory)"], horizontal=True)
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if "補強" in train_type:
                muscle = st.selectbox("細分肌群", ["胸 (Chest)", "肩 (Shoulders)", "背 (Back)", "臀部 (Glutes)", "腿後 (Hamstrings)", "小腿 (Calves)", "股四頭 (Quads)", "手臂 (Arms)", "核心 (Core)"])
            else:
                muscle = st.selectbox("主項肌群", ["胸 (Chest)", "背 (Back)", "腿 (Legs)", "肩 (Shoulders)", "全身 (Full Body)"])
                
        with col_m2:
            pattern = st.selectbox("動作模式", ["上肢推", "上肢拉", "下肢推", "下肢拉", "核心/斜向", "單關節孤立"])
            
        exercise = st.text_input("動作名稱 (如：引體向上)")
        
        st.markdown("---")
        intensity = st.number_input("目標強度 (% 1RM)", min_value=0.0, max_value=120.0, value=75.0, step=2.5)
        
        col1, col2 = st.columns(2)
        with col1:
            weight = st.number_input("重量 (kg) 💡徒手可填0或體重", min_value=0.0, step=2.5)
            sets = st.number_input("組數 (Sets)", min_value=1, step=1)
        with col2:
            reps = st.number_input("次數 (Reps)", min_value=1, step=1)
            rpe = st.slider("RPE (疲勞度)", min_value=1, max_value=10, value=8)
            
        notes = st.text_area("備註 (狀況、感受等)")
        submit_btn = st.form_submit_button("🚀 送出紀錄")
        
        if submit_btn:
            # 🟢 修正：拿掉 weight > 0 的限制，只要有寫動作名稱就可以送出！
            if exercise:
                volume = weight * reps * sets
                est_1rm = round(weight * (1 + (reps / 30)), 1) 
                
                unique_id = f"ID_{int(time.time() * 1000)}"
                
                type_tag = "[補強]" if "補強" in train_type else "[主項]"
                final_notes = f"{type_tag} {notes}" if notes else type_tag
                
                payload = {
                    "action": "add", "Date": str(date), "Phase": phase, "Muscle_Group": muscle, 
                    "Movement_Pattern": pattern, "Exercise": exercise, "Weight_kg": weight, "Reps": reps, 
                    "Sets": sets, "RPE": rpe, "Intensity_Pct": intensity, 
                    "Volume": volume, "Est_1RM": est_1rm, "Notes": final_notes, "ID": unique_id
                }
                
                with st.spinner("寫入雲端資料庫中..."):
                    res = requests.post(GAS_URL, json=payload)
                    if res.status_code == 200:
                        st.success("紀錄成功！")
                        st.cache_data.clear() 
                        st.rerun() 
            else:
                st.warning("請填寫動作名稱！(重量可以填 0)")

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
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🤖 專屬教練", "📈 體能預測", "📊 數據圖表", "🧍‍♂️ InBody 檢視", "📋 歷史清單"])
    
    # ----------------- 🟢 TAB 1: 專屬教練建議 -----------------
    with tab1:
        st.markdown("### 🔍 基於近期數據的戰術分析")
        recent_df = df.sort_values('Date', ascending=False).head(5)
        
        avg_rpe = recent_df['RPE'].mean() if not recent_df.empty else 0
        if avg_rpe >= 9:
            st.markdown(f"""<div class="alert-card"><b>🚨 疲勞過度警告 (RPE 過高)</b><br>近期平均 RPE 達到了 {avg_rpe:.1f}！這表示你幾乎每組都練到力竭。<br><b>建議：</b> 中樞神經可能已經疲乏，建議下週切換至 <b>「減量期 (Deload)」</b>，讓身體超補償恢復。</div>""", unsafe_allow_html=True)
        elif avg_rpe > 0 and avg_rpe <= 6 and "減量" not in str(current_phase):
            st.markdown(f"""<div class="coach-card"><b>💪 強度提升空間</b><br>近期平均 RPE 只有 {avg_rpe:.1f}，保留次數偏多。<br><b>建議：</b> 你的身體已經適應目前的重量，下一次訓練可以嘗試增加 2.5kg - 5kg，給肌肉新的刺激。</div>""", unsafe_allow_html=True)

        if not recent_df.empty:
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

    # ----------------- 🟢 TAB 2: 疲勞與體能預測 -----------------
    with tab2:
        st.markdown("### 🧬 體能超補償動態預測 (Banister Model)")
        st.markdown("系統自動將你的 `訓練量 × RPE` 計算為**身體疲勞積累**與**長期體能適應**，藉此精準捕捉你何時達到超越極限的超補償狀態。")
        
        daily_df = df.sort_values('Date').copy()
        daily_df['Load'] = daily_df['Volume'] * (daily_df['RPE'] / 10.0)
        daily_summary = daily_df.groupby('Date')['Load'].sum().reset_index()
        
        if not daily_summary.empty:
            idx = pd.date_range(start=daily_summary['Date'].min(), end=daily_summary['Date'].max())
            daily_summary.set_index('Date', inplace=True)
            daily_summary = daily_summary.reindex(idx, fill_value=0).reset_index().rename(columns={'index': 'Date'})
            
            fitness, fatigue, readiness = [], [], []
            fit_curr, fat_curr = 0, 0
            
            for index, row in daily_summary.iterrows():
                load = row['Load']
                fit_curr = fit_curr * 0.95 + load * 0.1
                fat_curr = fat_curr * 0.85 + load * 0.3
                fitness.append(fit_curr)
                fatigue.append(fat_curr)
                readiness.append(fit_curr - fat_curr)
                
            daily_summary['體能指數 (Fitness)'] = fitness
            daily_summary['疲勞指數 (Fatigue)'] = fatigue
            daily_summary['準備度/超補償 (Readiness)'] = readiness
            
            fig_banister = go.Figure()
            fig_banister.add_trace(go.Scatter(x=daily_summary['Date'], y=daily_summary['體能指數 (Fitness)'], name='📈 體能累積', line=dict(color='#10B981', width=2)))
            fig_banister.add_trace(go.Scatter(x=daily_summary['Date'], y=daily_summary['疲勞指數 (Fatigue)'], name='📉 疲勞蓄積', line=dict(color='#EF4444', width=2, dash='dot')))
            fig_banister.add_trace(go.Scatter(x=daily_summary['Date'], y=daily_summary['準備度/超補償 (Readiness)'], name='🔥 競技準備度', fill='tozeroy', fillcolor='rgba(245, 158, 11, 0.2)', line=dict(color='#F59E0B', width=3)))
            
            fig_banister.update_layout(xaxis_title="日期", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_banister, use_container_width=True)
            
            latest_readiness = readiness[-1]
            with st.expander("🗣️ 科學化 Tapering 備戰策略演算法判讀"):
                if latest_readiness > max(readiness) * 0.7 and "減量" in str(current_phase):
                    st.markdown(f"""<div class="gold-card"><b>🏆 進入黃金超補償窗口！</b><br>數據顯示你目前的準備度高達 {latest_readiness:.1f}，且疲勞已大幅衰減。<br><b>測驗指引：</b> 這是衝擊 <b>1RM 生涯新紀錄 (PR)</b> 的絕佳完美時機！本週請保持高神經興奮度，直接進行最大強度測試。</div>""", unsafe_allow_html=True)
                elif latest_readiness < 0:
                    st.markdown(f"""<div class="alert-card"><b>🚨 處於「機能低迷期」</b><br>當前你的疲勞值大於體能適應（準備度：{latest_readiness:.1f}）。<br><b>調整指引：</b> 此時強行測驗只會增加受傷機率。請立刻開始進行 <b>減量調整 (Tapering)</b>：維持原本訓練強度的 85%，但將總組數砍掉 50%，讓疲勞歸零！</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="coach-card"><b>💪 穩健體能堆疊期</b><br>目前的準備度狀態平穩 ({latest_readiness:.1f})，身體正在適應當前訓練總量。<br><b>調整指引：</b> 請繼續按照原有週期穩步推進，累積足夠的體能底蘊。</div>""", unsafe_allow_html=True)

    # ----------------- 🟢 TAB 3: 數據視覺化圖表 -----------------
    with tab3:
        st.markdown("### 📊 多維度重訓數據視覺化矩陣")
        
        col_chart1, col_chart2 = st.columns([1, 1.2])
        
        with col_chart1:
            if 'Exercise' in df.columns:
                selected_ex = st.selectbox("選擇主項動作查看 1RM 突破", df['Exercise'].dropna().unique())
                ex_df = df[df['Exercise'] == selected_ex].sort_values('Date')
                
                if not ex_df.empty:
                    max_1rm = ex_df['Est_1RM'].max()
                    latest_1rm = ex_df.iloc[-1]['Est_1RM']
                    st.metric("🎯 預估 1RM 最高紀錄 / 當前狀態", f"{max_1rm} kg", f"當前: {latest_1rm} kg")
                    
                    fig_line = px.line(ex_df, x='Date', y='Est_1RM', markers=True, title=f"{selected_ex} - 漸進性超負荷曲線")
                    fig_line.update_traces(line_color='#F59E0B', marker=dict(size=8))
                    st.plotly_chart(fig_line, use_container_width=True)

        with col_chart2:
            if 'Muscle_Group' in df.columns and 'Volume' in df.columns:
                tree_df = df.groupby(['Muscle_Group', 'Exercise'])['Volume'].sum().reset_index()
                tree_df = tree_df[tree_df['Volume'] > 0]
                
                if not tree_df.empty:
                    fig_tree = px.treemap(tree_df, path=['Muscle_Group', 'Exercise'], values='Volume',
                                          title="主項與補強容量分佈矩陣 (點擊區塊放大)",
                                          color='Muscle_Group', color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_tree, use_container_width=True)

        st.markdown("---")
        
        st.markdown("#### 🕸️ 高階肌群平衡雷達網 (含細分補強)")
        base_muscles = pd.DataFrame({"Muscle_Group": [
            "胸 (Chest)", "肩 (Shoulders)", "背 (Back)", "核心 (Core)", 
            "臀部 (Glutes)", "大腿前側/腿 (Quads)", "腿後 (Hamstrings)", "小腿 (Calves)", "手臂 (Arms)"
        ]})
        
        vol_df = df.copy()
        vol_df['Muscle_Group'] = vol_df['Muscle_Group'].replace({'腿 (Legs)': '大腿前側/腿 (Quads)', '腿': '大腿前側/腿 (Quads)'})
        vol_sum = vol_df.groupby('Muscle_Group')['Volume'].sum().reset_index()
        
        radar_df = pd.merge(base_muscles, vol_sum, on='Muscle_Group', how='left').fillna(0)
        
        fig_radar = px.line_polar(radar_df, r='Volume', theta='Muscle_Group', line_close=True)
        fig_radar.update_traces(fill='toself', line_color='#38BDF8', fillcolor='rgba(56, 189, 248, 0.4)')
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False)), margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_radar, use_container_width=True)

    # ----------------- 🟢 TAB 4: InBody 體態與失衡檢視 -----------------
    with tab4:
        st.markdown("### 🧍‍♂️ 當月動作比例 vs InBody 肌肉失衡交叉檢視")
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        df['Date_dt'] = pd.to_datetime(df['Date'])
        this_month_df = df[(df['Date_dt'].dt.month == current_month) & (df['Date_dt'].dt.year == current_year)]
        
        col_inbody, col_pattern = st.columns([1, 1.2])
        
        with col_inbody:
            st.markdown("#### 📝 輸入近期 InBody 肌肉量")
            with st.container(border=True):
                inb_l_arm = st.number_input("💪 左上肢 (kg)", min_value=0.0, value=3.5, step=0.1)
                inb_r_arm = st.number_input("💪 右上肢 (kg)", min_value=0.0, value=3.6, step=0.1)
                inb_trunk = st.number_input("🎽 軀幹 (kg)", min_value=0.0, value=25.0, step=0.5)
                inb_l_leg = st.number_input("🦵 左下肢 (kg)", min_value=0.0, value=9.5, step=0.1)
                inb_r_leg = st.number_input("🦵 右下肢 (kg)", min_value=0.0, value=9.4, step=0.1)
                
        with col_pattern:
            st.markdown(f"#### 📊 {current_month} 月訓練動作比例")
            if 'Movement_Pattern' in this_month_df.columns and not this_month_df.empty:
                pattern_df = this_month_df.groupby('Movement_Pattern')['Volume'].sum().reset_index()
                if not pattern_df.empty:
                    fig_pattern = px.pie(pattern_df, values='Volume', names='Movement_Pattern', hole=0.4,
                                         color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_pattern.update_traces(textinfo='percent+label', textfont_size=14)
                    fig_pattern.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
                    st.plotly_chart(fig_pattern, use_container_width=True)
                else:
                    st.info("本月尚無有效訓練數據。")

        st.markdown("---")
        st.markdown("#### 🩺 AI 體態失衡診斷報告")
        
        if 'Movement_Pattern' in this_month_df.columns and not this_month_df.empty:
            p_vol = this_month_df.groupby('Movement_Pattern')['Volume'].sum().to_dict()
            up_push = p_vol.get('上肢推', 0)
            up_pull = p_vol.get('上肢拉', 0)
            low_push = p_vol.get('下肢推', 0)
            low_pull = p_vol.get('下肢拉', 0)
            
            issues_found = False
            
            if abs(inb_r_arm - inb_l_arm) >= 0.3:
                issues_found = True
                weaker_arm = "左" if inb_r_arm > inb_l_arm else "右"
                st.markdown(f"""<div class="alert-card"><b>🚨 上肢左右失衡警告</b><br>InBody 顯示你的雙手肌肉量相差達 {abs(inb_r_arm - inb_l_arm):.1f}kg。<br><b>處方：</b> 請強制加入<b>單邊啞鈴訓練或 Cable 單手補強</b>，並由較弱的「{weaker_arm}手」先開始執行！</div>""", unsafe_allow_html=True)
                
            if abs(inb_r_leg - inb_l_leg) >= 0.4:
                issues_found = True
                weaker_leg = "左" if inb_r_leg > inb_l_leg else "右"
                st.markdown(f"""<div class="alert-card"><b>🚨 下肢左右失衡警告 (受傷高風險)</b><br>雙腿肌肉量落差達 {abs(inb_r_leg - inb_l_leg):.1f}kg。<br><b>處方：</b> 請在菜單中加入<b>保加利亞分腿蹲或單腿 RDL</b>，針對「{weaker_leg}腿」進行強化！</div>""", unsafe_allow_html=True)
            
            if up_push > 0 and up_pull > 0:
                if up_push > up_pull * 1.3:
                    issues_found = True
                    st.markdown(f"""<div class="alert-card"><b>🚨 圓肩危機：推 > 拉</b><br>本月你的「上肢推」容量是「上肢拉」的 {up_push/up_pull:.1f} 倍。<br><b>處方：</b> 胸練太多了！請將背部（划船、引體向上）比例拉高，或加入面拉 (Face Pull) 補強。</div>""", unsafe_allow_html=True)
            
            if low_push > 0 and low_pull > 0:
                if low_push > low_pull * 1.5:
                    issues_found = True
                    st.markdown(f"""<div class="alert-card"><b>🚨 骨盆前傾危機：股四頭肌主導</b><br>本月「下肢推(深蹲)」遠大於「下肢拉(硬舉)」。<br><b>處方：</b> 請加入羅馬尼亞硬舉 (RDL) 或腿後勾，專注於<b>臀部與腿後</b>的弱點補強！</div>""", unsafe_allow_html=True)

            if not issues_found:
                st.markdown(f"""<div class="coach-card"><b>🏆 體態平衡極佳！</b><br>目前的 InBody 對稱性非常好，且本月的推拉比例相當健康。請繼續保持這份完美的課表！</div>""", unsafe_allow_html=True)

    # ----------------- 🟢 TAB 5: 歷史清單與刪除 -----------------
    with tab5:
        st.markdown("### 🗑️ 刪除錯誤紀錄")
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
            st.dataframe(df.drop(columns=['ID', 'Display', 'Date_dt'], errors='ignore').sort_values('Date', ascending=False), use_container_width=True)
        else:
            st.info("💡 刪除功能已經準備就緒。新紀錄若填錯即可在這裡刪除！")
            st.dataframe(df.drop(columns=['Date_dt'], errors='ignore').sort_values('Date', ascending=False), use_container_width=True)
