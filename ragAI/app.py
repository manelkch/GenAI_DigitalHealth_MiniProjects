from functions import *
import streamlit as st

st.set_page_config(page_title="RAG System", page_icon="🌐", layout="wide")

start = time.perf_counter()

st.title("Augmented Retrieval System")

query = st.text_input("Enter your question : ")

if query:
    docs = deserialize_file('list_docs_file.pkl')

    relevant_docs = query_database(deserialize_file('list_docs_file.pkl'), [query], 2)

    response = llm(query, relevant_docs)

    formatted_text = response['answer'].replace("\n", "<br>")

    cleaned = clean_markdown(response['answer'])

    with st.container():
        st.markdown(f"""
            <div style="
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 20px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                margin-top: 20px;
            ">
            {cleaned}
            </div> """,unsafe_allow_html=True)
    

    for source in response['list_of_chunks']:
        st.markdown(f'<a style="color: #007aff; text-decoration: none; font-weight: 500;" href="{source["source_url"]}" target="_blank">{source["source_url"]}</a>', unsafe_allow_html=True)
        for i, chunk in enumerate(source["chunks"]):
            st.markdown(f'<div style="background-color: #f0f0f5; padding: 15px; border-radius: 12px; margin-top: 10px; font-size: 14px;"><strong>Chunk {i+1} :</strong> {chunk}</div>', unsafe_allow_html=True)

    #st.write(response['list_of_chunks'])

    end = time.perf_counter()
    print("Execution time:", end - start, "seconds")