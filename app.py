import glob
import os
import pandas as pd
import streamlit as st
import openai
from PyPDF2 import PdfReader
from pyzotero import zotero
from collections import defaultdict
from openai.embeddings_utils import get_embedding, cosine_similarity

# Set dataframe display options
st.set_page_config(layout="wide")


def get_zotero(zotero_user_id, zotero_key):
    """

    :type zotero_user_id: str
    :type zotero_key: str
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
    # st.write(pdf_items)
    # st.write(f"### Found {len(pdf_items)} PDFs")
    pdf_data = []
    for pdf_item in pdf_items:
        pdf_metadata = pdf_item['data']
        parent_id = pdf_item['data'].get('parentItem')
        try:
            parent_item = next(item for item in items if item['data']['key'] == parent_id)
            parent_metadata = parent_item['data']
            pdf_data.append({
                'title': parent_metadata.get('title', ''),
                # 'date': parent_metadata.get('date', ''),
                'type': parent_metadata.get('itemType', ''),
                'publication': parent_metadata.get('publicationTitle', ''),
                'doi': parent_metadata.get('DOI', ''),
                'id': pdf_item['key'],
                'parent_id': parent_id,
            })
        except StopIteration:
            pass

    return pd.DataFrame(pdf_data)


def extract_text_from_pdf(pdf_path, pdf_title):
    """
    extract text from pdf
    :param pdf_title:
    :param pdf_path:
    :return:
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


def get_pdf_text(zotero_path, pdf_id, pdf_title):
    """

    :param pdf_title:
    :param zotero_path:
    :param pdf_id:
    :return:
    """
    pdf_path = os.path.join(zotero_path, 'storage', pdf_id)
    print(pdf_path)
    pdf_files = glob.glob(os.path.join(pdf_path, "*.pdf"))
    if len(pdf_files) > 0:
        return extract_text_from_pdf(pdf_files[0], pdf_title)
    else:
        st.warning(f"PDF not found for {pdf_id}")
        return ''


def calculate_similarity(paper_df, query, n=3):
    """
    calculate the similarity of query and paper text
    :param paper_df:
    :param query:
    :param n:
    :return:
    """
    embedding_model = 'text-embedding-ada-002'
    paper_df['embeddings'] = paper_df.text.apply(lambda x: get_embedding(x, engine=embedding_model))
    query_embedding = get_embedding(query, engine=embedding_model)
    # calculate cosine similarity
    paper_df['similarity'] = paper_df.embeddings.apply(lambda x: cosine_similarity(x, query_embedding))
    results = paper_df.sort_values("similarity", ascending=False, ignore_index=True)
    results = results.head(n)
    # st.write(results)
    return results


def paper_chat(paper_df, query):
    """

    :param query:
    :param paper_df:
    :return:
    """
    chat_model = 'gpt-3.5-turbo'
    results = calculate_similarity(paper_df, query, n=3)

    embeddings_1 = str(results.iloc[0]['text'][:500])
    embeddings_2 = str(results.iloc[1]['text'][:500])
    embeddings_3 = str(results.iloc[2]['text'][:500])

    system_role = f"""Act as an academician whose expertise is reading and summarizing scientific papers. You are given a query, a series of text embeddings and the title from a paper in order of their cosine similarity to the query. You must take the given embeddings and return a very detailed summary of the paper in the language of the query. The embeddings are as follows: 1. {embeddings_1}. 2. {embeddings_2}. 3. {embeddings_3}. The title of the paper is: {paper_df.iloc[0].title}"""
    user_content = f"""Given the question: "{str(query)}". Return a detailed answer based on the paper:"""

    messages = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": user_content}, ]

    response = openai.ChatCompletion.create(
        model=chat_model,
        messages=messages,
        temperature=0.7,
        max_tokens=3000
    ).choices[0]["message"]["content"]

    return {"embedding_1": embeddings_1, "embedding_2": embeddings_2, "embedding_3": embeddings_3, 'response': response}


# Get local zotero pdf path
zotero_path = st.sidebar.text_input("Zotero Path", value='/Users/baoyi/Zotero')

# Get Zotero API key and user ID
zotero_user_id = st.sidebar.text_input("Zotero User ID", value='')
zotero_key = st.sidebar.text_input("Zotero API Key", type="password", value='')

# Get OpenAI API key
openai_key = st.sidebar.text_input("OpenAI API Key", type="password",
                                   value='')
openai.api_key = openai_key

if zotero_user_id and zotero_key and openai_key:
    df = get_zotero(zotero_user_id, zotero_key)
    st.dataframe(df, width=1200)

    paper_df = get_pdf_text(zotero_path, df.iloc[4]['id'], df.iloc[4].title)
    input_query = st.text_input("Input query:")
    st.write(paper_chat(paper_df, input_query))
else:
    st.write("### Please enter your Zotero API key and user ID")
