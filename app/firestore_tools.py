"""Firestore tools for reading and writing travel destinations and itineraries."""

import json
from google.cloud import firestore

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-3e01eedce187"


def get_firestore_client() -> firestore.Client:
    """Initialize and return a Firestore client using hardcoded project ID."""
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def get_destination(destination_id: str) -> str:
    """Get detailed information about a travel destination from Firestore.

    Args:
        destination_id: The unique ID of the destination (e.g. 'tokyo', 'san-francisco', 'paris', 'kyoto').

    Returns:
        JSON string or error message describing the destination details.
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("destinations").document(destination_id.lower().strip())
        doc = doc_ref.get()

        if doc.exists:
            return json.dumps(doc.to_dict(), indent=2)
        else:
            return f"Destination with ID '{destination_id}' not found in Firestore database."
    except Exception as e:
        return f"Error retrieving destination from Firestore: {str(e)}"


def search_destinations(category: str = "", max_daily_budget: int = 0) -> str:
    """Search and filter destinations stored in Firestore based on category or daily budget.

    Args:
        category: Optional category filter (e.g. 'Cultural & Art', 'Coastal & Scenic', 'Art & History', 'Historic & Spiritual').
        max_daily_budget: Optional maximum daily budget limit in USD. If 0, no budget filter is applied.

    Returns:
        JSON string listing matching destinations.
    """
    try:
        db = get_firestore_client()
        docs = db.collection("destinations").stream()

        results = []
        for doc in docs:
            data = doc.to_dict()

            if category and category.lower() not in data.get("category", "").lower():
                continue

            if max_daily_budget > 0 and data.get("avg_daily_budget_usd", 0) > max_daily_budget:
                continue

            results.append(data)

        if not results:
            return "No matching destinations found in Firestore for the specified criteria."

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching destinations in Firestore: {str(e)}"


def save_travel_itinerary(destination_id: str, title: str, itinerary_notes: str) -> str:
    """Save or update a travel itinerary for a destination in Firestore.

    Args:
        destination_id: The destination ID (e.g. 'tokyo', 'san-francisco', 'paris', 'kyoto').
        title: Title of the itinerary (e.g. '3-Day Art & Food Tour').
        itinerary_notes: Detailed day-by-day notes, activities, or schedule.

    Returns:
        Success confirmation message.
    """
    try:
        db = get_firestore_client()
        itinerary_ref = db.collection("itineraries").document()

        itinerary_data = {
            "id": itinerary_ref.id,
            "destination_id": destination_id.lower().strip(),
            "title": title,
            "itinerary_notes": itinerary_notes,
            "created_at": firestore.SERVER_TIMESTAMP,
        }

        itinerary_ref.set(itinerary_data)
        return f"Successfully saved travel itinerary '{title}' for destination '{destination_id}' (Itinerary ID: {itinerary_ref.id})."
    except Exception as e:
        return f"Error saving itinerary to Firestore: {str(e)}"


def add_destination_note(destination_id: str, note: str) -> str:
    """Add a tip or note to a destination in Firestore.

    Args:
        destination_id: The destination ID (e.g. 'tokyo', 'san-francisco', 'paris', 'kyoto').
        note: The tip or note text to add.

    Returns:
        Success confirmation message.
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("destinations").document(destination_id.lower().strip())
        doc = doc_ref.get()

        if not doc.exists:
            return f"Destination '{destination_id}' does not exist in Firestore."

        data = doc.to_dict()
        notes = data.get("notes", [])
        notes.append(note)

        doc_ref.update({"notes": notes})
        return f"Successfully added note to destination '{destination_id}'."
    except Exception as e:
        return f"Error adding note to Firestore: {str(e)}"
