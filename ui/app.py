import streamlit as st


st.title("India Electoral Bonds")

st.write("You may ask questions about parties who encashed the electoral bonds or donors who purchased the electoral bonds")

def handle_submit(query):
    """
    Submit handler:
    """

    # Handle the response
    with st.spinner('Thinking...'):
        response = " :smile: Response to the question: " + query
        write_message('assistant', response)


def write_message(role, content):
    """
    This is a helper function that writes a message to the UI
    """

    # Write to UI
    with st.chat_message(role):
        st.markdown(content)


# Handle any user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    write_message('user', prompt)

    # Generate a response
    handle_submit(prompt)
    

