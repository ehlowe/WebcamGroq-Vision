import os

import requests
from flask import Flask, request, jsonify

app = Flask(__name__, static_folder='src', static_url_path='/')

# Replace 'YOUR_DEFAULT_API_KEY' with the name of the environment variable
DEFAULT_API_KEY = os.environ.get('YOUR_DEFAULT_API_KEY', 'YOUR_DEFAULT_API_KEY')

@app.route('/')
def index():
    """Return the index.html page."""
    return app.send_static_file('index.html')


@app.route('/process_image', methods=['POST'])
def process_image():
    data = request.json
    base64_image = data.get('image', '')

    if base64_image:
        api_key = DEFAULT_API_KEY
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        if DEFAULT_API_KEY.startswith('gsk'):
            model_name = "llava-v1.5-7b-4096-preview"
            provider_url="https://api.groq.com/openai/v1/chat/completions"
            user_prompt="briefly describe the image"
        else:
            model_name = "gpt-4o"
            provider_url="https://api.openai.com/v1/chat/completions"
            user_prompt="What’s in this image? Be descriptive. For each significant item recognized, wrap this word in <b> tags. Example: The image shows a <b>man</b> in front of a neutral-colored <b>wall</b>. He has short hair, wears <b>glasses</b>, and is donning a pair of over-ear <b>headphones</b>. ... Also output an itemized list of objects recognized, wrapped in <br> and <b> tags with label <br><b>Objects:."

        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0,
        }

        response = requests.post(
            provider_url,
            headers=headers,
            json=payload
        )

        if model_name=="llava-v1.5-7b-4096-preview":
            if response.status_code != 200:
                return jsonify({'error': 'Failed to process the image.'}), 500
            response_content = response.json()
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": "What’s in this image? Be descriptive. For each significant item recognized, wrap this word in <b> tags. Example: The image shows a <b>man</b> in front of a neutral-colored <b>wall</b>. He has short hair, wears <b>glasses</b>, and is donning a pair of over-ear <b>headphones</b>. ... Also output an itemized list of objects recognized, wrapped in <br> and <b> tags with label <br><b>Objects:."
                    },
                    {
                        "role": "user",
                        "content": response_content['choices'][0]['message']['content']
                    }
                ],
                "max_tokens": 300,
                "temperature": 0,
            }

            response = requests.post(
                provider_url,
                headers=headers,
                json=payload
            )

        if response.status_code != 200:
            return jsonify({'error': 'Failed to process the image.'}), 500
        return response.content

    else:
        return jsonify({'error': 'No image data received.'}), 400


if __name__ == '__main__':
    app.run(debug=True)
