import argparse
import pandas as pd
from data_engine import DisasterDataEngine

# Define our targets
EVENTS = {
    "historical": {
        "name": "Haiti Earthquake 2021",
        "country": "Haiti",
        "start_date": "2021-08-14",
        "end_date": "2021-09-14", # One month window for media
        "min_mag": 7.0
    },
    "recent": {
        "name": "Myanmar Earthquake 2025",
        "country": "Myanmar",
        "start_date": "2025-03-28",
        "end_date": "2025-04-28", 
        "min_mag": 7.5
    }
}

def main():
    parser = argparse.ArgumentParser(description="Disaster Response Pipeline CLI")
    parser.add_argument('action', choices=['list', 'run'], help="Action to perform")
    parser.add_argument('--event', help="Specific event key (historical/recent) to run")
    
    args = parser.parse_args()
    
    engine = DisasterDataEngine()
    
    if args.action == "list":
        print("\nAvailable Events:")
        for key, val in EVENTS.items():
            print(f" - {key}: {val['name']} ({val['start_date']})")
            
    elif args.action == "run":
        results = []
        keys_to_run = [args.event] if args.event else EVENTS.keys()
        
        for key in keys_to_run:
            if key not in EVENTS:
                print(f"Error: Event '{key}' not found.")
                continue
                
            params = EVENTS[key]
            data = engine.get_event_data(params['name'], specific_params=params)
            data['event_type'] = key # Tag as historical/recent
            results.append(data)
            
        # Save Raw Data
        df = pd.DataFrame(results)
        df.to_csv("disaster_data_raw.csv", index=False)
        print("\n[+] Data Collection Complete. Saved to 'disaster_data_raw.csv'")
        print(df[['event_name', 'magnitude', 'alert_level', 'article_count', 'vulnerability']])

if __name__ == "__main__":
    main()