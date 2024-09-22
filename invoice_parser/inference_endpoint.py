from flask import Flask, request, jsonify
from transformers import pipeline
import torch

app = Flask(__name__)

# Load the model when the server starts
model_name = "unsloth/llama-3-8b-Instruct-bnb-4bit"
pipe = pipeline(
    "text-generation",
    model=model_name,
    model_kwargs={"torch_dtype": torch.bfloat16},
)

def inference_llama(messages):
    outputs = pipe(
        messages,
        max_new_tokens=256,
        do_sample=False,
    )
    # Extract the last generated content
    assistant_response = outputs[0]["generated_text"]  # Corrected from previous misunderstanding
    return assistant_response

@app.route('/', methods=['POST'])
def generate_text():
    print(request.get_json())
    data = request.get_json()
    message = data.get('message', '')
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    response = inference_llama(message)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
