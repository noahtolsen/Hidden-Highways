import requests

def search_places(text_query, api_key):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "*"  # Retrieve all available fields
    }
    payload = {
        "textQuery": text_query
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json().get('places', [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []
