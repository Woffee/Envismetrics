import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join('logs')
UPLOAD_FOLDER = os.path.join('uploads')
OUTPUT_FOLDER = os.path.join('outputs')
TMP_FOLDER = os.path.join('outputs')
ALLOWED_EXTENSIONS = {'csv', 'txt', 'xlsx'}
