#!/usr/bin/env python3

import os
import sys
import shutil
import markdown
from natsort import natsorted

# HTML template with placeholders for the title and content for each tab
html_template = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <style>
      body {{
        display: flex;
        margin: 0;
        font-family: Arial, sans-serif;
      }}
      .pane {{
        height: 100vh;
        overflow-y: auto;
        padding: 10px;
      }}
      .processed {{
        width: 70%;
        background-color: #f9f9f9;
      }}
      .raw {{
        width: 30%;
        background-color: #fff;
        border-left: 1px solid #ddd;
        font-family: monospace;
      }}
      .tab {{
        display: none;
        padding: 10px;
      }}
      .tab-content {{
        display: block;
      }}
      .tab-buttons {{
        display: flex;
        gap: 5px;
        margin-bottom: 10px;
      }}
      .tab-buttons button {{
        cursor: pointer;
        padding: 5px 10px;
      }}
      iframe {{
        width: 100%;
        height: 100%;
        border: none;
      }}
      pre {{
        white-space: pre-wrap;
        word-wrap: break-word;
      }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.17"></script>
    <script>
      function openTab(event, tabName) {{
        var tabs = document.getElementsByClassName("tab");
        for (var i = 0; i < tabs.length; i++) {{
          tabs[i].style.display = "none";
        }}
        document.getElementById(tabName).style.display = "block";

        var buttons = document.getElementsByClassName("tab-button");
        for (var i = 0; i < buttons.length; i++) {{
          buttons[i].classList.remove("active");
        }}
        event.currentTarget.classList.add("active");
      }}
    </script>
  </head>
  <body>
    <div class="pane processed">
      <iframe src="{processed_html_path}" title="Processed HTML Content"></iframe>
    </div>

    <div class="pane raw">
      <h2>{title}</h2>
      <div class="tab-buttons">
        <button class="tab-button active" onclick="openTab(event, 'markdown')">Map</button>
        <button class="tab-button" onclick="openTab(event, 'txt')">Text</button>
        <button class="tab-button" onclick="openTab(event, 'summary')">Summary</button>
        <button class="tab-button" onclick="openTab(event, 'lda')">lda</button>
        <button class="tab-button" onclick="openTab(event, 'questions')">Questions</button>
        <button class="tab-button" onclick="openTab(event, 'entities')">Entities</button>
      </div>

      <div id="markdown" class="tab tab-content">
        {markdown_audio}
        <pre>{markdown_content}</pre>
      </div>
      <div id="txt" class="tab">
        {txt_audio}
        <pre>{txt_content}</pre>
        
      </div>
      <div id="summary" class="tab">
        {summary_audio}
        <pre>{summary_content}</pre>
        
      </div>
      <div id="lda" class="tab">
        {lda_audio}
        <pre>{lda_content}</pre>
      </div>
      <div id="questions" class="tab">
        {questions_audio}
        <pre>{questions_content}</pre>
      </div>
      <div id="entities" class="tab">
        {entities_audio}
        {entities_content}
      </div>
    </div>
  </body>
</html>"""

index_template = """<!DOCTYPE html>
<html>
<head>
  <title>{title}</title>
</head>
<body>
  <h1>{title}</h1>
  <ul>
{links}
  </ul>
</body>
</html>"""

def copy_to_output(file_path, output_subfolder, new_name=None):
    """
    Copies a file to a subfolder within the output directory and returns the relative path.
    If new_name is specified, renames the copied file to new_name.
    """
    if os.path.exists(file_path):
        os.makedirs(output_subfolder, exist_ok=True)
        dest_path = os.path.join(output_subfolder, new_name if new_name else os.path.basename(file_path))
        shutil.copy(file_path, dest_path)
        return os.path.relpath(dest_path, output_subfolder)
    return None

def get_file_content(folder, base_filename, extension, default_message="Content not available."):
    file_path = os.path.join(folder, f"{base_filename}.{extension}")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return default_message

def generate_audio_content(input_folder, base_filename, output_folder, tab_name):
    """
    Generate unique audio file for each tab to avoid overwrites and create HTML audio element.
    """
    audio_path = os.path.join(input_folder, f"{base_filename}.wav")
    if os.path.exists(audio_path):
        unique_name = f"{base_filename}_{tab_name}.wav"  # Unique name per tab
        audio_dest = copy_to_output(audio_path, output_folder, new_name=unique_name)
        return f'<audio controls><source src="{audio_dest}" type="audio/wav">Your browser does not support the audio element.</audio>'
    return "Audio content not available."

def convert_markdown_to_html(input_folder, output_folder, lda_folder, txt_folder, sum_folder, que_folder, ent_folder, htmlmap_folder):
    os.makedirs(output_folder, exist_ok=True)
    processed_html_output_folder = os.path.join(output_folder, "mark_maps")
    links = []

    for filename in os.listdir(input_folder):
        if filename.endswith('.md'):
            base_filename = filename.rsplit('.', 1)[0]
            file_path = os.path.join(input_folder, filename)
            html_filename = f"{base_filename}.html"
            html_path = os.path.join(output_folder, html_filename)

            # Copy `mark_maps` HTML file with a unique name
            processed_html_src = os.path.join(htmlmap_folder, f"{base_filename}.html")
            processed_html_relative = os.path.join("mark_maps", f"{base_filename}_markmap.html")
            copy_to_output(processed_html_src, processed_html_output_folder, new_name=f"{base_filename}_markmap.html")

            # Get content for each tab
            markdown_content = markdown.markdown(get_file_content(input_folder, base_filename, 'md'))
            lda_content = markdown.markdown(get_file_content(lda_folder, base_filename, 'lda'))
            entities_content = markdown.markdown(get_file_content(ent_folder, base_filename, 'ent'), extensions=['tables'])
            txt_content = get_file_content(txt_folder, base_filename, 'ssf')
            summary_content = markdown.markdown(get_file_content(sum_folder, base_filename, 'sum')) #get_file_content(sum_folder, base_filename, 'sum')
            questions_content = markdown.markdown(get_file_content(que_folder, base_filename, 'que'))

            # Generate unique audio references per tab
            markdown_audio = generate_audio_content(input_folder, base_filename, output_folder, "markdown")
            lda_audio = generate_audio_content(lda_folder, base_filename, output_folder, "lda")
            entities_audio = generate_audio_content(ent_folder, base_filename, output_folder, "entities")
            txt_audio = generate_audio_content(txt_folder, base_filename, output_folder, "txt")
            summary_audio = generate_audio_content(sum_folder, base_filename, output_folder, "summary")
            questions_audio = generate_audio_content(que_folder, base_filename, output_folder, "questions")

            # Insert content and title into the HTML template
            html_output = html_template.format(
                title=base_filename,
                processed_html_path=processed_html_relative,
                markdown_content=markdown_content,
                markdown_audio=markdown_audio,
                lda_content=lda_content,
                lda_audio=lda_audio,
                txt_content=txt_content,
                txt_audio=txt_audio,
                summary_content=summary_content,
                summary_audio=summary_audio,
                questions_content=questions_content,
                questions_audio=questions_audio,
                entities_content=entities_content,
                entities_audio=entities_audio
            )

            # Save the generated HTML file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_output)
            print(f"Converted '{filename}' to '{html_filename}' in '{output_folder}'")

            links.append((filename, f'    <li><a href="{html_filename}">{filename}</a></li>'))

    # Sort links naturally by filename
    links = natsorted(links, key=lambda x: x[0])

    # Generate index HTML content
    index_content = index_template.format(
        title="Index",
        links="\n".join(link[1] for link in links)
    )

    # Write index.html file
    index_path = os.path.join(output_folder, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    print(f"Index file created at '{index_path}'")

if __name__ == "__main__":
    default_input_folder = './output/md'
    default_output_folder = './output/html'
    default_lda_folder = './output/lda'
    default_txt_folder = './output/ssf'
    default_sum_folder = './output/sum'
    default_que_folder = './output/que'
    default_ent_folder = './output/ent'
    default_htmlmap_folder = './output/map'

    input_folder = sys.argv[1] if len(sys.argv) > 1 else default_input_folder
    output_folder = sys.argv[2] if len(sys.argv) > 2 else default_output_folder
    lda_folder = sys.argv[3] if len(sys.argv) > 3 else default_lda_folder
    txt_folder = sys.argv[4] if len(sys.argv) > 4 else default_txt_folder
    sum_folder = sys.argv[5] if len(sys.argv) > 5 else default_sum_folder
    que_folder = sys.argv[6] if len(sys.argv) > 6 else default_que_folder
    ent_folder = sys.argv[7] if len(sys.argv) > 7 else default_ent_folder
    htmlmap_folder = sys.argv[8] if len(sys.argv) > 8 else default_htmlmap_folder

    convert_markdown_to_html(input_folder, output_folder, lda_folder, txt_folder, sum_folder, que_folder, ent_folder, htmlmap_folder)