<<<<<<< HEAD
import streamlit as st
import pandas as pd
from parser import Parser
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder

st.set_page_config(layout="wide")

# Define the columns for your table
columns = ["Nume produs", "Cantitate", "Pret unitar", "TVA", "Data Scadenta", 
           "Data Eliberare", "Total", "Furnizor", "Client"]


# Initialize the table in the session state if it doesn't exist
if 'table' not in st.session_state:
    st.session_state.table = pd.DataFrame(columns=columns)
    # add a test row

gb = GridOptionsBuilder.from_dataframe(st.session_state.table)
gb.configure_default_column(
    resizable=True,
    filterable=True,
    sortable=True,
    editable=True,
)
grid_options = gb.build()   

# Display the AgGrid component with configured options
response = AgGrid(
    st.session_state.table,
    gridOptions=grid_options,
    height=300,
    width='100%',
    theme='alpine',
    fit_columns_on_grid_load=True,
    update_on='data_change',
)


# File uploader widget
uploaded_file = st.file_uploader('Upload Invoice', type=['pdf', 'png', 'jpg', 'jpeg'], key='uploader')

if st.button('Parse Invoice', key='add_invoice'):
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.pdf'):
            with st.spinner('Parsing invoice...'):
                # Assume Parser is a defined class that can handle uploaded files
                invoice_parser = Parser(uploaded_file)
                invoice_parser.parse()
                st.write('Invoice parsed successfully!')
                st.write(invoice_parser.response)
                # Simulating data extraction function and adding data to the session state table
                data = invoice_parser.extrage_date_factura()  # Assuming this function returns a DataFrame
                st.write(data)
                # create a df with the columns defined above and the data extracted
                data = pd.DataFrame(data, columns=columns)
                print(data)
                st.session_state.add_button = True
                st.session_state.table = pd.concat([st.session_state.table, data], ignore_index=True)
                st.success('Invoice parsed successfully!')
        else:
            st.error('Please upload a PDF invoice file to continue.')
    else:
        st.error('No file uploaded. Please upload an invoice file to continue.')

if st.button('Add to table') and 'add_button' in st.session_state:
    # clear the uploader
    st.session_state.add_button = False
    if 'uploaded_file' in st.session_state:
        del st.session_state.uploaded_file
    st.rerun()

if st.button('Reset Table'):
    st.session_state.table = pd.DataFrame(columns=["Nume produs", "Cantitate", "Pret unitar", "TVA", "Data Scadenta", 
                                                   "Data Eliberare", "Total Factura", "Furnizor", "Client"])
    st.rerun()
=======
from transformers import LayoutLMv3FeatureExtractor, LayoutLMv3TokenizerFast, LayoutLMv3Processor, LayoutLMv3ForSequenceClassification
from tqdm import tqdm
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from sklearn.model_selection import train_test_split
# import imgkit
# import easyocr
import torchvision.transforms as T
from pathlib import Path
import matplotlib.pyplot as plt
import os
# import cv2
from typing import List
import json
from torchmetrics import Accuracy
from huggingface_hub import notebook_login
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import streamlit as st
import io
from invoice_parser.parser import Parser

	
	
# Add a file uploader widget
uploaded_file = st.file_uploader('Upload Invoice', type=['pdf', 'png', 'jpg', 'jpeg'])

if st.button('Parse Invoice'):
    if uploaded_file is not None and uploaded_file.name.endswith('.pdf'):
        st.write('Parsing invoice...')
        invoice_parser = Parser(uploaded_file)
        invoice_parser.parse()
        st.write(invoice_parser.response)
        st.write('Invoice parsed successfully!')
        # write the output to the screen
        # st.write(invoice_parser.response)
        data = invoice_parser.extrage_date_factura()
        st.write(data)

    else:
        st.error('Please upload an invoice file to continue.')
>>>>>>> 8346fbc1300d0d45409599dabbea2d2b4dc231d9
