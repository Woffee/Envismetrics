"""
app.py - Main Flask Application for Envismetrics Electrochemical Analysis Suite
-------------------------------------------------------------------------------

This module defines the backend server logic for the Envismetrics software package.
It provides a web-based user interface (UI) for performing electrochemical data
analysis using CV (Cyclic Voltammetry), CA (Chronoamperometry), and HDV (Hydrodynamic Voltammetry) modules.

Core Responsibilities:
----------------------
- Sets up and launches a Flask web application to serve Envismetrics UI.
- Handles routing for various views including:
    - Main landing page
    - About page
    - File upload and processing
    - Results visualization and downloads
- Coordinates frontend interactions with backend data analysis classes.

Features:
---------
- Uploads and stores user data to a designated session directory.
- Dynamically loads module-specific analysis pipelines (CV, CA, HDV).
- Manages user sessions and filesystem separation by version (timestamp).
- Uses Jinja2 templates for rendering HTML interfaces.

Structure:
----------
- Uses the Flask web framework for routing and request handling.
- Static files (JS, CSS) served from /static directory.
- HTML templates located in /templates directory.

Dependencies:
-------------
- Flask: lightweight web framework for Python
- os, shutil, uuid: for session and file handling
- Envismetrics modules (CV.py, CA.py, HDV.py)

Typical Usage:
--------------
To launch the application, run this file directly:

    $ python app.py

Then navigate to http://localhost:5000/ in a web browser.

Date: 2025
"""

import sys
import os

# Python version check
if sys.version_info < (3, 10):
    print("Error: This project requires Python 3.10 or a higher version.")
    print(f"The current version of Python: {sys.version}")
    print("Please upgrade the Python version and try again.")
    sys.exit(1)

from werkzeug.utils import secure_filename
from flask import Flask, render_template, send_from_directory, jsonify, request, redirect, send_file, abort
import time
import datetime
import logging
import json
import configparser
from datetime import datetime
from HDV import HDV
from CV import CV
import hashlib
import shutil
from config import *
from utils import init_logging, check_folders
import threading
import traceback
from CA import CA

# Add the current file's directory to the system path to enable local imports (e.g., config.py, utils.py)
sys.path.append(os.path.dirname(__file__))

# Import global configuration variables and constants (e.g., UPLOAD_FOLDER, ALLOWED_EXTENSIONS)
from config import *

# Import utility functions for logging and folder validation
from utils import init_logging, check_folders

# Initialize the Flask web application
app = Flask(__name__)

# Configure the upload directory for storing user-submitted files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure required folders (e.g., upload, output) exist; create if missing
check_folders()

# Initialize logging system to record backend runtime events
init_logging()

