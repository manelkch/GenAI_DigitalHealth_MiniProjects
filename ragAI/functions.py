from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from numpy.linalg import norm
import numpy as np
import os
from dotenv import load_dotenv
from mistralai import Mistral
import json
import pickle
import joblib 
import requests
from pathlib import Path
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from tika import parser 
import pickle 
import time
import re 


# RETRIEVE DATA

# get the list of document references from NICE website
def get_references_nice() -> list[str]:
    # Excel file path
    file_path = "NICE_Documents_References.xlsx"

    # load file in a dataframe
    df = pd.read_excel(file_path)

    refs = list(df["Reference number"])
    
    return refs

# get pdf url of a reference
def get_pdf_url(ref):
    base_url = "https://www.nice.org.uk"
    url = f"https://www.nice.org.uk/guidance/{ref}"
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text

    soup = BeautifulSoup(html_content, "html.parser")
    #print(soup)
    pdf_link = soup.find_all('a', class_='btn btn--cta mr--0 mb--e mb--d-sm show-ib show-sm text-center')
    endpoint = pdf_link[0]['href']
    
    pdf_url = f"{base_url}{endpoint}"
    
    return pdf_url


# download automatically pdf from pdf url
def download_pdf(ref : str, pdf_url : str):
    #url = "https://www.nice.org.uk/guidance/ng255/resources/suspected-sepsis-in-pregnant-or-recently-pregnant-people-recognition-diagnosis-and-early-management-pdf-66144018745285"
    #output_path = Path("ng255_sepsis.pdf")
    output_path = Path(f"documents/{ref}.pdf")

    response = requests.get(pdf_url)
    response.raise_for_status()  # stop if request failed

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"PDF saved to {output_path}")


def get_content_pdf(ref):
    source_url = f"https://www.nice.org.uk/guidance/{ref}"
    raw = parser.from_file(f'/Users/familyelkouch/ragAI/documents/{ref}.pdf')
    content = raw['content'].replace("\n", " ").replace("\t", " ")
    return {"source_url" : source_url, "content" : content}


def get_list_documents_content(refs):
    list_docs = []
    for ref in refs[0:2396]:
        doc = get_content_pdf(ref)
        list_docs.append(doc)
    serialize_list_documents(list_docs)
    return list_docs


def serialize_list_documents(docs):
    with open('list_docs_file.pkl', 'wb') as f:  # open a text file
        pickle.dump(docs, f) # serialize the list
        f.close()


def deserialize_file(file):
    with open(f'{file}', 'rb') as f:
        list_docs_loaded = pickle.load(f) # deserialize using load()
    return list_docs_loaded



# BUILD RAG SYSTEM


# lets you index a collection of document
def index_document(documents: list[str]):

    vectorizer = TfidfVectorizer()
    
    X = vectorizer.fit_transform(documents)

    res_vectors = X.toarray()
    
    return res_vectors, vectorizer


# returns the top_n most relevant documents
def query_database(list_dict_documents: list[dict], query, top_n):
    documents = [doc['content'] for doc in list_dict_documents]

    documents_vector, vectorizer = index_document(documents)
    
    # vectorize the query using the same vectorizer as the documents, to have the same vocabulary
    query_vector = vectorizer.transform(query).toarray()

    # compute cosine similarity score between query vector and each document vector
    scores = cosine_similarity(query_vector, documents_vector)[0]

    #print(scores)

    # get the top_n sccores
    idx = np.argsort(scores)
    res = scores[idx][-top_n:]

    top_n_idx = []
    for score in res:
        #print(np.where(scores == score))
        top_n_idx.append(int(np.where(scores == score)[0][0]))

    top_n_idx = np.sort(top_n_idx)[::-1]
    relevant_docs = [list_dict_documents[i] for i in top_n_idx]

    return relevant_docs
    


def llm(query, relevant_documents):
    system_query = f""" 
        Answer to this query : {query}
        Make sure to use only these documents to generate your answer to the query : {relevant_documents}
        And return in a JSON format the answer and, for each document in {relevant_documents}, the  top 3 chunks of the {relevant_documents} that helped you to answer to the given {query}. Make sure that the JSON is structured like this :
            answer : str
            list_of_chunks : list[dict] with these keys : 'source_url' (str) and 'chunks' (list[str])
        Make sure that the JSON is valid and make sure to remove the "json ``` and ```" mention from the result.
    """

    load_dotenv()

    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MODEL = "mistral-medium-latest" 

    client = Mistral(api_key=MISTRAL_API_KEY)

    # Appel au LLM
    response = client.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": system_query}]
    )

    result_text = response.choices[0].message.content
    result_text = result_text.strip("`").strip("json").replace("\n", " ")

    result_json = json.loads(result_text)

    return result_json


def clean_markdown(text):
    # Add newline before numbered list items (1. 2. 3.)
    text = re.sub(r'(?<!\n)(\d+\.\s)', r'\n\1', text)

    # Add newline before bullet points
    text = re.sub(r'(?<!\n)(-\s)', r'\n\1', text)

    # Add blank line before numbered sections like "1. Title:"
    text = re.sub(r'\n(\d+\.\s)', r'\n\n\1', text)

    # Ensure space after colon if list follows
    text = re.sub(r':\s*-\s', r':\n\n- ', text)

    return text.strip()