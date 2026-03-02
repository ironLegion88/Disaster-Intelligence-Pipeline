# INFORM Risk Index (2024/2025 Data) - Static fallback if GDACS Impact tab is unreachable
# Scale 0-10 (10 is highest vulnerability)
INFORM_SCORES = {
    "Myanmar": 7.8,   # High vulnerability due to conflict/infrastructure
    "Haiti": 8.1,     # Very high vulnerability
    "Turkey": 5.2,    # Medium-High
    "Japan": 2.3,     # Low
    "Nepal": 5.9
}

# Configuration for APIs
USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
RELIEFWEB_API_URL = "https://api.reliefweb.int/v1/reports"