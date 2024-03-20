import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from utils import generate_response

st.title("India Electoral Bonds")

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


def handle_submit(query):
    """
    Submit handler:
    """

    # Handle the response
    with st.spinner('Thinking...'):
        #response = " :smile: Response to the question: " + query
        response = generate_response(query)
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
    