def allowed_file(filename):
    """
    Check whether the uploaded filename has an allowed extension.

    Args:
        filename (str): The uploaded file's name.

    Returns:
        bool: True if file extension is allowed, False otherwise.

    Purpose:
        Prevents users from uploading unsupported file types, based on ALLOWED_EXTENSIONS in config.py.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/doc")
def demo():
    """
    Route: /doc

    Renders the documentation page.

    Returns:
        HTML template: Renders doc.html, optionally with notes or instructions.

    Note:
        The `notes` list is currently empty, but can be populated dynamically if needed.
    """
    notes = []
    return render_template('doc.html', notes=notes)

@app.route("/")
def index():
    """
    Route: /

    Landing page of the web application.

    Returns:
        HTML template: Renders index.html with optional data.

    Note:
        The `data` dictionary can be used to pass backend variables to the homepage view.
    """
    data = {}
    return render_template('index.html', data=data)

# ================================
# Menu 1: Hydrodynamic Voltammetry (HDV) Interface
# ================================

@app.route("/hyd_elec")
def hyd_elec():
    """
    Route: /hyd_elec

    Renders the landing page for the HDV (Hydrodynamic Voltammetry) module.

    Returns:
        HTML page: m1_hyd_elec.html (initial interface for user interaction)
    """
    return render_template('m1_hyd_elec.html')

@app.route("/hyd_elec/<version>")
def hyd_elec2(version=None):
    """
    Route: /hyd_elec/<version>

    Load analysis results and step-specific display for HDV module based on session version.

    Args:
        version (str): Unique identifier (e.g., timestamp) representing this analysis session.

    Query Parameters:
        step (int): Step number of HDV process (default: 2).
        method (int): Method index for step 3 (default: -1, will be handled by UI).

    Returns:
        HTML page: m1_hyd_elec_step2.html or m1_hyd_elec_step3.html based on step.
    """

    # Fixed module name for routing HDV logic
    module = 'HDV'

    # Extract step from query parameter; default to 2 if invalid
    step = int(request.args.get('step', '2'))
    step = 2 if step < 2 else step

    # Locate corresponding output folder and data file
    data_path = os.path.join('outputs', version)
    if not os.path.exists(data_path):
        abort(404)  # Return 404 if session folder doesn't exist

    data_file = os.path.join(data_path, 'data.json')

    # Get method index (used in step 3 display)
    method = int(request.args.get('method', '-1'))

    # Attempt to load and parse stored results
    if os.path.exists(data_file):
        try:
            data = json.loads(open(data_file).read())
            data = data[module]
            print('---')
            print(data)

            # Determine which form (data block) to display based on step
            if step == 2:
                f = 'form1'
            elif step == 3:
                f = 'form2_{}'.format(method)
            else:
                f = 'form1'

            # Get current status of analysis step
            status = data[f]['status']
        except Exception as e:
            traceback.print_exc()  # Print traceback for debugging
            data = {}
            status = 'processing'  # Default display state
    else:
        traceback.print_exc()
        data = {}
        status = 'processing'

    # Display logic for front-end UI rendering
    data['method'] = method
    data['processing_display'] = 'none' if status == 'done' else 'block'
    data['form1_processing_display'] = 'block' if status == 'done' else 'none'
    data['version'] = version
    data['step'] = step

    # Dynamically render the appropriate HTML template
    if step == 2:
        return render_template('m1_hyd_elec_step2.html', data=data)
    elif step == 3:
        return render_template('m1_hyd_elec_step3.html', data=data)
    else:
        return render_template('m1_hyd_elec_step2.html', data=data)

# ================================
# Menu 2: Cyclic Voltammetry (CV) Interface
# ================================

@app.route("/cv")
def cv():
    """
    Route: /cv

    Renders the landing page for the CV (Cyclic Voltammetry) module.

    Returns:
        HTML page: m2_cv.html (initial interface for user interaction)
    """
    return render_template('m2_cv.html')

@app.route("/cv/<version>")
def cv2(version=None):
    """
    Route: /cv/<version>

    Load analysis results and dynamically display the appropriate CV step or function result
    based on the session version and query parameters.

    Args:
        version (str): Unique identifier for the analysis session (e.g., timestamp).

    Query Parameters:
        step (int): Step number to display (default = 2).
        func (int): Function index (used in step 3 to select which CV feature to render).

    Returns:
        HTML page:
            - m2_cv_step2.html: Standard CV data processing page.
            - m2_cv_step3.html: General CV step 3 results.
            - m2_cv_step3_func3.html / func4 / func5: Specific CV function visualizations.
    """

    module = 'CV'
    step = int(request.args.get('step', '2'))
    step = 2 if step < 2 else step  # Ensure minimum step is 2

    data_path = os.path.join('outputs', version)
    if not os.path.exists(data_path):
        abort(404)  # Return 404 if output folder not found

    data_file = os.path.join(data_path, 'data.json')

    # Try loading stored result metadata
    if os.path.exists(data_file):
        try:
            data = json.loads(open(data_file).read())
            data = data[module]
            print("data:", json.dumps(data))

            # For step N, load form N-1 result (due to frontend dependencies)
            kk = 'form{}'.format(step - 1)
            status = data[kk]['status']
        except Exception as e:
            traceback.print_exc()
            data = {}
            status = 'processing'
    else:
        traceback.print_exc()
        data = {}
        status = 'processing'

    # UI display logic
    data['status'] = status
    data['processing_display'] = 'none' if status == 'done' else 'block'
    data['version'] = version
    data['step'] = step

    # Render appropriate template based on step and function
    if step == 2:
        return render_template('m2_cv_step2.html', data=data)
    else:
        func = int(request.args.get('func', '-1'))
        if func == 3:
            return render_template('m2_cv_step3_func3.html', data=data)
        elif func == 4:
            return render_template('m2_cv_step3_func4.html', data=data)
        elif func == 5:
            return render_template('m2_cv_step3_func5.html', data=data)
        else:
            return render_template('m2_cv_step3.html', data=data)

@app.route("/cv/results/<version>")
def cv_res(version=None):
    """
    Route: /cv/results/<version>

    Loads the final results for the selected CV function (step 3), including rendered plots,
    regression results, or parameter extraction.

    Args:
        version (str): Unique session identifier.

    Query Parameters:
        func (int): CV function to visualize (3 = peak fitting, 4 = Randles-Sevcik, 5 = Tafel).

    Returns:
        HTML page:
            - m2_cv_step3_func{N}_res.html based on selected func.
        Or:
            - 404 error if function not supported.
    """
    module = 'CV'
    func = int(request.args.get('func', '0'))

    data_path = os.path.join('outputs', version)
    if not os.path.exists(data_path):
        abort(404)

    data_file = os.path.join(data_path, 'data.json')

    # Load data if available
    if os.path.exists(data_file):
        try:
            data = json.loads(open(data_file).read())
            data = data[module]
            print('---')
            print(data)

            # Use 'formN' as key to check if results are ready
            kk = 'form{}'.format(func)
            status = data[kk]['status']
        except Exception as e:
            traceback.print_exc()
            data = {}
            status = 'processing'
    else:
        traceback.print_exc()
        data = {}
        status = 'processing'

    # Update UI state
    data['status'] = status
    data['func'] = func
    data['processing_display'] = 'none' if status == 'done' else 'block'
    data['version'] = version

    # Render appropriate function result page
    if func == 3:
        return render_template('m2_cv_step3_func3_res.html', data=data)
    elif func == 4:
        return render_template('m2_cv_step3_func4_res.html', data=data)
    elif func == 5:
        return render_template('m2_cv_step3_func5_res.html', data=data)
    else:
        abort(404)  # Function not recognized

# ================================
# Menu 3: Chronoamperometry (CA) Interface
# ================================

@app.route("/step_methods")
def step_methods():
    """
    Route: /step_methods

    Renders the landing page for the CA (Chronoamperometry) module.

    Returns:
        HTML page: m3_step_methods.html
    """
    return render_template('m3_step_methods.html')

@app.route("/step_methods/<version>")
def step_methods2(version=None):
    """
    Route: /step_methods/<version>

    Renders a specific step page for a given CA (Chronoamperometry) analysis session.

    This function loads the JSON result file corresponding to the session (by version ID)
    and dynamically displays the correct step (step 2 or step 3). It uses query parameters
    to determine what to render and handles missing data and status flags accordingly.

    Args:
        version (str): Unique analysis version identifier (e.g., timestamp folder name).

    Query Parameters:
        step (int): Step number to render (default = 2). Valid values: 2 or 3.

    Returns:
        HTML page:
            - m3_step_methods_step2.html: if step == 2
            - m3_step_methods_step3.html: if step == 3
            - fallback to step2 page if step is not recognized

    Behavior:
        - If the required data file (`data.json`) is missing, returns a 404 error.
        - Loads and checks the 'status' field from the corresponding form result (form1 for step2, form2 for step3).
        - Controls UI visibility with `processing_display` and `form1_processing_display` flags.
    """

    module = 'CA'
    step = int(request.args.get('step', '2'))
    step = 2 if step < 2 else step  # Ensure step is at least 2

    data_path = os.path.join('outputs', version)
    if not os.path.exists(data_path):
        abort(404)  # Folder does not exist

    data_file = os.path.join(data_path, 'data.json')

    if os.path.exists(data_file):
        try:
            # Attempt to load stored JSON result data
            data = json.loads(open(data_file).read())
            data = data[module]
            print('---')
            print(data)

            # Determine which form result to check (form1 for step2, form2 for step3)
            f = 'form{}'.format(step - 1)
            status = data[f]['status']
        except Exception as e:
            traceback.print_exc()
            data = {}
            status = 'processing'
    else:
        traceback.print_exc()
        data = {}
        status = 'processing'

    # Update UI display flags and pass data to template
    data['processing_display'] = 'none' if status == 'done' else 'block'
    data['form1_processing_display'] = 'block' if status == 'done' else 'none'
    data['version'] = version
    data['step'] = step

    # Render the appropriate HTML template
    if step == 2:
        return render_template('m3_step_methods_step2.html', data=data)
    elif step == 3:
        return render_template('m3_step_methods_step3.html', data=data)
    else:
        return render_template('m3_step_methods_step2.html', data=data)  # fallback

@app.route("/check/<module>/<version>")
def check(module, version):
    """
    Route: /check/<module>/<version>

    Performs backend status checking for a given module (HDV, CV, or CA) and version.
    This route is called asynchronously by the frontend to determine whether the computation
    for a given analysis step is complete or still in progress.

    URL Parameters:
    ----------------
    module (str): One of ['CV', 'HDV', 'CA'], case-insensitive
    version (str): Unique version ID corresponding to an output folder (e.g., "20250808_152001")

    Query Parameters:
    -----------------
    step (int, default=1): Step number in the workflow (e.g., 2 or 3)
    func (int, optional, CV only): If provided, check a specific sub-function of step 3 (e.g., func=3)
    method (int, optional, HDV only): Used to identify the specific sub-method in step 3 (e.g., method=2)

    Returns:
    --------
    JSON Response:
        {
            "result": "done" | "processing" | "<error_message>"
        }

    Behavior:
    ---------
    - Checks for existence of result file: outputs/<version>/data.json
    - Reads the file and extracts the status of the requested form
    - Returns 'done' if the form status is complete
    - Returns 'processing' otherwise, or in case of any exceptions
    - Handles different logic for each module:

        For CV:
            - If func is specified, use form{func}
            - Otherwise use form{step-1}

        For HDV:
            - Step 2 => form1
            - Step 3 => form2_{method}

        For CA:
            - Step N => form{step-1}

    Notes:
    ------
    - This endpoint is typically used for real-time progress monitoring.
    - The frontend can periodically poll this route to determine whether
      to refresh the view or show a "still processing" message.
    """

    step = int(request.args.get('step', '1'))
    module = module.upper()

    print("version: {}, module: {}, step: {}".format(version, module, step))

    data_file = os.path.join('outputs', version, 'data.json')
    if not os.path.exists(data_file):
        data = {'result': 'processing'}
        return jsonify(data)

    data = json.loads(open(data_file).read())

    if module not in data.keys():
        data = {'result': 'processing'}
        return jsonify(data)

    if module.upper() == 'CV':
        func = int(request.args.get('func', '0'))
        if func > 0:
            f = 'form{}'.format(func)
        else:
            f = 'form{}'.format(step - 1)

        try:
            if data[module][f]['status'] == 'done':
                data = {'result': 'done'}
            else:
                data = {'result': data[module][f]['status']}
        except Exception as e:
            data = {'result': 'processing'}
        return jsonify(data)
    elif module.upper() == 'HDV':
        if step == 2:
            f = 'form1'
        elif step == 3:
            method = int(request.args.get('method', '1'))
            f = 'form2_{}'.format(method)
        else:
            data = {'result': 'processing'}
            return jsonify(data)

        try:
            data = {'result': data[module][f]['status']}
        except Exception as e:
            data = {'result': 'processing'}
        return jsonify(data)
    elif module.upper() == 'CA':
        f = 'form{}'.format(step-1)
        try:
            data = {'result': data[module][f]['status']}
        except Exception as e:
            data = {'result': 'processing'}
        return jsonify(data)

    # Fallback
    data = {'result': 'processing'}
    return jsonify(data)

def calculate_file_md5(file_path):
    """
    Calculate the MD5 hash of a file.

    This function reads the file in binary mode and computes its MD5 checksum
    by iterating over the file in 4KB chunks. This method is memory-efficient
    for large files.

    Args:
        file_path (str): Absolute path to the file.

    Returns:
        str: Hexadecimal string of the MD5 hash.
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        # Read file in 4096-byte chunks to reduce memory usage
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def check_if_file_exists(md5_hash):
    """
    Check if a file with the given MD5 hash already exists in the upload folder.

    This function scans the UPLOAD_FOLDER and compares filenames (excluding extensions)
    against the target hash. If a match is found, returns True and its path.

    Args:
        md5_hash (str): Target MD5 hash string.

    Returns:
        tuple: (exists_flag (bool), file_path (str))
    """
    folder_files = os.listdir(UPLOAD_FOLDER)
    for existing_file in folder_files:
        existing_file_name, _ = os.path.splitext(existing_file)
        if existing_file_name == md5_hash:
            print("File already exists:", existing_file)
            return True, os.path.join(UPLOAD_FOLDER, existing_file)
    return False, ''

