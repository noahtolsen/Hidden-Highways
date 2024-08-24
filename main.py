import requests
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json

# Load environment variables
load_dotenv()

maps_api_key = os.getenv("MAPS_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI model
model = ChatOpenAI(model="gpt-4")

# Function to get places from Google Places API
def search_places(text_query, api_key):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "*"  # This will retrieve all available fields
    }
    payload = {
        "textQuery": text_query
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json().get('places', [])
    elif response.status_code == 400:
        print("Bad Request: Your request is invalid.")
    elif response.status_code == 401:
        print("Unauthorized: Check your API key.")
    elif response.status_code == 403:
        print("Forbidden: You don't have permission to access this resource.")
    elif response.status_code == 404:
        print("Not Found: The requested resource couldn't be found.")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    return []

# Function to analyze places using LangChain
def analyze_places_with_langchain(places, what_i_want):
    # Convert the response to a formatted string for the prompt
    places_str = "\n".join([
        f"Name: {place.get('displayName', 'Unknown')}, "
        f"Address: {place.get('formattedAddress', 'Unknown')}, "
        f"Rating: {place.get('rating', 'No rating')}, "
        f"Total Reviews: {place.get('userRatingsTotal', 'No reviews')}, "
        f"Price Level: {place.get('priceLevel', 'N/A')}"
        for place in places
    ])

    # Define the sequence of messages for LangChain
    messages = [
        SystemMessage(content="You are a travel assistant helping users discover local gems during their road trips. "
                              "The user wants to find unique, high-quality, local restaurants, coffee shops, and bakeries, avoiding big chains. "
                              "Based on the data provided, please review the list of places and select those that are likely to be locally owned, "
                              "offer a unique experience, or have exceptional reviews. Please return your recommendations to the user as JSON with three keys: the name of the place, your rating (0-10), and a brief explanation of why you recommend it. Return the JSON and nothing else."),
        HumanMessage(content=f"Here is the list of places:\n{places_str}\n\nPlease review and provide your recommendations. For this review, the user is looking for a {what_i_want}."),
    ]

    # Invoke the model with the messages
    response = model.invoke(messages)

    # Return the response from the model
    return response

# Example usage
if __name__ == "__main__":
    text_query = "Coffee in Middlesex VT"
    what_i_want = "coffee shop"

    # Get places from Google Places API
    places = search_places(text_query, maps_api_key)
    
    if places:
        # Analyze places with LangChain
        recommendations = analyze_places_with_langchain(places, what_i_want)
        content = recommendations.content
        
        # Replace \n with actual newlines
        cleaned_content = content.replace('\\n', '\n')
        
        # Try to load and pretty-print the JSON
        try:
            json_content = json.loads(cleaned_content)
            print(json.dumps(json_content, indent=4))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {str(e)}")
            print("Raw content:")
            print(cleaned_content)
    else:
        print("No places found.")
