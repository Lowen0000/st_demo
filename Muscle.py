import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# ================= 版面與全局設定 =================
st.set_page_config(page_title="科學化肌力訓練艙", layout="wide")

# 🟢 你的 Google Apps Script URL
GAS_URL = "https://script.google.com/macros/s/AKfycbztfxKApaVJLmG11eO6ZinQ6KXigxZkTm65bVZcN-O7XubE7Sdfjrb-w0P5LNT2Qvlyzw/exec"

st.markdown("""
    <style>
    .big-font { font-size:22px !important; font-weight: bold; color: #38BDF8; }
    .coach-card { background-color: #F3F4F6; color: #0F172A !important; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; margin-bottom: 10px; }
    .alert-card { background-color: #FEF2F2; color: #7F1D1D !important; padding: 20px; border-radius: 10px; border-left: 5px solid #EF4444; margin-bottom: 10px; }
    .gold-card { background-color: #FFFBEB; color: #78350F !important; padding: 20px; border-radius: 10px; border-left: 5px solid #F59E0B; margin-bottom: 10px; }
    .radar-insight-card { background-color: #F8FAFC; color: #334155 !important; padding: 20px; border-radius: 10px; border-left: 5px solid #64748B; margin-top: 15px; }
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
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce', utc=True).dt.tz_convert('Asia/Taipei').dt.date
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
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🤖 專屬教練", "📈 ACWR 疲勞監控", "📊 數據圖表", "🧍‍♂️ InBody 檢視", "📋 歷史清單"])
    
    # ----------------- 🟢 TAB 1: 專屬教練建議 -----------------
    with tab1:
        st.markdown("### ⏱️ 週期進度與轉換雷達")
        if not df.empty and 'Phase' in df.columns:
            df_chronological = df.sort_values('Date', ascending=True).reset_index(drop=True)
            df_chronological['Phase_Change'] = df_chronological['Phase'] != df_chronological['Phase'].shift(1)
            last_change_idx = df_chronological[df_chronological['Phase_Change']].index[-1] if not df_chronological[df_chronological['Phase_Change']].empty else 0
            
            current_phase_df = df_chronological.iloc[last_change_idx:]
            phase_start_date = current_phase_df['Date'].min()
            last_log_date = current_phase_df['Date'].max()
            
            days_in_phase = (last_log_date - phase_start_date).days
            weeks_in_phase = (days_in_phase // 7) + 1
            
            col_p1, col_p2 = st.columns([1.5, 3])
            with col_p1:
                st.metric(label="📊 當前執行週期進度", value=f"{current_phase.split(' ')[0]}", delta=f"🚀 進入第 {weeks_in_phase} 週", delta_color="normal")
            
            with col_p2:
                advice_msg = ""
                phase_name = current_phase.split(' ')[0]
                
                if "適應" in phase_name:
                    if weeks_in_phase >= 4:
                        advice_msg = "⚠️ <b>適應期已達上限：</b> 你的肌腱與神經應該已完全適應當前動作。為了避免停滯，強烈建議下週切換至 <b>「肌肥大期」</b> 增加肌肉量！"
                    else:
                        advice_msg = "💡 <b>穩紮穩打：</b> 目前適應期進度良好。請專注於「動作控制與肌肉感受度」，先不要急著加重，為未來的爆發打好地基。"
                elif "肌肥大" in phase_name:
                    if weeks_in_phase >= 6:
                        advice_msg = "⚠️ <b>肌肥大期即稍微收尾：</b> 超過 6 週的高容量訓練極易產生代謝疲勞。若感覺進步停滯，建議下週切換至 <b>「最大肌力期」</b>，用大重量將剛長出的肌肉轉化為真實力量！"
                    else:
                        advice_msg = "💡 <b>持續榨乾肌肉：</b> 目前正處於肌肥大的黃金成長期！請繼續保持高容量 (Volume) 訓練，並確保做到力竭邊緣 (RPE 8-9)。"
                elif "最大肌力" in phase_name:
                    if weeks_in_phase >= 4:
                        advice_msg = "🚨 <b>神經疲勞警戒區：</b> 最大肌力期超過 4 週會對中樞神經(CNS)造成極大壓力。建議下週立刻安排 1 週的 <b>「減量期 (Deload)」</b>，或準備進行 <b>「PR 測試」</b>！"
                    else:
                        advice_msg = "💡 <b>挑戰極限：</b> 這是發展絕對力量的關鍵期！請確保組間休息時間充足 (3-5分鐘)，專注神經徵召，勇敢推起大重量。"
                elif "減量" in phase_name:
                    if weeks_in_phase > 1:
                        advice_msg = "⚠️ <b>減量過度警告：</b> 減量期通常只需 1 週。疲勞已經消退，再不增加強度會開始流失體能！建議下週立刻進入新的 <b>「適應期」或「肌肥大期」</b>。"
                    else:
                        advice_msg = "💡 <b>積極恢復中：</b> 本週請將總容量砍半，重量維持在平常的 70-80% 左右。讓身體好好超補償，下週準備迎接更強的自己！"
                elif "PR" in phase_name:
                    advice_msg = "🏆 <b>享受成果：</b> 測完 PR 後，神經與關節會非常疲勞。下週請務必直接進入 <b>「減量期 (Deload)」</b>，或是重新啟動新的 <b>「適應期」</b>。"
                else:
                    advice_msg = "💡 <b>資料累積中：</b> 請持續穩定紀錄你的訓練數據。"
                
                if "⚠️" in advice_msg or "🚨" in advice_msg:
                    st.markdown(f"""<div class="alert-card">{advice_msg}</div>""", unsafe_allow_html=True)
                elif "🏆" in advice_msg:
                    st.markdown(f"""<div class="gold-card">{advice_msg}</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="coach-card">{advice_msg}</div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🔍 近期單次訓練狀態分析")
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
                st.markdown(f"""<div class="alert-card"><b>⚠️ 單次課表目標偏移 (肌肥大期)</b><br>你目前處於肌肥大期，但最新一筆設定的強度高達 {intensity_pct}% 或是次數過低 ({reps} 下)，這更偏向神經徵召。<br><b>建議：</b> 稍微降重至 <b>65%-80% 1RM</b>，將次數拉高至 <b>8-12 下</b>，以達到最佳的代謝壓力。</div>""", unsafe_allow_html=True)
            elif "最大肌力" in phase and (reps > 6 or intensity_pct < 80):
                st.markdown(f"""<div class="alert-card"><b>⚠️ 單次課表目標偏移 (最大肌力期)</b><br>你目前處於最大肌力期，但最新一筆訓練強度偏低 ({intensity_pct}%) 或是次數過多 ({reps} 下)。<br><b>建議：</b> 勇敢加重！請將重量提升至 <b>85%-95% 1RM</b>，次數控制在 <b>1-5 下</b>，專注神經系統徵召。</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="coach-card"><b>🎯 課表執行精準</b><br>最新一筆的訓練強度 ({intensity_pct}% 1RM) 與次數 ({reps} 下) 非常符合 <b>{phase.split(" ")[0]}</b> 的課表設計，請繼續保持這個紀律！</div>""", unsafe_allow_html=True)

    # ----------------- 🟢 TAB 2: 全新 ACWR 疲勞監控 -----------------
    with tab2:
        st.markdown("### ⚖️ ACWR 急慢性負荷比 (傷病預警系統)")
        st.markdown("職業運動普遍採用的黃金指標。不盲目要求休息，而是看你**「本週的訓練量 (急性)」**相較於**「過去四周打下的底子 (慢性)」**是否暴增。只要循序漸進，你的負荷可以無限疊加！")
        
        if not df.empty and 'Volume' in df.columns:
            load_df = df.copy()
            load_df['Date'] = pd.to_datetime(load_df['Date'])
            load_df['Load'] = load_df['Volume'] * (load_df['RPE'] if 'RPE' in load_df.columns else 1)
            
            latest_date = load_df['Date'].max()
            
            acute_start = latest_date - pd.Timedelta(days=6)
            chronic_start = latest_date - pd.Timedelta(days=27)
            
            acute_load = load_df[(load_df['Date'] >= acute_start) & (load_df['Date'] <= latest_date)]['Load'].sum()
            chronic_load_total = load_df[(load_df['Date'] >= chronic_start) & (load_df['Date'] <= latest_date)]['Load'].sum()
            chronic_load_weekly_avg = chronic_load_total / 4.0
            
            acwr = acute_load / chronic_load_weekly_avg if chronic_load_weekly_avg > 0 else 0
            
            col_a1, col_a2, col_a3 = st.columns(3)
            col_a1.metric("🔴 急性負荷 (近7天總和)", f"{acute_load:,.0f} AU")
            col_a2.metric("🔵 慢性負荷 (近4週平均)", f"{chronic_load_weekly_avg:,.0f} AU")
            
            acwr_color = "normal"
            if acwr < 0.8:
                acwr_status = "📉 訓練量不足 (Under-training)"
                acwr_msg = f"""<div class="coach-card"><b>💡 體能流失警告：</b> 你這禮拜的訓練量遠低於過去四周的平均水準 (ACWR: {acwr:.2f})。如果不是刻意減量，請趕快加把勁，不然辛苦練出來的底子會流失喔！</div>"""
            elif 0.8 <= acwr <= 1.3:
                acwr_status = "🟢 黃金適應區 (Sweet Spot)"
                acwr_msg = f"""<div class="gold-card"><b>🏆 完美的漸進性超負荷！</b><br>你這週的負荷與過去一個月的底子完美契合 (ACWR: {acwr:.2f})。受傷機率極低，且體能正在穩定成長，請繼續保持這個節奏！</div>"""
            elif 1.3 < acwr <= 1.5:
                acwr_status = "🟡 疲勞警戒區 (Caution)"
                acwr_color = "off"
                acwr_msg = f"""<div class="alert-card" style="border-left-color: #F59E0B;"><b>⚠️ 疲勞攀升中：</b> 你的急性負荷偏高 (ACWR: {acwr:.2f})。身體正在承受較大的壓力，請確保睡眠充足與營養補充，下次訓練可稍微下調強度。</div>"""
            else:
                acwr_status = "🚨 傷病高危險區 (Danger Zone)"
                acwr_color = "inverse"
                acwr_msg = f"""<div class="alert-card"><b>🚨 受傷風險暴增！</b><br>你這週的訓練量突然暴增太多 (ACWR 高達 {acwr:.2f})！神經與肌肉完全來不及修復，繼續硬練極度容易受傷。請立刻暫停大重量訓練，啟動主動恢復！</div>"""

            col_a3.metric("🎯 ACWR 指數", f"{acwr:.2f}", acwr_status, delta_color=acwr_color)
            
            st.markdown(acwr_msg, unsafe_allow_html=True)
            st.markdown("---")
            
            st.markdown("#### 🗓️ 週疲勞總量堆疊圖 (Weekly Stress Stacking)")
            st.markdown("用「週」為單位，一眼看穿你的疲勞起伏。顏色區塊代表該週各肌群的疲勞佔比。")
            
            weekly_df = load_df.copy()
            weekly_df['Week'] = weekly_df['Date'].dt.strftime('%Y-W%V')
            weekly_group = weekly_df.groupby(['Week', 'Muscle_Group'])['Load'].sum().reset_index()
            
            if not weekly_group.empty:
                fig_weekly = px.bar(weekly_group, x='Week', y='Load', color='Muscle_Group', 
                                    title="每週肌群疲勞堆疊軌跡",
                                    labels={'Load': '訓練壓力指數 (AU)', 'Week': '年份-週數'},
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_weekly.update_layout(barmode='stack', xaxis_type='category')
                st.plotly_chart(fig_weekly, use_container_width=True)
            else:
                st.info("尚無足夠數據繪製週疲勞堆疊圖。")

    # ----------------- 🟢 TAB 3: 數據視覺化圖表 -----------------
    with tab3:
        st.markdown("### 📊 多維度重訓數據視覺化矩陣")
        
        col_chart1, col_chart2 = st.columns([1, 1.2])
        
        with col_chart1:
            if 'Exercise' in df.columns:
                # 🟢 只抓取備註欄位含有 [主項] 標籤的動作
                if 'Notes' in df.columns:
                    main_exercises = df[df['Notes'].astype(str).str.contains(r'\[主項\]', regex=True, na=False)]['Exercise'].dropna().unique()
                else:
                    main_exercises = []

                if len(main_exercises) > 0:
                    selected_ex = st.selectbox("選擇主項動作查看 1RM 突破", main_exercises)
                    ex_df = df[df['Exercise'] == selected_ex].sort_values('Date')
                    
                    if not ex_df.empty:
                        max_1rm = ex_df['Est_1RM'].max()
                        latest_1rm = ex_df.iloc[-1]['Est_1RM']
                        st.metric("🎯 預估 1RM 最高紀錄 / 當前狀態", f"{max_1rm} kg", f"當前: {latest_1rm} kg")
                        
                        fig_line = px.line(ex_df, x='Date', y='Est_1RM', markers=True, title=f"{selected_ex} - 漸進性超負荷曲線")
                        fig_line.update_traces(line_color='#F59E0B', marker=dict(size=8))
                        st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("尚無「主項」訓練紀錄可供 1RM 曲線分析。")

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
        
        col_r1, col_r2 = st.columns([1.5, 1])
        
        with col_r1:
            fig_radar = px.line_polar(radar_df, r='Volume', theta='Muscle_Group', line_close=True)
            fig_radar.update_traces(fill='toself', line_color='#38BDF8', fillcolor='rgba(56, 189, 248, 0.4)')
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False)), margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_radar, use_container_width=True)
            
        with col_r2:
            st.markdown("#### 🗣️ 雷達圖解析與教練建議")
            if radar_df['Volume'].sum() == 0:
                st.info("尚無訓練數據，趕快去左側新增一筆吧！")
            else:
                max_muscle = radar_df.loc[radar_df['Volume'].idxmax()]['Muscle_Group']
                zero_muscles = radar_df[radar_df['Volume'] == 0]['Muscle_Group'].tolist()
                
                explanation = f"**1. 強勢發展區：**<br>圖表顯示你目前將最大心力投入在 **「{max_muscle}」**，雷達圖在此處明顯凸出。<br><br>"
                
                if zero_muscles:
                    zero_str = "、".join(zero_muscles)
                    explanation += f"**2. 嚴重忽略區 (警報🚨)：**<br>雷達圖往內凹陷到底的地方，代表你完全沒有紀錄過 **「{zero_str}」** 的訓練。長期的忽視容易造成關節代償與體態變形。<br><br>"
                else:
                    min_muscle = radar_df.loc[radar_df['Volume'].idxmin()]['Muscle_Group']
                    explanation += f"**2. 相對弱點區：**<br>你目前訓練容量最少的是 **「{min_muscle}」**，雷達圖在此處較為凹陷。建議未來的課表可以多分配 1~2 個補強動作。<br><br>"
                
                non_zero_count = len(radar_df[radar_df['Volume'] > 0])
                total_muscles = len(radar_df)
                if non_zero_count <= 3:
                    explanation += f"**3. 幾何平衡度：尖銳三角形**<br>你的雷達圖目前呈現極端偏科。完美的體能應該趨近於對稱的圓形，請盡快將未訓練的肌群排入課表中！"
                elif non_zero_count < total_muscles - 2:
                    explanation += f"**3. 幾何平衡度：不規則多邊形**<br>你的訓練涵蓋了多個部位，但仍有特定死角。試著補齊凹陷的缺口，邁向六邊形戰士！"
                else:
                    explanation += f"**3. 幾何平衡度：全方位發展！**<br>太棒了！你的雷達圖發展得非常均勻，主項與單關節補強都有顧及，請繼續維持！"
                
                st.markdown(f"""<div class="radar-insight-card">{explanation}</div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🎯 週期化訓練強度 (% 1RM) 軌跡觀測")
        if 'Intensity_Pct' in df.columns:
            intensity_df = df[(df['Intensity_Pct'] > 0) & (df['Volume'] > 0)].copy()
            if not intensity_df.empty:
                fig_int = px.scatter(
                    intensity_df, x='Date', y='Intensity_Pct', color='Phase', size='Volume',
                    hover_name='Exercise', hover_data={'Date': True, 'Weight_kg': True, 'Reps': True, 'Sets': True, 'Volume': False},
                    labels={'Intensity_Pct': '目標強度 (% 1RM)', 'Date': '訓練日期', 'Phase': '訓練週期'},
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig_int.update_traces(marker=dict(line=dict(width=1, color='rgba(255,255,255,0.8)')))
                fig_int.update_layout(yaxis=dict(range=[0, max(110, intensity_df['Intensity_Pct'].max() + 10)]))
                st.plotly_chart(fig_int, use_container_width=True)
            else:
                st.info("尚無有效的強度 % 數據可以繪製圖表。")

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
