"""Seed Firestore database with travel destination items."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-3e01eedce187"

SEED_DESTINATIONS = [
    {
        "id": "tokyo",
        "name": "Tokyo",
        "country": "Japan",
        "category": "Cultural & Art",
        "description": "High-tech metropolis with historic temples, world-class art museums, and vibrant cuisine.",
        "avg_daily_budget_usd": 150,
        "top_attractions": ["Mori Building Digital Art Museum", "Meiji Shrine", "Ghibli Museum", "Shinjuku Gyoen"],
        "vegetarian_friendly": True,
    },
    {
        "id": "san-francisco",
        "name": "San Francisco",
        "country": "USA",
        "category": "Coastal & Scenic",
        "description": "Famous coastal city known for the Golden Gate Bridge, steep rolling hills, and rich culinary culture.",
        "avg_daily_budget_usd": 200,
        "top_attractions": ["Golden Gate Bridge", "SFMOMA", "Fisherman's Wharf", "Chinatown"],
        "vegetarian_friendly": True,
    },
    {
        "id": "paris",
        "name": "Paris",
        "country": "France",
        "category": "Art & History",
        "description": "City of Light known for iconic architecture, world-renowned art galleries, and historic landmarks.",
        "avg_daily_budget_usd": 220,
        "top_attractions": ["Louvre Museum", "Eiffel Tower", "Musée d'Orsay", "Montmartre"],
        "vegetarian_friendly": True,
    },
    {
        "id": "kyoto",
        "name": "Kyoto",
        "country": "Japan",
        "category": "Historic & Spiritual",
        "description": "Japan's ancient capital celebrated for classical Buddhist temples, gardens, and imperial palaces.",
        "avg_daily_budget_usd": 130,
        "top_attractions": ["Fushimi Inari Shrine", "Kinkaku-ji (Golden Pavilion)", "Arashiyama Bamboo Grove"],
        "vegetarian_friendly": True,
    },
]


def seed():
    """Seed the destinations collection in Firestore."""
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("destinations")
    print(f"Seeding Firestore collection 'destinations' in project '{PROJECT_ID}'...")

    for item in SEED_DESTINATIONS:
        doc_id = item["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"  [✓] Seeded destination: {item['name']} (ID: {doc_id})")

    print("\nFirestore seeding complete!")


if __name__ == "__main__":
    seed()
