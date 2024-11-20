import os
import PyPDF2
import base64
import ollama
import fitz  # PyMuPDF for PDF-to-image conversion

# Set up constants
PDF_FOLDER = "./pdfs"  # Path to your local PDF folder
TEMP_IMAGE_FOLDER = "./temp_images"  # Temporary folder to save images from PDFs
TEXT_OUTPUT_FOLDER = "./extracted_texts"  # Folder to save extracted text

# Create necessary directories
os.makedirs(TEMP_IMAGE_FOLDER, exist_ok=True)
os.makedirs(TEXT_OUTPUT_FOLDER, exist_ok=True)

# Initialize Llama 3.2 Vision parameters
LLAMA_MODEL = "llama3.2-vision"

# Convert PDF to images
def convert_pdf_to_images(pdf_path, output_folder):
    """Convert a multi-page PDF into images and save them to the output folder."""
    pdf_document = fitz.open(pdf_path)
    image_paths = []

    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]
        pix = page.get_pixmap()
        image_path = os.path.join(
            output_folder,
            f"{os.path.basename(pdf_path).replace('.pdf', '')}_page_{page_number + 1}.png"
        )
        # Save the image
        pix.save(image_path)
        image_paths.append(image_path)

    return image_paths

# Encode image to base64
def encode_image_to_base64(image_path):
    """Encode an image file in base64 format for Llama 3.2 Vision."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {image_path}. Error: {e}")
        return None

# Process a single image with Llama 3.2 Vision
def process_image_with_llama(image_path):
    """Send an image to Llama 3.2 Vision for text extraction."""
    try:
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return None
        response = ollama.chat(
            model=LLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": "Apply OCR on this image of an open book, reply with the text found in the book pages",
                    "images": [base64_image],
                }
            ]
        )
        print(response)
        # Ensure we only return the text content
        return response.get('message', None)
    except Exception as e:
        print(f"[ERROR] Failed to process {image_path}: {e}")
        return None
    
# Process PDFs into images and extract text
def process_pdfs_in_folder_as_images(pdf_folder, temp_image_folder, text_output_folder):
    """Convert PDFs to images and process each image for text extraction."""
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        print(f"Processing {pdf_file}...")

        # Convert PDF to images
        image_paths = convert_pdf_to_images(pdf_path, temp_image_folder)

        for image_path in image_paths:
            # Process each image with Llama 3.2 Vision
            extracted_text = process_image_with_llama(image_path)

            if extracted_text and isinstance(extracted_text, str):
                # Save the extracted text
                text_output_path = os.path.join(
                    text_output_folder,
                    f"{os.path.basename(image_path).replace('.png', '.txt')}"
                )
                with open(text_output_path, 'w') as text_file:
                    text_file.write(extracted_text)
                print(f"[INFO] Extracted text saved to {text_output_path}")
            else:
                print(f"[ERROR] No valid text extracted for {image_path}")

# Main script
if __name__ == "__main__":
    process_pdfs_in_folder_as_images(PDF_FOLDER, TEMP_IMAGE_FOLDER, TEXT_OUTPUT_FOLDER)