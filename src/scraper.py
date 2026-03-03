import os
import requests
import json
from datetime import datetime, timedelta

class GDACSDeepScraper:
    BASE_URL = "https://www.gdacs.org/gdacsapi/api"

    def __init__(self):
        self.session = requests.Session()
        os.makedirs(os.path.join("data", "raw"), exist_ok=True)

    def search_events(self, start_date, end_date, country, event_type="EQ", min_mag=7.0):
        
        print(f"\nSearching GDACS for {event_type} in {country} ({start_date} to {end_date})...")
        
        endpoint = f"{self.BASE_URL}/Events/geteventlist/search"
        params = {
            "eventlist": event_type,
            "fromDate": start_date,
            "toDate": end_date
        }

        try:
            resp = self.session.get(endpoint, params=params, timeout=50000)
            resp.raise_for_status()
            data = resp.json()
            features = data.get('features',[])
            
            candidates =[]
            for feat in features:
                props = feat.get('properties', {})
                ev_country = props.get('country', '').lower()
                
                mag = props.get('severitydata', {}).get('severity', 0)
                
                if country.lower() in ev_country and mag >= min_mag:
                    candidates.append(props)
            
            if not candidates:
                print("    No events found matching criteria.")
                return None
                
            best_match = max(candidates, key=lambda x: x.get('severitydata', {}).get('severity', 0))
            print(f"    Match Found: {best_match['name']} (Mag: {best_match.get('severitydata', {}).get('severity')}) - EventID: {best_match['eventid']}")
            return best_match

        except Exception as e:
            print(f"    Search failed: {e}")
            return None

    def get_deep_data(self, eventtype, eventid):
        
        print(f"Getting Deep Data for EventID {eventid}...")
        full_event_data = {"eventid": eventid, "eventtype": eventtype}

        print("    Fetching Main Event Data...")
        ev_data_endpoint = f"{self.BASE_URL}/Events/geteventdata"
        resp = self.session.get(ev_data_endpoint, params={"eventtype": eventtype, "eventid": eventid})
        if resp.status_code == 200:
            full_event_data['details'] = resp.json()
        
        print("    Fetching Alert Levels & Vulnerability...")
        alert_endpoint = f"{self.BASE_URL}/Events/geteventalertlevel"
        resp = self.session.get(alert_endpoint, params={"eventtype": eventtype, "eventid": eventid})
        if resp.status_code == 200:
            full_event_data['alerts'] = resp.json()

        print("    Fetching Media / News Articles...")
        news_endpoint = f"{self.BASE_URL}/Emm/getemmnewsbykey"
        resp = self.session.get(news_endpoint, params={"eventtype": eventtype, "eventid": eventid, "limit": 500})
        if resp.status_code == 200:
            full_event_data['news_articles'] = resp.json()

        print("    Fetching Media Statistics...")
        stats_endpoint = f"{self.BASE_URL}/Emm/getemmnewsstatisticbykey"
        resp = self.session.get(stats_endpoint, params={"eventtype": eventtype, "eventid": eventid})
        if resp.status_code == 200:
            full_event_data['news_stats'] = resp.json()

        if 'details' in full_event_data and 'properties' in full_event_data['details']:
            props = full_event_data['details']['properties']
            
            impact_results =[]
            impacts = props.get('impacts',[])
            print(f"    Fetching {len(impacts)} Impact Resource(s)...")
            for imp in impacts:
                resources = imp.get('resource', {})
                for key, url in resources.items():
                    try:
                        imp_resp = self.session.get(url)
                        if imp_resp.status_code == 200:
                            impact_results.append({key: imp_resp.json()})
                    except:
                        pass
            full_event_data['impact_analysis'] = impact_results

        return full_event_data

    def run_pipeline(self, event_alias, start_date, end_date, country, min_mag=7.0):
        
        base_event = self.search_events(start_date, end_date, country, "EQ", min_mag)
        
        if not base_event:
            return None
            
        deep_data = self.get_deep_data(base_event['eventtype'], base_event['eventid'])
        
        final_record = {
            "search_metadata": base_event,
            "deep_data": deep_data
        }
        
        filename = f"{event_alias.replace(' ', '_').lower()}.json"
        filepath = os.path.join("data", "raw", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_record, f, indent=4)
            
        print(f"Successfully saved comprehensive data to {filepath}\n")
        return final_record

if __name__ == "__main__":
    scraper = GDACSDeepScraper()
    
    scraper.run_pipeline(
        event_alias="Haiti_2021",
        start_date="2021-08-01T00:00:00",
        end_date="2021-09-01T00:00:00",
        country="Haiti",
        min_mag=7.0
    )

    scraper.run_pipeline(
        event_alias="Myanmar_2025",
        start_date="2025-03-01T00:00:00",
        end_date="2025-04-30T00:00:00",
        country="Myanmar",
        min_mag=7.5
    )