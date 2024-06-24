import os
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import google.generativeai as genai

# Load environment variables
load_dotenv(override=True)

# Set variable if script is running in a docker container
DOCKER_ENV = False

try:
    # Set the Google Application Credentials (Needed when running in a docker container)
    if "/app/credentials.json" in os.listdir("/app"): # This is th case when running in a docker container
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/app/credentials.json'
        DOCKER_ENV = True
except:
    print("Not running in a docker container")
    pass

# Configure Google GenerativeAI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompt for summarization
prompt = """Welcome, Video Summarizer! Your task is to distill the essence of a given YouTube video transcript into a concise summary. Your summary should capture the key points and essential information, presented in bullet points, within a 250-word limit. Let's dive into the provided transcript and extract the vital details for our audience."""


# Function to extract transcript details from a YouTube video URL
def extract_transcript_details(youtube_video_url):
    """
    Extracts transcript details from a YouTube video URL.

    Args:
        youtube_video_url (str): The URL of the YouTube video.

    Returns:
        str: The transcript of the YouTube video.

    Raises:
        ValueError: If the YouTube URL has an invalid format.
    """
    # Check if the URL contains "=" which indicates a full YouTube URL
    if "v=" in youtube_video_url:
        video_id = youtube_video_url.split("v=")[-1].split("&")[0]
        print(f"Video ID with 'v=': {video_id}")
    # Check if the URL contains the short form "youtu.be"
    elif "youtu.be" in youtube_video_url:
        video_id = youtube_video_url.split("/")[-1]
        print(f"Video ID with 'youtu.be': {video_id}")
    else:
        # If the URL doesn't match the expected format, raise an error
        raise ValueError("The YouTube URL has an invalid format.")

    # Display the video thumbnail
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

    # Get the transcript for the YouTube video
    try:
        # Get the list of available transcripts
        transcript_list = list(YouTubeTranscriptApi.list_transcripts(video_id))
        # Check if there are any transcripts available
        if not transcript_list:
            st.write("Sorry, no transcript available for the provided YouTube video.")
            return None
        else:
            # Get the transcript for the video in English or German
            try:
                transcript_text = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["en", "de"]
                )
                
                # Combine the text from all the transcript items into a single string
                transcript = " ".join(item["text"] for item in transcript_text)

                # Return the transcript
                return transcript
            except Exception as e:
                # If there is an error in fetching the transcript, raise the error
                raise e

    # Handle the case where the video has disabled subtitles
    except TranscriptsDisabled:
        st.write("Subtitles are disabled for this video.")
        return None
    # Handle any other exceptions
    except Exception as e:
        st.write(f"An error occurred: {str(e)}")
        return None


# Function to generate summary using Google Gemini Pro
def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + transcript_text)
    # Return the generated summary
    return response.text


# Streamlit UI
st.title(
    "Gemini YouTube Transcript Summarizer: Extract Key Insights from YouTube Videos"
)
# Input field for the YouTube video link
youtube_link = st.text_input("Enter YouTube Video Link:")

# Check if the YouTube link is provided
if youtube_link:
    transcript_text = extract_transcript_details(youtube_link)

    if transcript_text:
        # Generate summary using Gemini Pro
        summary = generate_gemini_content(transcript_text, prompt)

        # Display summary
        st.markdown("## Detailed Notes:")
        st.write(summary)
