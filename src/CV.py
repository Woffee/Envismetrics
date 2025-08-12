"""
CV.py - Cyclic Voltammetry Analysis Module
------------------------------------------

This module is part of the Envismetrics software suite and provides a complete pipeline
for analyzing cyclic voltammetry (CV) data obtained from electrochemical experiments.

Core Functions:
---------------
1. Data Reading and Preprocessing:
   - Reads .csv, .xlsx, or .txt files with scan rate encoded in the filename.
   - Extracts potential and current data for individual cycles.
   - Supports Gaussian smoothing for noise reduction.

2. Step 1: Raw Data Visualization
   - Plots raw and smoothed CV curves.
   - Allows selection of a specific scan cycle for plotting.

3. Step 2: Peak Identification
   - Detects anodic and cathodic peaks in user-defined potential ranges.
   - Stores peak potentials, currents, and calculates Ef and ΔE0 for each scan.

4. Step 3: Randles–Ševčík Analysis
   - Uses linear regression to plot Ip vs. sqrt(scan rate).
   - Calculates diffusion coefficients D for both anodic and cathodic processes.

5. Step 4: Kinetic Parameter Estimation
   - Estimates heterogeneous rate constants (k0) using the Nicholson method.
   - Fits ψ–ΔEp and ψ–v⁻¹/² plots to extract slopes for k₀ calculation.

6. Step 5: Tafel Analysis
   - Two methods implemented to estimate the charge transfer coefficient α.
   - Method 1: based on d(logJ)/dE (Tafel slope).
   - Method 2: based on d(ln(I² / (Ip - I)))/dE.

Features:
---------
- Modular design built on the `BaseModule` foundation.
- Output is saved in versioned folders under `/outputs`.
- Fully automatic plotting and result export as .png images and .json/.pkl files.
- Easily extendable for new electrode systems or devices (Autolab, EC-Lab, etc.)

Usage:
------
To use this module independently, run the script directly:
    python CV.py

You can also use the class methods `start1`, `start2`, `start3`, etc., within your own workflow.

Dependencies:
-------------
- numpy, pandas, matplotlib, scipy, sklearn
- config.py (user-defined settings)
- BaseModule.py (provides save/load utilities)
"""


import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from sklearn.linear_model import LinearRegression
import math
import re
import json
from config import *
from BaseModule import BaseModule
import ast
from datetime import datetime

# Define a color palette for plotting (10 distinct colors)
colors = [
    '#1f77b4',  # tab:blue
    '#ff7f0e',  # tab:orange
    '#2ca02c',  # tab:green
    '#d62728',  # tab:red
    '#9467bd',  # tab:purple
    '#8c564b',  # tab:brown
    '#e377c2',  # tab:pink
    '#7f7f7f',  # tab:gray
    '#bcbd22',  # tab:olive
    '#17becf'   # tab:cyan
]

def find_max(x, y, start, end):
    """
    Find the maximum y-value and corresponding x in a given x-range.

    Parameters:
        x (list or np.array): x-values
        y (list or np.array): y-values
        start (float): lower x-bound
        end (float): upper x-bound

    Returns:
        tuple: (x, y) position of maximum y-value within range
    """
    ma = -1       # Initialize max y with a sentinel; assumes y-values are non-negative
    xx = -1       # Placeholder for x corresponding to max y
    yy = -1       # Placeholder for max y itself

    # Iterate through all x-values to identify those within the specified range
    for i in range(len(x)):
        if start <= x[i] <= end:
            # Update max only if current y-value exceeds previous max
            if y[i] > ma:
                ma = y[i]
                xx = x[i]
                yy = y[i]

    # Return the (x, y) coordinates of the max y-value found in the given range
    return xx, yy


def find_min(x, y, start, end):
    """
    Find the minimum y-value and corresponding x in a given x-range.

    Parameters:
        x (list or np.array): x-values
        y (list or np.array): y-values
        start (float): lower x-bound
        end (float): upper x-bound

    Returns:
        tuple: (x, y) position of minimum y-value within range
    """
    mi = 10000    # Initialize min y with a large number as sentinel
                  # Assumes y-values are significantly smaller than 10^4
    xx = -1       # Placeholder for x corresponding to min y
    yy = -1       # Placeholder for min y itself

    # Iterate through all x-values to check which ones fall in the target range
    for i in range(len(x)):
        if start <= x[i] <= end:
            # Update min only if current y-value is smaller
            if y[i] < mi:
                mi = y[i]
                xx = x[i]
                yy = y[i]

    # Return the (x, y) coordinates of the min y-value found in the specified range
    return xx, yy


def find_y(x, y, xi):
    """
    Find the y-value corresponding to a given x-value (xi).

    Parameters:
        x (list): list of x-values
        y (list): list of y-values
        xi (float): x target

    Returns:
        float: y-value at xi or -1 if not found
    """
    # Linear scan to find the x that exactly matches xi
    for i in range(len(x)):
        if x[i] == xi:
            return y[i]

    # If xi not found in x (e.g., due to floating-point mismatch), return fallback
    return -1


def separater(x, y, left, right):
    """
    Separate a cyclic voltammogram into upper and lower sweep segments.

    Parameters:
        x (pd.Series): potential values
        y (pd.Series): current values
        left (float): left potential bound
        right (float): right potential bound

    Returns:
        tuple: (upperx, lowerx, uppery, lowery)
    """
    upperx = []  # Stores x-values (potential) for forward (upper) scan
    lowerx = []  # Stores x-values for reverse (lower) scan
    uppery = []  # Stores corresponding y-values (current) for upper scan
    lowery = []  # Stores y-values for lower scan

    x = x.tolist()  # Convert input from pd.Series to native Python list
    y = y.tolist()

    # Identify the index of key potential boundaries
    boundary_l = x.index(left)
    boundary_r = x.index(right)

    # Determine scan direction based on index positions of left/right bounds
    # This accommodates both clockwise and counter-clockwise CV loops
    if boundary_r < boundary_l:
        # Sweep goes past the array end and wraps around
        # Upper scan is from left to right via wrap-around
        upperx = x[boundary_l:] + x[:boundary_r + 1]
        uppery = y[boundary_l:] + y[:boundary_r + 1]

        # Lower scan is the remaining part (reverse direction)
        lowerx = x[boundary_r:boundary_l + 1]
        lowery = y[boundary_r:boundary_l + 1]
    else:
        # Standard scan direction (left to right within bounds)
        upperx = x[boundary_l:boundary_r + 1]
        uppery = y[boundary_l:boundary_r + 1]

        # Lower scan wraps around the other side
        lowerx = x[boundary_r:] + x[:boundary_l + 1]
        lowery = y[boundary_r:] + y[:boundary_l + 1]

    # Return separated potential and current values for both scan directions
    return upperx, lowerx, uppery, lowery


def Search_scan_rate(filename):
    """
    Extract scan rate (e.g. 10 from "DMAB_10mVs.csv") from filename.

    Parameters:
        filename (str): input filename

    Returns:
        int: scan rate in mV/s or -1 if not found
    """
    # Look for digits followed by 'mVs' using regex
    match = re.search(r'(\d+)mVs', filename)
    if match:
        return int(match.group(1))  # Convert matched digits to integer
    else:
        return -1  # Return -1 if no match is found (e.g., malformed filename)


def Milad(filename):
    """
    Extract numeric value after 'PFOS_' prefix in filename.

    Parameters:
        filename (str): input filename

    Returns:
        int: extracted number or -1 if not found
    """
    # Look for digits following the prefix 'PFOS_'
    match = re.search(r'PFOS_(\d+)', filename)
    if match:
        return int(match.group(1))  # Extract and return the numeric portion
    else:
        return -1  # Return fallback value if pattern is not found

def read_ec_lab_file(file_path, encoding='utf-8'):
    """
    Read and parse a text file generated by EC-Lab software.

    Parameters:
        file_path (str): Path to the .txt file.
        encoding (str): File encoding, default is 'utf-8'.

    Returns:
        pd.DataFrame: DataFrame with columns ['Ewe/V', '<I>/mA'] containing potential and current values.
    """
    with open(file_path, 'r', encoding=encoding) as file:
        lines = file.readlines()

    # EC-Lab exports typically contain 56 header lines before data begins
    # Header includes metadata, settings, and column descriptions
    num_header_lines = 56

    # Extract only the data lines after the header section
    data_lines = lines[num_header_lines:]

    data = []
    for line in data_lines:
        if line.strip():  # Skip blank lines to avoid parsing errors
            parts = line.split()
            if len(parts) == 2:  # Expect exactly two columns per data line
                ewe, i_mA = parts
                data.append((float(ewe), float(i_mA)))  # Convert strings to floats

    # Return as a pandas DataFrame with electrochemical column names
    return pd.DataFrame(data, columns=['Ewe/V', '<I>/mA'])