def save_files(files, save_path, version):
    """
    Save uploaded files, check for duplication via MD5, and generate metadata.

    This function processes a list of uploaded files, checks whether each file
    already exists (via its MD5 hash), and saves it into the UPLOAD_FOLDER
    only if it's new. All uploaded file metadata is stored in fileinfo.json.

    Args:
        files (list): List of `werkzeug.datastructures.FileStorage` objects from Flask.
        save_path (str): Output directory path to save metadata.
        version (str): Unique version identifier for the session.

    Returns:
        str: Path to the generated 'fileinfo.json' metadata file.

    Output Format:
        fileinfo.json: [
            {
                "version": "20250808_142300",
                "filename": "raw_data.csv",            # Original name
                "md5": "a9d0239abc...",                # File hash
                "existed_filename": "uploads/a9d...."  # Server-side path
            },
            ...
        ]
    """
    info = []

    # Iterate over uploaded files
    for file in files:
        # Skip empty filenames
        if file.filename == '':
            return 'No selected file'

        # Check file type before proceeding
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Temporarily save file for MD5 hashing
            to_file_tmp = os.path.join(TMP_FOLDER, filename)
            file.save(to_file_tmp)
            print("uploaded to " + to_file_tmp)

            # Compute MD5 to detect duplicates
            md5_hash = calculate_file_md5(to_file_tmp)

            # Check for existing file with same hash
            existed, existed_filename = check_if_file_exists(md5_hash)

            if not existed:
                # Save new file to UPLOAD_FOLDER with hash-based filename
                extension = filename.rsplit('.', 1)[1].lower()
                existed_filename = os.path.join(UPLOAD_FOLDER, f"{md5_hash}.{extension}")

                # Move from temp folder to final storage
                file.save(existed_filename)
                shutil.move(to_file_tmp, existed_filename)
                print("saved to " + existed_filename)

            # Record file metadata
            info.append({
                'version': version,
                'filename': filename,
                'md5': md5_hash,
                'existed_filename': existed_filename,
            })

    # Save metadata to JSON
    to_file_info = os.path.join(save_path, "fileinfo.json")
    with open(to_file_info, 'w') as f:
        f.write(json.dumps(info))

    return to_file_info

