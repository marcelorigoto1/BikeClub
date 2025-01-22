import os
import json

# Define the data folder and output file paths
data_folder = os.path.join(os.getcwd(), "data")
output_file = os.path.join(data_folder, "files.json")

# List of supported file extensions
supported_extensions = [".jpeg", ".jpg", ".png", ".mp4", ".MP4", ".JPG"]

# Function to generate files.json structure
def generate_files_json(folder):
    result = {}
    for route_name in os.listdir(folder):
        route_path = os.path.join(folder, route_name)
        if os.path.isdir(route_path):
            # Filter files based on the supported extensions
            files = [
                file
                for file in os.listdir(route_path)
                if os.path.isfile(os.path.join(route_path, file)) and file.endswith(tuple(supported_extensions))
            ]
            result[route_name] = files
    return result

# Generate the JSON structure and write it to files.json
files_json = generate_files_json(data_folder)

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(files_json, f, indent=2)

print(f"Generated files.json at {output_file}")
