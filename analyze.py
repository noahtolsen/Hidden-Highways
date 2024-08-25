from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json

model = ChatOpenAI(model="gpt-4")

def analyze_places_with_langchain(places, what_i_want):
    places_str = "\n".join([
        f"Name: {place.get('displayName', 'Unknown')}, "
        f"Address: {place.get('formattedAddress', 'Unknown')}, "
        f"Rating: {place.get('rating', 'No rating')}, "
        f"Total Reviews: {place.get('userRatingsTotal', 'No reviews')}, "
        f"Price Level: {place.get('priceLevel', 'N/A')}"
        for place in places
    ])

    messages = [
        SystemMessage(content="You are a travel assistant helping users discover local gems during their road trips. "
                              "The user wants to find unique, high-quality, local restaurants, coffee shops, and bakeries, avoiding big chains. "
                              "Based on the data provided, please review the list of places and select those that are likely to be locally owned, "
                              "offer a unique experience, or have exceptional reviews. Please return your recommendations to the user as JSON with three keys: the name of the place, your rating (0-10), and a brief explanation of why you recommend it. Return the JSON and nothing else."),
        HumanMessage(content=f"Here is the list of places:\n{places_str}\n\nPlease review and provide your recommendations. For this review, the user is looking for a {what_i_want}."),
    ]

    response = model.invoke(messages)
    return response
