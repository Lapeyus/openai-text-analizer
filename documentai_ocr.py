#!/usr/bin/env python3
import os
import requests
import json
import base64
import PyPDF2
import io
import re
import argparse
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.cloud import texttospeech
from pydub import AudioSegment

# Constants
DOCUMENT_AI_API_URL = "https://us-documentai.googleapis.com/v1/projects/30256189746/locations/us/processors/b4a7fb495ba75820:process"
SERVICE_ACCOUNT_FILE = "./key.json"  # Path to your service account JSON key file
PDF_FOLDER = "."  # Replace with your local PDF folder path
TEMP_PDF_FOLDER = "./pdf"  # Folder to save temporary one-page PDFs
RESPONSES_FOLDER = "./responses"  # Folder to save API responses
TEXTS_FOLDER = "./texts"  # Folder to save extracted text files
AUDIO_FOLDER = "./audio"  # Folder to save audio files
COMBINED_TEXT_FILE = "./combined.txt"  # Path to the combined text file
COMBINED_AUDIO_FILE = "./audio/combined_audio.mp3"  # Path to the combined audio file
COMBINED_PDF_FILE = "./combined.pdf"  # Path to the combined PDF file

# Initialize credentials using service account
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

def get_access_token():
    """Get OAuth 2.0 access token."""
    credentials.refresh(Request())
    return credentials.token

def split_pdf_into_one_pagers(pdf_path):
    """Split a multi-page PDF into one-page PDFs and return the paths."""
    pdf_reader = PyPDF2.PdfReader(pdf_path)
    total_pages = len(pdf_reader.pages)
    one_pager_paths = []

    for page_number in range(total_pages):
        pdf_writer = PyPDF2.PdfWriter()
        pdf_writer.add_page(pdf_reader.pages[page_number])

        output_pdf_path = os.path.join(TEMP_PDF_FOLDER, f"{os.path.basename(pdf_path).replace('.pdf', '')}_page_{page_number + 1}.pdf")
        with open(output_pdf_path, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)
        
        one_pager_paths.append(output_pdf_path)
    
    return one_pager_paths

def send_pdf_to_api(pdf_path):
    """Send a single PDF to the Document AI API."""
    with open(pdf_path, 'rb') as f:
        file_content = f.read()

    # Base64 encode the PDF content as required by Document AI API
    encoded_content = base64.b64encode(file_content).decode('utf-8')

    headers = {
        'Authorization': f'Bearer {get_access_token()}',
        'Content-Type': 'application/json',
    }

    # Update the request body to use 'inlineDocument'
    body = {
        'inlineDocument': {
            'content': encoded_content,
            'mimeType': 'application/pdf'
        }
    }

    response = requests.post(DOCUMENT_AI_API_URL, headers=headers, json=body)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} for file {pdf_path}")
        print(f"Response: {response.text}")
        return None
    
def text_to_speech(text, language_code, output_audio_path):
    """Convert text to speech using Google Text-to-Speech API and save to an audio file."""
    client = texttospeech.TextToSpeechClient(credentials=credentials)
    
    # Define the byte limit for the text
    byte_limit = 5000
    
    # Split the text into chunks that fit within the byte limit
    def chunk_text(text, byte_limit):
        chunks = []
        current_chunk = ""
        for sentence in text.split('.'):
            sentence = sentence.strip() + ". "
            if len(current_chunk.encode('utf-8')) + len(sentence.encode('utf-8')) > byte_limit:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence
        if current_chunk:
            chunks.append(current_chunk.strip())  # Add the last chunk
        return chunks
    
    text_chunks = chunk_text(text, byte_limit)
    
    # Process each chunk separately and combine the audio
    combined_audio = AudioSegment.empty()
    for i, chunk in enumerate(text_chunks):
        input_text = texttospeech.SynthesisInput(text=chunk)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)

        # Load the audio content into an AudioSegment
        audio_segment = AudioSegment.from_file(io.BytesIO(response.audio_content), format='mp3')

        combined_audio += audio_segment

    # Export the combined audio to output_audio_path
    combined_audio.export(output_audio_path, format='mp3')
    print(f"Audio content written to {output_audio_path}")

