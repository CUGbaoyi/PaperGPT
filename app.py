import glob
import os
import pandas as pd
import streamlit as st
import openai
from PyPDF2 import PdfReader
from pyzotero import zotero
from collections import defaultdict
from openai.embeddings_utils import get_embedding, cosine_similarity

N_EMBED = 3


# Set dataframe display options
st.set_page_config(layout="wide")


# @st.cache_data
def get_zotero(zotero_user_id, zotero_key):
    """
    Get PDF metadata from Zotero library
    """
    # Authenticate with Zotero API
    zot = zotero.Zotero(zotero_user_id, 'user', zotero_key)

    # Get collections from Zotero library
    collections_info = zot.collections()
    # Get collections from Zotero library
    collections = [
        {'id': c['key'], 'name': c['data']['name'], 'count': c['meta']['numItems']}
        for c in zot.collections()
    ]

    # Display collection names in a selectbox
    selected_collection = st.sidebar.selectbox(
        'Select collection',
        [f"{c['name']} ({c['count']} items)" for c in collections]
    )

    # Get items from selected collection
    collection_id = next(c['id'] for c in collections if c['name'] == selected_collection.split(' (')[0])
    items = zot.collection_items(collection_id)

    # Get items with PDFs
    pdf_items = [item for item in items if item['data'].get('contentType', '') == 'application/pdf']
    pdf_data = []
    for pdf_item in pdf_items:
        parent_id = pdf_item['data'].get('parentItem')
        try:
            parent_item = next(item for item in items if item['data']['key'] == parent_id)
            parent_metadata = parent_item['data']
            pdf_data.append({
                'title': parent_metadata.get('title', ''),
                'type': parent_metadata.get('itemType', ''),
                'publication': parent_metadata.get('publicationTitle', ''),
                'doi': parent_metadata.get('DOI', ''),
                'id': pdf_item['key'],
                'parent_id': parent_id,
            })
        except StopIteration:
            pass

    return pd.DataFrame(pdf_data)


# @st.cache_data
def extract_text_from_pdf(pdf_path, pdf_title):
    """
    Extract text from PDF file
    """
    paper_dict = defaultdict(list)
    with open(pdf_path, "rb") as f:
        pdf_reader = PdfReader(f)
        for page_num, page in enumerate(pdf_reader.pages):
            page_info = page.extract_text()
            for paragraph in page_info.split('\n\n'):
                paper_dict['page'].append(page_num + 1)
                paper_dict['text'].append(paragraph)
                paper_dict['title'].append(pdf_title)
    return pd.DataFrame(paper_dict)


# @st.cache_data
def get_pdf_text(zotero_path, pdf_id, pdf_title):
    """
    Get text content from a PDF file
    """
    pdf_path = os.path.join(zotero_path, 'storage', pdf_id)
    pdf_files = glob.glob(os.path.join(pdf_path, "*.pdf"))
    if len(pdf_files) > 0:
        return extract_text_from_pdf(pdf_files[0], pdf_title)
    else:
        st.warning(f"PDF not found for {pdf_id}")
        return pd.DataFrame()


# @st.cache_data
def calculate_similarity(paper_df, query, n=3):
    """
    Calculate the cosine similarity between the embeddings of the papers and the query
    """
    embedding_model = 'text-embedding-ada-002'
    paper_df['embeddings'] = paper_df.text.apply(lambda x: get_embedding(x, engine=embedding_model))
    query_embedding = get_embedding(query, engine=embedding_model)
    # Calculate cosine similarity
    paper_df['similarity'] = paper_df.embeddings.apply(lambda x: cosine_similarity(x, query_embedding))
    results = paper_df.sort_values("similarity", ascending=False, ignore_index=True)
    results = results.head(n)
    return results

def paper_chat(paper_df, query, titles, n_paper):
    """
    Get a response from OpenAI GPT-3
    """
    chat_model = 'gpt-3.5-turbo'
    results = calculate_similarity(paper_df, query, n=N_EMBED)
    
    embeddings = " ".join([f"{x}: {results.iloc[x]['text'][:500]}" for x in range(N_EMBED)])
    paper_titles = ",".join(titles)

    system_role = f"""Act as an academician whose expertise is reading and summarizing scientific papers. You are given a query, a series of text embeddings and the title from {n_paper} papers in order of their cosine similarity to the query. You must take the given embeddings and return a very detailed summary of the papers in the language of the query. The embeddings are as follows: {embeddings}. The title of the papers are as follows: {paper_titles}"""
    user_content = f"""Given the question: "{str(query)}". Return a detailed answer based on the paper:"""

    messages = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": user_content},
    ]

    response = openai.ChatCompletion.create(
        model=chat_model,
        messages=messages,
        temperature=0.7,
        max_tokens=3000
    ).choices[0]["message"]["content"]

    return response

st.write("# PaperGPT")
    
# Get local Zotero PDF path
zotero_path = st.sidebar.text_input("Zotero Path", value='/Users/XXX/Zotero')

# Get Zotero API key and user ID
zotero_user_id = st.sidebar.text_input("Zotero User ID", value='')
zotero_key = st.sidebar.text_input("Zotero API Key", type="password", value='')

# Get OpenAI API key
openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value='')

if zotero_user_id and zotero_key and openai_key:
    # Get PDF metadata from Zotero library
    df = get_zotero(zotero_user_id, zotero_key)
    st.dataframe(df, width=1200)
    
    # Get user query input
    input_query = st.text_input("Input query:")
    
    # add multiselect
    if st.sidebar.checkbox('Enable multiple paper selection'):
        paper_list = st.multiselect('Select paper id:', df.index.unique())

    # Execute paper search and display results on button click
    if st.button("Search"):
        # Get text content from selected PDF
        papers = []
        titles = []
        for paper in paper_list:
            title = df.iloc[paper].title
            papers.append(get_pdf_text(zotero_path, df.iloc[paper]['id'], title))
            
            titles.append(title)

        paper_df = pd.concat(papers, ignore_index=True)
         
        with st.spinner("Searching..."):
            response = paper_chat(paper_df, input_query, titles, len(papers))
            st.text_area("Response:", value=response, height=500, max_chars=None)
else:
    st.write("### Please enter your Zotero API key and user ID")