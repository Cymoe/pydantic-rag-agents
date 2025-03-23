import streamlit as st
from agents.pydantic_ai_expert import pydantic_ai_expert

st.title('Pydantic AI RAG System')

query = st.text_input('Enter your question:')

if query:
    result = pydantic_ai_expert.run(query)
    st.write(result)