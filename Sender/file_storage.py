# file_storage.py
stored_file = None

def store_file(filepath):
    global stored_file
    stored_file = filepath
    print("[Storage] File stored:", filepath)

def get_stored_file():
    return stored_file
