import streamlit as st
import fitz
from PIL import Image
import io
import json
import google.generativeai as genai
import os
import pyperclip
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize GenerativeModel
model_vision = genai.GenerativeModel('gemini-pro-vision')
model_text = genai.GenerativeModel("gemini-1.5-pro-latest")

# Paths
INTERMEDIATE_JSON_PATH = "temp.json"
INTERMEDIATE_JOB_DESC_PATH = "temp_job_desc.txt"

def load_prompt(prompt_file_path):
    with open(prompt_file_path, "r") as file:
        return file.read()

# Function to process PDF and extract content
def process_pdf_and_save_job_desc(uploaded_file, job_description):
    if not uploaded_file:
        return None, "No file provided"

    # Read the PDF content
    pdf_content = uploaded_file.read()

    # Convert PDF to image
    doc = fitz.open(stream=pdf_content, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap()
    img_bytes = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_bytes))
    doc.close()

    # Further processing with the image
    prompt = load_prompt("prompts/resume_parsing_prompt.txt")
    response = model_vision.generate_content([prompt, image])
    
    json_data = response.text

    # Save the JSON data for other tabs to access
    with open(INTERMEDIATE_JSON_PATH, "w") as json_file:
        json.dump(json_data, json_file)

    with open(INTERMEDIATE_JOB_DESC_PATH, "w") as file:
        file.write(job_description)

    return image, json_data

# Function to generate interview questions
def generate_interview_questions_for_employer():
    with open(INTERMEDIATE_JSON_PATH, "r") as json_file:
        json_data = json.load(json_file)
    
    prompt = load_prompt("prompts/interview_questions_prompt.txt") + json_data
    responses = model_text.generate_content(prompt)

    try:
        return responses.text
    except:
        st.write(responses)

def generate_interview_questions_for_employee():
    with open(INTERMEDIATE_JSON_PATH, "r") as json_file:
        json_data = json.load(json_file)
    
    prompt = load_prompt("prompts/interview_Questions_employee.txt") + json_data
    responses = model_text.generate_content(prompt)

    try:
        return responses.text
    except:
        st.write(responses)

# Function to generate job-related questions
def generate_job_related_questions(resume_data, job_description):
    # Create prompt
    prompt = load_prompt("prompts/job_questions_prompt.txt").replace(
            "job_description", job_description).replace("resume_description", resume_data)

    # Generate responses using the model
    responses = model_text.generate_content(prompt)
    try:
        return responses.text
    except:
        st.write(responses)

# Modify generate_cover_letter to take job description input
def generate_cover_letter():
    try:
        # Read the saved job description
        with open(INTERMEDIATE_JOB_DESC_PATH, "r") as file:
            job_description = file.read()

        # Read the saved resume data (JSON)
        with open(INTERMEDIATE_JSON_PATH, "r") as file:
            json_data = file.read()

        # Create a prompt for the cover letter
        prompt = load_prompt("prompts/cover_letter_prompt.txt").replace(
            "job_description", job_description).replace("json_data", json_data)

        # Generate the cover letter using the model
        response = model_text.generate_content(prompt, stream=True)
        response.resolve()

        return response.text

    except Exception as e:
        return f"An error occurred: {e}"
    
def generate_rating(resume_data, job_description):
    prompt = load_prompt("prompts/ratings_prompt.txt").replace(
        "job_description", job_description).replace("resume_data", resume_data)
    responses = model_text.generate_content(prompt)
    try:
        return int(responses.text)
    except:
        return 'No response'

def loadingScreen():
    st.text("🔍 Processing your resume...")
    st.text("📝 Generating personalized content...")
    st.text("🎯 Analyzing your qualifications...")
    st.text("🚀 Success! Your content is ready!")

def star_rating(rating):
    # Display stars based on the rating
    stars = '★' * int(rating) + '☆' * (10 - int(rating))
    return stars    

def get_fit_level(rating):
    if rating <= 2:
        return "Not a great fit"
    elif rating <= 4:
        return "Below average fit"
    elif rating <= 6:
        return "Average fit"
    elif rating <= 8:
        return "Good fit"
    else:
        return "Best fit"    

def main():
    st.set_page_config(page_title="ResumeMagic", 
                   page_icon="📄",
                   layout="wide",
                   initial_sidebar_state="expanded"
                   )
    
    # Custom CSS for better UI
    st.markdown(
        """
        <style>
        .main {
            background-color: black;
            color: white;
        }
        .stApp {
            background-color: black;
            color: white !important;
        }
        div[data-testid="stText"] {
            color: white !important;
        }
        div[data-testid="stMarkdown"] {
            color: white !important;
        }
        div[data-testid="stHorizontalBlock"] div[role="listbox"] {
            color: white !important;
        }
        input[type="text"], input[type="email"], input[type="password"], textarea, select {
            color: white !important;
            background-color: black !important;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )
    
    # Upload resume and job description
    st.title("📄 ResumeMagic Resume Analyzer")
    st.markdown("### Upload your resume and job description to get started.")
    st.markdown('___')

    uploaded_file = st.file_uploader("📁 Upload your resume (PDF)", type=["pdf"])
    
    # Input job description
    job_description_input = st.text_area("📝 Enter job description")
    
    st.markdown('___')
    st.markdown("### ✅ Select the options you want to perform:")
    extractResumeOption = st.checkbox('🧬 Extract Resume Information')
    generateCoverLetterOption = st.checkbox('📫 Generate Personalized Cover Letter')
    generatePersonalizedQuestionsOption = st.checkbox('✨ Generate Personalized Interview Questions')

    if st.button("🚀 Process"):
        if uploaded_file and job_description_input:
            with st.spinner('Processing...'):
                image, json_data = process_pdf_and_save_job_desc(uploaded_file, job_description_input)
                ratingval = generate_rating(json_data, job_description_input)

                st.markdown('___')
                st.markdown(f"### Fit Level: {star_rating(ratingval)} - {get_fit_level(ratingval)}")
                
                # Display processed PDF and extracted JSON content
                if extractResumeOption:
                    st.image(image, caption="Processed PDF")
                    st.subheader("Extracted JSON Content:")
                    st.json(json_data)

                if generateCoverLetterOption:
                    st.subheader("Generated Cover Letter")
                    result = generate_cover_letter()
                    st.write(result)
                    st.button("📋 Copy to Clipboard", on_click=lambda: pyperclip.copy(result))

                if generatePersonalizedQuestionsOption:
                    st.subheader("Personalized Interview Questions")
                    st.text_area(label='', value=generate_interview_questions_for_employee(), height=300)
        else:
            st.warning("⚠️ Please upload a resume and enter a job description to proceed.")

if __name__ == "__main__":
    main()
