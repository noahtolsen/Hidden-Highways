import os
from dotenv import load_dotenv
from fasthtml.common import *
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List
from search import search_places

# Load environment variables
load_dotenv()

maps_api_key = os.getenv("MAPS_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI model
llm = ChatOpenAI(model="gpt-4")

# Define the expected output schema using Pydantic
class PlaceRecommendation(BaseModel):
    name: str = Field(..., description="The name of the place")
    rating: float = Field(..., description="The rating of the place out of 10")
    reason: str = Field(..., description="The reason for recommending this place")

# Define a wrapper model for a list of recommendations
class PlaceRecommendations(BaseModel):
    recommendations: List[PlaceRecommendation]

# Create the structured output model
structured_llm = llm.with_structured_output(PlaceRecommendations)

# Initialize FastHTML app
app, rt = fast_app()

@rt("/")
def get():
    return Titled(
        "HiddenHighways",
        Div(
            Link(rel="stylesheet", href="/static/styles.css"),
            Img(src="/static/logo.webp", alt="HiddenHighways Logo", style="width: 200px; display: block; margin: 0 auto;"),
            Form(
                Label("Search Query:", _for="query"),
                Input(id="query", name="query", placeholder="e.g., Coffee in Middlesex VT", required=True),
                Label("What are you looking for?", _for="what_i_want"),
                Input(id="what_i_want", name="what_i_want", placeholder="e.g., coffee shop", required=True),
                Button(
                    "Find",
                    type="submit",
                    hx_post="/search",
                    hx_trigger="click",
                    hx_target="#results",
                    hx_swap="innerHTML",
                    hx_indicator="#spinner"
                )
            ),
            Div(id="spinner", children=[
                Img(src="/static/spinner.gif", alt="Loading...", style="width: 50px;")
            ]),
            Div(id="results")
        )
    )

@rt("/search", methods=["POST"])
async def post(req):
    form_data = await req.form()
    query = form_data.get("query")
    what_i_want = form_data.get("what_i_want")

    # Get places from Google Places API
    places = search_places(query, maps_api_key)
    
    if isinstance(places, list) and places:
        # Prepare the data for the LLM, excluding Google ratings
        places_str = "\n".join([
            f"Name: {place.get('displayName', 'Unknown')}, "
            f"Address: {place.get('formattedAddress', 'Unknown')}, "
            f"Total Reviews: {place.get('userRatingsTotal', 'No reviews')}, "
            f"Price Level: {place.get('priceLevel', 'N/A')}"
            for place in places
        ])

        messages = [
            SystemMessage(content="You are a travel assistant helping users discover local gems during their road trips. "
                                  "Please evaluate each place in the list below and provide a rating (out of 10) and a reason for each recommendation, considering the search criteria."
                                  "The goal is to avoid big chains that advertise on highways and instead recommend unique, high-quality, local options."),
            HumanMessage(content=f"Here is the list of places:\n{places_str}\n\nPlease provide your recommendations with ratings and reasons for each place.")
        ]

        # Invoke the model with structured output
        response = structured_llm.invoke(messages)

        # Print the structured response for debugging
        print("Structured model output:", response)

        try:
            # Extract recommendations
            recommendations = response.recommendations

            # Build the results to display
            results = Div(
                *[Div(
                    H2(rec.name),
                    P(f"Rating: {rec.rating} / 10"),  # Display LLM's rating
                    P(rec.reason),
                    style="margin-bottom: 20px; padding: 10px; border: 1px solid #ccc; border-radius: 8px; background-color: #2c2c2e; color: white;"
                ) for rec in recommendations],
                id="results"
            )
            return results
        except Exception as e:
            return P(f"Failed to parse response: {str(e)}", id="results")
    else:
        return P("No places found or an error occurred.", id="results")

serve()