def extract_language_from_page(page):
    """Extract the detected language from a page."""
    language_code = "en-US"  # Default language code

    detected_languages = page.get('detectedLanguages', [])
    if detected_languages:
        language_code = detected_languages[0].get('languageCode', 'en-US')
    return language_code

def extract_text_from_layout(layout, document_text):
    """Extract text from layout using textAnchor positions."""
    extracted_text = ""
    
    if 'textAnchor' in layout:
        for segment in layout['textAnchor']['textSegments']:
            start_index = int(segment.get('startIndex', 0))
            end_index = int(segment.get('endIndex', len(document_text)))
            extracted_text += document_text[start_index:end_index]
    else:
        print("No textAnchor found in layout.")
    
    return extracted_text

def clean_paragraph_text(text):
    """Remove line breaks inside paragraphs, recombine hyphenated words, and clean up the text."""
    # Remove line breaks inside paragraphs
    text = text.replace("\n", " ").strip()
    # Recombine words split with hyphens due to line breaks
    text = re.sub(r'(\w)-\s*(\w)', r'\1\2', text)
    return text

def remove_header_footer(text, header_pattern, footer_pattern):
    """Remove header and footer from the text based on regex patterns."""
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        if header_pattern and re.search(header_pattern, line):
            continue
        if footer_pattern and re.search(footer_pattern, line):
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def format_page_text(page, document_text, header, footer):
    """Format document text by processing paragraphs without duplication."""
    formatted_text = ""

    # Process paragraphs only to avoid duplication
    for paragraph in page.get('paragraphs', []):
        paragraph_text = extract_text_from_layout(paragraph['layout'], document_text)
        if paragraph_text:
            paragraph_text = clean_paragraph_text(paragraph_text)
            # Remove header and footer from the paragraph text
            paragraph_text = remove_header_footer(paragraph_text, header, footer)
            if paragraph_text:
                formatted_text += paragraph_text + "\n"  # Single line break between paragraphs

    return formatted_text.strip()

def extract_text_from_response(response, header, footer):
    """Extracts text and language code from the Document AI response."""
    document = response.get('document', {})
    document_text = document.get('text', '')

    if not document_text:
        print("No 'text' field found in the 'document' JSON response.")
        return '', 'en-US'

    extracted_text = ''
    language_code = 'en-US'  # Default language code

    # Process each page
    for page in document.get('pages', []):
        page_text = format_page_text(page, document_text, header, footer)
        if page_text:
            extracted_text += page_text + "\n\n"

        # Extract language code from the page
        page_language_code = extract_language_from_page(page)
        if page_language_code:
            language_code = page_language_code  # Use the detected language code

    return extracted_text.strip(), language_code

# Function to extract page number from filename
def extract_page_number(filename):
    match = re.search(r'_page_(\d+)', filename)
    if match:
        return int(match.group(1))
    else:
        return float('inf')  # Files without a page number go to the end

def combine_all_text_files(input_folder, output_file):
    """Combine all text files in input_folder into one output_file in correct page order."""
    # Get all text files in the folder
    text_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
    
    # Sort files based on the extracted page numbers
    text_files.sort(key=extract_page_number)
    
    with open(output_file, 'w') as outfile:
        for text_file in text_files:
            with open(os.path.join(input_folder, text_file), 'r') as infile:
                outfile.write(infile.read() + "\n\n")
    print(f"Combined text file saved to {output_file}")

    # After combining the text files, save the combined text as a PDF
    save_text_as_pdf(output_file, COMBINED_PDF_FILE)

