import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import platform
import io

# ---------------------------------------------------------
# การตั้งค่าหน้าเว็บ & ฟอนต์ภาษาไทยสำหรับ Matplotlib
# ---------------------------------------------------------
st.set_page_config(
    page_title="Advanced AI Student Dashboard",
    page_icon="📊",
    layout="wide"
)

# ตั้งค่าฟอนต์ภาษาไทยให้รองรับทุกระบบ (Windows / macOS / Linux)
if platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.family'] = 'Tahoma'
elif platform.system() == 'Windows':  # Windows
    plt.rcParams['font.family'] = 'Tahoma'
else:  # Linux / Ubuntu
    plt.rcParams['font.family'] = 'DejaVu Sans'

plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------
# โหลดและรวมข้อมูล 10 ปี (พ.ศ. 2560 - 2569)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    files = [f"Competition_Dataset_{year}.xlsx" for year in range(2560, 2570)]
    dfs = []
    for f in files:
        if os.path.exists(f):
            xls = pd.ExcelFile(f)
            df = pd.read_excel(f, sheet_name=xls.sheet_names[0])
            dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("❌ ไม่พบไฟล์ข้อมูล Excel กรุณาตรวจสอบว่ามีไฟล์ Competition_Dataset_2560.xlsx ถึง Competition_Dataset_2569.xlsx ในโฟลเดอร์เดียวกัน")
