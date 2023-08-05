import openai
import streamlit as st
import pandas as pd
import requests

st.title("Digital Book Tutor")

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Load the lessons from the CSV
lessons_df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vT42k3EGPUsfJQ4FWqqwRjMY6KsUm6lRicOVMJ9AmaaEzLL99CDRRYg4tpaRdfoz_biAIvkUnv8v9dC/pub?gid=0&single=true&output=csv')

# 1. Add the Authentication Sidebar
email = st.sidebar.text_input("Enter your email:")
auth_code = st.sidebar.text_input("Enter your authentication code:", type="password")

# 3. Validate the Authentication Code
authenticated = auth_code in st.secrets.get("VALID_AUTH_CODES", [])

# 2. Limit the Lessons Dropdown
if not authenticated:
    lessons_available = lessons_df['Lesson Number'].unique()[:2]  # Show only first 2 lessons
else:
    lessons_available = lessons_df['Lesson Number'].unique()

lesson_number = st.selectbox('Choose a lesson', lessons_available)

# Create dropdown for lesson selection
lesson_number = st.selectbox('Choose a lesson', lessons_df['Lesson Number'].unique())

# Fetch the prompt text
prompt_text = requests.get('https://raw.githubusercontent.com/jamesrothmann/aibooktutor/main/prompt.txt').text

# Get the lesson material for the selected lesson
lesson_material = lessons_df.loc[lessons_df['Lesson Number'] == lesson_number, 'Lesson Material'].values[0]

# Combine the prompt text and lesson material
full_prompt_text = f"{prompt_text} {lesson_material}"

# Continue with the chat interface
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo-16k"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Let's begin!!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
       for response in openai.ChatCompletion.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": "system", "content": full_prompt_text}
            ] + [
                {"role": "user", "content": "I'm ready to begin"}
            ] + [
                {"role": "assistant", "content": "Next up, I'll provide a meticulous summary of the prime concepts encapsulated in the chapter, streamlining complex ideas into clear insights."}
            ] + [
                {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
            ],
            stream=True,
            temperature=0,
            max_tokens=2000,
            n=1,
            stop=None,
            frequency_penalty=0,
            presence_penalty=0
        ):
            full_response += response.choices[0].delta.get("content", "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
