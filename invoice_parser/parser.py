from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
import pymupdf as fitz
import io
from PIL import Image
import pytesseract
import pdfplumber	
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import pipeline
import torch
import requests
import re

def horizontally_aligned(bbox1, bbox2, threshold):
    # Check if the vertical centers are within the threshold
    center1 = (bbox1[1] + bbox1[3]) / 2
    center2 = (bbox2[1] + bbox2[3]) / 2
    return abs(center1 - center2)

def vertically_aligned(bbox1, bbox2, threshold):
    # Check if the horizontal centers are within the threshold
    center1 = (bbox1[0] + bbox1[2]) / 2
    center2 = (bbox2[0] + bbox2[2]) / 2
    return abs(center1 - center2)

def plot_graph_with_text(G):
    pos = {}  # Position map for nodes
    node_labels = {}  # Labels for each node
    edge_colors = []  # Colors for edges based on type

    # Calculate positions and prepare labels
    for node, data in G.nodes(data=True):
        bbox = node[1]  # Extract bbox stored in node
        # Calculate the position based on bbox center
        pos[node] = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
        # Prepare text, limit length if necessary
        text = data.get('text', '')[0:50]  # Show only first 50 characters if needed
        node_labels[node] = text

    # Define colors based on edge type
    for u, v, data in G.edges(data=True):
        if data['type'] == 'vertical':
            edge_colors.append('red')
        else:
            edge_colors.append('blue')

    # Draw the graph
    plt.figure(figsize=(12, 8))  # Set a larger figure size
    nx.draw(G, pos, edge_color=edge_colors, with_labels=False, node_color='lightgreen', node_size=3000, alpha=0.6)
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)  # Adjust font size as needed

    plt.title('PDF Layout Graph with Text')
    plt.show()

