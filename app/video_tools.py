import base64
import os
import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

PROJECT_ID = "qwiklabs-gcp-01-3e01eedce187"
BUCKET_NAME = "smart-travel-concierge-media-qwiklabs-gcp-01-3e01eedce187"


async def generate_destination_video(
    prompt: str, tool_context: ToolContext = None
) -> str:
    """Generates a short travel preview video for a destination or attraction using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Args:
        prompt: Description of the travel destination or scenic video to generate (e.g. 'A short cinematic video preview of Kyoto cherry blossoms').
        tool_context: ADK tool context injected automatically for saving artifacts.

    Returns:
        The public HTTPS URL of the generated video uploaded to Cloud Storage.
    """
    try:
        os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
        os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "True"

        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

        res = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        output_video = getattr(res, "output_video", None)
        if not output_video:
            return "Failed to generate video: no video output returned from gemini-omni-flash-preview."

        mime_type = str(getattr(output_video, "mime_type", None) or "video/mp4")
        raw_data = getattr(output_video, "data", None)

        if isinstance(raw_data, str):
            video_bytes = base64.b64decode(raw_data)
        elif isinstance(raw_data, bytes):
            video_bytes = raw_data
        else:
            return "Failed to extract video bytes from gemini-omni-flash-preview response."

        filename = f"destination_video_{uuid.uuid4().hex[:8]}.mp4"

        # (1) Save video artifact in Playground panel if tool_context is provided
        if tool_context is not None:
            try:
                artifact_part = types.Part.from_bytes(
                    data=video_bytes, mime_type=mime_type
                )
                await tool_context.save_artifact(
                    filename=filename, artifact=artifact_part
                )
            except Exception as artifact_err:
                print(f"Warning: Could not save video artifact in tool_context: {artifact_err}")

        # (2) Upload video bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_path = f"videos/{filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
        return public_url

    except Exception as e:
        return f"Error generating destination video: {str(e)}"
