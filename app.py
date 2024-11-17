import openai
import streamlit as st
import pandas as pd
import requests
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

st.title("Digital Book Tutor")

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Load the lessons from the CSV
lessons_df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vT42k3EGPUsfJQ4FWqqwRjMY6KsUm6lRicOVMJ9AmaaEzLL99CDRRYg4tpaRdfoz_biAIvkUnv8v9dC/pub?gid=0&single=true&output=csv')

# 1. Define the verify_license function
def verify_license(product_id, license_key):
    endpoint = "https://api.gumroad.com/v2/licenses/verify"
    data = {
        "product_id": product_id,
        "license_key": license_key
    }
    response = requests.post(endpoint, data=data)
    if response.status_code == 200:
        json_response = response.json()
        if json_response.get("success"):
            return True
    return False

# 2. Create Sidebar Elements
license_key = st.sidebar.text_input("Enter your Gumroad license key:", type="password")
verify_button = st.sidebar.button("Verify License Key")
st.sidebar.markdown("### [Get a licence key](https://jamesrothmann.gumroad.com/l/zyuxle)")

lessons_available = lessons_df['Lesson Number'].unique()[:2]  # Default to first 2 lessons

# 3. Integrate the Gumroad API and Verify License
if verify_button:
    product_id = "UDzAb2J6_bbk7V4xH0I5NQ=="
    if verify_license(product_id, license_key):
        st.sidebar.markdown("✅ License key verified!")
        lessons_available = lessons_df['Lesson Number'].unique()
    else:
        st.sidebar.markdown("❌ Invalid license key. Please try again or purchase a valid key.")

# 4. Define the lesson_number dropdown
lesson_number = st.selectbox('Choose a lesson', lessons_available)

# 5. Access lesson_material
lesson_material = lessons_df.loc[lessons_df['Lesson Number'] == lesson_number, 'Lesson Material'].values[0]

# Fetch the prompt text
prompt_text = requests.get('https://raw.githubusercontent.com/jamesrothmann/aibooktutor/main/prompt.txt').text

# Get the lesson material for the selected lesson
lesson_material = lessons_df.loc[lessons_df['Lesson Number'] == lesson_number, 'Lesson Material'].values[0]

# Combine the prompt text and lesson material
full_prompt_text = f"{prompt_text} {lesson_material}"

# Continue with the chat interface
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Let's begin!!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # New API call using OpenAI client
        try:
            response = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": "system", "content": full_prompt_text},
                    {"role": "user", "content": "I'm ready to begin"},
                    {"role": "assistant", "content": "Next up, I'll provide a meticulous summary of the prime concepts encapsulated in the chapter, streamlining complex ideas into clear insights."}
                ] + [
                    {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                ],
                temperature=0,
                max_tokens=2000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type": "text"}
            )

            # Process response content
            full_response = response['choices'][0]['message']['content']
            message_placeholder.markdown(full_response)

        except Exception as e:
            message_placeholder.markdown(f"⚠️ Error: {str(e)}")

    # Append assistant response to the session state
    st.session_state.messages.append({"role": "assistant", "content": full_response})