else:
    min_year = int(df['ปีการศึกษา'].min())
    max_year = int(df['ปีการศึกษา'].max())
    all_levels = list(df['ระดับชั้น'].unique())
    departments = sorted(df['แผนกวิชา'].unique())

    # ---------------------------------------------------------
    # INITIALIZE SESSION STATE (สำหรับระบบ Reset Filters)
    # ---------------------------------------------------------
    if 'year_range' not in st.session_state:
        st.session_state.year_range = (min_year, max_year)
    if 'selected_levels' not in st.session_state:
        st.session_state.selected_levels = all_levels
    if 'selected_dept' not in st.session_state:
        st.session_state.selected_dept = "ทั้งหมด"
    if 'search_keyword' not in st.session_state:
        st.session_state.search_keyword = ""
    if 'show_ai_forecast' not in st.session_state:
        st.session_state.show_ai_forecast = True

    def reset_filters():
        st.session_state.year_range = (min_year, max_year)
        st.session_state.selected_levels = all_levels
        st.session_state.selected_dept = "ทั้งหมด"
        st.session_state.search_keyword = ""
        st.session_state.show_ai_forecast = True

    # ---------------------------------------------------------
    # CUSTOM CSS (รองรับ Dark / Light Theme อัตโนมัติ)
    # ---------------------------------------------------------
    st.markdown("""
        <style>
        .section-header {
            background-color: #1e293b;
            color: #ffffff;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .mini-stats-box {
            background-color: var(--secondary-background-color);
            color: var(--text-color);
            border: 1px solid rgba(150, 150, 150, 0.3);
            border-radius: 8px;
            padding: 14px;
            margin-top: 15px;
            font-size: 13px;
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # SIDEBAR: ตัวกรองอัจฉริยะ (Smart Filters)
    # ---------------------------------------------------------
    st.sidebar.header("🔍 ตัวกรองข้อมูล (Smart Filters)")

    # ปุ่มรีเซ็ตตัวกรองทั้งหมด
    st.sidebar.button("🔄 รีเซ็ตตัวกรองทั้งหมด (Reset Filters)", on_click=reset_filters, use_container_width=True)
    st.sidebar.markdown("---")

    # 1. Multi-year Range Slider
    selected_year_range = st.sidebar.slider(
        "📅 เลือกช่วงปีการศึกษา (Year Range)",
        min_value=min_year,
        max_value=max_year,
        key="year_range",
        step=1
    )

    # 2. Filter by Level
    selected_levels = st.sidebar.multiselect(
        "🎓 เลือกระดับชั้นปี",
        options=all_levels,
        key="selected_levels"
    )

    # 3. Filter by Department & Search Box
    selected_dept = st.sidebar.selectbox("🏫 เลือกแผนกวิชา", ["ทั้งหมด"] + list(departments), key="selected_dept")
    search_keyword = st.sidebar.text_input("🔎 ค้นหาคำสำคัญ (Search Department)", key="search_keyword").strip()

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ ตัวกรองเพิ่มเติม (Advanced Options)")
    
    # 4. Advanced Filter Toggles
    show_ai_forecast = st.sidebar.checkbox("🤖 แสดงการพยากรณ์ AI (Show AI Forecast)", key="show_ai_forecast")

    # ---------------------------------------------------------
    # การกรองข้อมูลตามเงื่อนไข (Data Filtering)
    # ---------------------------------------------------------
    filtered_df = df[
        (df['ปีการศึกษา'] >= selected_year_range[0]) & 
        (df['ปีการศึกษา'] <= selected_year_range[1]) &
        (df['ระดับชั้น'].isin(selected_levels))
    ]

    if selected_dept != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df['แผนกวิชา'] == selected_dept]

    if search_keyword:
        filtered_df = filtered_df[filtered_df['แผนกวิชา'].str.contains(search_keyword, case=False, na=False)]

    # 5. Quick Mini-Stats สรุปข้อมูลด่วนใต้ Sidebar
    active_depts_count = filtered_df['แผนกวิชา'].nunique()
    total_records = len(filtered_df)
    
    st.sidebar.markdown(f"""
        <div class="mini-stats-box">
            📌 <b>สถานะข้อมูลปัจจุบัน (Quick Summary)</b><br>
            • แสดงข้อมูล: <b>{total_records:,}</b> รายการ<br>
            • จำนวนแผนก: <b>{active_depts_count}</b> แผนกวิชา<br>
            • ช่วงปีการศึกษา: <b>พ.ศ. {selected_year_range[0]} - {selected_year_range[1]}</b><br>
            • ระดับชั้น: <b>{len(selected_levels)}</b> ระดับชั้น
        </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # HEADER & MAIN CONTENT
    # ---------------------------------------------------------
    st.markdown("""<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;"><img src="https://www.srtc.ac.th/admission/images/logosrtc.png" width="200" height="150"><h1 style="margin: 0; font-size: 45px;">แดชบอร์ดวิเคราะห์สถิตินักศึกษาวิทลัยเทคนิคสุราษฎร์ธานีย้อนหลัง 10 ปี</h1></div>""", unsafe_allow_html=True)
    st.caption(f"แสดงข้อมูลช่วงปีการศึกษา พ.ศ. {selected_year_range[0]} - {selected_year_range[1]} | แผนก: {selected_dept}")
    st.markdown("---")

    # ---------------------------------------------------------
    # SECTION 1: OVERVIEW & GROWTH RATE (% Change)
    # ---------------------------------------------------------
    st.markdown('<div class="section-header">📌 สรุปภาพรวมและอัตราการเติบโต</div>', unsafe_allow_html=True)

    total_students = filtered_df['รวมทั้งหมด (คน)'].sum()
    total_male = filtered_df['เพศชาย (คน)'].sum()
    total_female = filtered_df['เพศหญิง (คน)'].sum()
    
    yearly_totals = filtered_df.groupby('ปีการศึกษา')['รวมทั้งหมด (คน)'].sum().sort_index()
    
    growth_delta_val = None
    if len(yearly_totals) >= 2:
        latest_year_val = yearly_totals.iloc[-1]
        prev_year_val = yearly_totals.iloc[-2]
        if prev_year_val > 0:
            growth_pct = ((latest_year_val - prev_year_val) / prev_year_val) * 100
            growth_delta_val = f"{growth_pct:+.2f}% (เทียบปี {yearly_totals.index[-2]})"
    elif len(yearly_totals) == 1:
        growth_delta_val = "0.00%"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="**👥 นักศึกษารวม (ช่วงที่เลือก)**", value=f"{total_students:,} คน")
    with col2:
        st.metric(label="**👨‍🎓 นักศึกษาชาย**", value=f"{total_male:,} คน")
    with col3:
        st.metric(label="**👩‍🎓 นักศึกษาหญิง**", value=f"{total_female:,} คน")
    with col4:
        st.metric(label="**📈 อัตราการเติบโตปีล่าสุด (YoY)**", value=f"{yearly_totals.iloc[-1]:,} คน" if len(yearly_totals) > 0 else "0 คน", delta=growth_delta_val)

    retained_count = filtered_df[filtered_df['ระดับชั้น'] == 'ตกค้าง']['รวมทั้งหมด (คน)'].sum()
    pvc1_count = filtered_df[filtered_df['ระดับชั้น'] == 'ปวช.1']['รวมทั้งหมด (คน)'].sum()
    pvc2_count = filtered_df[filtered_df['ระดับชั้น'] == 'ปวช.2']['รวมทั้งหมด (คน)'].sum()
    pvc3_count = filtered_df[filtered_df['ระดับชั้น'] == 'ปวช.3']['รวมทั้งหมด (คน)'].sum()
    pvs1_count = filtered_df[filtered_df['ระดับชั้น'] == 'ปวส.1']['รวมทั้งหมด (คน)'].sum()
    pvs2_count = filtered_df[filtered_df['ระดับชั้น'] == 'ปวส.2']['รวมทั้งหมด (คน)'].sum()
    bachelor_count = filtered_df[filtered_df['ระดับชั้น'] == 'ป.ตรี']['รวมทั้งหมด (คน)'].sum()

    sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)
    with sub_col1:
        st.metric(label="**⚠️ ยอดนักศึกษาตกค้างรวม**", value=f"{retained_count:,} คน")
    with sub_col2:
        st.metric(label="**📘 ปวช. (1-3)**", value=f"{(pvc1_count+pvc2_count+pvc3_count):,} คน")
    with sub_col3:
        st.metric(label="**📗 ปวส. (1-2)**", value=f"{(pvs1_count+pvs2_count):,} คน")
    with sub_col4:
        st.metric(label="**📙 ป.ตรี**", value=f"{bachelor_count:,} คน")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # SECTION 1.5: RETAINED STUDENTS COMPARISON (เปรียบเทียบยอดตกค้างรายแผนกวิชา)
    # ---------------------------------------------------------
    

    # ---------------------------------------------------------
    # SECTION 2: VISUALIZATION & COMPARISON
    # ---------------------------------------------------------
    st.markdown('<div class="section-header">📊 แผนภูมิเปรียบเทียบและการเติบโตรายปี</div>', unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 จำนวนนักศึกษาแยกตามระดับชั้น")
        fig, ax = plt.subplots(figsize=(7, 4.5))
        
        level_summary = filtered_df.groupby('ระดับชั้น')['รวมทั้งหมด (คน)'].sum()
        if not level_summary.empty:
            bars = ax.bar(level_summary.index, level_summary.values, color="#00BDC7", width=0.40, edgecolor="black")
            ax.set_title("จำนวนนักศึกษารวม แยกตามระดับชั้น", fontsize=12, fontweight='bold')
            ax.set_xlabel("ระดับชั้น", fontsize=10)
            ax.set_ylabel("จำนวน (คน)", fontsize=10)
            ax.grid(axis='y', linestyle='--', alpha=0.3)
            
            for bar in bars:
                h = bar.get_height()
                ax.annotate(f'{h:,}', xy=(bar.get_x() + bar.get_width()/2, h),
                            xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'ไม่พบข้อมูลตามเงื่อนไข', ha='center', va='center')

        plt.tight_layout()
        st.pyplot(fig)

    with chart_col2:
        st.subheader("📈 แนวโน้มการเปลี่ยนแปลงตามช่วงปี")
        fig2, ax2 = plt.subplots(figsize=(7, 4.5))
        
        if len(yearly_totals) > 0:
            ax2.plot(yearly_totals.index, yearly_totals.values, marker='o', color="#00d3cc", linewidth=2.5, label='จำนวนนักศึกษา', markeredgecolor="black")
            ax2.set_title(f"แนวโน้มจำนวนนักศึกษารวม ({selected_year_range[0]} - {selected_year_range[1]})", fontsize=12, fontweight='bold')
            ax2.set_xlabel("ปีการศึกษา", fontsize=10)
            ax2.set_ylabel("จำนวนรวม (คน)", fontsize=10)
            
            ax2.set_xticks(yearly_totals.index)
            ax2.set_xticklabels([str(int(y)) for y in yearly_totals.index])
            
            ax2.grid(True, linestyle='--', alpha=0.3)
            
            for x, y in zip(yearly_totals.index, yearly_totals.values):
                ax2.annotate(f'{y:,}', (x, y), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=8)
        else:
            ax2.text(0.5, 0.5, 'ไม่พบข้อมูลแนวโน้ม', ha='center', va='center')

        plt.tight_layout()
        st.pyplot(fig2)

    st.markdown('<div class="section-header">⚠️ เปรียบเทียบยอดนักศึกษาตกค้างรายแผนกวิชา</div>', unsafe_allow_html=True)
                    
    retained_full_df = df[df['ระดับชั้น'] == 'ตกค้าง']
    if selected_year_range:
                        retained_full_df = retained_full_df[
                            (retained_full_df['ปีการศึกษา'] >= selected_year_range[0]) & 
                            (retained_full_df['ปีการศึกษา'] <= selected_year_range[1])
                        ]
                
                    # เลือกแผนกวิชาเพื่อเปรียบเทียบในกราฟเดียว
    all_depts_list = sorted(df['แผนกวิชา'].unique())
    default_select = all_depts_list[:2] if len(all_depts_list) >= 2 else all_depts_list
                
    selected_compare_depts = st.multiselect(
                        "🏫 เลือกแผนกวิชาที่ต้องการเปรียบเทียบยอดตกค้าง (เลือกได้หลายแผนกเพื่อเปรียบเทียบในกราฟเดียว):",
                        options=all_depts_list,
                        default=default_select
                    )
                
    r_col1, r_col2 = st.columns([2, 1])
    with r_col1:
                        st.subheader("📊 กราฟเปรียบเทียบยอดนักศึกษาตกค้างรายแผนก (Comparative Retained Trend)")
                        fig_r, ax_r = plt.subplots(figsize=(8, 4.5))
                        
                        if selected_compare_depts:
                            comp_df = retained_full_df[retained_full_df['แผนกวิชา'].isin(selected_compare_depts)]
                            for dept in selected_compare_depts:
                                dept_data = comp_df[comp_df['แผนกวิชา'] == dept].groupby('ปีการศึกษา')['รวมทั้งหมด (คน)'].sum().sort_index()
                                if not dept_data.empty:
                                    ax_r.plot(dept_data.index, dept_data.values, marker='o', linewidth=2.5, label=f'แผนก: {dept}')
                            
                            ax_r.set_title("เปรียบเทียบจำนวนนักศึกษาตกค้างรายแผนกวิชา", fontsize=12, fontweight='bold')
                            ax_r.set_xlabel("ปีการศึกษา", fontsize=10)
                            ax_r.set_ylabel("จำนวนคนตกค้าง (คน)", fontsize=10)
                            
                            all_years_r = retained_full_df['ปีการศึกษา'].unique()
                            if len(all_years_r) > 0:
                                ax_r.set_xticks(sorted(all_years_r))
                                ax_r.set_xticklabels([str(int(y)) for y in sorted(all_years_r)])
                
                            ax_r.legend(loc='upper left', fontsize=9)
                            ax_r.grid(True, linestyle='--', alpha=0.3)
                        else:
                            ax_r.text(0.5, 0.5, 'กรุณาเลือกอย่างน้อย 1 แผนกวิชา', ha='center', va='center')
                
                        plt.tight_layout()
                        st.pyplot(fig_r)
                
    with r_col2:
                        st.subheader("📋 ตารางเปรียบเทียบยอดตกค้าง")
                        if selected_compare_depts:
                            table_df = retained_full_df[retained_full_df['แผนกวิชา'].isin(selected_compare_depts)]
                            summary_table = table_df.pivot_table(index='แผนกวิชา', columns='ปีการศึกษา', values='รวมทั้งหมด (คน)', aggfunc='sum', fill_value=0)
                            st.dataframe(summary_table, use_container_width=True)
                        else:
                            st.info("ยังไม่ได้เลือกแผนกวิชา")
                
    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
# 📊 ฟีเจอร์เสริม: วิเคราะห์และพยากรณ์ความนิยมรายแผนกวิชาในอนาคต (แสดงตัวเลขกำกับแบบมีเครื่องหมาย *)
# ==========================================
st.markdown("---")
st.subheader("🚀 DEPARTMENT TREND & POPULARITY FORECAST : วิเคราะห์แผนกยอดนิยมในอนาคต")
st.markdown("ระบบวิเคราะห์อัตราการเติบโตย้อนหลังและพยากรณ์แนวโน้มความนิยมของแต่ละแผนกวิชา พร้อมแสดงตัวเลขพยากรณ์ล่วงหน้า")

if 'แผนกวิชา' in df.columns and 'ปีการศึกษา' in df.columns and 'รวมทั้งหมด (คน)' in df.columns:
    import numpy as np
    
    # รวมข้อมูลยอดนักศึกษาของแต่ละแผนกแยกตามปี
    dept_trend = df.groupby(['ปีการศึกษา', 'แผนกวิชา'])['รวมทั้งหมด (คน)'].sum().reset_index()
    
    # ให้ผู้ใช้เลือกแผนกที่จะนำมาเปรียบเทียบแนวโน้มความนิยม
    all_departments = sorted(dept_trend['แผนกวิชา'].unique())
    selected_depts_forecast = st.multiselect(
        "เลือกแผนกวิชาที่ต้องการวิเคราะห์และพยากรณ์ความนิยม (เลือกได้หลายแผนก):",
        all_departments,
        default=all_departments[:3] # ค่าเริ่มต้นเลือก 3 แผนกแรก
    )
    
    if selected_depts_forecast:
        fig_dept, ax_dept = plt.subplots(figsize=(10, 6))
        
        forecast_summary_data = []
        
        for dept in selected_depts_forecast:
            sub_df = dept_trend[dept_trend['แผนกวิชา'] == dept].sort_values('ปีการศึกษา')
            
            if len(sub_df) > 1:
                X = sub_df['ปีการศึกษา'].values
                y = sub_df['รวมทั้งหมด (คน)'].values
                
                # พล็อตข้อมูลจริง (Historical Trend)
                ax_dept.plot(X, y, marker='o', linewidth=2.5, label=f'ข้อมูลจริง: {dept}')
                
                # คำนวณ Linear Regression เพื่อพยากรณ์อนาคต 3 ปีข้างหน้า (เช่น พ.ศ. 2570 - 2572)
                slope, intercept = np.polyfit(X, y, 1)
                future_years = np.array([X[-1] + 1, X[-1] + 2, X[-1] + 3])
                future_preds = slope * future_years + intercept
                
                # นำจุดสุดท้ายของข้อมูลจริงมาต่อกับอาเรย์พยากรณ์ เพื่อให้เส้นประพุ่งเชื่อมต่อกันพอดี
                extended_years = np.concatenate([[X[-1]], future_years])
                extended_preds = np.concatenate([[y[-1]], future_preds])
                
                # พล็อตเส้นพยากรณ์อนาคต
                ax_dept.plot(extended_years, extended_preds, linestyle='--', marker='s', alpha=0.8, label=f'พยากรณ์ (AI): {dept}', color="#0ae802", markeredgecolor="black")
                
                for fx, fy in zip(future_years, future_preds):
                  ax_dept.text(fx, fy + 2, f"{int(fy):,}*", fontsize=9, fontweight='bold', ha='center', va='bottom', color="#14aa03")
                
                # เก็บข้อมูลสรุปอัตราการเติบโต
                growth_rate = ((y[-1] - y[0]) / y[0]) * 100
                forecast_summary_data.append({
                    "แผนกวิชา": dept,
                    "ยอดปัจจุบัน (2569)": y[-1],
                    "อัตราเติบโตสะสม 10 ปี (%)": round(growth_rate, 2),
                    "คาดการณ์ปีหน้า (2570)": int(future_preds[0])
                })
                
        ax_dept.set_title("กราฟวิเคราะห์แนวโน้มและความนิยมรายแผนกวิชา (Historical & AI Forecast)", fontsize=14, fontweight='bold')
        ax_dept.set_xlabel("ปีการศึกษา", fontsize=12)
        ax_dept.set_ylabel("จำนวนนักศึกษารวม (คน)", fontsize=12)
        ax_dept.grid(True, linestyle='--', alpha=0.6)
        ax_dept.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.tight_layout()
        st.pyplot(fig_dept)
        
        # แสดงตารางสรุปผลวิเคราะห์ความนิยม
        if forecast_summary_data:
            st.markdown("### 📋 ตารางสรุปอัตราการเติบโตและแนวโน้มความนิยม")
            summary_df = pd.DataFrame(forecast_summary_data)
            st.dataframe(summary_df, use_container_width=True)
    else:
        st.warning("กรุณาเลือกอย่างน้อย 1 แผนกวิชา เพื่อแสดงกราฟวิเคราะห์")
else:
    st.info("ไม่พบคอลัมน์ที่จำเป็นสำหรับประมวลผลแนวโน้มรายแผนก")


    # ---------------------------------------------------------
    # SECTION 3: SIMPLE AI FORECASTING (พยากรณ์ข้อมูล 3 ปีข้างหน้า)
    # ---------------------------------------------------------
if show_ai_forecast:
        st.markdown('<div class="section-header">🤖 การพยากรณ์แนวโน้ม 3 ปีข้างหน้าโดยใช้ปัญญาประดิษฐ์ในการพยากรณ์</div>', unsafe_allow_html=True)
        st.info("💡 **ระบบพยากรณ์ด้วย Machine Learning (Linear Trend Analysis):** คำนวณแนวโน้มอัตราการเติบโตจากข้อมูลสถิติตลอด 10 ปี เพื่อทำนายจำนวนนักศึกษาในอีก 3 ปีข้างหน้า")

        full_yearly = df.groupby('ปีการศึกษา')['รวมทั้งหมด (คน)'].sum().sort_index()
        X_years = full_yearly.index.values
        y_totals = full_yearly.values

        if len(X_years) >= 3:
            poly = np.polyfit(X_years, y_totals, 1)
            future_years = np.array([X_years[-1] + 1, X_years[-1] + 2, X_years[-1] + 3])
            future_preds = np.polyval(poly, future_years).astype(int)

            forecast_col1, forecast_col2 = st.columns([2, 1])

            with forecast_col1:
                fig_fc, ax_fc = plt.subplots(figsize=(8, 4.5))
                
                ax_fc.plot(X_years, y_totals, marker='o', color="#209dc0", linewidth=2.5, label='ข้อมูลจริง', markeredgecolor="black")
                
                all_x_fc = np.append(X_years[-1], future_years)
                all_y_fc = np.append(y_totals[-1], future_preds)
                ax_fc.plot(all_x_fc, all_y_fc, marker='s', color="#17e300", linewidth=2.5, linestyle='--', label='ประมาณการพยากรณ์',markeredgecolor="black")
                
                all_years_combined = np.append(X_years, future_years)
                ax_fc.set_xticks(all_years_combined)
                ax_fc.set_xticklabels([str(int(y)) for y in all_years_combined], rotation=45)

                for x, y in zip(future_years, future_preds):
                    ax_fc.annotate(f'{y:,}*', (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, fontweight='bold', color="#11ae00")

                ax_fc.set_title("กราฟแสดงข้อมูลจริงและการพยากรณ์ล่วงหน้า 3 ปี", fontsize=12, fontweight='bold')
                ax_fc.set_xlabel("ปีการศึกษา", fontsize=10)
                ax_fc.set_ylabel("ประมาณการนักศึกษา (คน)", fontsize=10)
                ax_fc.legend(loc='upper left')
                ax_fc.grid(True, linestyle='--', alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig_fc)

            with forecast_col2:
                st.subheader("🔮 สรุปผลการทำนาย (Forecast Table)")
                forecast_data = []
                for y_n, p_val in zip(future_years, future_preds):
                    forecast_data.append({"ปีการศึกษา": f"พ.ศ. {y_n}", "ประมาณการนักศึกษา": f"{p_val:,} คน"})
                
                st.table(pd.DataFrame(forecast_data))
                st.caption("* หมายเหตุ: คำนวณประมวลผลตามอัลกอริทึม Linear Regression Model")

        st.markdown("---")

    # ---------------------------------------------------------
    # SECTION 4: EXPORT & DETAILED TABLE (ส่งออกข้อมูลเป็นไฟล์ Excel)
    # ---------------------------------------------------------
st.markdown('<div class="section-header">📋 DATA EXPORT & TABLE : ตารางรายละเอียดและส่งออกข้อมูล</div>', unsafe_allow_html=True)

st.write(f"แสดงข้อมูลที่ผ่านการกรองทั้งหมด **{len(filtered_df):,}** รายการ")
    
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Filtered_Data')
excel_data = output.getvalue()

st.download_button(
        label="📥 ดาวน์โหลดรายงานสรุปเป็นไฟล์ Excel (.xlsx)",
        data=excel_data,
        file_name=f"student_summary_{selected_year_range[0]}_{selected_year_range[1]}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="กดเพื่อดาวน์โหลดข้อมูลที่ถูกกรองตามเงื่อนไขนำไปใช้งานต่อใน Excel"
    )

st.dataframe(filtered_df, use_container_width=True)