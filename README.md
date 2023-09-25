# OpenAI Text Analizer

## Overview

This script uses the OpenAI API to process text files based on the modes and language preferences defined by the user. It's designed to be flexible, allowing you to specify input and output directories, file types, output language, and more through command-line arguments and a configuration file.

## Requirements

- Python 3.x
- `openai` Python package
- A valid OpenAI API key

## Installation Steps

1. **Clone the repository:**
    ```bash
    git clone https://your-repo-url.git
    ```

2. **Navigate to the directory:**
    ```bash
    cd your-repo-directory
    ```

3. **Install the required package:**
    ```bash
    pip install openai
    ```

4. **Set up the `config.json` file:**
    Create a `config.json` in the same directory as the script. Add necessary configurations such as API key, default engine, etc.

5. **Set OpenAI API key (Optional):**
    You can either add your OpenAI API key in the `config.json` file or set it as an environment variable:
    ```bash
    export OPENAI_API_KEY="your-api-key-here"
    ```

## Usage

To run the script, you can use the following command format:

```bash
python3 your-script-name.py --f [Processing Path] --o [Output Path] --m [Mode] --i [Input File Type] --l [Output Language]
```

### Command-Line Arguments

- `--f` : Path to the directory containing the text files to be processed. (Default: `./txt`)
- `--o` : Path to the directory where the processed files will be saved. (Default: `./out`)
- `--m` : Mode to be used, as defined in `config.json`. (Default: `openai`)
- `--i` : Input file type. (Default: `txt`)
- `--l` : Language for the OpenAI API to generate the output in. (Default: `english`)

## Example

```bash
python3 your-script-name.py --f ./ocr --o ./map --i txt --l french --m map
```

This will process all `.txt` files in the `./ocr` directory and save the output in the `./map` directory. The OpenAI API will generate output in French according to the mode `map`.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
