import streamlit as st
import anthropic
import json
import time

# Load prompts from Markdown files
@st.cache_data
def load_prompts():
    with open('prompts/config.json', 'r') as config_file:
        config = json.load(config_file)
    
    prompts = {}
    for key, filename in config.items():
        with open(f'prompts/{filename}', 'r') as file:
            prompts[key] = file.read()
    
    return prompts

prompts = load_prompts()

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def send_prompt_to_claude(prompt, system_prompt=""):
    api_key = st.secrets["CLAUDE_KEY"]
    
    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=8192,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return response.content[0].text
    except anthropic.APIError as e:
        if "rate limit" in str(e).lower():
            raise Exception("Rate limit exceeded. Please wait a moment and try again.")
        else:
            raise Exception(f"An API error occurred: {str(e)}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")

# Streamlit UI
st.title("T&C Generator Bot")

# User input form
with st.form("user_input_form"):
    st.write("Please provide the following information:")
    promotion_reward = st.text_input("1. Promotion Reward:")
    promotion_period = st.text_input("2. Promotion Period:")
    eligible_providers = st.text_input("3. Eligible Providers/Products:")
    max_redemptions = st.text_input("4. Maximum number of redemptions:")
    additional_eligibility = st.text_area("5. Additional eligibility requirements:")
    specific_requirements = st.text_area("6. Specific product requirements:")
    additional_info = st.text_area("7. Any additional information:")

    submit_button = st.form_submit_button("Generate T&Cs")

if submit_button:
    if not all([promotion_reward, promotion_period, eligible_providers, max_redemptions]):
        st.error("Please fill in all required fields (1-4).")
    else:
        user_input = f"""
        1. {promotion_reward}
        2. {promotion_period}
        3. {eligible_providers}
        4. {max_redemptions}
        5. {additional_eligibility}
        6. {specific_requirements}
        7. {additional_info}
        """

        full_prompt = f"""
        You are tasked with drafting T&Cs for the fulfilment of rewards given during promotional campaigns. You have a process for creating T&C's which you follow diligently.
        First, review your template and reference documents cited below enclosed in xml tags.
        Second, use the variables provided by the user between the <user_input></user_input> tags below in order to fill in the T&C.
        Third, extract from the template the section named "General Promotional Terms & Conditions". Paste it verbatim at the end of the T&C document you generate.
        Return a full, comprehensive T&C document in markdown with the updated information similar to the examples. Remember to include include the "General Promotional Terms & Conditions" after the generated T&C.

        <template>
        {prompts['template']}
        </template>

        <user_input>
        {user_input}
        </user_input>

        <example1>
        {prompts['example1']}
        </example1>

        <example2>
        {prompts['example2']}
        </example2>
        """

        with st.spinner("Generating T&Cs..."):
            try:
                result = send_prompt_to_claude(full_prompt, prompts['system_prompt'])
                if result:
                    st.markdown("## Generated T&Cs:")
                    st.markdown(result)
                    st.session_state.chat_history.append({"role": "assistant", "content": "T&Cs generated successfully."})
                else:
                    st.error("Failed to generate T&Cs. The response was empty.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.error("If this persists, please contact the administrator.")
            
            time.sleep(1)

else:
    st.info("Please fill out the form to generate T&Cs.")

# Display chat history
st.subheader("Chat History")
for message in st.session_state.chat_history:
    st.write(f"{message['role']}: {message['content']}")

# Clear chat history button
if st.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.success("Chat history cleared.")