from functions import *

refs = get_references_nice()

'''
for ref in refs:
    url = get_pdf_url(ref)
    download_pdf(ref, url)


docs = get_list_documents_content(refs)

print(len(docs))
'''

list_docs = deserialize_file('list_docs_file.pkl')
print(list_docs[0])