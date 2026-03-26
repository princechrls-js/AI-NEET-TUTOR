import os

filepath = 'app/main.py'
with open(filepath, 'rb') as f:
    content = f.read()

# try to decode as utf-16
try:
    text = content.decode('utf-16le')
    if text.startswith('\ufeff'):
        text = text[1:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully converted app/main.py to utf-8")
except Exception as e:
    print(f"Failed to convert: {e}")
