import os
# import cv2
from typing import List
import json
import streamlit as st
import io
from parser import Parser

	
	
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
