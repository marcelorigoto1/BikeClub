import os

media_dir = "data"
output_file = "media.html"

html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Media Files</title>
</head>
<body>
    <h1>Media Files</h1>
    <ul>
"""

for root, dirs, files in os.walk(media_dir):
    for file in files:
        file_path = os.path.join(root, file).replace("\\", "/")
        html_content += f'        <li><a href="{file_path}" target="_blank">{file}</a></li>\n'

html_content += """    </ul>
</body>
</html>"""

with open(output_file, "w") as f:
    f.write(html_content)

print(f"Media page generated: {output_file}")
