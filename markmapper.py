#!/usr/bin/env python3

import os
import sys

# HTML template with placeholders for the title and content
html_template = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <style>
      svg.markmap {{
        width: 100%;
        height: 100vh;
      }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.17"></script>
  </head>
  <body>
    <div class="markmap">
      <script type="text/template">
        ---
        markmap:
          maxWidth: 300
          initialExpandLevel: -1
          spacingHorizontal: 80
          spacingVertical: 5
          duration: 1000
          colorFreezeLevel: 3
        ---

{content}

      </script>
    </div>
  </body>
</html>"""

def validate_markdown_content(markdown_content):
    # Define valid markdown starting characters
    valid_markdown_characters = ('#', '-', '*', '>', '`', '=')

    # Check each line, skip empty lines, and add '-' if missing valid markdown character
    validated_lines = [
        line if line.startswith(valid_markdown_characters) or not line.strip() else f"- {line}"
        for line in markdown_content.splitlines()
    ]
    return "\n".join(validated_lines)

def convert_markdown_to_html(input_folder, output_folder):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Process each markdown file in the folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.md'):
            file_path = os.path.join(input_folder, filename)
            html_filename = filename.rsplit('.', 1)[0] + '.html'
            html_path = os.path.join(output_folder, html_filename)

            # Read markdown content and validate it
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Validate and indent markdown content
            validated_content = validate_markdown_content(markdown_content)
            indented_content = "\n".join("        " + line for line in validated_content.splitlines())

            # Insert content and title into the HTML template
            html_output = html_template.format(
                title=filename.rsplit('.', 1)[0],
                content=indented_content
            )

            # Save the generated HTML file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_output)
            print(f"Converted '{filename}' to '{html_filename}' in '{output_folder}'")

if __name__ == "__main__":
    # Set the default folder paths
    default_input_folder = './output/md'
    default_output_folder = './output/map'

    # Use folder paths provided via command-line arguments, if any
    input_folder = sys.argv[1] if len(sys.argv) > 1 else default_input_folder
    output_folder = sys.argv[2] if len(sys.argv) > 2 else default_output_folder

    # Run the conversion
    convert_markdown_to_html(input_folder, output_folder)