import os
import pdfplumber

def pdf_to_text(pdf_path, txt_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

def convert_all_pdfs(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                relative_path = os.path.relpath(pdf_path, input_dir)
                txt_file = os.path.splitext(relative_path)[0] + ".txt"
                txt_path = os.path.join(output_dir, txt_file)

                # Ensure output subfolders exist
                os.makedirs(os.path.dirname(txt_path), exist_ok=True)

                try:
                    print(f"Converting: {pdf_path}")
                    pdf_to_text(pdf_path, txt_path)
                except Exception as e:
                    print(f"Failed to convert {pdf_path}: {e}")





# Example usage
x = [2022,2023,2024,2025]
for year in x:
    input_dir = f"folder loc here"
    output_dir = f"folder loc here"
    convert_all_pdfs(input_dir, output_dir)