def save_text_as_pdf(text_file, output_pdf):
    """Save a text file as a PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit

    c = canvas.Canvas(output_pdf, pagesize=letter)
    width, height = letter
    text = open(text_file, 'r').read()
    lines = simpleSplit(text, c._fontname, c._fontsize, width - 2*72)
    text_object = c.beginText(72, height - 72)

    for line in lines:
        text_object.textLine(line)
        if text_object.getY() < 72:
            c.drawText(text_object)
            c.showPage()
            text_object = c.beginText(72, height - 72)
    c.drawText(text_object)
    c.save()
    print(f"Combined PDF file saved to {output_pdf}")

def combine_audio_files(audio_folder, output_audio_file):
    """Combine multiple audio files into one in correct page order."""
    # Get all audio files in the folder
    audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3')]
    
    # Sort files based on the extracted page numbers
    audio_files.sort(key=extract_page_number)
    
    # Combine audio files in order
    combined = AudioSegment.empty()
    for audio_file in audio_files:
        audio_path = os.path.join(audio_folder, audio_file)
        audio = AudioSegment.from_file(audio_path)
        combined += audio
    combined.export(output_audio_file, format='mp3')
    print(f"Combined audio file saved to {output_audio_file}")

def process_pdfs_in_folder(folder_path, header, footer):
    """Process all PDFs in the folder, splitting them into one-pagers, extracting text, and generating audio."""
    pdf_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.pdf')])

    if not os.path.exists(AUDIO_FOLDER):
        os.makedirs(AUDIO_FOLDER)

    if not os.path.exists(TEMP_PDF_FOLDER):
        os.makedirs(TEMP_PDF_FOLDER)

    if not os.path.exists(RESPONSES_FOLDER):
        os.makedirs(RESPONSES_FOLDER)

    if not os.path.exists(TEXTS_FOLDER):
        os.makedirs(TEXTS_FOLDER)

    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"Processing {pdf_file}...")

        # Split into one-pagers
        one_pager_paths = split_pdf_into_one_pagers(pdf_path)

        # Prepare the overall text file for this PDF
        text_output_file = os.path.join(TEXTS_FOLDER, os.path.splitext(pdf_file)[0] + '.txt')
        for idx, one_pager_path in enumerate(one_pager_paths):
            # Determine the response file path for this page
            response_file_path = os.path.join(RESPONSES_FOLDER, f"{os.path.splitext(pdf_file)[0]}_page_{idx + 1}.json")
            
            if os.path.exists(response_file_path):
                print(f"Response file {response_file_path} already exists. Loading response from file.")
                with open(response_file_path, 'r') as json_file:
                    result = json.load(json_file)
            else:
                print(f"Sending API request for {one_pager_path}...")
                result = send_pdf_to_api(one_pager_path)
                if result:
                    # Save the response to the response file
                    with open(response_file_path, 'w') as json_file:
                        json.dump(result, json_file, indent=2)
                    print(f"Response saved to {response_file_path}")
                else:
                    print(f"Failed to get response for {one_pager_path}")
                    continue  # Skip to next page if failed
            # Extract text and language code from the response
            text, language_code = extract_text_from_response(result, header, footer)
            # Save the text to a per-page text file
            page_text_file = os.path.join(TEXTS_FOLDER, f"{os.path.splitext(pdf_file)[0]}_page_{idx + 1}.txt")
            with open(page_text_file, 'w') as page_file:
                page_file.write(text)
            print(f"Extracted text for page {idx + 1} saved to {page_text_file}")

            # Determine the per-page audio file path
            audio_output_path = os.path.join(AUDIO_FOLDER, f"{os.path.splitext(pdf_file)[0]}_page_{idx + 1}.mp3")
            # Check if the audio file already exists
            if os.path.exists(audio_output_path):
                print(f"Audio file {audio_output_path} already exists. Skipping TTS API call.")
            # else:
                # Generate audio per page
                # text_to_speech(text, language_code, audio_output_path)
        print(f"Extracted text for {pdf_file} saved to {text_output_file}")

    # Optionally combine all text files into one combined text file
    combine_all_text_files(TEXTS_FOLDER, COMBINED_TEXT_FILE)

    # Optionally combine all audio files into one combined audio file
    # audio_files = [os.path.join(AUDIO_FOLDER, f) for f in sorted(os.listdir(AUDIO_FOLDER)) if f.endswith('.mp3')]
    # combine_audio_files(AUDIO_FOLDER, COMBINED_AUDIO_FILE)

def main():
    parser = argparse.ArgumentParser(description='Process PDFs and remove headers and footers.')
    parser.add_argument('--header', type=str, default='', help='Header text or regex pattern to remove')
    parser.add_argument('--footer', type=str, default='', help='Footer text or regex pattern to remove')
    args = parser.parse_args()

    # Call the processing function with header and footer
    process_pdfs_in_folder(PDF_FOLDER, args.header, args.footer)

if __name__ == "__main__":
    main()

# Example usage:

# python scriptname.py --header "^Page \d+$" --footer "^Chapter \d+"