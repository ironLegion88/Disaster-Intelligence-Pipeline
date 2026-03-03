import os
import json
import re
from datetime import datetime
import pandas as pd
import spacy
from textblob import TextBlob

class DisasterProcessor:
    def __init__(self):
        print("Loading NLP Models...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            raise

    def parse_datetime(self, date_str):
        if not date_str: return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", ""))
        except Exception:
            return None

    def extract_base_metrics(self, data):
        props = data['deep_data'].get('details', {}).get('properties', {})
        
        alerts = data['deep_data'].get('alerts',[])
        pop_100km = 0
        vulnerability = 0.0
        
        if alerts:
            for val in alerts[0].get('values',[]):
                if val['key'] == 'eqpop100':
                    pop_100km = val['value']
                elif val['key'] == 'eqvulnerability':
                    vulnerability = val['value']

        news_stats = data['deep_data'].get('news_stats', {})
        total_news = news_stats.get('coverage', {}).get('total', 0)

        return {
            "Magnitude": props.get('severitydata', {}).get('severity'),
            "Alert_Level": props.get('alertlevel', 'Unknown'),
            "Country": props.get('country'),
            "Population_100km": pop_100km,
            "Vulnerability_Score": vulnerability,
            "Total_News_Articles": total_news,
            "System_Alert_Time": props.get('fromdate')
        }

    def analyze_temporal_delta(self, data, system_alert_str):
        daily_news = data['deep_data'].get('news_stats', {}).get('dailyNews',[])
        if not daily_news or not system_alert_str:
            return None, None
            
        peak_day = max(daily_news, key=lambda x: x['total'])
        peak_time_str = peak_day['date']
        
        sys_time = self.parse_datetime(system_alert_str)
        peak_time = self.parse_datetime(peak_time_str)
        
        if sys_time and peak_time:
            delta = peak_time - sys_time
            return peak_time_str, delta.total_seconds() / (3600 * 24)
        return peak_time_str, None

    def analyze_nlp_and_entities(self, articles):
        orgs = set()
        total_polarity = 0
        total_subjectivity = 0
        death_mentions =[]
        
        death_pattern = re.compile(r'\b(\d+[\d,]*)\s*(deaths|killed|dead|fatalities|casualties)\b', re.IGNORECASE)
        
        articles_to_process = articles[:200]
        
        for article in articles_to_process:
            text = article.get('title', '')
            if not text: continue
                
            blob = TextBlob(text)
            total_polarity += blob.sentiment.polarity
            total_subjectivity += blob.sentiment.subjectivity
            
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    org_name = ent.text.upper()
                    if org_name not in["AP", "REUTERS", "AFP", "CNN", "BBC"]:
                        orgs.add(org_name)
            
            match = death_pattern.search(text)
            if match:
                death_mentions.append(match.group(0))

        count = len(articles_to_process) if articles_to_process else 1
        avg_polarity = total_polarity / count
        avg_subjectivity = total_subjectivity / count
        
        tone = "Neutral"
        if avg_polarity < -0.1:
            tone = "Alarmist / Negative"
        elif avg_polarity > 0.1:
            tone = "Positive / Relief-Focused"
            
        if avg_subjectivity < 0.3:
            tone += " (Highly Analytical)"
        elif avg_subjectivity > 0.5:
            tone += " (Highly Subjective)"

        return {
            "Avg_Sentiment_Polarity": round(avg_polarity, 3),
            "Avg_Subjectivity": round(avg_subjectivity, 3),
            "Reporting_Tone": tone,
            "Key_Organizations": list(orgs)[:10],
            "Casualty_Mentions_Found": list(set(death_mentions))[:5]
        }

    def process_event(self, event_alias, filepath):
        print(f"\nProcessing Event: {event_alias}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        metrics = self.extract_base_metrics(data)
        metrics['Event'] = event_alias
        
        peak_date, delta_days = self.analyze_temporal_delta(data, metrics['System_Alert_Time'])
        metrics['Peak_Media_Date'] = peak_date
        metrics['Response_Delta_Days'] = round(delta_days, 2) if delta_days is not None else "N/A"

        articles = data['deep_data'].get('news_articles',[])
        nlp_results = self.analyze_nlp_and_entities(articles)
        metrics.update(nlp_results)

        if metrics['Population_100km'] > 0:
            index_val = metrics['Total_News_Articles'] / (metrics['Population_100km'] / 100000)
            metrics['Forgotten_Crisis_Index'] = round(index_val, 2)
        else:
            metrics['Forgotten_Crisis_Index'] = 0

        metrics['Estimated_Coping_Capacity'] = round(10 - metrics['Vulnerability_Score'], 2)

        return metrics

    def run_all(self):
        files = {
            "Haiti_2021 (Historical)": "data/raw/haiti_2021_1.json",
            "Myanmar_2025 (Current)": "data/raw/myanmar_2025_1.json"
        }
        
        results =[]
        for alias, path in files.items():
            if os.path.exists(path):
                res = self.process_event(alias, path)
                results.append(res)
            else:
                print(f"File missing: {path}")
                
        os.makedirs(os.path.join("data", "processed"), exist_ok=True)
        df = pd.DataFrame(results)
        
        cols =['Event', 'Country', 'Magnitude', 'Alert_Level', 'Population_100km', 
                'Vulnerability_Score', 'Estimated_Coping_Capacity', 'Total_News_Articles',
                'Forgotten_Crisis_Index', 'Response_Delta_Days', 'Reporting_Tone', 
                'Avg_Sentiment_Polarity', 'Key_Organizations', 'Casualty_Mentions_Found']
        
        final_cols = [c for c in cols if c in df.columns]
        df = df[final_cols]
        
        out_path = "data/processed/clean_metrics.csv"
        df.to_csv(out_path, index=False)
        print(f"\nProcessing Complete. Clean data saved to '{out_path}'")
        
        return df

if __name__ == "__main__":
    processor = DisasterProcessor()
    final_df = processor.run_all()
    print("\n   Insight Summary")
    print(final_df[['Event', 'Forgotten_Crisis_Index', 'Reporting_Tone', 'Response_Delta_Days']])