"""
@app.route('/upload', methods=['POST'])

Handles all form submissions for data upload and task initiation.

Overview:
---------
This is the central API endpoint for receiving and processing file uploads
and user-defined parameters across all modules in the Envismetrics platform,
including CV (Cyclic Voltammetry), HDV (Hydrodynamic Voltammetry),
and CA (Chronoamperometry).

It supports:
    - File validation and de-duplication (via MD5 hash).
    - Parameter parsing for each module.
    - Version-based session management.
    - Asynchronous processing using background threads.

Supported Modules:
------------------
1. CV: Multi-step, multi-function input system.
   - Step 1: Upload raw CV files.
   - Step 2+: Trigger analysis functions (func 3, 4, 5) with parameters.

2. HDV: Two-step workflow.
   - Step 1: Upload RDE datasets + sigma parameter.
   - Step 2: Select method and calculate diffusion coefficients.

3. CA: Two-step chronoamperometry analysis.
   - Step 1: Upload CA datasets.
   - Step 2: Compute diffusion coefficient using Cottrell regression.

Request Method:
---------------
POST

Request Form Fields (common):
-----------------------------
- module: str, one of ['CV', 'HDV', 'CA']
- step: str, '1' or '2'
- version: str, (optional) session version identifier
- files[]: list of uploaded files

Returns:
--------
- JSON response indicating status, message, and generated version ID (if applicable).

Design Note:
------------
The upload logic handles each module separately to maintain modularity
and accommodate different parameter schemes. All tasks are dispatched
as background threads to keep the main thread responsive and ensure a
non-blocking user experience.

Thread Target:
--------------
`background_task(user_input)` where user_input is a dict of:
- version
- module
- step
- data: dict containing file paths and parameters

"""
@app.route('/upload', methods=['POST'])
def upload_file():
    version = None  # Initialize version variable (will be generated later if needed)

    try:
        # Attempt to parse submitted form data from the POST request
        print(request.form)
        module = request.form.get('module')  # Get the module name: 'CV', 'HDV', or 'CA'
        print("module: " + module)
    except Exception as e:
        # If parsing fails, default to 'None' as module name
        print(str(e))
        module = "None"

    # ======================== CV Module Upload Logic ========================
    if module.upper() == 'CV':
        step = request.form.get('step', '0')         # Step number in the workflow
        func = int(request.form.get('func', '0'))    # Optional analysis function for Step 3

        # -------- Case: Step 3 with analysis function 4 or 5 --------
        if func > 0:
            if func == 4 or func == 5:
                # Use user-provided version identifier
                version = request.form.get('version')
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], version)

                # Load pre-saved file info (JSON file listing uploaded data)
                files_info = os.path.join(save_path, "fileinfo.json".format(version))

                # Collect all form parameters and attach file info reference
                all_params = request.form.to_dict()
                all_params['files_info'] = files_info

                # Prepare task payload for background processing
                user_input = {
                    'version': version,
                    'module': module,
                    'step': step,
                    'func': func,
                    'data': all_params
                }

                # Start background thread to perform analysis
                background_thread = threading.Thread(target=background_task, args=(user_input,))
                background_thread.start()

                return {
                    'status': True,
                    'message': 'Success, please wait.',
                    'version': version
                }

            else:
                # Invalid func (not supported in current step)
                return jsonify({
                    'status': False,
                    'message': 'One or more files are not allowed.'
                })

        # -------- Case: Step 1 or Step 2 (no func specified) --------
        else:
            if step == '1':
                # Generate a new version identifier based on current timestamp
                version = "version_" + datetime.now().strftime("%m%d_%H%M%S")

                # Define file save path
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], version)
                if not os.path.exists(save_path):
                    os.makedirs(save_path, exist_ok=True)

                # Create corresponding output folder
                data_path = os.path.join('outputs', version)
                if not os.path.exists(data_path):
                    os.makedirs(data_path, exist_ok=True)

                # Ensure the form contains files
                if 'files[]' not in request.files:
                    return 'No file part'

                # Save uploaded files and generate file metadata
                files = request.files.getlist('files[]')
                files_info = save_files(files, save_path, version)

                # Prepare all user parameters for downstream analysis
                all_params = request.form.to_dict()
                all_params['files_info'] = files_info

                # Package everything into a dictionary to pass to the background worker
                user_input = {
                    'version': version,
                    'module': module,
                    'step': step,
                    'data': all_params
                }

                # Start a new background thread to run the processing task asynchronously
                background_thread = threading.Thread(target=background_task, args=(user_input,))
                background_thread.start()

                return jsonify({
                    'status': True,
                    'message': 'Success, please wait.',
                    'version': version
                })

            else:
                # Step > 1 but without func — process using existing version and parameters
                version = request.form.get('version')
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], version)
                files_info = os.path.join(save_path, "fileinfo.json".format(version))

                all_params = request.form.to_dict()
                all_params['files_info'] = files_info

                user_input = {
                    'version': version,
                    'module': module,
                    'step': step,
                    'data': all_params
                }

                # Start background analysis thread
                background_thread = threading.Thread(target=background_task, args=(user_input,))
                background_thread.start()

                return {
                    'status': True,
                    'message': 'Success, please wait.',
                    'version': version
                }

    # ======================== HDV Module Upload Logic ========================
    elif module.upper() == 'HDV':
        step = request.form.get('step', '1')  # Default to Step 1 if not provided

        # -------- Case: Step 1 – Upload new files for analysis --------
        if step == '1':
            # Generate a unique version name using the current timestamp
            version = "version_" + datetime.now().strftime("%m%d_%H%M%S")

            # Create the directory to store uploaded files
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], version)
            if not os.path.exists(save_path):
                os.makedirs(save_path, exist_ok=True)

            # Ensure the request contains files
            if 'files[]' not in request.files:
                return 'No file part'

            # Extract list of uploaded files and save them to disk
            files = request.files.getlist('files[]')
            files_info = save_files(files, save_path, version)

            # Retrieve user-provided sigma value (used for smoothing or fitting)
            sigma = float(request.form.get('sigma', 10))

            # Construct the input payload to pass to the background processing function
            user_input = {
                'version': version,
                'module': module,
                'step': step,
                'data': {
                    'files_info': files_info,  # List of file metadata
                    'sigma': sigma              # Smoothing parameter for HDV fitting
                }
            }

            # Launch background task in a separate thread
            background_thread = threading.Thread(target=background_task, args=(user_input,))
            background_thread.start()

            # Return success response to the frontend
            return jsonify({
                'status': True,
                'message': 'Success, please wait.',
                'version': version
            })

        # -------- Case: Step 2 – Continue with already uploaded version --------
        elif step == '2':
            # Load version and form data (likely from user inputs on the Step 2 UI)
            version = request.form.get('version')
            all_params = request.form.to_dict()

            # Package input and launch background task for computation
            user_input = {
                'version': version,
                'module': module,
                'step': step,
                'data': all_params
            }

            # Start background thread to run the step 2 analysis
            background_thread = threading.Thread(target=background_task, args=(user_input,))
            background_thread.start()


    # ======================== CA Module Upload Logic ========================
    elif module.upper() == 'CA':
        step = request.form.get('step', '1')  # Default to Step 1 if not provided

        # -------- Case: Step 1 – Initial file upload for CA analysis --------
        if step == '1':
            # Generate a new unique version name using current time
            version = "version_" + datetime.now().strftime("%m%d_%H%M%S")

            # Create directory for saving uploaded files
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], version)
            if not os.path.exists(save_path):
                os.makedirs(save_path, exist_ok=True)

            # Create corresponding output directory for storing results
            data_path = os.path.join('outputs', version)
            if not os.path.exists(data_path):
                os.makedirs(data_path, exist_ok=True)

            # Ensure that at least one file has been uploaded
            if 'files[]' not in request.files:
                return 'No file part'

            # Save uploaded files and generate MD5-based filenames
            files = request.files.getlist('files[]')
            files_info = save_files(files, save_path, version)

            # Construct input dictionary to pass to background task
            user_input = {
                'version': version,
                'module': module,
                'step': step,
                'data': {
                    'files_info': files_info,  # File metadata
                    # 'sigma': float(sigma)    # Optional parameter, currently commented
                }
            }

            # Launch background computation in a new thread
            background_thread = threading.Thread(target=background_task, args=(user_input,))
            background_thread.start()

            # Return status to the frontend
            return jsonify({
                'status': True,
                'message': 'Success, please wait.',
                'version': version
            })

        # -------- Case: Step 2 – Execute regression and parameter extraction --------
        elif step == '2':
            version = request.form.get('version')

            # Construct file info path based on version (might differ slightly from other modules)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], version)
            files_info = os.path.join(save_path, "fileinfo_{}.json".format(version))

            # Gather all numerical and range inputs required for Cottrell regression (D, n, A, C)
            user_input = {
                'version': version,
                'module': module,
                'step': step,
                'data': {
                    'files_info': files_info,
                    'interval': 5,  # Fixed time interval for sampling points
                    'n': int(request.form.get('input_n', 1)),   # Number of electrons transferred
                    'a': float(request.form.get('input_a', 0.07068583470577035)),  # Electrode area in cm²
                    'c': float(request.form.get('input_c', 0.000966e-3)),  # Initial concentration in mol/cm³
                    'x_range': request.form.get('input_range', ''),       # Regression range for t⁻½
                }
            }

            # Run background process to compute slope, D, and generate plots
            background_thread = threading.Thread(target=background_task, args=(user_input,))
            background_thread.start()

            return {
                'status': True,
                'message': 'Success, please wait.',
                'version': version
            }

        # -------- Fallback case: Step not supported or invalid --------
        else:
            return jsonify({
                'status': False,
                'message': 'One or more files are not allowed.'
            })

    # Final fallback (for malformed input that didn’t match any module)
    return jsonify({
        'status': True,
        'message': 'Success, please wait.',
        'version': version
    })

