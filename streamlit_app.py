import streamlit as st
from openai import OpenAI
import json

# Show title and description.
st.title("💬 Chat with UTS Research")
st.write(
    "University of Technology Sydney (UTS) had over 1,000 researchers across various disciplines and research programs. "
    "Chat privately with our AI to discover which UTS researchers can help you."
)
st.warning('This demo AI agent is trained on famous scientists, rather than using proprietary data about UTS research.', icon="⚠️")

# keep list of researchers and excluded
if "researchers" not in st.session_state:
    st.session_state.researchers = []

if "researchers_excluded" not in st.session_state:
    st.session_state.researchers_excluded = []

def exclude_researcher(researcher):
    st.session_state.researchers_excluded.append(researcher)

    researchers_remaining = list(set([r for r in st.session_state.researchers if r not in st.session_state.researchers_excluded]))
    content = f'{researcher} has left the chat. Please continue your chat with ' + ' and '.join(researchers_remaining) + '.'

    st.session_state.messages.append({"role": "assistant", "content": content})

openai_api_key = st.secrets["openai_key"]
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")

else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            try:
                messages = json.loads(message["content"])

                cols = st.columns(len(messages))

                # Display each answer in its respective column
                for idx, col in enumerate(cols):
                    researcher = messages[idx]['researcher']
                    if not researcher in st.session_state.researchers_excluded:

                        with col:
                            st.subheader(researcher, divider=True)
                            st.markdown(messages[idx]['response'])

            except Exception as err:
                st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    placeholder = "What's your research interest?"
    if len(st.session_state.messages):
        placeholder = "Continue your chat"

    if prompt := st.chat_input(placeholder):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        system_message = 'You are an AI system that impersonates famous historical and fictional scientists and inventors, who chat with users and answer their questions about the research being conducted at the University of Technology Sydney (UTS). All scientific research ever conducted has happened at UTS. '
        
        researchers_remaining = list(set([r for r in st.session_state.researchers if r not in st.session_state.researchers_excluded]))

        if len(researchers_remaining):
            system_message += 'The people to impersonate: ' + ', '.join(researchers_remaining) + '. '

        else:
            system_message += 'Pick three relevant scientists to impersonate.  '

        system_message += 'Respond as an array of JSON objects, for example [{"researcher":"Thomas Edison", "response":"I can help..."}, {"researcher":"Marie Curie", "response":"I can help too..."}]'

        messages = [{"role": "system", "content": system_message}]
        
        # hided excluded parts
        for message in st.session_state.messages:

            try:
                message_content = json.loads(message["content"])

                # Display each answer in its respective column
                for response in message_content:
                    researcher = response['researcher']
                    if not researcher in st.session_state.researchers_excluded:
                        messages.append({"role": message["role"], "content": researcher + ': ' + response['response']})

            except Exception as err:
                messages.append({"role": message["role"], "content": message["content"]})
        
        #messages += [
        #    {"role": m["role"], "content": m["content"]}
        #    for m in st.session_state.messages
        #]

        # Generate a response using the OpenAI API.
        ai_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            #stream=True,
        )
        response_dict = ai_response.model_dump()
        message_content = response_dict["choices"][0]["message"]["content"]

        st.session_state.messages.append({"role": "assistant", "content": message_content})

        with st.chat_message("assistant"):
            try:
                messages = json.loads(message_content)

                cols = st.columns(len(messages))

                # Display each answer in its respective column
                for idx, col in enumerate(cols):
                    researcher = messages[idx]['researcher']
                    st.session_state.researchers = list(set(st.session_state.researchers + [researcher]))
                    
                    with col:    
                        st.subheader(researcher, divider=True)
                        st.markdown(messages[idx]['response'])
                        
                        button_cols = st.columns(2)
                        with button_cols[0]: 
                            st.link_button('Contact', url='https://profiles.uts.edu.au/Glen.Babington', type="primary")

                            with button_cols[1]: 
                                if len(cols) > 1:
                                    st.button('Hide', key=f"contact-{idx}", type="tertiary", on_click=exclude_researcher, args=(researcher,))

            except Exception as err:
                st.markdown(message_content)
