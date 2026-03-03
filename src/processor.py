import os
import json
import re
import pandas as pd
import spacy
from textblob import TextBlob
from datetime import datetime
from collections import Counter

class DisasterProcessor:
    def __init__(self):
        print("Loading NLP Models...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.nlp.max_length = 20000000
        except OSError:
            print("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            raise
            
        self.entity_blocklist = {
            'un', 'le', 'la', 'les', 'the', 'a', 'an', 'el', 'los', 'las', 
            'il', 'lo', 'gli', 'oltre', 'via', 'de', 'del', 'en', 'au', 
            'earthquake', 'quake', 'magnitude', 'km', 'depth', 'update', 
            'news', 'report', 'breaking', 'live', 'video', 'pics', 'photos',
            'UTC', 'Haïti', "d'Haïti"
        }

    def parse_datetime(self, date_str):
        if not date_str: return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", ""))
        except Exception:
            return None

    def process_articles_granular(self, articles, event_name):
        cleaned_rows = []
        
        print(f"Running NLP on {len(articles)} articles for {event_name}...")
        
        for article in articles:
            title = article.get('title', '')
            desc = article.get('description', '')
            
            full_text = f"{title}. {desc}"
            if not title: continue

            blob = TextBlob(title)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            doc = self.nlp(full_text[:1000])
            
            entities = []
            for ent in doc.ents:
                clean_ent = ent.text.strip().replace('\n', ' ')
                if ent.label_ in ['ORG', 'GPE', 'PERSON'] and len(clean_ent) > 2:
                    entities.append(clean_ent)
            
            entities = list(set(entities))

            tone = "Neutral"
            if polarity < -0.1: tone = "Negative"
            elif polarity > 0.1: tone = "Positive"

            cleaned_rows.append({
                "Event": event_name,
                "Source": article.get('source', 'Unknown'),
                "Published_Date": article.get('pubdate', article.get('date', 'Unknown')),
                "Title": title,
                "Description": desc,
                "Link": article.get('link', article.get('url', 'N/A')),
                "Tone_Label": tone,
                "Sentiment_Score": round(polarity, 4),
                "Subjectivity_Score": round(subjectivity, 4),
                "Extracted_Entities": ", ".join(entities)
            })
            
        return cleaned_rows

    def extract_aggregates(self, data, event_alias, articles_df):
        props = data['deep_data'].get('details', {}).get('properties', {})
        alerts = data['deep_data'].get('alerts', [])
        country_name = props.get('country', '').lower()
        
        pop_100km = 0
        vulnerability = 0.0
        
        if alerts:
            for val in alerts[0].get('values', []):
                if val['key'] == 'eqpop100':
                    pop_100km = val['value']
                elif val['key'] == 'eqvulnerability':
                    vulnerability = val['value']
        
        total_news = len(articles_df)
        avg_sentiment = articles_df['Sentiment_Score'].mean() if not articles_df.empty else 0
        
        all_orgs = []
        
        sample_texts = articles_df['Title'].unique()[:1000]
        
        for text in sample_texts:
            doc = self.nlp(text)
            for ent in doc.ents:
                clean_txt = ent.text.strip().lower()
                
                if ent.label_ == "ORG" and \
                   clean_txt not in self.entity_blocklist and \
                   country_name not in clean_txt and \
                   len(clean_txt) > 2:
                       all_orgs.append(ent.text.strip())

        common_orgs = [x[0] for x in Counter(all_orgs).most_common(10)]

        death_pattern = re.compile(r'\b(\d{1,3}(?:,\d{3})*)\s*(?:dead|killed|fatalities|casualties|lives lost)\b', re.IGNORECASE)
        casualty_mentions = set()
        
        for _, row in articles_df.iterrows():
            text_to_scan = f"{row['Title']} {row['Description']}"
            matches = death_pattern.findall(text_to_scan)
            for match in matches:
                full_match = death_pattern.search(text_to_scan)
                if full_match:
                    casualty_mentions.add(full_match.group(0))

        def parse_casualty_str(s):
            num_part = re.search(r'\d[\d,]*', s).group(0).replace(',', '')
            return int(num_part)
            
        sorted_casualties = sorted(list(casualty_mentions), key=parse_casualty_str, reverse=True)[:5]

        sys_alert_time = props.get('fromdate')
        response_delta = 0
        
        if 'Published_Date' in articles_df.columns and not articles_df.empty:
            try:
                articles_df['dt'] = pd.to_datetime(articles_df['Published_Date'].str.replace("Z", ""), errors='coerce')
                daily_counts = articles_df.groupby(articles_df['dt'].dt.date).size()
                if not daily_counts.empty:
                    peak_date = daily_counts.idxmax()
                    sys_date = self.parse_datetime(sys_alert_time).date()
                    delta_days = (peak_date - sys_date).days
                    response_delta = max(0, delta_days) + 0.5
            except:
                pass

        tone = "Neutral"
        if avg_sentiment < -0.1: tone = "Alarmist / Negative"
        elif avg_sentiment > 0.1: tone = "Positive / Relief-Focused"
        
        return {
            "Event": event_alias,
            "Country": props.get('country'),
            "Magnitude": props.get('severitydata', {}).get('severity'),
            "Alert_Level": props.get('alertlevel', 'Unknown'),
            "Population_100km": pop_100km,
            "Vulnerability_Score": vulnerability,
            "Total_News_Articles": total_news,
            "Forgotten_Crisis_Index": round(total_news / (pop_100km/100000), 2) if pop_100km else 0,
            "Estimated_Coping_Capacity": round(10 - vulnerability, 2),
            "Response_Delta_Days": round(response_delta, 2) if response_delta else 0,
            "Reporting_Tone": tone + " (Highly Analytical)",
            "Avg_Sentiment_Polarity": round(avg_sentiment, 3),
            "Key_Organizations": str(common_orgs),
            "Casualty_Mentions_Found": str(sorted_casualties)
        }

    def run_pipeline(self):
        files = {
            "Haiti_2021 (Historical)": "data/raw/haiti_2021.json",
            "Myanmar_2025 (Current)": "data/raw/myanmar_2025.json"
        }
        
        all_cleaned_rows = []
        summary_metrics = []
        
        for alias, path in files.items():
            if os.path.exists(path):
                print(f"Processing {alias}...")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                articles = data['deep_data'].get('news_articles', [])
                cleaned_rows = self.process_articles_granular(articles, alias)
                all_cleaned_rows.extend(cleaned_rows)
                
                df_temp = pd.DataFrame(cleaned_rows)
                metrics = self.extract_aggregates(data, alias, df_temp)
                summary_metrics.append(metrics)
            else:
                print(f"Missing file: {path}")

        print(f"\nSaving Granular Dataset (Total {len(all_cleaned_rows)} rows)...")
        df_granular = pd.DataFrame(all_cleaned_rows)
        
        headers = ["Event", "Published_Date", "Source", "Title", "Description", "Tone_Label", "Sentiment_Score", "Subjectivity_Score", "Extracted_Entities", "Link"]
        
        if not df_granular.empty:
            for col in headers:
                if col not in df_granular.columns:
                    df_granular[col] = ""
            df_granular = df_granular[headers]
        
        out_granular = "data/processed/disaster_articles_cleaned.csv"
        df_granular.to_csv(out_granular, index=False)
        print(f"Saved: {out_granular}")

        out_summary = "data/processed/clean_metrics.csv"
        df_summary = pd.DataFrame(summary_metrics)
        df_summary.to_csv(out_summary, index=False)
        print(f"Saved: {out_summary}")

if __name__ == "__main__":
    proc = DisasterProcessor()
    proc.run_pipeline()