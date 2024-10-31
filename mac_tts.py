#!/usr/bin/env python3

import os
import re
import subprocess
from pydub import AudioSegment
from natsort import natsorted

def clean_markdown(text):
    """
    Removes common Markdown syntax from the text, such as headings, lists, and other markers.
    """
    text = re.sub(r'(\*|_|#|`|!?$begin:math:display$.*?$end:math:display$$begin:math:text$.*?$end:math:text$|\$\$begin:math:display\$\$.*?\$\$end:math:display\$\$|\$\$begin:math:text\$\$.*?\$\$end:math:text\$\$)', '', text)
    text = re.sub(r'\n\s*-\s*', '\n', text)  # Remove bullet points
    text = re.sub(r'\n\s*\d+\.\s*', '\n', text)  # Remove numbered lists
    text = re.sub(r'\n{2,}', '\n', text)  # Replace multiple newlines with a single newline
    return text.strip()

def speak_text_files_in_folder(folder_path, output_folder, final_output_file):
    """
    Reads all text files in a folder, speaks their content using the macOS TTS engine,
    and saves the speech for each file to an individual .wav file in an output folder. 
    Combines all generated audio files into a single final .wav file.

    Args:
      folder_path: The path to the folder containing the text files.
      output_folder: The path to the folder where individual audio files will be saved.
      final_output_file: The path for the final combined audio file.
      voice: The TTS voice (default is 'Samantha').
    """
    voice = "Samantha"
    os.makedirs(output_folder, exist_ok=True)
    audio_files = []

    # Process each file in the folder if it matches the required extensions
    for filename in natsorted(os.listdir(folder_path)):  # Use natsorted for natural order
        if any(filename.endswith(f".{ext}") for ext in in_paths):  # Check against each extension in in_paths
            file_path = os.path.join(folder_path, filename)
            output_file_name = filename.rsplit(".", 1)[0] + ".wav"  # Replace extension with .wav
            output_file_path = os.path.join(output_folder, output_file_name)

            # Skip if the audio file already exists
            if os.path.exists(output_file_path):
                print(f"Skipping '{filename}' - audio file already exists.")
                audio_files.append(output_file_path)  # Add to list for combining later
                continue

            # Read file contents and clean Markdown
            with open(file_path, 'r') as file:
                file_contents = file.read()
                cleaned_text = clean_markdown(file_contents).replace('"', '\\"')  # Escape quotes

            # Generate the audio file using macOS 'say' command with .wav format
            subprocess.run(['say', '-v', voice, cleaned_text, '-o', output_file_path, '--data-format=LEF32@22050'])
            print(f"Generated audio for '{filename}' with voice '{voice}' and saved to '{output_file_path}'")

            # Add the generated file to the list for final combination
            audio_files.append(output_file_path)

    # Combine all .wav files into a single final file
    combined_audio = AudioSegment.empty()
    for audio_file in audio_files:
        combined_audio += AudioSegment.from_wav(audio_file)
    
    # Export the combined audio to the specified final output path
    combined_audio.export(final_output_file, format="wav")
    print(f"Combined all audio files into '{final_output_file}'")

# List of folder names (extensions) to process
# in_paths = ["lda", "ent", "que", "sum", "ssf", "md"]
in_paths = ["ssf"]

# Example usage
for path in in_paths:
    folder_path = f'./output/{path}'  # Folder for each category
    output_folder = f'./output/{path}/'  # Output folder for audio files
    final_output_file = f'./output/{path}_final_output.wav'  # Path for the combined final file
    speak_text_files_in_folder(folder_path, output_folder, final_output_file)