import openai
import json
import os
import argparse
from pathlib import Path

# Initialize argument parser
parser = argparse.ArgumentParser(description='Process text files using OpenAI API.')
parser.add_argument('--f', type=str, help='Processing path', default='./txt')
parser.add_argument('--o', type=str, help='Output path', default='./out')
parser.add_argument('--m', type=str, help='Mode for file extension and prompt', default='res')
parser.add_argument('--i', type=str, help='Input file type', default='txt')
parser.add_argument('--l', type=str, help='Output language', default='english')

# Parse the arguments
args = parser.parse_args()

# Load the configuration
with open('config.json', 'r') as file:
    config = json.load(file)

# Set OpenAI API key from environment or config
api_key = os.environ.get('OPENAI_API_KEY', config.get('api_key', ''))
openai.api_key = api_key

# Validate and set paths, mode, and language
process_path = Path(args.f)
output_path = Path(args.o)
mode = args.m
input_file_type = args.i
output_language = args.l
# The encoding should be set as per config or a default value
file_encoding = config['default'].get('encoding', 'utf-8')

# Create directories if they don't exist
process_path.mkdir(parents=True, exist_ok=True)
output_path.mkdir(parents=True, exist_ok=True)

# Iterate through the text files and process them
for text_file in process_path.glob(f'*.{input_file_type}'):
    with open(text_file, 'r', encoding=file_encoding) as file:
        text_content = file.read()

    output_file = output_path / text_file.with_suffix(f'.{mode}').name

    if output_file.exists():
        print(f'The file {output_file} already exists, skipping...')
        continue

    messages = [
        {
            'role': 'system',
            'content': config.get('modes', {}).get(mode, {}).get('prompt', '') + " Please don't add outro or intro to your response and reply using this language: " + output_language
        },
        {
            'role': 'user',
            'content': text_content
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            model=config['default']['engine'],
            messages=messages,
            temperature=float(config['default']['temperature']),
            max_tokens=int(config['default']['max_tokens']),
            top_p=float(config['default']['top_p']),
            frequency_penalty=float(config['default']['frequency_penalty']),
            presence_penalty=float(config['default']['presence_penalty'])
        )
        ssml_text = response['choices'][0]['message']['content']
    except Exception as e:
        print(f'Error: {e}')
        continue

    with open(output_file, 'w', encoding=file_encoding) as file:
        file.write(ssml_text)

    print(f'File {output_file} created successfully.')