# ============================ File Download Endpoints ============================

@app.route('/outputs/<filename>')
def uploaded_file(filename):
    """
    Serves result files located in the global /outputs directory.

    Args:
        filename (str): Name of the file to serve

    Returns:
        Flask Response: Sends the requested file to the browser for download/display.
    """
    return send_from_directory(os.path.join(BASE_DIR, '../outputs'), filename)


@app.route('/outputs/<version>/<filename>')
def uploaded_file2(version, filename):
    """
    Serves result files from a specific versioned output directory.

    This is useful for serving files that belong to a specific data processing session,
    where 'version' is used as a unique identifier for a set of output files.

    Args:
        version (str): Unique version folder name (e.g., 'version_0808_1423')
        filename (str): Name of the file to serve

    Returns:
        Flask Response: Sends the requested file to the browser from a versioned subdirectory.
    """
    return send_from_directory(os.path.join(BASE_DIR, f'../outputs/{version}'), filename)


@app.route('/files/<filename>')
def files(filename):
    """
    Serves example input files from the /data/example_files directory.

    Files are sent as attachments so that users are prompted to download them.

    Args:
        filename (str): Name of the file to serve

    Returns:
        Flask Response: File download response with attachment disposition.
    """
    return send_file(
        os.path.join(BASE_DIR, f'../data/example_files/{filename}'),
        as_attachment=True
    )



