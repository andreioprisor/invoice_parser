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