def read_auto_lab_file(file):
    """
    Read a file exported from Autolab (either CSV or Excel format).

    Parameters:
        file (str): Path to the file.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    if file.endswith('.csv'):
        # Autolab CSV format uses standard comma delimiter
        df = pd.read_csv(file, delimiter=',')
    else:
        # Excel format (.xlsx) must be read using openpyxl engine
        # Assumes data is stored in the first sheet named 'Sheet1'
        df = pd.read_excel(file, sheet_name='Sheet1', engine='openpyxl')

    return df


def create_file_template_CV(file_name):
    """
    Replace scan rate numbers in filename with a '%d' placeholder.

    This utility enables automated batch processing across multiple scan rates.

    Parameters:
        file_name (str): Original filename (e.g., 'DMAB_10mVs.xlsx')

    Returns:
        str: Template string with placeholder (e.g., 'DMAB_%dmVs.xlsx')
    """
    pattern = r'(\d+)mVs'  # Match any numeric scan rate (e.g., '10mVs')
    template = re.sub(pattern, '%dmVs', file_name)  # Replace with printf-style token
    return template


def make_color_darker(color, factor):
    """
    Darken a given hex color by a certain factor.

    Parameters:
        color (str): Original hex color (e.g., '#1f77b4').
        factor (float): Darkening factor (e.g., 0.8 for 20% darker).

    Returns:
        str: New hex color string.
    """
    # Parse the R, G, B components from the hex string
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

    # Apply scaling factor to darken each channel
    # Ensure the result stays within [0, 255] using max()
    r = max(0, int(r * factor))
    g = max(0, int(g * factor))
    b = max(0, int(b * factor))

    # Return the modified color in hex format (2-digit padded lowercase hex)
    return f'#{r:02x}{g:02x}{b:02x}'



def check_files(files):
    """
    Check if a list of filenames all have valid extensions.

    Parameters:
        files (list of str): List of file paths.

    Returns:
        bool: True if all files are allowed, False otherwise.
    """
    for f in files:
        # Extract file extension (case-insensitive)
        ext = f.split('.')[-1].lower()

        # Validate extension against global ALLOWED_EXTENSIONS (e.g., ['xlsx', 'txt', 'csv'])
        if ext not in ALLOWED_EXTENSIONS:
            return False  # Early return on first invalid file
    return True


def find_max(x, y, start, end):
    """
    Find the (x, y) point with the maximum y-value in a given x range.

    Parameters:
        x (list or np.array): x-values
        y (list or np.array): y-values
        start (float): minimum x value
        end (float): maximum x value

    Returns:
        tuple: (x, y) position of max y in the interval [start, end]
    """
    ma = -1       # Initialize max y-value; assumes non-negative current/potential
    xx = -1       # Placeholder for x-coordinate at max y
    yy = -1       # Placeholder for max y

    # Iterate through all points to find max y within specified x-range
    for i in range(len(x)):
        if start <= x[i] <= end:
            if y[i] > ma:
                ma = y[i]
                xx = x[i]
                yy = y[i]

    # Return coordinates corresponding to max y within range
    return xx, yy


def find_min(x, y, start, end):
    """
    Find the (x, y) point with the minimum y-value in a given x range.

    Parameters:
        x (list or np.array): x-values
        y (list or np.array): y-values
        start (float): minimum x value
        end (float): maximum x value

    Returns:
        tuple: (x, y) position of min y in the interval [start, end]
    """
    mi = 10000  # Sentinel value for initialization; assumes y-values < 10^4
    xx = -1     # Placeholder for x at min y
    yy = -1     # Placeholder for min y

    # Iterate through all points and track the minimum y-value within x-range
    for i in range(len(x)):
        if start <= x[i] <= end:
            if y[i] < mi:
                mi = y[i]
                xx = x[i]
                yy = y[i]

    return xx, yy


def find_y(x, y, xi):
    """
    Find the y-value corresponding to the x-value xi in (x, y) data.

    Parameters:
        x (list or np.array): x-values
        y (list or np.array): y-values
        xi (float): target x

    Returns:
        float: corresponding y-value or -1 if not found
    """
    # Perform exact-match lookup on x-values
    for i in range(len(x)):
        if x[i] == xi:
            return y[i]

    # Return fallback if xi is not present in x (e.g., due to float mismatch)
    return -1


def extract_peak_range(str_peak_range):
    """
    Parse a string containing peak ranges into a list of (start, end) float tuples.

    Example input: '((-1.0, -0.5),(0.0, 0.2))'
    Returns: [(-1.0, -0.5), (0.0, 0.2)]

    Parameters:
        str_peak_range (str): String representing peak regions in format '((a, b),(c, d))'

    Returns:
        list of tuple: List of (start, end) float tuples
    """
    res = []

    # Remove whitespace and split the string into individual (a, b) chunks
    arr = str_peak_range.strip().replace(" ", "").split('),(')

    for a in arr:
        # Clean leading/trailing parentheses and extract start/end values
        start = a.split(",")[0].replace("(", "").replace(")", "").strip()
        end = a.split(",")[1].replace("(", "").replace(")", "").strip()

        # Convert string values to floats and append as tuple
        res.append((float(start), float(end)))

    return res

def separater(x, y, left, right):
    """
    Separate x-y data into forward (upper) and backward (lower) segments of a CV scan.

    Parameters:
        x (pd.Series): x-axis data (e.g., potential)
        y (pd.Series): y-axis data (e.g., current)
        left (float): starting x-value (usually minimum potential)
        right (float): ending x-value (usually maximum potential)

    Returns:
        tuple: (upperx, lowerx, uppery, lowery), each a list of floats
    """
    upperx = []
    lowerx = []
    uppery = []
    lowery = []

    # Convert pandas Series to native Python lists for indexing and concatenation
    x = x.tolist()
    y = y.tolist()

    # Identify the index corresponding to left and right potential limits
    boundary_l = x.index(left)
    boundary_r = x.index(right)

    # Determine scan direction based on index order
    if boundary_r < boundary_l:
        # CV trace wraps around (e.g., reverse scan recorded first)
        # Forward (upper) scan: concatenate the two segments split by wrap
        upperx = x[boundary_l:] + x[:boundary_r + 1]
        uppery = y[boundary_l:] + y[:boundary_r + 1]

        # Backward (lower) scan: segment between right and left
        lowerx = x[boundary_r:boundary_l + 1]
        lowery = y[boundary_r:boundary_l + 1]
    else:
        # Standard scan direction: left → right is forward
        upperx = x[boundary_l:boundary_r + 1]
        uppery = y[boundary_l:boundary_r + 1]

        # Backward scan: wraps around from right back to left
        lowerx = x[boundary_r:] + x[:boundary_l + 1]
        lowery = y[boundary_r:] + y[:boundary_l + 1]

    # Return two sweep segments as (x, y) pairs
    return upperx, lowerx, uppery, lowery


def reorder(filename):
    """
    Extract scan rate from filename for sorting purposes.

    Parameters:
        filename (str): Input filename (e.g., 'data_50mVs.csv')

    Returns:
        int: Scan rate (e.g., 50), or -1 if pattern not found
    """
    # Match integer followed by 'mVs' to identify scan rate
    match = re.search(r'(\d+)mVs', filename)

    # Return scan rate as integer for use in sorting or indexing
    return int(match.group(1)) if match else -1


def filter_files(files):
    """
    Filter a list of filenames to only include files with allowed extensions.

    Parameters:
        files (list of str): List of filenames

    Returns:
        list of str: Valid filenames with extensions in ALLOWED_EXTENSIONS
    """
    res = []

    for f in files:
        # Extract file extension and convert to lowercase for case-insensitive match
        ext = f.split('.')[-1].lower()

        # Retain only files with extensions in the allowed list (e.g., ['csv', 'xlsx', 'txt'])
        if ext in ALLOWED_EXTENSIONS:
            res.append(f)

    return res


def special_log(a_list):
    """
    Custom log10 transformation for an array:
    - log10(x) if x > 0
    - log10(-x) if x < 0
    - 0 if x == 0 (user-defined convention to avoid -inf)

    This function is useful for visualizing data with both positive and negative values
    on a symmetric logarithmic scale (e.g., electrochemical current response).

    Parameters:
        a_list (np.array): Input numeric array

    Returns:
        np.array: Transformed array with log10 applied per element
    """
    a_list_special_log = np.zeros_like(a_list)  # Initialize output array with zeros

    for idx, value in enumerate(a_list):
        if value > 0:
            a_list_special_log[idx] = np.log10(value)
        elif value < 0:
            a_list_special_log[idx] = np.log10(-value)
        else:
            # Avoid math domain error; define log(0) as 0 for plotting consistency
            a_list_special_log[idx] = 0

    return a_list_special_log

def special_ln(a_list):
    """
    Custom natural log transformation for an array:
    - ln(x) if x > 0
    - ln(-x) if x < 0
    - 0 if x == 0

    This function enables visualization or transformation of data containing both
    positive and negative values using a symmetric ln-scale.
    The value 0 is mapped to 0 explicitly to avoid math domain errors.

    Parameters:
        a_list (np.array): Input numeric array

    Returns:
        np.array: Transformed array with ln applied element-wise
    """
    # Initialize the output array with zeros, same shape and type as input
    # This avoids preallocation overhead and ensures correct dtype handling
    a_list_special_ln = np.zeros_like(a_list)

    # Iterate through each element and apply symmetric natural logarithm
    for idx, value in enumerate(a_list):
        if value > 0:
            # Standard natural log for positive values
            a_list_special_ln[idx] = np.log(value)
        elif value < 0:
            # Reflect negative values to apply log transform (abs),
            # useful for bipolar data such as current responses in CV
            a_list_special_ln[idx] = np.log(-value)
        else:
            # For zero input, avoid ln(0) = -inf by assigning 0 as a safe default
            # This is a practical convention for visualization (e.g., symmetric log plots)
            a_list_special_ln[idx] = 0

    return a_list_special_ln

class CV(BaseModule):
    """
    CV Module class for handling cyclic voltammetry (CV) data processing.

    This class provides structured methods for:
    - Reading and parsing CV data files
    - Splitting forward/backward scans
    - Extracting electrochemical features (peaks, onset potentials, etc.)
    - Generating processed outputs for visualization or analysis

    Inherits:
        BaseModule: A base class providing versioning and file handling support.
    """
    def __init__(self, version, files_info):
        """
        Initialize the CV module with versioning and input metadata.

        Parameters:
            version (str): Unique identifier for the processing session.
                           Used to namespace outputs and avoid overwriting.
            files_info (str): Path to JSON file containing list of CV file metadata.
                              Expected to include filenames, sample IDs, and scan rates.
        """
        super().__init__(version)  # Initialize base class (handles shared utilities)
        self.version = version
        self.files_info = files_info

        # Define output directory based on session version
        self.savepath = 'outputs/' + version

        # Ensure output directory exists before writing processed data
        if not os.path.exists(self.savepath):
            os.makedirs(self.savepath)

    # Note: demo_data() and read_csv() are commented out, likely deprecated.
    # demo_data() was used for internal testing with synthetic CV inputs.
    # read_csv() handled local filesystem file loading in early versions.
    # These are excluded in the deployed backend version, where files are uploaded via API.

    def read_data(self):
        """
        Read CV data files described in a JSON metadata list.

        The metadata must include:
            - 'filename': a user-defined or display name (used for sorting)
            - 'existed_filename': full resolved path on disk

        Supported input formats:
            - .xlsx: Excel files (auto-converted to .csv for caching)
            - .csv: Comma-separated plain text
            - .txt: Semicolon-delimited plain text (from EC-Lab)

        Returns:
            dict: Mapping of scan rate (int, in mV/s) → pandas DataFrame of CV data
        """
        # Load file metadata list from JSON file
        with open(self.files_info, 'r') as f:
            info_list = json.loads(f.read())

        files = []              # Stores logical filenames (used for sorting)
        real_file_path = {}     # Maps logical name to actual file path

        for info in info_list:
            f = info['filename']                  # Logical file name (e.g., for display)
            file = info['existed_filename']       # Actual full path to file

            if not os.path.isfile(file):          # Skip missing or invalid paths
                continue

            files.append(f)
            real_file_path[f] = file

        # Sort filenames by scan rate extracted from string (e.g., '20mVs')
        files = sorted(files, key=reorder)
        print("len of files: ", len(files), self.files_info)

        data = {}  # Final output: mapping scan rate → DataFrame

        for f in files:
            file = real_file_path[f]

            if not os.path.isfile(file):
                continue  # Skip if file was deleted or moved after JSON load

            print("filename:", f)

            rpm = Search_scan_rate(f)  # Extract scan rate from filename
            if rpm is None:
                continue  # Skip if scan rate is not found (invalid naming)

            print("rpm:", rpm)

            # === File format handling ===
            if file.endswith(".xlsx"):
                # Try reading from CSV cache to speed up repeated reads
                csv_file = file + ".csv"

                if os.path.exists(csv_file):
                    data[rpm] = pd.read_csv(csv_file, delimiter=',', dtype={'Current range': str})
                else:
                    # Read from Excel and cache as CSV
                    data0 = pd.ExcelFile(file)
                    data[rpm] = data0.parse('Sheet1')
                    data[rpm].to_csv(csv_file, sep=',', index=False)
                    print("saved csv file to {}".format(csv_file))

            elif file.endswith(".txt"):
                # Assume EC-Lab format (.txt) with semicolon separator
                data[rpm] = pd.read_csv(file, delimiter=';', dtype={'Current range': str})

            elif file.endswith(".csv"):
                data[rpm] = pd.read_csv(file, delimiter=',', dtype={'Current range': str})

        print("data: ", len(data))
        return data

    def check_columns(self, data):
        """
        Validate that all expected columns exist in each DataFrame.

        Expected columns:
            - 'WE(1).Current (A)'
            - 'WE(1).Potential (V)'
            - 'Scan' (cycle number)

        Parameters:
            data (dict): Dictionary mapping scan rates to DataFrames

        Returns:
            str: Empty if valid; otherwise an error string listing missing columns
        """
        cols = ['WE(1).Current (A)', 'WE(1).Potential (V)', 'Scan']
        missing_cols = []

        for scan_rate, df in data.items():
            for col in cols:
                if col not in df.columns:
                    missing_cols.append(col)

        if len(missing_cols) > 0:
            return "error: Missing columns: " + ", ".join(missing_cols)

        return ''


    def start1_figure(self, data, apply_sigma=False, all_params={}):
        """
        Plot CV curves from the input data, with optional Gaussian smoothing.

        There are two parts:
        1. Plot a single cycle (Scan number) from each scan rate.
        2. Plot all raw data (all cycles) for comparison.

        Parameters:
            data (dict): Dictionary mapping scan_rate → DataFrame
            apply_sigma (bool): Whether to apply Gaussian filter for smoothing
            all_params (dict): Includes user settings like:
                               - 'sigma' (float): std dev of Gaussian kernel
                               - 'cycle' (int): cycle number to extract

        Returns:
            tuple: (path_to_filtered_or_raw_image, path_to_all_cycles_image)
        """
        cycle = int(all_params['cycle'])
        sigma = float(all_params['sigma'])

        # === First plot: only the specified scan cycle ===
        for scan_rate, df0 in data.items():
            # Filter only the selected cycle
            df = df0[df0['Scan'] == cycle]
            E = df['WE(1).Potential (V)']
            I = df['WE(1).Current (A)']

            # Split into forward and backward scans using potential direction
            upperE, lowerE, upperI, lowerI = separater(E, I, min(E), max(E))

            if apply_sigma:
                # Apply Gaussian filter with specified sigma for smoothing
                smoothed_upperI = gaussian_filter(upperI, sigma=sigma)
                smoothed_lowerI = gaussian_filter(lowerI, sigma=sigma)
            else:
                # No smoothing applied; use raw current
                smoothed_upperI = upperI
                smoothed_lowerI = lowerI

            # Reconstruct full E–I curve from upper and lower halves
            I = np.concatenate((smoothed_upperI, smoothed_lowerI))
            E = upperE + lowerE

            # Scatter plot per scan rate
            plt.scatter(E, I, label=scan_rate, s=1)

        plt.xlabel('Applied potential/V')
        plt.ylabel('Current/A')
        plt.legend()

        # Determine output filename based on smoothing flag
        if apply_sigma:
            to_file1 = os.path.join(self.savepath, "form1_sigma{}.png".format(sigma))
        else:
            to_file1 = os.path.join(self.savepath, "form1_original.png")

        # Save first figure (selected cycle only)
        plt.savefig(to_file1)
        plt.close()

        # === Second plot: full CV data (all cycles) ===
        for scan_rate, df0 in data.items():
            E = df0['WE(1).Potential (V)']
            I = df0['WE(1).Current (A)']
            plt.scatter(E, I, label=scan_rate, s=1)

        plt.xlabel('Applied potential/V')
        plt.ylabel('Current/A')
        plt.legend()

        to_file3 = os.path.join(self.savepath, "form1_cycle.png")
        plt.savefig(to_file3)
        plt.close()

        return to_file1, to_file3


    def start1(self, all_params):
        """
        Top-level entry point for the CV 'Form 1' plotting workflow.

        This method:
        - Loads all input data
        - Checks for structural integrity
        - Generates both raw and smoothed CV plots for the specified cycle
        - Saves results to JSON alongside image paths

        Parameters:
            all_params (dict): Includes:
                - 'sigma' (float): Gaussian filter parameter
                - 'cycle' (int): Cycle number to analyze

        Returns:
            dict: A status dictionary with processing results, image paths, and logs
        """
        sigma = float(all_params['sigma'])
        status_msg = ''

        # === Step 1: Read and validate input data ===
        data = self.read_data()
        if data is None:
            status_msg = 'error: one or more files are not allowed.'

        # Construct string of available scan rates
        mVs_list_str = ', '.join(["'{}mVs'".format(k) for k in data])

        # Check required columns in each input file
        if status_msg == '':
            status_msg = self.check_columns(data)

        # === Step 2: Generate plots ===
        if status_msg == '':
            try:
                # Plot raw cycle curves (form1_original.png)
                to_file1, to_file3 = self.start1_figure(data, apply_sigma=False, all_params=all_params)

                # Plot smoothed version using Gaussian filter (form1_sigmaX.png)
                to_file2, _ = self.start1_figure(data, apply_sigma=True, all_params=all_params)

            except Exception as e:
                # Catch any unexpected processing errors
                status_msg = str(e)

        # === Step 3: Write output to persistent storage ===
        data_file = os.path.join('outputs', self.version, 'data.json')

        if os.path.exists(data_file):
            data = json.loads(open(data_file, 'r').read())
        else:
            data = {'version': self.version}

        # Ensure 'CV' section exists in data file
        if 'CV' not in data:
            data['CV'] = {}

        if status_msg == '':
            # All went well → Save results to JSON
            all_params['uploaded_files'] = []
            data['CV']['form1'] = {
                'status': 'done',
                'input': all_params,
                'output': {
                    'mVs_list_str': mVs_list_str,
                    'file1': to_file1.split("/")[-1],
                    'file2': to_file2.split("/")[-1],
                    'file3': to_file3.split("/")[-1],
                }
            }
            with open(data_file, 'w') as f:
                f.write(json.dumps(data))
                print("saved to: {}".format(data_file))

            return {
                'status': True,
                'version': self.version,
                'message': 'Success',
                'data': data
            }
        else:
            # Some failure occurred → Report and record in output
            all_params['uploaded_files'] = []
            data['CV']['form1'] = {
                'status': status_msg,
                'input': all_params
            }
            with open(data_file, 'w') as f:
                f.write(json.dumps(data))
                print("saved to: {}".format(data_file))

            return {
                'status': False,
                'version': self.version,
                'message': status_msg,
                'data': data
            }

    def start2_prepare(self, data, method, p1_start, p1_end, p2_start, p2_end):
        """
        Prepare peak data for analysis from a range of CV scans.

        For each scan rate and scan cycle (Scan 3 to 11), this function:
        - Separates upper and lower branches of the CV curve
        - Optionally applies Gaussian smoothing to current signals
        - Identifies oxidation (anodic) and reduction (cathodic) peak positions
        - Computes ΔEp (peak potential separation) and Ef (midpoint potential)

        Parameters:
            data (dict): Dictionary mapping scan_rate → DataFrame
            method (str): Reserved for future use (e.g., 'Max', 'Mean')
            p1_start (float): Start of oxidation peak search window
            p1_end (float): End of oxidation peak search window
            p2_start (float): Start of reduction peak search window
            p2_end (float): End of reduction peak search window

        Returns:
            tuple of lists: (Ef1, DelE01, Ea1, Ec1, Ia1, Ic1, Ic1, Scan_Rate1)
                Ef1: Midpoint potentials
                DelE01: ΔEp values
                Ea1, Ec1: Peak positions (V)
                Ia1, Ic1: Peak currents (A)
                Scan_Rate1: Associated scan rates (mV/s)
        """
        Ef1 = []
        DelE01 = []
        Ea1 = []
        Ec1 = []
        Ia1 = []
        Ic1 = []
        Scan_Rate1 = []

        for jj, df0 in data.items():
            j = int(jj.replace("mVs", ""))  # Extract scan rate as integer
            name = str(j) + "mV"            # Label for plotting/debug
            num = j

            # Temporary lists to store per-cycle peaks for this scan rate
            Ea1j = []
            Ec1j = []
            Ia1j = []
            Ic1j = []

            # Analyze scan cycles 3 through 11
            for i in range(3, 12):
                df = df0[df0['Scan'] == i]
                Ui = np.array(df['WE(1).Potential (V)'])
                Ii = np.array(df['WE(1).Current (A)'])

                # Separate forward and backward scans
                upperU, lowerU, upperI, lowerI = separater(Ui, Ii, min(Ui), max(Ui))

                # Optional: apply Gaussian filter to smooth noise
                apply_gaussian_filter = False  # Set True if needed
                if apply_gaussian_filter:
                    smoothed_upperI = gaussian_filter(upperI, sigma=1)
                    smoothed_lowerI = gaussian_filter(lowerI, sigma=1)
                else:
                    smoothed_upperI = upperI
                    smoothed_lowerI = lowerI

                # Extract peak positions from user-defined windows
                top_x1, top_y1 = find_max(upperU, smoothed_upperI, p1_start, p1_end)
                bottom_x1, bottom_y1 = find_min(lowerU, smoothed_lowerI, p2_start, p2_end)

                # Compute ΔEp and midpoint potential
                DelE01i = top_x1 - bottom_x1
                Ef1i = (top_x1 + bottom_x1) / 2

                # Record results
                Ea1.append(top_x1)
                Ec1.append(bottom_x1)
                Ia1.append(find_y(upperU, smoothed_upperI, top_x1))
                Ic1.append(find_y(lowerU, smoothed_lowerI, bottom_x1))
                DelE01.append(DelE01i)
                Ef1.append(Ef1i)
                Scan_Rate1.append(num)

                # Also store per-cycle peaks for visualization if needed
                Ea1j.append(top_x1)
                Ec1j.append(bottom_x1)
                Ia1j.append(find_y(upperU, smoothed_upperI, top_x1))
                Ic1j.append(find_y(lowerU, smoothed_lowerI, bottom_x1))

                # Debug/plotting (commented out):
                # plt.scatter(upperU, smoothed_upperI, s=2, c='#1f77b4')
                # plt.scatter(lowerU, smoothed_lowerI, s=2, c='#ff7f0e')
                # plt.scatter(Ea1j, Ia1j, s=10, c='r')
                # plt.scatter(Ec1j, Ic1j, s=10, c='r')

            # Return all results as tuple of lists
            return (Ef1, DelE01, Ea1, Ec1, Ia1, Ic1, Ic1, Scan_Rate1)


    def start2_figure1(self, data, Ea_res, sigma=10, pr1=None, pr2=None):
        """
        Plot one representative CV curve with red markers at identified peak positions.

        Parameters:
            data (dict): Dictionary mapping scan_rate → DataFrame
            Ea_res (list): Peak result tuples from `start2_prepare()`
            sigma (float): Standard deviation for Gaussian filter (smoothing)
            pr1 (list): List of (start, end) tuples for oxidation peak search window
            pr2 (list): List of (start, end) tuples for reduction peak search window

        Returns:
            str: Path to saved image file (PNG)
        """
        # Use the first available scan rate as the representative example
        df0 = None
        for k, d in data.items():
            df0 = d
            break

        img_path = os.path.join(self.datapath, "CV_form2_p1.png")

        # Select cycle 6 (mid-scan) for visualization
        df = df0[df0['Scan'] == 6]
        Ui = np.array(df['WE(1).Potential (V)'])
        Ii = np.array(df['WE(1).Current (A)'])

        upperU, lowerU, upperI, lowerI = separater(Ui, Ii, min(Ui), max(Ui))

        apply_gaussian_filter = True  # Always apply smoothing here for clarity

        if apply_gaussian_filter:
            smoothed_upperI = gaussian_filter(upperI, sigma=sigma)
            smoothed_lowerI = gaussian_filter(lowerI, sigma=sigma)
        else:
            smoothed_upperI = upperI
            smoothed_lowerI = lowerI

        # Plot smoothed forward and backward scans
        plt.scatter(upperU, smoothed_upperI, s=1, c='#1f77b4')
        plt.scatter(lowerU, smoothed_lowerI, s=1, c='#ff7f0e')

        # For each peak range, extract and plot peak markers
        for pp, (Ef1, DelE01, Ea1, Ec1, Ia1, Ic1, _, _) in enumerate(Ea_res):
            p1_start, p1_end = pr1[pp]
            p2_start, p2_end = pr2[pp]

            # Extract peak positions from specified windows
            top_x1, top_y1 = find_max(upperU, smoothed_upperI, p1_start, p1_end)
            bottom_x1, bottom_y1 = find_min(lowerU, smoothed_lowerI, p2_start, p2_end)

            # Add red dots to indicate peaks
            plt.scatter(top_x1, top_y1, s=10, c='r')
            plt.scatter(bottom_x1, bottom_y1, s=10, c='r')

        plt.xlabel('Applied potential/V')
        plt.ylabel('Current/A')
        # plt.ylim(-2e-5,2e-5)
        plt.savefig(img_path)
        plt.close()
        return img_path

    def start2_figure2(self, data, Ea_res, sigma=10, pr1=None, pr2=None):
        """
        Plot full CV curves (smoothed) with red dots showing peak positions.

        Parameters:
            data (dict): Dictionary mapping scan_rate => DataFrame
            Ea_res (list): List of peak result tuples
            sigma (float): Smoothing factor for Gaussian filter
            pr1, pr2: Optional peak range data (unused in this version)

        Returns:
            str: Path to saved image
        """
        img_path = os.path.join(self.datapath, "CV_form2_p2.png")

        # Plot all CV curves with smoothing
        for jj, df0 in data.items():
            j = int(jj.replace("mVs", ""))
            scan_rate = str(j) + "mV"

            E = df0['WE(1).Potential (V)']
            I = df0['WE(1).Current (A)']

            # Separate forward and backward scan segments
            upperE, lowerE, upperI, lowerI = separater(E, I, min(E), max(E))

            # Apply Gaussian smoothing for better visualization
            smoothed_upperI = gaussian_filter(upperI, sigma=sigma)
            smoothed_lowerI = gaussian_filter(lowerI, sigma=sigma)

            # Concatenate full curve and plot
            E_combined = upperE + lowerE
            I_combined = np.concatenate((smoothed_upperI, smoothed_lowerI))
            plt.scatter(E_combined, I_combined, label=scan_rate, s=1)

        # Overlay extracted peak positions as red markers
        for pp, (Ef1, DelE01, Ea1, Ec1, Ia1, Ic1, _, _) in enumerate(Ea_res):
            plt.scatter(Ea1, Ia1, s=10, c='r')
            plt.scatter(Ec1, Ic1, s=10, c='r')

        plt.xlabel('Applied potential/V')
        plt.ylabel('Current/A')
        plt.legend()
        plt.savefig(img_path)
        plt.close()
        return img_path


    def start2(self, all_params):
        """
        Main function for peak extraction and analysis in CV form2.

        This function:
        1. Parses user-defined input ranges and parameters
        2. Loads CV data from selected files
        3. Iteratively analyzes multiple peak regions
        4. Extracts and stores key electrochemical parameters (Ea, Ec, Ef, ΔEp, Ia, Ic)

        Parameters:
            all_params (dict): Contains user-specified settings for peak analysis, including:
                - peak_range_top, peak_range_bottom: strings defining (start, end) ranges
                - scan_rate_from / after: slice indices for which scan rates to include
                - cycle_range: range of scan cycles to use
                - example_scan / cycle: identifiers for figure generation

        Returns:
            None (prints progress and updates internal peak_info dictionary)
        """
        status_msg = ''
        try:
            print(all_params)

            # --- 1. Parse user input parameters ---
            method = all_params['method']
            peak_info = {}

            # Convert string inputs to Python lists of tuples/ints
            peak_range_ox = ast.literal_eval(all_params['peak_range_top'])
            peak_range_re = ast.literal_eval(all_params['peak_range_bottom'])
            discard_scan_start = ast.literal_eval(all_params['scan_rate_from'])
            discard_scan_end = ast.literal_eval(all_params['scan_rate_after'])
            cycle_range_input = ast.literal_eval(all_params['cycle_range'])
            cycle_range = range(cycle_range_input[0], cycle_range_input[1])

            example_scan_rate = all_params['example_scan']
            example_cycle = all_params['example_cycle']

            # Use sigma from previous form1 input for consistent smoothing
            sigma = float(self.res_data['CV']['form1']['input']['sigma'])

            # --- 2. Read file metadata and resolve real paths ---
            with open(self.files_info, 'r') as f:
                info_list = json.loads(f.read())
            files = []
            real_file_path = {}
            for info in info_list:
                f = info['filename']
                ef = info['existed_filename']
                if not os.path.isfile(ef):
                    continue
                files.append(f)
                real_file_path[f] = ef

            # --- 3. Sort and filter by device type ---
            files = sorted(files, key=Search_scan_rate)
            device = 'Autolab'
            if device == 'Autolab':
                Filter_files = [file for file in files if file.endswith('.xlsx') or file.endswith('.csv')]
            elif device == 'EClab':
                Filter_files = [file for file in files if file.endswith('.txt')]
            else:
                Filter_files = []
                print('device not found in library')

            # Create template string for variable naming
            file_template = os.path.splitext(create_file_template_CV(Filter_files[0]))[0]

            # --- 4. Load data into memory and assign dynamic variable names ---
            data_list = []
            myglobals = {}
            for file in Filter_files:
                scan_rate = Search_scan_rate(file)
                df = read_auto_lab_file(real_file_path[file])
                var_name = file_template % scan_rate  # e.g., HDV_20mVs_CV
                myglobals[var_name] = df
                data_list.append(var_name)
                print(var_name)

            # --- 5. Loop over all peak regions (z = peak set index) ---
            for z in range(len(peak_range_ox)):
                # Initialize containers for this peak window
                for param in ['Ef', 'DelE0', 'Ea', 'Ec', 'Ia', 'Ic', 'Scan_Rate']:
                    peak_info[f'{param}{z}'] = []

                print(f'\n\033[1mFigure Set for Peak{z + 1}:\033[0m')
                plt.figure()

                # Determine which subset of scan rates to use for this peak window
                selected_data_list = data_list[discard_scan_start[z]:discard_scan_end[z]]
                print("\033[1mGoing to process the following files:\033[0m")
                for file in selected_data_list:
                    print(file)
                print("\n")

                # --- 6. Loop over files and extract peaks ---
                for var_name in selected_data_list:
                    df = myglobals[var_name]
                    print(var_name)
                    scan_rate = Search_scan_rate(var_name)

                    for i in cycle_range:
                        cycle_df = df[df['Scan'] == i]
                        if len(cycle_df) == 0:
                            continue

                        # Extract potential and current for this scan cycle
                        Ui = np.array(cycle_df['WE(1).Potential (V)'])
                        Ii = np.array(cycle_df['WE(1).Current (A)'])

                        # Separate into upper (oxidation) and lower (reduction) branches
                        upperU, lowerU, upperI, lowerI = separater(Ui, Ii, min(Ui), max(Ui))

                        # Optional: apply Gaussian smoothing to reduce noise
                        apply_gaussian_filter = False
                        if apply_gaussian_filter:
                            smoothed_upperI = gaussian_filter(upperI, sigma=1)
                            smoothed_lowerI = gaussian_filter(lowerI, sigma=1)
                        else:
                            smoothed_upperI = upperI
                            smoothed_lowerI = lowerI

                        # Extract peak positions and currents within user-specified window
                        top_x = find_max(upperU, smoothed_upperI, peak_range_ox[z][0], peak_range_ox[z][1])[0]
                        bottom_x = find_min(lowerU, smoothed_lowerI, peak_range_re[z][0], peak_range_re[z][1])[0]

                        DelE02i = top_x - bottom_x
                        Ef2i = (top_x + bottom_x) / 2

                        # Record extracted values
                        peak_info[f'Ea{z}'].append(top_x)
                        peak_info[f'Ia{z}'].append(find_y(upperU, smoothed_upperI, top_x))
                        peak_info[f'Ec{z}'].append(bottom_x)
                        peak_info[f'Ic{z}'].append(find_y(lowerU, smoothed_lowerI, bottom_x))
                        peak_info[f'DelE0{z}'].append(DelE02i)
                        peak_info[f'Ef{z}'].append(Ef2i)
                        peak_info[f'Scan_Rate{z}'].append(scan_rate)

            # Log completion timestamp
            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            print("Done:", formatted_time)

            def show_info(peak_info, n=5):
                """
                Display the first n values from each list in the peak_info dictionary.

                Useful for debugging peak extraction results by printing the length
                and head of each result list.

                Parameters:
                    peak_info (dict): Dictionary containing lists of extracted peak parameters.
                    n (int): Number of values to show from each list (default: 5).
                """
                for key, values in peak_info.items():
                    display_length = min(len(values), n)
                    print(f'{key}: {[len(values)]} {values[:display_length]}')


            # Print summary of peak search results
            show_info(peak_info)


            # Compute and display the mean value of Ef for each peak range
            mean_Ef = {}
            for i in range(len(peak_range_ox)):
                Ef = np.mean(peak_info[f'Ef{i}'])
                mean_Ef[f'Ef{i + 1}'] = Ef

            for key, value in mean_Ef.items():
                print(f"{key}: {value}")


            # === Visualization: Plot all peak positions on full CV traces ===

            plt.figure()
            for data_i in data_list:
                df = myglobals[data_i]  # Access stored DataFrame from memory
                print(data_i)
                U = df['WE(1).Potential (V)']
                I = df['WE(1).Current (A)']
                scan_rate = Search_scan_rate(data_i)
                plt.scatter(U, I, label=f'{scan_rate} mV', s=1, c='#1f77b4')  # Raw CV traces

            # Overlay peak markers on full CV data
            for i in range(len(peak_range_ox)):
                Ea = peak_info[f'Ea{i}']
                Ec = peak_info[f'Ec{i}']
                Ia = peak_info[f'Ia{i}']
                Ic = peak_info[f'Ic{i}']
                plt.scatter(Ea, Ia, s=10, c='r')  # Oxidation peaks
                plt.scatter(Ec, Ic, s=10, c='r')  # Reduction peaks

            plt.xlabel('Applied potential/V')
            plt.ylabel('Current/A')
            plt.legend()
            to_file1 = os.path.join(self.datapath, "CV_step2_p1.png")
            plt.savefig(to_file1)
            plt.close()


            # === Visualization: Plot selected cycle of example scan with peaks ===

            search_key = str(example_scan_rate) + "mV"
            matching_data = [name for name in data_list if search_key in name]
            plt.figure()

            if matching_data:
                df = myglobals[matching_data[0]]
                df = df[df['Scan'] == int(example_cycle)]

                U = df['WE(1).Potential (V)']
                I = df['WE(1).Current (A)']
                upperU, lowerU, upperI, lowerI = separater(U, I, min(U), max(U))

                # Apply optional smoothing
                if apply_gaussian_filter:
                    smoothed_upperI = gaussian_filter(upperI, sigma=1)
                    smoothed_lowerI = gaussian_filter(lowerI, sigma=1)
                else:
                    smoothed_upperI = upperI
                    smoothed_lowerI = lowerI

                # Plot CV segment
                plt.scatter(upperU, smoothed_upperI, s=1, c='#1f77b4')
                plt.scatter(lowerU, smoothed_lowerI, s=1, c='#ff7f0e')

                # Highlight extracted peaks
                for z in range(len(peak_range_ox)):
                    top_x, top_y = find_max(upperU, smoothed_upperI, peak_range_ox[z][0], peak_range_ox[z][1])
                    bottom_x, bottom_y = find_min(lowerU, smoothed_lowerI, peak_range_re[z][0], peak_range_re[z][1])
                    plt.scatter(top_x, top_y, s=20, c='r')
                    plt.scatter(bottom_x, bottom_y, s=20, c='r')

            plt.xlabel('Applied potential/V')
            plt.ylabel('Current/A')
            to_file2 = os.path.join(self.datapath, "CV_step2_p2.png")
            plt.savefig(to_file2)
            plt.close()


            # === Save temporary analysis results to a .pkl file ===
            tmp_res_filename = "form2_res.pkl"
            tmp_res = {
                'peak_range_ox': peak_range_ox,
                'peak_info': peak_info,
                'data_list': data_list,
                'globals': myglobals,
            }
            self.pkl_save(tmp_res, tmp_res_filename)

        except Exception as e:
            status_msg = str(e)


        # === Save final results into result JSON ===

        data = self.res_data
        if 'CV' not in data.keys():
            data['CV'] = {}

        if status_msg == '':
            data['CV']['form2'] = {
                'status': 'done',
                'input': all_params,
                'output': {
                    'img1': to_file1.split('/')[-1],
                    'img2': to_file2.split('/')[-1],
                }
            }
            self.save_result_data(data)

            return {
                'status': True,
                'version': self.version,
                'message': 'Success',
                'data': data
            }
        else:
            data['CV']['form2'] = {
                'status': status_msg,
                'input': all_params,
            }
            self.save_result_data(data)

            return {
                'status': False,
                'version': self.version,
                'message': status_msg,
                'data': data
            }

    def start3(self, all_params):
        """
        Perform Randles–Ševčík analysis to calculate diffusion coefficients (D) based on scan rate and peak current.

        Parameters:
            all_params (dict): Dictionary containing electrochemical parameters:
                - 'n': number of electrons transferred
                - 'c': concentration of redox species in mol/cm³
                - 't': temperature in K
                - 'd': electrode diameter in cm

        Returns:
            dict: Contains success status, version, message, and output image for Randles–Ševčík plot
        """
        status_msg = ''
        try:
            form2_res = self.pkl_load("form2_res.pkl")
            peak_range_ox = form2_res['peak_range_ox']
            peak_info = form2_res['peak_info']

            # input calculate parameter
            # n = 1  # number of electron transfer
            # C = 2e-6  # initial concertration in mol/cm3
            # T = 298.15  # temperature in K
            n = int(all_params['n'])
            C = float(all_params['c'])
            T = float(all_params['t'])
            electrode_dia = float(all_params['d'])
            # print(all_params)

            # Diameter in cm
            # electrode_dia = 0.30  # electorde diameter in cm
            A_Real = np.pi * (electrode_dia / 2) ** 2
            print('Electrode Surface Area:', A_Real)


            # constant number don't change
            F = 96485.33212
            R = 8.314462618

            # Randles–Ševčík plot sprt scan_rate vs Ipeak
            D_cal = []
            D_ox = []
            D_re = []
            plt.figure()
            for i in range(len(peak_range_ox)):
                scan_rate_05 = ((np.array(peak_info[f'Scan_Rate{i}'])) / 1000) ** 0.5
                scan_rate = np.array(peak_info[f'Scan_Rate{i}']) / 1000

                La = LinearRegression().fit(np.array(scan_rate_05).reshape(-1, 1),
                                            np.array(peak_info[f'Ia{i}']).reshape(-1, 1))
                Ia = La.intercept_[0]
                Sa = La.coef_[0][0]

                Lc = LinearRegression().fit(np.array(scan_rate_05).reshape(-1, 1),
                                            np.array(peak_info[f'Ic{i}']).reshape(-1, 1))
                Ic = Lc.intercept_[0]
                Sc = Lc.coef_[0][0]

                #     Ia_sim = 0.4463 * (n * F * C * A_Real * ((n * F * scan_rate * D[i]) / (R * T)) ** 0.5) + Ia
                #     Ic_sim = -0.4463 * (n * F * C * A_Real * ((n * F * scan_rate * D[i]) / (R * T)) ** 0.5) + Ic

                sim_x = np.linspace(min(scan_rate_05), max(scan_rate_05), 100)
                sim_ya = Sa * sim_x + Ia
                sim_yc = Sc * sim_x + Ic

                D_cala = (Sa / (0.446 * n * F * C * A_Real * ((n * F) / (R * T)) ** 0.5)) ** 2
                D_calc = (Sc / (0.446 * n * F * C * A_Real * ((n * F) / (R * T)) ** 0.5)) ** 2

                D_cal.append((D_cala, D_calc))
                D_ox.append(D_cala)
                D_re.append(D_calc)

                darker_color = make_color_darker(colors[i], 0.5)
                plt.scatter(scan_rate_05, peak_info[f'Ia{i}'], label=f'Exp-Ox{i + 1}', s=10, color=colors[i])
                #     plt.scatter(scan_rate_05,Ia_sim,label=f'Sim-Ox{i+1}',s=10, marker='^', color = darker_color)

                plt.plot(sim_x, sim_ya, color='red')
                plt.xlabel('Scanning Rate ν^1/2')
                plt.ylabel('Current Peak/A')
                plt.legend()

                plt.scatter(scan_rate_05, peak_info[f'Ic{i}'], label=f'Exp-Re{i + 1}', s=10, color=colors[i+1])
                #     plt.scatter(scan_rate_05,Ic_sim,label=f'Sim-Re{i+1}',s=10, marker='^', color = darker_color)
                plt.plot(sim_x, sim_yc, color='red')
                plt.xlabel('Scanning Rate ν^1/2')
                plt.ylabel('Current Peak/A')
                plt.legend()

            to_file1 = os.path.join(self.datapath, "CV_step3_p1.png")
            plt.savefig(to_file1)
            plt.close()
        except  Exception as e:
            status_msg = str(e)

        data = self.res_data

        if 'CV' not in data.keys():
            data['CV'] = {}

        if status_msg == '':
            data['CV']['form3'] = {
                'status': 'done',
                'input': all_params,
                'output': {
                    'img1': to_file1.split('/')[-1],
                }
            }
            self.save_result_data(data)

            return {
                'status': True,
                'version': self.version,
                'message': 'Success',
                'data': data
            }
        else:
            data['CV']['form3'] = {
                'status': status_msg,
                'input': all_params
            }
            self.save_result_data(data)

            return {
                'status': False,
                'version': self.version,
                'message': status_msg,
                'data': data
            }

    def start3(self, all_params):
        """
        Perform Randles–Ševčík analysis to calculate diffusion coefficients (D)
        using peak current vs. scan rate^0.5 relationship.

        Parameters:
            all_params (dict): Dictionary containing electrochemical parameters:
                - 'n': Number of electrons transferred
                - 'c': Concentration of redox species in mol/cm³
                - 't': Temperature in Kelvin
                - 'd': Electrode diameter in cm

        Returns:
            dict: Contains status, version, message, and output plot file for Randles–Ševčík analysis
        """
        status_msg = ''
        try:
            # === Load preprocessed peak data from form2 ===
            form2_res = self.pkl_load("form2_res.pkl")
            peak_range_ox = form2_res['peak_range_ox']
            peak_info = form2_res['peak_info']

            # === Parse user-input parameters ===
            n = int(all_params['n'])                     # number of electrons
            C = float(all_params['c'])                   # concentration of redox species (mol/cm^3)
            T = float(all_params['t'])                   # temperature in Kelvin
            electrode_dia = float(all_params['d'])       # electrode diameter (cm)
            A_Real = np.pi * (electrode_dia / 2) ** 2    # calculate geometric electrode surface area
            print('Electrode Surface Area:', A_Real)

            # === Physical constants ===
            F = 96485.33212                              # Faraday constant (C/mol)
            R = 8.314462618                              # Gas constant (J/mol/K)

            # === Prepare figure for Randles–Ševčík plot ===
            D_cal = []     # list of calculated D values (paired: oxidation and reduction)
            D_ox = []      # D values for oxidation peaks
            D_re = []      # D values for reduction peaks
            plt.figure()

            # === Loop over each redox peak (e.g., Peak 1, Peak 2...) ===
            for i in range(len(peak_range_ox)):
                # Convert scan rate to V/s and take square root (as required by Randles–Ševčík)
                scan_rate_05 = ((np.array(peak_info[f'Scan_Rate{i}'])) / 1000) ** 0.5
                scan_rate = np.array(peak_info[f'Scan_Rate{i}']) / 1000

                # === Linear regression of Ipa vs sqrt(scan rate) for oxidation ===
                La = LinearRegression().fit(scan_rate_05.reshape(-1, 1), np.array(peak_info[f'Ia{i}']).reshape(-1, 1))
                Ia = La.intercept_[0]
                Sa = La.coef_[0][0]

                # === Linear regression of Ipc vs sqrt(scan rate) for reduction ===
                Lc = LinearRegression().fit(scan_rate_05.reshape(-1, 1), np.array(peak_info[f'Ic{i}']).reshape(-1, 1))
                Ic = Lc.intercept_[0]
                Sc = Lc.coef_[0][0]

                # === Simulated curves (optional) ===
                sim_x = np.linspace(min(scan_rate_05), max(scan_rate_05), 100)
                sim_ya = Sa * sim_x + Ia
                sim_yc = Sc * sim_x + Ic

                # === Randles–Ševčík Equation Rearranged to Calculate D ===
                # I_p = 0.446 × n × F × A × C × (nFvD / RT)^0.5
                D_cala = (Sa / (0.446 * n * F * C * A_Real * ((n * F) / (R * T)) ** 0.5)) ** 2
                D_calc = (Sc / (0.446 * n * F * C * A_Real * ((n * F) / (R * T)) ** 0.5)) ** 2

                # Store calculated D values
                D_cal.append((D_cala, D_calc))
                D_ox.append(D_cala)
                D_re.append(D_calc)

                # === Plot experimental and fitted oxidation/reduction curves ===
                darker_color = make_color_darker(colors[i], 0.5)
                plt.scatter(scan_rate_05, peak_info[f'Ia{i}'], label=f'Exp-Ox{i + 1}', s=10, color=colors[i])
                plt.plot(sim_x, sim_ya, color='red')

                plt.scatter(scan_rate_05, peak_info[f'Ic{i}'], label=f'Exp-Re{i + 1}', s=10, color=colors[i+1])
                plt.plot(sim_x, sim_yc, color='red')

            # === Final plot settings and save ===
            plt.xlabel('Scan Rate $\\nu^{1/2}$ (V$^{1/2}$/s$^{1/2}$)')
            plt.ylabel('Peak Current (A)')
            plt.legend()
            to_file1 = os.path.join(self.datapath, "CV_step3_p1.png")
            plt.savefig(to_file1)
            plt.close()

        except Exception as e:
            status_msg = str(e)

        # === Save Results ===
        data = self.res_data
        if 'CV' not in data:
            data['CV'] = {}

        if status_msg == '':
            data['CV']['form3'] = {
                'status': 'done',
                'input': all_params,
                'output': {'img1': to_file1.split('/')[-1]},
            }
            self.save_result_data(data)
            return {'status': True, 'version': self.version, 'message': 'Success', 'data': data}
        else:
            data['CV']['form3'] = {
                'status': status_msg,
                'input': all_params,
            }
            self.save_result_data(data)
            return {'status': False, 'version': self.version, 'message': status_msg, 'data': data}

    def start4(self, all_params):
        """
        Perform Laviron-type analysis to estimate the heterogeneous rate constant (k₀)
        for electron transfer reactions based on ΔEp (peak separation), diffusion
        coefficient, and scan rate.

        Parameters:
            all_params (dict): Required inputs include:
                - input_a (float): Charge transfer coefficient α (usually ~0.5)
                - input_n (str): List of number of electrons transferred for each peak, e.g. "[1, 1, 1]"
                - input_d (str): List of diffusion coefficients (D) for each redox event, e.g. "[1e-5, 2e-5]"
                - input_t (str): Temperature in Kelvin (e.g., "298.15")

        Returns:
            dict: Contains result status and paths to two generated plots per peak:
                - Ψ vs ΔEp
                - Ψ vs 1/√scan_rate
        """
        status_msg = ''
        try:
            # === Load peak info from Step 2 ===
            form2_res = self.pkl_load("form2_res.pkl")
            peak_info = form2_res['peak_info']

            # === Parse electrochemical input parameters ===
            a = float(all_params['input_a'])                             # Transfer coefficient α
            n = ast.literal_eval(all_params['input_n'])                  # List of n values
            D = ast.literal_eval(all_params['input_d'])                  # List of D values
            T = float(ast.literal_eval(all_params['input_t']))           # Temperature in K

            # === Constants (unchanging) ===
            F = 96485.33212                                              # Faraday constant
            R = 8.314462618                                              # Gas constant

            k_list = []      # Store calculated rate constants
            res = []         # Store results and image paths

            # === Loop through each peak (for each redox couple) ===
            for i in range(len(n)):
                DelE = peak_info[f'DelE0{i}']                            # Peak separation ΔEp (V)
                Scan_Rate = peak_info[f'Scan_Rate{i}']                   # Scan rate in mV/s
                Scan_Rate_V = np.array(Scan_Rate) / 1000                 # Convert to V/s
                DelE_mV = np.array(DelE) * 1000                          # Convert ΔEp to mV for plotting

                print(f"DelE_mV{i}: ", DelE_mV)

                # === Calculate Ψ using Laviron equation ===
                # Ψ = 2.18 * sqrt(α / π) * exp(-α²·F·n·ΔEp / (R·T))
                # This form is simplified for reversible/quasi-reversible systems
                fai_lambda = lambda DelEi: 2.18 * ((a / math.pi) ** 0.5) * math.exp(
                    -((a ** 2 * F) / (R * T)) * n[i] * DelEi
                )
                fai = list(map(fai_lambda, DelE))  # Apply to each ΔEp value

                # === Plot 1: Ψ vs ΔEp (mV) ===
                plt.figure()
                plt.scatter(DelE_mV, fai, s=5)
                plt.xlabel('$\Delta E_p$ (mV)')
                plt.ylabel('$\Psi$')
                img_path1 = os.path.join(self.datapath, "CV_step3_func3_p1.png")
                plt.savefig(img_path1)
                plt.close()

                # === Plot 2: Ψ vs 1/√ν (Laviron linearization to extract k₀) ===
                # x = [πDnF/RT]^(-1/2) * ν^(-1/2)
                term = ((math.pi * D[i] * n[i] * F) / (R * T)) ** (-1 / 2)
                x_value = term * (Scan_Rate_V ** (-1 / 2))

                # Linear fit: Ψ = slope * x + intercept
                slope, intercept = np.polyfit(x_value, fai, 1)

                plt.figure()
                plt.scatter(x_value, fai, s=1)
                plt.plot(x_value, slope * np.array(x_value) + intercept, color='red')

                # Annotate slope equation
                equation = f"$y = {slope:.4f}x + {intercept:.4f}$"
                plt.text(0.1, 0.9, equation, transform=plt.gca().transAxes)

                plt.xlabel(f'$[\\pi D n \\nu F / RT]^{{-1/2}} \\cdot \\nu^{{-1/2}}$  (Term={term:.3e})')
                plt.ylabel('$\Psi$')
                print("Slope:", slope)

                # Save image and store result
                img_path2 = os.path.join(self.datapath, "CV_step3_func3_p2.png")
                plt.savefig(img_path2)
                plt.close()

                res.append({
                    'img1': img_path1.split('/')[-1],
                    'img2': img_path2.split('/')[-1],
                    'slope': slope,
                })

        except Exception as e:
            status_msg = str(e)

        # === Save Results ===
        data = self.res_data
        if 'CV' not in data:
            data['CV'] = {}

        if status_msg == '':
            data['CV']['form4'] = {
                'status': 'done',
                'input': all_params,
                'output': {'files': res}
            }
            self.save_result_data(data)
            return {
                'status': True,
                'version': self.version,
                'message': 'Success',
                'data': data
            }
        else:
            data['CV']['form4'] = {
                'status': status_msg,
                'input': all_params
            }
            self.save_result_data(data)
            return {
                'status': False,
                'version': self.version,
                'message': status_msg,
                'data': data
            }

    def start5(self, all_params):
        """
        Compute the Tafel slope and transfer coefficient (α) using two methods:

        Method 1: Derive α from the local slope of log(J) vs. E.
        Method 2: Modified Laviron approach using I_p-based expression.

        Parameters:
            all_params (dict):
                - cycle (int): CV scan cycle number to analyze
                - input_n (int): Number of electrons transferred
                - input_t (float): Temperature in Kelvin
                - electrode_dia (float): Electrode diameter in cm
                - current_peak (int): Index of peak (starting from 1)

        Returns:
            dict: Result structure containing plot filenames and metadata
        """
        status_msg = ''
        try:
            # Load prior results from form2: peak positions and data references
            form2_res = self.pkl_load("form2_res.pkl")
            peak_info = form2_res['peak_info']
            data_list = form2_res['data_list']
            myglobals = form2_res['globals']

            # Parse input parameters from frontend or script
            cycle = int(all_params['cycle'])
            n = int(all_params['input_n'])  # number of electrons transferred
            T = float(ast.literal_eval(all_params['input_t']))  # temperature in K
            electrode_dia = float(ast.literal_eval(all_params['electrode_dia']))  # diameter in cm
            A_Real = np.pi * (electrode_dia / 2) ** 2  # compute electrode area in cm²
            Which_Current_Peak = int(all_params['current_peak'])  # which peak to use (1-based index)
            cycle_range = range(2, 15)  # used to determine index offset within peak_info arrays

            # Constants: Faraday and gas constants
            F = 96485.33212
            R = 8.314462618

            m1_files = []

            # ----------------------------
            # Method 1: Tafel slope from d(logJ)/dE
            # ----------------------------
            for i, var_name in enumerate(data_list):
                df = myglobals[var_name]
                scan_rate = Search_scan_rate(var_name)
                name = f"{scan_rate}mV"

                # Extract current-voltage data from specified cycle
                cycle_df = df[df['Scan'] == cycle]
                Ui = np.array(cycle_df['WE(1).Potential (V)'])
                Ii = np.array(cycle_df['WE(1).Current (A)'])
                Ji = Ii / A_Real  # convert current to current density (A/cm²)

                # Separate forward (oxidation) and reverse (reduction) scans
                upperU, lowerU, upperJ, lowerJ = separater(Ui, Ji, min(Ui), max(Ui))

                # Optionally apply Gaussian smoothing (off by default)
                if False:
                    smoothed_upperJ = gaussian_filter(upperJ, sigma=1)
                else:
                    smoothed_upperJ = upperJ

                # Compute d(logJ)/dE numerically
                logJ_upper = special_log(smoothed_upperJ)  # apply log, handling negatives
                dlogJ_dU = np.gradient(logJ_upper, upperU)  # numerical derivative
                Tafel_slope = 1 / dlogJ_dU  # inverse slope per definition
                alpha = (2.303 * R * T) / (Tafel_slope * n * F)  # Tafel equation rearranged to solve for α

                # Plot current density and α on dual-axis plot
                fig, ax1 = plt.subplots()
                ax1.set_xlabel('Applied Potential [V]')
                ax1.set_ylabel('Current density [A/cm²]', color=colors[0])
                ax1.scatter(upperU, smoothed_upperJ, s=1, color=colors[0])
                ax1.tick_params(axis='y', labelcolor=colors[0])

                ax2 = ax1.twinx()
                ax2.set_ylabel('Transfer coefficient α', color=colors[1])
                ax2.scatter(upperU, alpha, s=1, color=colors[1])
                ax2.set_ylim([-1, 1])  # limit alpha range for visibility
                ax2.tick_params(axis='y', labelcolor=colors[1])

                plt.title(f'Tafel Plot and α (Method 1) - {name}, Cycle {cycle}')
                plt.grid(True)
                fig.tight_layout()
                img_path = os.path.join(self.datapath, f"CV_step3_func5_m1_p{i}.png")
                plt.savefig(img_path)
                plt.close()
                m1_files.append(os.path.basename(img_path))

            # ----------------------------
            # Method 2: Modified Laviron method using I_peak-based term
            # ----------------------------
            m2_files = []
            for i, var_name in enumerate(data_list):
                df = myglobals[var_name]
                scan_rate = Search_scan_rate(var_name)
                name = f"{scan_rate}mV"

                cycle_df = df[df['Scan'] == cycle]
                Ui = np.array(cycle_df['WE(1).Potential (V)'])
                Ii = np.array(cycle_df['WE(1).Current (A)'])

                # Separate forward scan
                upperU, _, upperI, _ = separater(Ui, Ii, min(Ui), max(Ui))

                # Optionally apply Gaussian smoothing (off by default)
                if False:
                    smoothed_upperI = gaussian_filter(upperI, sigma=1)
                else:
                    smoothed_upperI = upperI

                # Retrieve the I_peak value from form2 results
                I_Peak = peak_info[f'Ia{Which_Current_Peak - 1}'][i * len(cycle_range) + (cycle - min(cycle_range))]

                # Construct Laviron-type term: I^2 / (I_p - I)
                I_term = (I_Peak ** 2) / (I_Peak - smoothed_upperI)
                lnI_term = special_ln(I_term)  # log-transformed term (with safe handling)
                upperO = (F / (R * T)) * upperU  # normalized potential axis

                # Derive dln(I_term)/dE and back-calculate α
                dlnI_term_dU = np.gradient(lnI_term, upperU)
                alpha = 0.5 * (R * T / F) * dlnI_term_dU  # per rearranged Laviron expression

                # Plot current and α on dual y-axes
                fig, ax1 = plt.subplots()
                ax1.set_xlabel('Applied Potential [V]')
                ax1.set_ylabel('Current [A]', color=colors[0])
                ax1.scatter(upperU, smoothed_upperI, s=1, color=colors[0])
                ax1.tick_params(axis='y', labelcolor=colors[0])

                ax2 = ax1.twinx()
                ax2.set_ylabel('Transfer coefficient α', color=colors[1])
                ax2.scatter(upperU, alpha, s=1, color=colors[1])
                ax2.set_ylim([-1, 1])
                ax2.tick_params(axis='y', labelcolor=colors[1])

                plt.title(f'Tafel Plot and α (Method 2) - {name}, Cycle {cycle}')
                plt.grid(True)
                fig.tight_layout()
                img_path = os.path.join(self.datapath, f"CV_step3_func5_m2_p{i}.png")
                plt.savefig(img_path)
                plt.close()
                m2_files.append(os.path.basename(img_path))

        except Exception as e:
            status_msg = str(e)

        # Prepare result dictionary and persist metadata
        data = self.res_data
        if 'CV' not in data:
            data['CV'] = {}

        if status_msg == '':
            data['CV']['form5'] = {
                'status': 'done',
                'input': all_params,
                'output': {
                    'm1_files': m1_files,
                    'm2_files': m2_files,
                }
            }
            self.save_result_data(data)
            return {
                'status': True,
                'version': self.version,
                'message': 'Success',
                'data': data
            }
        else:
            data['CV']['form5'] = {
                'status': status_msg,
                'input': all_params
            }
            self.save_result_data(data)
            return {
                'status': False,
                'version': self.version,
                'message': status_msg,
                'data': data
            }

if __name__ == '__main__':
    """
    Entry point for direct execution.
    This block ensures that code inside is only executed when the script is run directly,
    and not when imported as a module in another script.
    """

    # === Step 1: Initialize CV analysis object ===
    # Instantiate the CV class with required parameters:
    # - "version_test_CV": A version label and output folder for storing results
    # - "data/CV_csv": Path to the directory containing raw CV data (in .csv/.txt/.xlsx)
    # - sigma=10.0: Optional smoothing parameter for later processing steps (e.g., Gaussian filter)
    c = CV("version_test_CV", "data/CV_csv", sigma=10.0)


    # === Step 2: Perform peak analysis (form2) ===
    # Call the peak detection module (start2) to identify key electrochemical features.
    #
    # Parameters:
    # - method: Strategy for peak detection, e.g. 'Max' to detect global maxima/minima in defined windows.
    # - peak_range_top: Electrochemical potential ranges for oxidation peaks (Ea/Ia).
    #                   Provided as a string of tuples that will be parsed internally.
    # - peak_range_bottom: Potential ranges for reduction peaks (Ec/Ic).
    #
    # Notes:
    # - Each tuple defines a region in volts (V) within which the algorithm will search for a peak.
    # - The number and order of these regions define how many redox events will be extracted.
    res = c.start2(
        method='Max',
        peak_range_top='(-1,-0.5),(0,0.2),(0.25,0.5)',       # 3 oxidation windows
        peak_range_bottom='(-0.9,-0.75),(0,0.125),(0.125,0.25)'  # 3 reduction windows
    )

    # === Step 3: Review result ===
    # Display the returned result dictionary from start2().
    # Typically includes:
    # - status: 'done' or error message
    # - input: the parameters used
    # - output: filenames of result plots or data
    print(res)
