#!/usr/bin/env python3
from openai import OpenAI
import json
import os
import argparse
from pathlib import Path

def initialize_client(mode, config):
    """Initialize the API client based on the mode (OpenAI or Ollama)."""
    if mode == 'ollama':
        # Use Ollama's local API compatible with OpenAI
        return OpenAI(
            base_url='http://localhost:11434/v1',  # Ollama's local API endpoint
            api_key='ollama'  # Dummy key, as Ollama doesn't require an actual API key
        )
    else:
        # Use OpenAI's actual API
        api_key = os.environ.get('OPENAI_API_KEY', config.get('api_key', ''))
        return OpenAI(api_key=api_key)

def load_config():
    """Load the configuration from config.json."""
    with open('config.json', 'r') as file:
        return json.load(file)

def setup_paths(process_path):
    """Ensure input directory exists."""
    process_path.mkdir(parents=True, exist_ok=True)

def split_text_into_chunks(text, max_tokens):
    """Split text into manageable chunks based on max token size."""
    return [text[i:i + max_tokens] for i in range(0, len(text), max_tokens)]

def process_file(client, text_file, config, mode, output_base_path):
    """Process a single file using the API and write to the output."""
    with open(text_file, 'r', encoding=config['default'].get('encoding', 'utf-8')) as file:
        text_content = file.read()

    max_input_tokens = int(config['default']['max_tokens'])
    text_chunks = split_text_into_chunks(text_content, max_input_tokens)
    
    # Determine modes to process
    modes_to_process = config['modes'].keys() if mode == "all" else [mode]
    
    for current_mode in modes_to_process:
        # Set prompt and output directory for each mode
        prompt_content = config['modes'].get(current_mode, {}).get('prompt', '')
        output_dir = output_base_path / current_mode
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set file extension based on mode
        file_extension = config['modes'].get(current_mode, {}).get('file_extension', 'txt')
        mode_output_file = output_dir / text_file.with_suffix(f'.{file_extension}').name

        # Skip if output file already exists
        if mode_output_file.exists():
            print(f'The file {mode_output_file} already exists, skipping...')
            continue

        llm_response = ''
        # Process chunks for each mode
        for idx, chunk in enumerate(text_chunks):
            print(f'Processing chunk {idx + 1} of {len(text_chunks)} for mode "{current_mode}"')
            messages = [
                {
                    'role': 'system',
                    'content': f"{prompt_content}. Please don't add outro or intro to your response"
                },
                {
                    'role': 'user',
                    'content': chunk
                }
            ]

            try:
                response = client.chat.completions.create(
                    model=config['default']['model'],
                    messages=messages,
                    temperature=float(config['default']['temperature']),
                    max_tokens=max_input_tokens,
                    top_p=float(config['default']['top_p']),
                    frequency_penalty=float(config['default']['frequency_penalty']),
                    presence_penalty=float(config['default']['presence_penalty'])
                )
                llm_response += response.choices[0].message.content + '\n'
            except Exception as e:
                print(f'Error processing chunk {idx + 1} for mode "{current_mode}": {e}')
                continue

        # Write output for each mode
        with open(mode_output_file, 'w', encoding=config['default'].get('encoding', 'utf-8')) as file:
            file.write(llm_response)
        print(f'File {mode_output_file} created successfully.')
        
def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(description='Process files using OpenAI API or compatible local API.')
    parser.add_argument('--f', type=str, help='Processing path', default='./txt')
    parser.add_argument('--m', type=str, help='Processing Mode (ent,sum,ssm,lda,que,map)', default='all')
    parser.add_argument('--output', type=str, help='Base output path', default='./output')

    # Parse the arguments
    args = parser.parse_args()
    print(args)

    # Load configuration and initialize client
    config = load_config()
    client = initialize_client("ollama", config)

    # Validate and set paths
    process_path = Path(args.f)
    output_base_path = Path(args.output)
    setup_paths(process_path)

    print(f'Processing files in {process_path} and outputting to {output_base_path}')

    # Iterate through the text files and process them
    for text_file in process_path.glob(f'*.txt'):
        print(f'Processing file: {text_file}')
        process_file(client, text_file, config, args.m, output_base_path)

if __name__ == "__main__":
    main()