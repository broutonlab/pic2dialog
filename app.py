import streamlit as st
import os, base64
from dotenv import load_dotenv
from openai import OpenAI
from io import BytesIO
from PIL import Image
load_dotenv()

if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-4o-mini"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to encode the image
def encode_image_from_file(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def encode_image(pil_image):
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")  # Save the image in memory in PNG format (or another format as needed)
    buffer.seek(0)  # Move to the start of the buffer
    return base64.b64encode(buffer.read()).decode("utf-8")

def describe_image(image):
    base64_image = encode_image(image)
    
    response = client.chat.completions.create(
        model=st.session_state.openai_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe the character on this image. Don't write preambule like 'the character in this image appears to be ...' or similar'. Your output should contain just description."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    
    return response.choices[0].message.content
        

st.title("Drag-and-Drop Image Upload")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not "uploaded_image" in st.session_state:
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.session_state.uploaded_image = image
        st.session_state.character_description = describe_image(image)
        st.rerun()
        
    
if "uploaded_image" in st.session_state:
    image = st.session_state.uploaded_image
    st.image(image, caption="Uploaded Image", use_container_width=True)        
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Your input"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        messages = [ {"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        messages.append({
            "role": "system",
            "content": f"answer on the user input. Keep in mind you can be described as following: {st.session_state.character_description}"
        })
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages= messages,
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})