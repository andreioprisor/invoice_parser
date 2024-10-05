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
if 'anaf_table' not in st.session_state:
    st.session_state.anaf_table = pd.DataFrame(columns=columns)

st.title('Produse Proforma')
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
if 'show_buttons' not in st.session_state:
    st.session_state['show_buttons'] = False

if st.button('Adauga proforma', key='proforma'):
    st.session_state['show_buttons'] = not st.session_state['show_buttons']
    # change the text of the button

if st.session_state['show_buttons']:
    uploaded_file = st.file_uploader('Upload Invoice', type=['pdf', 'png', 'jpg', 'jpeg'], key='uploader')
    container = st.container()
    cols = container.columns([1, 1])  # This creates three columns of equal width

    with cols[0]:
        if st.button('Parse Invoice', key='add_invoice', use_container_width=True):
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

    with cols[1]:
        if st.button('Add to table', use_container_width=True) and 'add_button' in st.session_state:
            # clear the uploader
            st.session_state.add_button = False
            if 'uploaded_file' in st.session_state:
                del st.session_state.uploaded_file
            st.rerun()


if st.button('Reseteaza tabela proforme', type='primary'):
    # your code here
    st.warning('Are you sure you want to reset the table?')

st.title('Produse eFactura')
AgGrid(
    st.session_state.anaf_table,
    height=300,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,  # Needed to allow dataframe row updates
)

if 'show_buttons_anaf' not in st.session_state:
    st.session_state['show_buttons_anaf'] = False

if st.button('Adauga factura', key='anaf'):
    st.session_state['show_buttons_anaf'] = not st.session_state['show_buttons_anaf']
    # change the text of the button

if st.session_state['show_buttons_anaf']:
    uploaded_file = st.file_uploader('Upload Invoice', type=['pdf', 'png', 'jpg', 'jpeg'], key='uploader_anaf')
    container = st.container()
    cols = container.columns([1, 1])  # This creates three columns of equal width

    with cols[0]:
        if st.button('Parse Invoice', key='add_invoice_anaf', use_container_width=True):
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
                        st.session_state.add_button_anaf = True
                        st.session_state.table = pd.concat([st.session_state.table, data], ignore_index=True)
                        st.success('Invoice parsed successfully!')
                else:
                    st.error('Please upload a PDF invoice file to continue.')
            else:
                st.error('No file uploaded. Please upload an invoice file to continue.')

    with cols[1]:
        if st.button('Adauga la tabela', use_container_width=True, key="add_btn_anaf") and 'add_button_anaf' in st.session_state:
            # clear the uploader
            st.session_state.add_button_anaf = False
            if 'uploaded_file' in st.session_state:
                del st.session_state.uploaded_file
            st.rerun()

if st.button('Reseteaza tabela eFactura', type='primary'):
    # your code here
    st.warning('Are you sure you want to reset the table?')