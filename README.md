# 🌍 Disaster Evolution & Response Pipeline

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B)

## 📖 Overview
The **Disaster Evolution & Response Pipeline** is a data science project designed to evaluate how the global community's response to natural disasters has evolved over time. By comparing a **Historical Event (Haiti Earthquake, 2021)** against a **Current Event (Myanmar Earthquake, 2025)**, this tool quantifies changes in media mobilization speed, sentiment, and humanitarian focus.

The pipeline overcomes the technical challenges of scraping dynamic, JavaScript-heavy disaster reports by reverse-engineering the **GDACS (Global Disaster Alert and Coordination System)** deep-tier APIs.

## 🚀 Live Dashboard
**[Click here to view the Interactive Intelligence Brief](https://disaster-intelligence.streamlit.app/)**

## 🔑 Key Features
*   **Robust API Scraper:** Bypasses frontend scraping limitations by traversing nested GDACS JSON endpoints to harvest heavy GeoJSON data (Impact/Shakemaps).
*   **NLP Intelligence Engine:** Uses `spaCy` and `TextBlob` to extract:
    *   **Response Delta:** Time difference between System Alert and Peak Media Volume.
    *   **Named Entities (NER):** Identifies NGOs, Governments, and technical agencies involved.
    *   **Casualty Extraction:** Regex-based parsing of death tolls from thousands of headlines.
*   **Comparative Metrics:** Calculates the "Forgotten Crisis Index" to identify under-reported disasters relative to population exposure.
*   **Interactive Dashboard:** A Streamlit web app featuring Resilience Radars, Dual-Timelines, and Sentiment Histograms.

## 🛠️ Tech Stack
*   **Core:** Python 3.x
*   **Data Collection:** `Requests` (API Reverse Engineering), `JSON` processing
*   **NLP & Analysis:** `spaCy` (NER), `TextBlob` (Sentiment), `Pandas`
*   **Visualization:** `Streamlit`, `Plotly Express`, `Plotly Graph Objects`

## 📂 Project Structure
```text
project_root/
├── src/
│   ├── scraper.py         # GDACS Deep-Tier API Scraper
│   ├── processor.py       # NLP Pipeline & Metric Calculation
│   └── app.py             # Streamlit Dashboard & Reporting
├── data/
│   ├── raw/               # Raw JSON payloads from GDACS
│   └── processed/         # Cleaned CSVs (Metrics & Granular Articles)
├── requirements.txt       # Project Dependencies
└── README.md              # Documentation
```

## 📊 Methodology & Case Study
The pipeline analyzes two specific seismic events to track the evolution of response:

1.  **Haiti (2021):** Magnitude 7.2 | High Media Saturation | Slower Mobilization (2.5 Days).
2.  **Myanmar (2025):** Magnitude 7.7 | "Forgotten Crisis" | Rapid Mobilization (1.5 Days).

**Key Insight:** While modern technology (satellite/spatial tech) has accelerated the global response time by **40%**, media coverage for high-vulnerability regions like Myanmar remains disproportionately low compared to the human impact.

## ⚙️ Installation & Usage

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/YOUR_USERNAME/Disaster-Intelligence-Pipeline.git
    cd Disaster-Intelligence-Pipeline
    ```

2.  **Set up Virtual Environment**
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```

4.  **Run the Dashboard**
    ```bash
    streamlit run src/app.py
    ```

## 📄 Output Data
The pipeline generates two key datasets in `data/processed/`:
1.  **`clean_metrics.csv`**: Aggregated insights (Forgotten Crisis Index, Response Delta, Sentiment).
2.  **`disaster_articles_cleaned.csv`**: A granular dataset of thousands of scraped news articles with calculated sentiment scores and extracted entities.

---
