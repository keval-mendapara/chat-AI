import streamlit as st 
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain_community.embeddings.huggingface import HuggingFaceInstructEmbeddings
from langchain_community.vectorstores import FAISS
import torch
from langchain_community.llms import OpenAI
from langchain_community.llms import HuggingFaceHub
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from InstructorEmbedding import INSTRUCTOR
from htmlTemplates import css, bot_template, user_template
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain 

def get_pdf_text(pdf_docs):
    text = ""  
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text
            
def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function = len
        ) 
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    #embeddings = OpenAIEmbeddings()
    DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
    embeddings = HuggingFaceInstructEmbeddings(model_name ="hkunlp/instructor-xl",model_kwargs={"device": DEVICE})
    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vector_store

def get_conversation_chain(vector_store):
    llm = ChatOpenAI()
    #llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    convesation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retreiver(),
        memory = memory
    )
    return convesation_chain

def handle_user_input(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']
    
    for i, message in enumerate[st.session_state.chat_history]:
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}",message.content),unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}",message.content),unsafe_allow_html=True) 
    
def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with multiple PDFs",page_icon=":books:")
    
    st.write(css, unsafe_allow_html=True)
    
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    st.header("Chat with multiple PDFs :books:")
    user_question = st.text_input("Ask a question your documents:")
    if user_question:
        handle_user_input(user_question)
    st.write(user_template.replace("{{MSG}}","Hello robot"), unsafe_allow_html=True)
    st.write(bot_template.replace("{{MSG}}","Hello Human"), unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Your Documents")
        pdf_docs = st.file_uploader("Upload your PDFs here and click on 'Process'",accept_multiple_files=True)
        
        if st.button("Process"):
            with st.spinner("Processing"):
                # get pdf text 
                raw_text = get_pdf_text(pdf_docs)
                
                # get the text chunks 
                text_chunks = get_text_chunks(raw_text)
                
                # create vector store 
                vector_store = get_vectorstore(text_chunks)
                
                # create conversation chain
                st.session_state.conversation = get_conversation_chain(vector_store)
                
    st.session_state.conversation        
                 


if __name__ == '__main__':
    main()