class Parser:
	def __init__(self, file):
		self.filestream = io.BytesIO(file.read())
		self.vendor = None
		self.issue_date = None
		self.items = [] # list of items with their details
		self.total = None
		self.due_date = None # due date of the invoice
		self.visited = set()  # Initialize a set to keep track of visited nodes
		self.painted_string = None
		self.prompt = None
		self.page_height = None
		self.page_width = None
		self.response = None
		# self.type = 'img' if self.path.endswith('.jpg') or self.path.endswith('.png') else 'pdf'

	def is_image_based_pdf(self):
		with open(self.path, 'rb') as f:
			parser = PDFParser(f)
			doc = PDFDocument(parser)
			if not doc.is_extractable:
				return True  # Text extraction is not allowed; likely image-based
			else:
				return False  # Text extraction is allowed; likely text-based


	def build_graph(self, df):
		# Initialize the graph
		G = nx.Graph()
		count = 0
		last_cluster = None  # Initialize last_cluster to None before the loop
		df.sort_values(by='vertical_cluster', inplace=True)
		df.reset_index(drop=True, inplace=True)
		df['index'] = df.index


		horizontal_clusters = df.groupby('horizontal_cluster').agg(
			{ 
				'index': lambda x: list(x),
			}
		)
		
		# Add nodes for each element in the DataFrame
		for index, row in df.iterrows():
			current_cluster = row['vertical_cluster']
			horizontal_cluster = row['horizontal_cluster']
			count += 1
			node_tuple = (row['x_left'], row['y_bottom'], row['vertical_cluster'], row['horizontal_cluster'], row['text'])
			G.add_node(index, node=node_tuple)
			if last_cluster == current_cluster and index > 0:
				G.add_edge(index, index - 1, weight=1)
			last_cluster = current_cluster

		for cluster in horizontal_clusters['index']:
			for i in range(len(cluster) - 1):
				G.add_edge(cluster[i], cluster[i + 1], weight=0)

		print("Total elements processed:", count)
		return G
	
	def dfs_horizontal(self,G, node, visited):
		""" Perform DFS on horizontal edges (edges with weight 0). """
		visited.add(node)
		# print(f"{G.nodes[node]['node']} --- ", end=" ")  # Print the node information
		
		# Traverse all neighbors of the current node
		for neighbor in G.neighbors(node):
			# Check if the edge is a horizontal edge (weight == 0)
			if G.get_edge_data(node, neighbor)['weight'] == 0 and neighbor not in visited:
				self.dfs_horizontal(G, neighbor, visited)  # Recursively visit the neighbor


	def extract_text_pdf(self):
		doc = fitz.open(stream=self.filestream, filetype="pdf")
		self.page_width = doc[0].rect.width
		self.page_height = doc[0].rect.height
		list_of_elements = []
		for page_number, page in enumerate(doc):
			text_instances = page.get_text("dict")['blocks']
			for block in text_instances:
				block_data = {
					'page_number': page_number + 1,
					'bbox': block['bbox'],  # Bounding box of the block
					'block_type': block['type'],  # Type of the block (e.g., text, image)
				}

				if block['type'] == 0:  # type 0 is text
					block_data['lines'] = []
					for line in block['lines']:
						line_data = {
							'bbox': line['bbox'],
							'spans': []
						}
						for span in line['spans']:
							span_data = {
								'text': span['text']
							}
							line_data['spans'].append(span_data)
						list_of_elements.append((line['bbox'], span_data['text']))
				
		texts = pd.DataFrame(list_of_elements, columns=['bbox', 'text'])
		texts.to_csv('texts.csv', index=False)
		return texts

	def normalize_bbox(self, df, page_width):
		df['x0'], df['x1'], df['y0'], df['y1'] = df['y1'], df['y0'], df['x1'], df['x0']
		df['x0'], df['x1'] = page_width - df['x0'], page_width - df['x1']
		return df

	def paint_image_string(self, df):
		painted_String = ''
		current_line_elems = []
		df.sort_values(by=['y1', 'x0'], inplace=True)
		df['separate'] = False
		for index, row in df.iterrows():
			if not current_line_elems:
				current_line_elems.append(row)
			else:
				if row['y0'] - current_line_elems[-1]['y0'] < 2.5 and row['x0'] != current_line_elems[-1]['x0']:
					row['separate'] = True
					current_line_elems.append(row)
				else:
					current_line_elems = sorted(current_line_elems, key=lambda x: x['x0'])
					for elem in current_line_elems:
						if elem['separate']:
							painted_String += '\t'
						painted_String += elem['text'] + '- '
					painted_String += '\n'
					current_line_elems = [row]

		return painted_String

	def extract_response(self):
		# extract the response from the mdoel
		pass

	def parse(self):
		text_df = self.extract_text_pdf()
		# extract the details from the invoice
		page_width = self.page_width
		page_height = self.page_height

		text_df['x0'] = text_df['bbox'].apply(lambda x: x[0])
		text_df['y0'] = text_df['bbox'].apply(lambda x: x[1])
		text_df['x1'] = text_df['bbox'].apply(lambda x: x[2])
		text_df['y1'] = text_df['bbox'].apply(lambda x: x[3])

		if page_width > page_height:
			text_df = self.normalize_bbox(text_df, page_width)

		painted_string = self.paint_image_string(text_df)
		self.painted_string = painted_string
		messages = [ {
			"role": "system", "content": self.prompt_template(painted_string) \
		}]
		self.response = self.inference_llama(messages)

	def export_csv(self):
		# export the details in csv format
		pass


	def inference_llama(self, messages):
		# create a post request to the inference endpoint
		url = "https://de06-2a02-2f0c-5610-1500-8416-d27f-1f9e-78e3.ngrok-free.app"
		response = requests.post(url, json={"message": messages})
		print(response)
		return response.json()['response'][1]["content"]
		
	
	def prompt_template(self, painted_string):
		# prompt the user to select the template
		question_prompt = "Extrage din textul unei facturi următoarele informații: \
                    - Numele beneficiarului/clientului/cumpărătorului \
                    - Numele vânzătorului/furnizorului/vendorului \
                    - Data emiterii facturii \
                    - Data scadenței facturii \
                    - Lista de produse cu pretul aferent separate de o virgula \
                    - Totalul de plată \
                   Afișează informațiile extrase în formatul următor: \
                    - beneficiar: [nume beneficiar] \
                    - vanzător: [nume vânzător] \
                    - data emiterii: [data] \
                    - lista de produse: [produse] \
                    - total de plata: [sumă] \
                    - data scadentei: [data] \
                   Asigură-te că răspunsul conține doar informațiile solicitate in formatul dat, fără text suplimentar."

		
		return question_prompt + painted_string
	
	def extrage_date_factura(self):
			# Dicționar pentru a stoca datele extrase
		text = self.response
		print(text)
		date_factura = {}
		
		# Expresii regulate pentru a extrage fiecare câmp
		patterns = {
			"beneficiar": "Client",
			"vânzător": "Furnizor",
			" vanz": "Furnizor",
			"vanzator": "Furnizor",
			" emiter": "Data Eliberare",
			" scaden": "Data Scadenta",
			"produse": "Lista de produse",
			"total": "Total"
		}
		
		# Aplicăm fiecare expresie regulată pe text și stocăm rezultatele
		lines = text.split("\n")

		for line in lines:
			for key in patterns.keys():
				if key in line.lower():
					key = patterns[key]
					value = line.split(":")[1].strip()
					if key == "Lista de produse":
						products = value.split(",")
						products_w_prices = []
						for product in products:
							price = re.search(r'\d+(?P<decimal>\.\d+)?', product)
							product_name = product.replace(price.group(), '')
							products_w_prices.append({"product": product_name.strip(), "price": price.group()})
						value = products_w_prices
					date_factura[key] = value
		# create a list of dictionaries for each product
		
		product_keys = {key: value for key, value in date_factura.items() if key != "Lista de produse"}

		# Create a list of dictionaries, each merging product_keys with individual product details
		lista_produse = [
			{
				**product_keys,  # Spread the fixed data into each product entry
				"Nume produs": product["product"],
				"Pret unitar": product["price"]
			} for product in date_factura["Lista de produse"]
		]
		print(lista_produse)
		return lista_produse

if __name__ == '__main__':
	path = '/home/oda/freelance/santier/facturi/FacturaPDF-NrReg.pdf'
	filestream = open(path, 'rb')
	parser = Parser(filestream)
	parser.parse()
	
	print(parser.response)
