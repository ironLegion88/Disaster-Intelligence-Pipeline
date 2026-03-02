import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta

class DisasterScraper:
    GDACS_API_URL = "https://www.gdacs.org/gdacsapi/api/Events" 
    RELIEFWEB_API_URL = "https://api.reliefweb.int/v1/reports"

    def __init__(self):
        self.session = requests.Session()

    def fetch_event_data(self, start_date, end_date, event_type="EQ", country=None):
        
        print(f"[*] Querying GDACS API for {event_type} between {start_date} and {end_date}...")
        
        params = {
            "fromdate": start_date,
            "todate": end_date,
            "eventtypes": event_type
        }

        try:
            response = self.session.get(self.GDACS_API_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', []) if 'features' in data else data
            
            matched_events = []
            for event in features:
                props = event.get('properties', event)
                
                event_countries = props.get('country', '').lower()
                if country and country.lower() not in event_countries:
                    continue
                
                mag = props.get('mag', props.get('magnitude', 0))
                if mag < 5.5: 
                    continue

                print(f"    -> Found Candidate: {props.get('name')} (Mag: {mag})")
                
                processed_event = self._process_single_event(props)
                matched_events.append(processed_event)
                
            return matched_events

        except Exception as e:
            print(f"[!] GDACS API Failed: {e}")
            return []

    def _process_single_event(self, props):
        event_date = props.get('fromdate', props.get('time'))
        country = props.get('country')
        
        event_data = {
            "event_id": props.get('eventid'),
            "name": props.get('name'),
            "country": country,
            "date": event_date,
            "magnitude": props.get('mag', props.get('magnitude')),
            "alert_level": props.get('alertlevel', 'Green').lower(),
            "population_exposed": props.get('population', 0),
            "latitude": props.get('latitude'),
            "longitude": props.get('longitude')
        }

        event_data['vulnerability_score'] = props.get('vulnerability', props.get('severitydata', {}).get('vulnerability', None))
        
        print(f"    -> Fetching Media Intelligence for {event_data['name']}...")
        rw_stats = self._fetch_reliefweb_stats(country, event_date)
        
        event_data['media_article_count'] = rw_stats['count']
        event_data['top_headlines'] = rw_stats['headlines']
        
        return event_data

    def _fetch_reliefweb_stats(self, country, date_str):
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', ''))
            date_from = dt.strftime('%Y-%m-%dT00:00:00+00:00')
            date_to = (dt + timedelta(days=30)).strftime('%Y-%m-%dT23:59:59+00:00')

            payload = {
                "appname": "gdacs_assignment",
                "query": {
                    "value": f"primary_country.name:\"{country}\" AND disaster.type:\"Earthquake\""
                },
                "filter": {
                    "field": "date.created",
                    "value": {
                        "from": date_from,
                        "to": date_to
                    }
                },
                "limit": 50,
                "fields": {"include": ["title", "source", "date"]}
            }
            
            resp = requests.post(self.RELIEFWEB_API_URL, json=payload, timeout=10)
            data = resp.json()
            
            return {
                "count": data.get('totalCount', 0),
                "headlines": [item['fields']['title'] for item in data.get('data', [])]
            }
        except Exception:
            return {"count": 0, "headlines": []}

if __name__ == "__main__":
    scraper = DisasterScraper()
    
    print("--- Test: Historical Event ---")
    haiti = scraper.fetch_event_data("2021-08-14", "2021-08-20", event_type="EQ", country="Haiti")
    print(haiti)

    print("\n--- Test: Recent Event ---")
    myanmar = scraper.fetch_event_data("2025-01-01", "2026-03-02", event_type="EQ", country="Myanmar")
    print(myanmar)