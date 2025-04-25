import streamlit as st
import os
import tempfile
import fnmatch
import mimetypes

def is_binary_file(file_path):
    """Check if file is binary using both mimetype and content analysis"""
    # Check by mime type first
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return not mime_type.startswith('text/')
    
    # If mime type is inconclusive, check file content
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk  # Binary files typically contain null bytes
    except Exception:
        return True  # If we can't read the file, treat it as binary

def should_ignore_path(path):
    # Common patterns to ignore
    ignore_patterns = [
        # Development related
        'env/*', '.env/*', 'venv/*', '.venv/*',  # Virtual environments
        '.gitignore', '.git/*',                   # Git related
        '__pycache__/*', '*.pyc', '*.pyo',       # Python cache
        '.pytest_cache/*', '.coverage',           # Test related
        '.DS_Store', 'Thumbs.db',                # System files
        'node_modules/*', '.npm/*',              # Node.js related
        '.cache/*', '*.log',                     # Cache and logs
        '*.min', '*.svg', '*.min.css', '*.woff', '*.min.js',
        '*.woff2', '*._.DS_Store', '*.DS_Store', '.DS_Store'
        
        # Binary and non-text file extensions
        '*.pdf', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico',  # Images
        '*.zip', '*.tar', '*.gz', '*.rar', '*.7z',              # Archives
        '*.exe', '*.dll', '*.so', '*.dylib',                    # Executables
        '*.db', '*.sqlite', '*.sqlite3',                        # Databases
        '*.pkl', '*.pickle',                                    # Python binary
        '*.bin', '*.dat',                                       # Binary data
        '*.mp3', '*.wav', '*.mp4', '*.avi', '*.mov',           # Media files
        '*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt',         # Office files
        '*.psd', '*.ai',                                        # Design files
    ]
    
    return any(fnmatch.fnmatch(path, pattern) for pattern in ignore_patterns)

def extract_file_content(file_path):
    # Skip binary files
    if is_binary_file(file_path):
        return f"[Skipped binary file: {file_path}]"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        return f"[Skipped: File {file_path} is not valid UTF-8 text]"
    except Exception as e:
        return f"[Error reading file {file_path}: {str(e)}]"

def get_files_from_directory(directory_path, ignore_list=None):
    if ignore_list is None:
        ignore_list = set()
    
    files_dict = {}
    for root, dirs, files in os.walk(directory_path):
        # Remove ignored directories to prevent walking into them
        dirs[:] = [d for d in dirs if not should_ignore_path(d)]
        
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, directory_path)
            
            # Skip files that match ignore patterns or are in ignore list
            if rel_path not in ignore_list and not should_ignore_path(rel_path):
                files_dict[rel_path] = full_path
    return files_dict

st.title("File Content Extractor")

# File/Directory uploader section
st.header("Upload Files or Directories")
uploaded_files = st.file_uploader("Drag and drop files here", accept_multiple_files=True)
uploaded_dir = st.text_input("Or paste a directory path from your computer")

# Process uploads and create file tree
files_to_process = {}
if uploaded_files:
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            files_to_process[uploaded_file.name] = tmp_file.name

if uploaded_dir and os.path.exists(uploaded_dir):
    dir_files = get_files_from_directory(uploaded_dir)
    files_to_process.update(dir_files)

# Create checkboxes for file selection
st.header("Select files to include")
ignore_list = set()
if files_to_process:
    st.write("Uncheck files to exclude them from the final output:")
    for file_name in sorted(files_to_process.keys()):
        if not st.checkbox(file_name, value=True, key=file_name):
            ignore_list.add(file_name)

# Generate and download button
if files_to_process and st.button("Generate Combined Text File"):
    combined_content = []
    
    for file_name, file_path in sorted(files_to_process.items()):
        if file_name not in ignore_list:
            combined_content.append(f"==================== {file_name} ====================\n")
            content = extract_file_content(file_path)
            combined_content.append(content + "\n\n")
    
    final_content = "\n".join(combined_content)
    
    st.download_button(
        label="Download Combined Text File",
        data=final_content,
        file_name="combined_content.txt",
        mime="text/plain"
    )

# Cleanup temporary files
for path in files_to_process.values():
    if path.startswith(tempfile.gettempdir()):
        try:
            os.unlink(path)
        except Exception as e:
            st.error(f"Error cleaning up temporary file: {e}")

