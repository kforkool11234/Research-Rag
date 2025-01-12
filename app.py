import streamlit as st
from isthisrag import main

# Set the title of the app
st.title("LLM Query Interface")

# Create an input area for user queries
user_query = st.text_area("Enter your query (max 60,000 words):")

# Button to submit the query
if st.button("Submit"):
    if user_query:
        # Calculate word count
        word_count = len(user_query.split())
        
        if word_count > 60000:
            st.error(f"Your query contains {word_count} words, which exceeds the limit of 60,000 words. Please reduce the length and try again.")
        else:
            # Show loading message and time estimate
            with st.spinner("Generating response..."):
                st.info("It takes around 1 minute 30 seconds to generate a paper and around 30 seconds to generate an answer from the paper.")
                # Call your LLM function here
                response = main(user_query)  # Replace with your LLM call
            
            st.subheader("Response:")
            st.write(response)
    else:
        st.warning("Please enter a query before submitting!")