def background_task(param):
    """
    Handles asynchronous processing of user-submitted analysis tasks in the background.

    This function dispatches the task based on the selected module (CV, HDV, CA),
    version ID, step number, and associated parameters. It is typically triggered
    in a separate thread after form submission, allowing the web UI to remain responsive.

    Args:
        param (dict): Dictionary containing task metadata:
            - module (str): Module name ('CV', 'HDV', 'CA')
            - version (str): Unique version identifier for the analysis session
            - step (str/int): Current step number in the workflow
            - func (int, optional): CV-specific sub-step identifier (e.g., 4 or 5)
            - data (dict): All user inputs including file info and method-specific parameters
    """
    print("Background task started with parameter:", param)

    # ----------- CV MODULE LOGIC -----------
    if param['module'].upper() == 'CV':
        # Handle CV step 4 or 5 (advanced analysis functions)
        if 'func' in param.keys() and param['func'] > 0:
            all_params = param['data']
            c = CV(version=all_params['version'], files_info=all_params['files_info'])

            if param['func'] == 4:
                c.start4(all_params)  # CV: Electron transfer kinetics (Tafel analysis)
            elif param['func'] == 5:
                c.start5(all_params)  # CV: Charge transfer coefficient (α) computation
        else:
            # Handle CV basic step 1 to 3
            all_params = param['data']
            c = CV(version=param['version'], files_info=all_params['files_info'])

            if param['step'] == '1':
                c.start1(all_params)  # CV: Initial data visualization
            elif param['step'] == '2':
                c.start2(all_params)  # CV: Peak current extraction and Epa/Epc analysis
            elif param['step'] == '3':
                c.start3(all_params)  # CV: Randles-Sevcik or Cottrell validation

    # ----------- HDV MODULE LOGIC -----------
    elif param['module'].upper() == 'HDV':
        d = param['data']
        h = HDV(version=param['version'])

        if param['step'] == '1':
            print("=======")
            print(d)
            h.step1(sigma=d['sigma'])  # HDV: Initial plot and slope estimation
        elif param['step'] == '2':
            # Depending on method, run Levich or Koutecky-Levich analysis
            if d['method'] == '1':
                h.step2_1(d)  # HDV: Levich plot and diffusion coefficient (D)
            else:
                h.step2_2(d)  # HDV: Koutecky-Levich combined plot and kinetics

    # ----------- CA MODULE LOGIC -----------
    elif param['module'].upper() == 'CA':
        if param['step'] == '1':
            d = param['data']
            h = CA(version=param['version'])
            h.step1()
        elif param['step'] == '2':
            d = param['data']
            h = CA(version=param['version'])
            h.step2(d['interval'], d['n'], d['a'], d['c'], d['x_range'])

    print("Background task completed")

if __name__ == "__main__":
    # Entry point for running the Flask development server.
    # - host='0.0.0.0': Allows external access from any IP address.
    # - debug=True: Enables debug mode (auto-reload on code changes, shows detailed errors).
    # - port=8080: Server will listen on port 8080.
    app.run(host='0.0.0.0', debug=True, port=8080)
