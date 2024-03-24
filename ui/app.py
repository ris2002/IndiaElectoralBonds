import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from utils import generate_response
import os
import base64
from utils import get_party_options, get_donor_options


def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def get_img_with_href(local_img_path):
    img_format = os.path.splitext(local_img_path)[-1].replace('.', '')
    bin_str = get_base64_of_bin_file(local_img_path)
    app_title = f'''<h1>India Electoral Bonds<sup style='font-size:.8em;'>
                    <img width="30" height="20" src="data:image/{img_format};base64,{bin_str}" 
                    alt='Beta Icon'></sup></h1>'''
    return app_title

app_title = get_img_with_href('images/beta.jpeg')

# Display the title using Markdown
st.markdown(app_title, unsafe_allow_html=True)

st.write("You may ask questions about parties who encashed the electoral bonds or donors who purchased the electoral bonds")

# Setup session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="How can I help you?"),
    ]

# Render current messages from session state
for msg in st.session_state.chat_history:
    if isinstance(msg, AIMessage):
        st.chat_message("ai").write(msg.content)
    elif isinstance(msg, HumanMessage):
        st.chat_message("human").write(msg.content)


def generate_history():
    context = []
    # If any history exists
    if st.session_state["chat_history"]:
        # Add the last three exchanges
        size = len(st.session_state["chat_history"])
        for i in range(max((size-1) - 6, 1), size-1):
            context.append(
                (st.session_state["chat_history"][i])
            )
    return context

def handle_submit(query):
    """
    Submit handler:
    """

    # Handle the response
    with st.spinner('Thinking...'):
        #response = " :smile: Response to the question: " + query
        history = generate_history()
        #print(history)
        # put the following line try catch block
        #try:
        query = "Selected parties: " + str(st.session_state.selected_parties) + " Selected donors: " + str(st.session_state.selected_donors) + " " + query
        response = generate_response(query)
        #except Exception as e:
        #response = f"I am unable to answer your question at this time. Please try again." + str(e)

        
        write_message('assistant', response)


def write_message(role, content):
    """
    This is a helper function that writes a message to the UI
    """

    # Write to UI
    #with st.chat_message(role):
        #st.markdown(content)
    if role == "user":
        st.session_state.chat_history.append(HumanMessage(content=content))        
    else:
        st.session_state.chat_history.append(AIMessage(content=content))
    with st.chat_message(role):
        st.markdown(content)


# Handle any user input

if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    write_message('user', prompt)

    # Generate a response
    handle_submit(prompt)

col1, col2 = st.columns(2)
with col1:
    # put the values in a session state    
    st.session_state.selected_parties = st.multiselect("Select Party", options=get_party_options(), default=[])
with col2:
    st.session_state.selected_donors = st.multiselect("Select Donor", options=get_donor_options(), default=[])

