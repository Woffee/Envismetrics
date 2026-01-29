"""
BaseModule.py

This file defines the BaseModule class, which serves as the parent class for all electrochemical 
analysis modules in Envismetrics (e.g., CV, HDV, CA).

It provides core functionalities for:
- Managing uploaded user data and file paths
- Reading and converting electrochemical data files (.xlsx, .txt, .csv)
- Maintaining analysis state across steps via JSON storage
- Saving and loading intermediate data structures using pickle

Utility functions are also provided for filename parsing and file format checks.

Last updated: August 8, 2025
License: MIT License

Dependencies:
    - os, json, re: file handling and text parsing
    - pandas: data processing
    - pickle: binary object serialization
    - config: project-specific paths (UPLOAD_FOLDER, etc.)

Example usage:
    base = BaseModule(version="version_0808_1530")
    df_list = base.read_data()
    base.save_result_data(...)
    data = base.pkl_load("some_object.pkl")
"""


import os
import json
import re
import pandas as pd
import pickle
from config import *

# === Utility Functions ===

def reorder(filename):
    """
    Extract RPM value from the filename and return it as an integer.

    Used to sort files based on their rotation speed.
    Returns -1 if no RPM pattern is found, so these files will be placed at the beginning.
    """
    match = re.search(r'(\d+)rpm', filename)
    if match:
        return int(match.group(1))
    else:
        return -1  # Default sorting value if RPM not found


def extract_rpm(filename):
    """
    Extract RPM value from filename.
    Alias for reorder() function for backward compatibility.
    """
    return reorder(filename)


def check_files(files):
    """
    Check whether all input files have supported extensions (.xlsx or .txt).

    Returns:
        True if all files are valid; otherwise, False.
    """
    for f in files:
        ext = f.split('.')[-1].lower()
        if ext not in ['xlsx', 'txt']:
            return False
    return True

# === Base Class for All Modules ===

class BaseModule(object):
    """
    Parent class for CV, HDV, and CA modules.

    Handles:
    - Reading uploaded file metadata
    - Preprocessing raw files into DataFrames
    - Saving/loading intermediate result files (JSON and pickle formats)
    """

    def __init__(self, version):
        """
        Constructor for BaseModule.

        INPUT:
            version (str): Unique identifier for this analysis run (used as folder name).

        EFFECT:
            Initializes paths for input and output data folders, reads result data if available.
        """
        self.version = version
        self.files_info = os.path.join('uploads', version, 'fileinfo.json')
        self.datapath = os.path.join('outputs', self.version)

        if not os.path.exists(self.datapath):
            os.mkdir(self.datapath)

        # Load existing result data (e.g. form1, form2, etc.), or initialize a new dictionary
        self.res_data = self.read_result_data()

    def get_num(self, filename):
        """
        Extract the first integer number found in a filename using regular expressions.

        Parameters:
            filename (str): Input filename string (e.g., '3PFOA400ppm_75075_CA.xlsx').

        Returns:
            int or None: The first numeric match converted to int, or None if no number is found.

        Notes:
            This is commonly used to extract concentration, ID, or numeric prefixes from filenames.
        """
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else None


    def read_result_data(self):
        """
        Read existing result JSON (data.json) from disk, or initialize a new dictionary.

        OUTPUT:
            dict containing previously saved analysis results.
        """
        data_file = os.path.join(self.datapath, 'data.json')
        if os.path.exists(data_file):
            data = json.loads(open(data_file, 'r').read())
        else:
            data = {'version': self.version}
        return data

    def save_result_data(self, data):
        """
        Save the updated result data dictionary to disk as data.json.

        INPUT:
            data (dict): Dictionary to be written as JSON.
        """
        data_file = os.path.join(self.datapath, 'data.json')
        with open(data_file, "w") as json_file:
            json.dump(data, json_file, indent=4)
            print("saved to: {}".format(data_file))


    def read_data(self):
        """
        Load uploaded data files (Excel or TXT) and return them as DataFrame objects.

        Supports:
        - .xlsx (converted to .csv for caching)
        - .txt (semicolon-delimited)
        - .csv (comma-delimited)

        OUTPUT:
            List of dictionaries: [{'filename': original name, 'df': pandas DataFrame}, ...]
        """
        with open(self.files_info, 'r') as f:
            info_list = json.loads(f.read())

        files = []
        real_file_path = {}
        for info in info_list:
            f = info['filename']
            file = info['existed_filename']
            if os.path.isfile(file):
                files.append(f)
                real_file_path[f] = file

        # Sort files by RPM if available
        files = sorted(files, key=reorder)

        data = []
        for f in files:
            file = real_file_path[f]
            print(f)
            df = self._read_file(file)
            if df is not None:
                data.append({'filename': f, 'df': df})
        
        print("data: ", len(data))
        return data

    def _read_file(self, filepath):
        """
        Read a single file and return as DataFrame.
        
        Args:
            filepath (str): Path to the file
            
        Returns:
            DataFrame or None if file format not supported
        """
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.xlsx':
            csv_file = filepath + ".csv"
            if os.path.exists(csv_file):
                return pd.read_csv(csv_file, sep=',')
            else:
                data0 = pd.ExcelFile(filepath)
                df = data0.parse('Sheet1')
                df.to_csv(csv_file, sep=',', index=False)
                print(f"saved csv file to {csv_file}")
                return df
        elif ext == '.txt':
            return pd.read_csv(filepath, delimiter=';')
        elif ext == '.csv':
            return pd.read_csv(filepath, delimiter=',')
        else:
            return None

    def pkl_save(self, data, filename):
        """
        Save arbitrary Python object as a pickle file.

        INPUT:
            data (any): Object to be saved.
            filename (str): Name of file (inside self.datapath) to store the pickle data.
        """
        full_filename = os.path.join(self.datapath, filename)
        with open(full_filename, 'wb') as f:
            pickle.dump(data, f)
            print("saved to: {}".format(full_filename))

    def pkl_load(self, filename):
        """
        Load a Python object from a previously saved pickle file.

        INPUT:
            filename (str): Name of file to be loaded (within self.datapath).
        OUTPUT:
            Loaded Python object, or None if file does not exist.
        """
        full_filename = os.path.join(self.datapath, filename)
        if not os.path.exists(full_filename):
            return None
        with open(full_filename, 'rb') as f:
            loaded_data = pickle.load(f)
        return loaded_data
