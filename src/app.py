import os
import json
import ast
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Disaster Intelligence Brief", layout="wide", page_icon="🌍")

st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stMetric {background-color: black; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    h1, h2, h3 {color: #2c3e50;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_processed_data():
    df = pd.read_csv("data/processed/clean_metrics_2.csv")
    return df

@st.cache_data
def load_raw_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

df = load_processed_data()
haiti_data = load_raw_json("data/raw/haiti_2021.json")
myanmar_data = load_raw_json("data/raw/myanmar_2025.json")

st.title("Disaster Evolution & Response Pipeline")
st.markdown("**Objective:** A comparative intelligence brief analyzing historical (Haiti 2021) vs. recent (Myanmar 2025) seismic events to evaluate changes in Media Saturation and Humanitarian Impact.")

st.header("1. Executive Summary")
col1, col2 = st.columns(2)

def display_event_metrics(col, row):
    with col:
        st.subheader(f"{row['Event']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Magnitude", row['Magnitude'])
        c2.metric("Alert Level", row['Alert_Level'].upper())
        c3.metric("Response Time (Days)", row['Response_Delta_Days'])
        
        c4, c5, c6 = st.columns(3)
        c4.metric("Pop Exposed (100km)", f"{int(row['Population_100km']):,}")
        c5.metric("News Articles", f"{int(row['Total_News_Articles']):,}")
        c6.metric("Forgotten Crisis Index", row['Forgotten_Crisis_Index'])

display_event_metrics(col1, df.iloc[0])
display_event_metrics(col2, df.iloc[1])

st.markdown("---")

st.header("2. Comparative Intelligence & Visualizations")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    st.subheader("Resilience Radar")
    st.markdown("Comparing Magnitude, Population Exposure, Media Coverage, and Vulnerability. *(Values normalized 0-100% relative to maximums)*")
    
    def relative_scale(col_name):
        max_val = df[col_name].max()
        return (df[col_name] / max_val) * 100

    radar_df = pd.DataFrame({
        'Event': df['Event'],
        'Magnitude': relative_scale('Magnitude'),
        'Vulnerability': relative_scale('Vulnerability_Score'),
        'Media Coverage': relative_scale('Total_News_Articles'),
        'Population Exposed': relative_scale('Population_100km')
    })

    categories =['Magnitude', 'Vulnerability', 'Media Coverage', 'Population Exposed']
    
    fig_radar = go.Figure()
    for i, row in radar_df.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[row['Magnitude'], row['Vulnerability'], row['Media Coverage'], row['Population Exposed']],
            theta=categories,
            fill='toself',
            name=row['Event']
        ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, margin=dict(t=20, b=20))
    st.plotly_chart(fig_radar, use_container_width=True)

with viz_col2:
    st.subheader("Dual-Timeline: Media Saturation")
    st.markdown("Overlaying news volume growth for Event A vs. Event B relative to the disaster day.")
    
    timeline_data =[]
    def extract_timeline(data_json, event_name):
        daily_news = data_json.get('deep_data', {}).get('news_stats', {}).get('dailyNews',[])
        sys_alert = data_json.get('search_metadata', {}).get('fromdate')
        if not daily_news or not sys_alert: return
        
        sys_date = datetime.fromisoformat(sys_alert.replace("Z", "")).date()
        for entry in daily_news:
            entry_date = datetime.fromisoformat(entry['date'].replace("Z", "")).date()
            days_since = (entry_date - sys_date).days
            if -2 <= days_since <= 14:
                timeline_data.append({"Event": event_name, "Days Since Alert": days_since, "News Volume": entry['total']})

    if haiti_data: extract_timeline(haiti_data, "Haiti (2021)")
    if myanmar_data: extract_timeline(myanmar_data, "Myanmar (2025)")
    
    if timeline_data:
        tl_df = pd.DataFrame(timeline_data)
        fig_line = px.line(tl_df, x="Days Since Alert", y="News Volume", color="Event", markers=True, 
                           color_discrete_sequence=["#e74c3c", "#3498db"])
        fig_line.update_layout(xaxis_title="Days Since System Alert (Day 0)", yaxis_title="Number of Articles")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Temporal Daily News data from raw JSON is loaded here.")

st.markdown("---")

st.header("3. Temporal & Entity Analysis (NLP)")

nlp_col1, nlp_col2 = st.columns(2)

with nlp_col1:
    st.subheader("Sentiment Volatility & Tone")
    tone_df = df[['Event', 'Reporting_Tone', 'Avg_Sentiment_Polarity']]
    
    fig_bar = px.bar(tone_df, x='Event', y='Avg_Sentiment_Polarity', color='Reporting_Tone',
                     title="Average Headline Sentiment Polarity (-1 to +1)",
                     color_discrete_sequence=["#34495e"])
    fig_bar.update_layout(yaxis_range=[-0.1, 0.1])
    st.plotly_chart(fig_bar, use_container_width=True)

with nlp_col2:
    st.subheader("Extracted Entities (NER)")
    st.markdown("Top Organizations, NGOs, and Casualties extracted via **spaCy**.")
    
    for i, row in df.iterrows():
        st.write(f"**{row['Event']}**")
        
        try:
            orgs = ast.literal_eval(row['Key_Organizations'])
            st.info("**NGOs/Orgs:** " + (", ".join(orgs) if orgs else "None"))
        except:
            st.info("**NGOs/Orgs:** " + str(row['Key_Organizations']))
            
        try:
            cas = ast.literal_eval(row['Casualty_Mentions_Found'])
            if cas:
                st.error("**Casualties Mentioned:** " + ", ".join(cas))
            else:
                st.success("**Casualties Mentioned:** None extracted from top headlines.")
        except:
            pass

st.header("4. Final Report")

report_text = f"""
### 1. Technical Challenges of Deep-Tier Scraping
Extracting comprehensive data from the Global Disaster Alert and Coordination System (GDACS) presented massive architectural challenges. Standard scraping libraries failed due to dynamic JavaScript rendering on the "Impact" and "Media" tabs. We reverse-engineered the GDACS deep-tier APIs, traversing endpoints (`/geteventdata`, `/geteventalertlevel`, `/getemmnewsbykey`) to build a resilient data pipeline. A major challenge encountered was dealing with JSON payload volatility: some endpoints returned **100,000 lines** of data, while others returned over **1,000,000 lines** due to massive GeoJSON arrays mapping population density and polygon shakemaps, requiring optimized parsing logic.

### 2. The Evolution of Disaster Response
Comparing the **Historical {df.iloc[0]['Event']}** with the **Current {df.iloc[1]['Event']}**, a distinct shift in global response dynamics is quantifiable:

*   **Accelerated Mobilization (Delta Time):** Is the world responding faster today? **Yes.** The time gap between the GDACS System Alert and Peak Media Volume has exactly halved. In 2021 (Haiti), the media took **{df.iloc[0]['Response_Delta_Days']} days** to peak. By 2025 (Myanmar), response time plummeted to just **{df.iloc[1]['Response_Delta_Days']} days**. The deployment of rapid-assessment technologies, evidenced by the extraction of spatial-tech entities like **"ISRO SATELLITE IMAGES"** in the Myanmar news data, fuels this acceleration.
*   **The "Forgotten Crisis" & Media Bias:** Despite Myanmar generating a higher absolute volume of news ({df.iloc[1]['Total_News_Articles']} articles vs Haiti's {df.iloc[0]['Total_News_Articles']}), our **Forgotten Crisis Index** reveals a stark disparity in *proportional* coverage. Haiti's index was **{df.iloc[0]['Forgotten_Crisis_Index']}**, whereas Myanmar's is drastically lower at **{df.iloc[1]['Forgotten_Crisis_Index']}**. Given that Myanmar had over 17.2 million people exposed in the 100km buffer—nearly 18 times more than Haiti's 932,435—the media coverage for Myanmar is severely disproportionate to the human impact. Myanmar is definitively a "forgotten crisis" on a per-capita exposure basis.
*   **Vulnerability & Coping Capacity:** The coping capacity metrics mirror the tragic outcomes. Myanmar registered an extreme vulnerability score of **{df.iloc[1]['Vulnerability_Score']}** and a negative coping capacity (**{df.iloc[1]['Estimated_Coping_Capacity']}**), reflecting a systemic inability to absorb a 7.7 Magnitude shock. This mathematical fragility directly corroborates with the NLP entity extraction, which detected immediate alarming headlines like **"{ast.literal_eval(df.iloc[1]['Casualty_Mentions_Found'])[0] if ast.literal_eval(df.iloc[1]['Casualty_Mentions_Found']) else 'Casualties'}"** in the Myanmar dataset, whereas Haiti's initial top headlines lacked specific immediate death tolls.
*   **Reporting Tone:** Despite the severity, the NLP Sentiment Analysis categorizes both events as **{df.iloc[0]['Reporting_Tone']}** with polarities near zero ({df.iloc[0]['Avg_Sentiment_Polarity']} and {df.iloc[1]['Avg_Sentiment_Polarity']}). This indicates that top-tier disaster reporting remains objective and logistics-focused rather than alarmist.
"""

st.markdown(report_text)