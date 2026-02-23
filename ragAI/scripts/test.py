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

# retrieve document content
def get_documents_content(docs_names: list[str]):
    content = []
    for name in docs_names:
        with open(name, 'r') as doc:
            file = doc.read()
            file = file.replace("\n", " ")
        content.append(file)
    
    return content

# lets you index a collection of document
def index_document(documents: list[str]):

    vectorizer = TfidfVectorizer()
    
    X = vectorizer.fit_transform(documents)

    res_vectors = X.toarray()
    
    return res_vectors, vectorizer


# returns the top_n most relevant documents
def query_database(documents: list[str], query, top_n):
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
    relevant_docs = [documents[i] for i in top_n_idx]

    return relevant_docs
    
def llm(query, relevant_documents):
    system_query = f""" 
        Answer to this query : {query}
        Using only these documents : {relevant_documents}
        And return in a JSON format the answer and, for each document in {relevant_documents}, the  top 3 chunks of the {relevant_documents} that helped you to answer to the given {query}. Make sure that the JSON is structured like this :
            answer : str
            list_of_chunks : list[dict] with these keys : 'source_url' (str) and 'chunks' (list[str])
    """

    load_dotenv()

    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MODEL = "mistral-tiny" 

    client = Mistral(api_key=MISTRAL_API_KEY)

    # Appel au LLM
    response = client.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": system_query}]
    )

    result_text = response.choices[0].message.content
    result_json = json.loads(result_text)

    print(result_json)

    return result_json

