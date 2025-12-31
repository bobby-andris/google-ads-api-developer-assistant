import sys
import markdown
import os
from markdown.extensions.toc import TocExtension

def convert_md_to_html(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Configure Markdown with Table of Contents extension
    # We use a custom marker [TOC] which the script will place in the sidebar
    md = markdown.Markdown(extensions=[
        TocExtension(baselevel=1, toc_depth="2"), 
        "fenced_code", 
        "tables"
    ])
    
    html_content = md.convert(md_content)
    toc_content = md.toc

    # Define the HTML template with a floating sidebar
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Allied Brass - {os.path.basename(input_file)}</title>
    <style>
        :root {{
            --sidebar-width: 300px;
            --primary-color: #2c3e50;
            --accent-color: #3498db;
            --bg-color: #f4f7f6;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            display: flex;
            background-color: var(--bg-color);
            color: #333;
        }}
        /* Sidebar Styles */
        #sidebar {{
            width: var(--sidebar-width);
            height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            background-color: white;
            border-right: 1px solid #ddd;
            overflow-y: auto;
            padding: 20px;
            box-shadow: 2px 0 5px rgba(0,0,0,0.05);
        }}
        #sidebar h2 {{
            font-size: 1.2rem;
            color: var(--primary-color);
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 10px;
        }}
        .toc {{
            list-style-type: none;
            padding: 0;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 15px;
        }}
        .toc a {{
            text-decoration: none;
            color: #666;
            font-size: 0.9rem;
            display: block;
            padding: 5px 0;
            transition: color 0.2s;
        }}
        .toc a:hover {{
            color: var(--accent-color);
        }}
        /* Main Content Styles */
        #content {{
            margin-left: var(--sidebar-width);
            padding: 40px 60px;
            max-width: 900px;
            flex-grow: 1;
            background-color: white;
            min-height: 100vh;
        }}
        h1, h2, h3 {{
            color: var(--primary-color);
            margin-top: 1.5em;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        code {{
            background-color: #f8f8f8;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
        }}
        pre {{
            background-color: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <nav id="sidebar">
        <h2>Contents</h2>
        {toc_content}
    </nav>
    <main id="content">
        {html_content}
    </main>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(template)
    
    print(f"Successfully converted {input_file} to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poetry run python saved_code/md_to_html.py <input_file.md>")
    else:
        input_md = sys.argv[1]
        output_html = input_md.replace(".md", ".html")
        convert_md_to_html(input_md, output_html)
