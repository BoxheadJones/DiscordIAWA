import os
import json
import random
import google.generativeai as genai
from google.cloud import storage  # Import the GCS client library

# --- Configure Gemini API ---
# Replace with your actual Gemini API key
genai.configure(api_key="YOUR_GEMINI_API_KEY")  # IMPORTANT: Replace this!
model = genai.GenerativeModel('gemini-2.0-flash-lite')
print(f"Attempting to use model: {model.model_name}")

# --- Google Cloud Storage Configuration ---
# Replace with your Google Cloud Storage bucket name
BUCKET_NAME = "iawa_storage"
# Path within the bucket where you want to store the file
ORACLE_GCS_PATH = "oracle/oracle.json"  # Corrected variable name

# --- Oracle Generation ---
def generate_oracle(tone="mythic conflict, fate-bound ambition, ancient sin"):
    prompt = f"""
Create 4 oracle tables, each named, each with 13 vivid, evocative story elements.
The tone is: "{tone}".

Output raw JSON only, like this:
{{
  "Oracle of [Table Name]": [
    "Element 1",
    ...
  ],
  ...
}}
"""
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.95
        ),
        safety_settings=[
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            },
        ]
    )
    content = response.text.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    try:
        oracle_json = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for oracle: {e}")
        print(f"Problematic content: {content}")
        return None

    # Upload to Google Cloud Storage
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(ORACLE_GCS_PATH)
        blob.upload_from_string(json.dumps(oracle_json, indent=2))
        gcs_url = f"gs://{BUCKET_NAME}/{ORACLE_GCS_PATH}"  # Construct the GCS URL
        print(f"Oracle data uploaded to {gcs_url}")
        return gcs_url # Return the URL
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None  # Indicate failure

def generate_gcs_link(bucket_name, blob_name):
    """Generates a GCS link."""
    return f"gs://{bucket_name}/{blob_name}"

if __name__ == "__main__":
    gcs_link = generate_oracle() # Capture the returned URL
    if gcs_link:
        print(f"Oracle data generated and uploaded successfully.  GCS Link: {gcs_link}")
    else:
        print("Oracle generation or upload failed.")
