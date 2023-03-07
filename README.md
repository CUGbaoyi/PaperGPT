PaperGPT
========

PaperGPT is a Streamlit application that uses OpenAI GPT-3 to perform scientific paper question-answering. Users can search for PDF files in their Zotero accounts, select the desired files, and ask questions to get answers.

[中文文档](README_CN.md)

How to Use
----------

1.  Install Dependencies
    
    PaperGPT uses Streamlit and PyZotero. Dependencies can be installed using the following command:
    
    ```sh
    pip install streamlit pyzotero openai PyPDF2
    ```
    
2.  Get API Keys
    
    Before using PaperGPT, you need to obtain the following API keys:
    
    *   Zotero API Key: Used to retrieve PDF metadata and content from your Zotero account.
    *   OpenAI API Key: Used to perform question-answering with OpenAI GPT-3.
3.  Run PaperGPT
    
    Enter the following command in your terminal to start PaperGPT:
    
    ```sh
    streamlit run app.py
    ```
    
4.  Configure PaperGPT
    
    After running PaperGPT, the application will open in your browser. In the sidebar, fill in the following information:
    
    *   Zotero Path: The path to your local Zotero library, e.g. `/Users/XXX/Zotero`.
    *   Zotero User ID: Your Zotero user ID.
    *   Zotero API Key: Your Zotero API key.
    *   OpenAI API Key: Your OpenAI API key.
5.  Search for PDF files and ask questions
    
    *   On the main page, select the collection of PDF files you want to search.
    *   Enter your question in the input box.
    *   Click the "Search" button.
    *   Select the PDF files you want to search in.
    *   Select multiple files using checkboxes.
    *   Click the "Search" button to get a detailed summary with the answer to your question.

Example Usage
-------------

The following example demonstrates how to search for PDF files and ask questions using PaperGPT:

1.  Create a collection in Zotero containing several PDF files.
    
2.  Run PaperGPT and fill in the necessary API keys.
    
3.  On the main page of PaperGPT, select the collection containing the PDF files.
    
4.  Enter your question in the input box and click the "Search" button.
    
5.  Select the PDF files you want to search for in the checkboxes below.
    
6.  Click the "Search" button.
    
7.  Get a detailed summary with the answer to your question.

![Demo](doc/demo.png)

Notes
-----

*   PaperGPT can only search for PDF files that you have added to Zotero.
*   Using OpenAI GPT-3 for question-answering may take some time.
*   If your Zotero PDF files are stored on Dropbox or another cloud service, they cannot be searched.

TODO
-----
*   Use database to cache query results to avoid multiple queries
*   Optimize user interaction interface, consider front and back-end separation architecture