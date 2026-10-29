import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

PROJECT_ID = "qwiklabs-gcp-01-3e01eedce187"
BUCKET_NAME = "smart-travel-concierge-media-qwiklabs-gcp-01-3e01eedce187"


async def generate_destination_image(
    prompt: str, tool_context: ToolContext = None
) -> str:
    """Generates a travel destination preview photo or landscape concept image using Gemini 3.1 Flash-Lite Image.

    Args:
        prompt: Description of the travel destination or scene to generate (e.g. 'A scenic view of Kyoto cherry blossoms at sunset').
        tool_context: ADK tool context injected automatically for saving artifacts.

    Returns:
        The public HTTPS URL of the generated image uploaded to Cloud Storage.
    """
    try:
        client = genai.Client(
            vertexai=True, project=PROJECT_ID, location="global"
        )
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or mime_type
                    break

        if not image_bytes:
            return "Failed to generate image: no image data returned from model."

        filename = f"destination_{uuid.uuid4().hex[:8]}.jpg"

        # (1) Save image artifact in Playground panel if tool_context is provided
        if tool_context is not None:
            try:
                artifact_part = types.Part.from_bytes(
                    data=image_bytes, mime_type=mime_type
                )
                await tool_context.save_artifact(
                    filename=filename, artifact=artifact_part
                )
            except Exception as artifact_err:
                print(f"Warning: Could not save artifact in tool_context: {artifact_err}")

        # (2) Upload image bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_path = f"images/{filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
        return public_url

    except Exception as e:
        return f"Error generating destination image: {str(e)}"
