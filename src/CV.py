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


import os as os
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
    ma = -1
    xx = -1
    yy = -1
    for i in range(len(x)):
        if x[i] >= start and x[i] <= end:
            if y[i] > ma:
                ma = y[i]
                xx = x[i]
                yy = y[i]
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
    mi = 10000
    xx = -1
    yy = -1
    for i in range(len(x)):
        if x[i] >= start and x[i] <= end:
            if y[i] < mi:
                mi = y[i]
                xx = x[i]
                yy = y[i]
    return xx, yy

def find_y(x,y,xi):
    """
    Find the y-value corresponding to a given x-value (xi).

    Parameters:
        x (list): list of x-values
        y (list): list of y-values
        xi (float): x target

    Returns:
        float: y-value at xi or -1 if not found
    """
    for i in range(len(x)):
        if x[i] == xi:
            return y[i]
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
    upperx = []
    lowerx = []
    uppery = []
    lowery = []

    x = x.tolist()  # Convert Int64Index to list
    y = y.tolist()  # Convert Int64Index to list

    boundary_l = x.index(left)
    boundary_r = x.index(right)

    if boundary_r < boundary_l:
        upperx = x[boundary_l:] + x[:boundary_r+1]
        uppery = y[boundary_l:] + y[:boundary_r+1]
        lowerx = x[boundary_r:boundary_l+1]
        lowery = y[boundary_r:boundary_l+1]
    else:
        upperx = x[boundary_l:boundary_r+1]
        uppery = y[boundary_l:boundary_r+1]
        lowerx = x[boundary_r:] + x[:boundary_l+1]
        lowery = y[boundary_r:] + y[:boundary_l+1]

    return upperx, lowerx, uppery, lowery


def Search_scan_rate(filename):
    """
    Extract scan rate (e.g. 10 from "DMAB_10mVs.csv") from filename.

    Parameters:
        filename (str): input filename

    Returns:
        int: scan rate in mV/s or -1 if not found
    """
    match = re.search(r'(\d+)mVs', filename)
    if match:
        return int(match.group(1))
    else:
        # Handle files without RPM values
        return -1  # You can use any default value or treatment


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

    # Determine the number of header lines
    num_header_lines = 56  # As per the given pattern

    # Extract the data lines (skipping the header)
    data_lines = lines[num_header_lines:]

    # Create a list to store the extracted data
    data = []

    for line in data_lines:
        if line.strip():  # Ignore empty lines
            parts = line.split()
            if len(parts) == 2:
                ewe, i_mA = parts
                data.append((float(ewe), float(i_mA)))

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['Ewe/V', '<I>/mA'])
    return df


def read_auto_lab_file(file):
    """
    Read a file exported from Autolab (either CSV or Excel format).

    Parameters:
        file (str): Path to the file.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    if file.endswith('.csv'):
        df = pd.read_csv(file, delimiter=',')
    else:
        df = pd.read_excel(file, sheet_name='Sheet1', engine='openpyxl')
    return df


def create_file_template_CV(file_name):
    """
    Replace scan rate numbers in filename with a '%d' placeholder.

    Parameters:
        file_name (str): Original filename (e.g., 'DMAB_10mVs.xlsx')

    Returns:
        str: Template string with placeholder (e.g., 'DMAB_%dmVs.xlsx')
    """
    pattern = r'(\d+)mVs'
    template = re.sub(pattern, '%dmVs', file_name)

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
    # Extract the RGB components from the hex color string
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

    # Apply the darkening factor to each component
    r = max(0, int(r * factor))
    g = max(0, int(g * factor))
    b = max(0, int(b * factor))

    # Convert the darkened RGB values back to a hex color string
    return f'#{r:02x}{g:02x}{b:02x}'

def extract_rpm(filename):
    """
    Extract the 'rpm' value from filename (e.g., '800rpm.csv').

    Parameters:
        filename (str): Input filename.

    Returns:
        str or None: Extracted rpm string (e.g., '800rpm'), or None if not found.
    """
    pattern = r'(?:^|_)(\d+rpm)\.'
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    else:
        return None


def extract_mvs(filename):
    """
    Extract the scan rate from filenames ending with '_CV.csv'.

    Parameters:
        filename (str): Input filename (e.g., 'sample_20mVs_CV.csv').

    Returns:
        str or None: Extracted scan rate string (e.g., '20mVs'), or None if not matched.
    """
    pattern = r'(?:^|_)(\d+mVs)_CV\.'
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    else:
        return None


def check_files(files):
    """
    Check if a list of filenames all have valid extensions.

    Parameters:
        files (list of str): List of file paths.

    Returns:
        bool: True if all files are allowed, False otherwise.
    """
    for f in files:
        ext = f.split('.')[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:  # ['xlsx', 'txt', 'csv']
            return False
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
    ma = -1
    xx = -1
    yy = -1
    for i in range(len(x)):
        if x[i] >= start and x[i] <= end:
            if y[i] > ma:
                ma = y[i]
                xx = x[i]
                yy = y[i]
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
    mi = 10000
    xx = -1
    yy = -1
    for i in range(len(x)):
        if x[i] >= start and x[i] <= end:
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
    for i in range(len(x)):
        if x[i] == xi:
            return y[i]
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
    arr = str_peak_range.strip().replace(" ", "").split('),(')
    for a in arr:
        start = a.split(",")[0].replace("(", "").replace(")", "").strip()
        end = a.split(",")[1].replace("(", "").replace(")", "").strip()
        res.append((float(start), float(end)))
    # # 使用正则表达式匹配坐标
    # pattern = r'\((-?\d+(\.\d+)?),(-?\d+(\.\d+)?)\)'
    # matches = re.findall(pattern, str(str_peak_range))
    #
    # # 提取匹配到的坐标
    # coordinates = [(float(match[0]), float(match[2])) for match in matches]
    # return coordinates
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

    x = x.tolist()  # Convert Int64Index to list
    y = y.tolist()  # Convert Int64Index to list

    boundary_l = x.index(left)
    boundary_r = x.index(right)

    if boundary_r < boundary_l:
        upperx = x[boundary_l:] + x[:boundary_r + 1]
        uppery = y[boundary_l:] + y[:boundary_r + 1]
        lowerx = x[boundary_r:boundary_l + 1]
        lowery = y[boundary_r:boundary_l + 1]
    else:
        upperx = x[boundary_l:boundary_r + 1]
        uppery = y[boundary_l:boundary_r + 1]
        lowerx = x[boundary_r:] + x[:boundary_l + 1]
        lowery = y[boundary_r:] + y[:boundary_l + 1]

    return upperx, lowerx, uppery, lowery


def reorder(filename):
    """
    Extract scan rate from filename for sorting purposes.

    Parameters:
        filename (str): Input filename (e.g., 'data_50mVs.csv')

    Returns:
        int: Scan rate (e.g., 50), or -1 if pattern not found
    """
    match = re.search(r'(\d+)mVs', filename)
    if match:
        return int(match.group(1))
    else:
        # Handle files without RPM values
        return -1  # You can use any default value or treatment


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
        ext = f.split('.')[-1].lower()
        if ext in ALLOWED_EXTENSIONS:
            res.append(f)
    return res


def special_log(a_list):
    """
    Custom log10 transformation for an array:
    - log10(x) if x > 0
    - log10(-x) if x < 0
    - 0 if x == 0

    Parameters:
        a_list (np.array): Input numeric array

    Returns:
        np.array: Transformed array
    """
    a_list_special_log = np.zeros_like(a_list)  # Initialize log array with zeros

    for idx, value in enumerate(a_list):
        if value > 0:
            a_list_special_log[idx] = np.log10(value)
        elif value < 0:
            a_list_special_log[idx] = np.log10(-value)
        else:  # value == 0
            a_list_special_log[idx] = 0

    return a_list_special_log


def special_ln(a_list):
    """
    Custom natural log transformation for an array:
    - ln(x) if x > 0
    - ln(-x) if x < 0
    - 0 if x == 0

    Parameters:
        a_list (np.array): Input numeric array

    Returns:
        np.array: Transformed array
    """
    a_list_special_ln = np.zeros_like(a_list)  # Initialize log array with zeros

    for idx, value in enumerate(a_list):
        if value > 0:
            a_list_special_ln[idx] = np.log(value)
        elif value < 0:
            a_list_special_ln[idx] = np.log(-value)
        else:  # value == 0
            a_list_special_ln[idx] = 0

    return a_list_special_ln

class CV(BaseModule):
    """
    CV Module class for handling cyclic voltammetry (CV) data processing.

    Inherits:
        BaseModule: A base class providing versioning and file handling support.
    """
    def __init__(self, version, files_info):
        """
        Initialize the CV module with versioning and input metadata.

        Parameters:
            version (str): Unique identifier for the processing session.
            files_info (str): Path to JSON file containing list of CV file metadata.
        """
        super().__init__(version)
        self.version = version
        self.files_info = files_info
        self.savepath = 'outputs/' + version
        if not os.path.exists(self.savepath):
            os.makedirs(self.savepath)

    # Note: demo_data() and read_csv() are commented out, likely deprecated.
    # The read_csv() function parses files from a local directory (not used in deployed backend).
    # They can be documented if reactivated.

    def read_data(self):
        """
        Read CV data files described in a JSON metadata list.

        The metadata must include 'filename' (used for sorting) and 'existed_filename' (actual path).
        Supported file formats: .xlsx, .csv, .txt.

        If Excel is read, a CSV cache file is optionally created for efficiency.

        Returns:
            dict: Mapping of scan rate (int) to pandas DataFrame of CV data.
        """
        with open(self.files_info, 'r') as f:
            info_list = json.loads(f.read())

        files = []
        real_file_path = {}
        for info in info_list:
            # input your file name here and switch rpm in to %d
            f = info['filename']
            file = info['existed_filename']
            if not os.path.isfile(file):
                continue
            files.append(f)
            real_file_path[f] = file
        files = sorted(files, key=reorder)
        print("len of files: ", len(files), self.files_info)

        data = {}
        for f in files:
            file = real_file_path[f]
            if not os.path.isfile(file):
                continue

            print("filename:", f)
            rpm = Search_scan_rate(f)
            if rpm is None:
                continue
            print("rpm:", rpm)

            if file.endswith(".xlsx"):
                csv_file = file + ".csv"
                if os.path.exists(csv_file):
                    data[rpm] = pd.read_csv(csv_file, delimiter=',', dtype={'Current range': str})
                else:
                    data0 = pd.ExcelFile(file)
                    data[rpm] = data0.parse('Sheet1')
                    data[rpm].to_csv(csv_file, sep=',', index=False)
                    print("saved csv file to {}".format(csv_file))
            elif file.endswith(".txt"):
                data[rpm] = pd.read_csv(file, delimiter=';', dtype={'Current range': str})
            elif file.endswith(".csv"):
                data[rpm] = pd.read_csv(file, delimiter=',', dtype={'Current range': str})

        print("data: ", len(data))
        return data

    def check_columns(self, data):
        cols = ['WE(1).Current (A)', 'WE(1).Potential (V)', 'Scan']
        missing_cols = []
        for scan_rate, df in data.items():
            for col in cols:
                if col not in df.columns:
                    missing_cols.append(col)
        if len(missing_cols) > 0:
            return "error: Missing columns: " + ", ".join(missing_cols)
        return ''

    def start1_figure(self, data, apply_sigma=False, all_params = {}):
        """
        Plot CV curves from the input data, with optional Gaussian smoothing.

        There are two parts:
        1. Plot the specified 'cycle' (Scan number) from each scan rate.
        2. Plot the full raw data (all cycles).

        Parameters:
            data (dict): Dictionary of scan_rate => DataFrame
            apply_sigma (bool): Whether to apply Gaussian filter for smoothing
            all_params (dict): Includes 'sigma' (float), 'cycle' (int)

        Returns:
            tuple: (file_path_filtered_or_raw, file_path_all_cycles)
        """
        cycle = int( all_params['cycle'] )
        sigma = float( all_params['sigma'] )

        # WIth cycle
        for scan_rate, df0 in data.items():
            # data0 = pd.ExcelFile(file)
            # df0 = data0.parse('Sheet1')
            df = df0[df0['Scan'] == cycle]
            E = df['WE(1).Potential (V)']
            I = df['WE(1).Current (A)']

            # Define the standard deviation (sigma) for the Gaussian filter

            upperE, lowerE, upperI, lowerI = separater(E, I, min(E), max(E))
            if apply_sigma:
                # Apply gaussian_filter with sigma=?
                smoothed_upperI = gaussian_filter(upperI, sigma=sigma)
                smoothed_lowerI = gaussian_filter(lowerI, sigma=sigma)
            else:
                smoothed_upperI = upperI
                smoothed_lowerI = lowerI

            I = np.concatenate((smoothed_upperI, smoothed_lowerI))
            E = upperE + lowerE

            #         print("length of E:",len(E))
            plt.scatter(E, I, label=scan_rate, s=1)

        plt.xlabel('$Applied potential\,(E)\,/\,V$')
        plt.ylabel('$Current\,(I)\,/\,A$')
        # plt.ylim(-2e-5,2e-5)
        plt.legend()
        # plt.grid()
        # plt.show()

        if apply_sigma:
            to_file1 = os.path.join(self.savepath, "form1_sigma{}.png".format(sigma))
        else:
            to_file1 = os.path.join(self.savepath, "form1_original.png")
        plt.savefig(to_file1)
        plt.close()

        # No cycle
        for scan_rate, df0 in data.items():
            # data0 = pd.ExcelFile(file)
            # df0 = data0.parse('Sheet1')
            df = df0
            E = df['WE(1).Potential (V)']
            I = df['WE(1).Current (A)']
            plt.scatter(E, I, label=scan_rate, s=1)
        plt.xlabel('$Applied potential\,(E)\,/\,V$')
        plt.ylabel('$Current\,(I)\,/\,A$')
        plt.legend()
        to_file3 = os.path.join(self.savepath, "form1_cycle.png")
        plt.savefig(to_file3)
        plt.close()
        return to_file1, to_file3

    def start1(self, all_params):
        """
        Top-level entry point for CV form1 plotting workflow.

        Reads data, generates original and smoothed CV plots for a given scan cycle,
        and saves output to the form1 slot in result JSON.

        Parameters:
            all_params (dict): Includes 'sigma', 'cycle', etc.

        Returns:
            dict: Result dictionary including output image paths
        """
        sigma = float(all_params['sigma'])
        status_msg = ''

        data = self.read_data()
        if data is None:
            status_msg = 'error: one or more files are not allowed.'
        mVs_list_str = ', '.join( ["'{}mVs'".format(k) for k in data] )
        if status_msg == '':
            status_msg = self.check_columns(data)

        if status_msg == '':
            try:
                to_file1, to_file3 = self.start1_figure(data, apply_sigma=False, all_params=all_params)
                to_file2, _ = self.start1_figure(data, apply_sigma=True, all_params=all_params)
            except Exception as e:
                status_msg = str(e)


        data_file = os.path.join('outputs', self.version, 'data.json')
        if os.path.exists(data_file):
            data = json.loads(open(data_file, 'r').read())
        else:
            data = {'version': self.version}

        if 'CV' not in data.keys():
            data['CV'] = {}

        if status_msg == '':
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

        For each scan rate and multiple cycles (Scan=3 to 11), this function:
        - Separates upper and lower branches of CV
        - Optionally smooths the current
        - Locates anodic and cathodic peak potentials and currents
        - Computes ΔEp (DelE0) and average potential (Ef)

        Parameters:
            data (dict): Dictionary of scan_rate => DataFrame
            method (str): Currently unused (e.g., "Max", "Mean")
            p1_start (float): Start of oxidation peak range
            p1_end (float): End of oxidation peak range
            p2_start (float): Start of reduction peak range
            p2_end (float): End of reduction peak range

        Returns:
            tuple: (Ef1, DelE01, Ea1, Ec1, Ia1, Ic1, Ic1, Scan_Rate1)
        """
        Ef1 = []
        DelE01 = []
        Ea1 = []
        Ec1 = []
        Ia1 = []
        Ic1 = []
        Scan_Rate1 = []
        for jj, df0 in data.items():
            j = int(jj.replace("mVs", ""))
            name = str(j) + "mV"
            num = j

            Ea1j = []
            Ec1j = []
            Ia1j = []
            Ic1j = []
            for i in range(3, 12):
                df = df0[df0['Scan'] == i]
                Ui = df['WE(1).Potential (V)']
                Ii = df['WE(1).Current (A)']
                cycle = str(i + 1)
                Ui = np.array(Ui)
                Ii = np.array(Ii)

                upperU, lowerU, upperI, lowerI = separater(Ui, Ii, min(Ui), max(Ui))

                # Apply Gaussian filter(optional)
                apply_gaussian_filter = False  # Set to True to apply the filter, False to not apply the filter

                if apply_gaussian_filter == True:
                    # Apply gaussian_filter with sigma=1
                    smoothed_upperI = gaussian_filter(upperI, sigma=1)
                    smoothed_lowerI = gaussian_filter(lowerI, sigma=1)
                else:
                    # If not applying the filter, assign the original arrays to the new variables
                    smoothed_upperI = upperI
                    smoothed_lowerI = lowerI

                top_x1, top_y1 = find_max(upperU, smoothed_upperI, p1_start, p1_end)
                bottom_x1, bottom_y1 = find_min(lowerU, smoothed_lowerI, p2_start, p2_end)
                DelE01i = top_x1 - bottom_x1
                Ef1i = (top_x1 + bottom_x1) / 2

                Ea1.append(top_x1)
                Ea1j.append(top_x1)
                Ia1.append(find_y(upperU, smoothed_upperI, top_x1))
                Ia1j.append(find_y(upperU, smoothed_upperI, top_x1))
                Ec1.append(bottom_x1)
                Ec1j.append(bottom_x1)
                Ic1.append(find_y(lowerU, smoothed_lowerI, bottom_x1))
                Ic1j.append(find_y(lowerU, smoothed_lowerI, bottom_x1))

                DelE01.append(DelE01i)
                Ef1.append(Ef1i)

                Scan_Rate1.append(num)


        return (Ef1, DelE01, Ea1, Ec1, Ia1, Ic1, Ic1, Scan_Rate1)

    def start2_figure1(self, data, Ea_res, sigma=10, pr1=None, pr2=None):
        """
        Plot a smoothed CV curve with red dots indicating peak positions for one example scan.

        Parameters:
            data (dict): Dictionary of scan_rate => DataFrame
            Ea_res (list): List of result tuples for each peak set
            sigma (float): Smoothing value for Gaussian filter
            pr1 (list): List of tuples for oxidation peak ranges
            pr2 (list): List of tuples for reduction peak ranges

        Returns:
            str: Path to saved image
        """
        df0 = None
        for k, d in data.items():
            df0 = d
            break

        img_path = os.path.join(self.datapath, "CV_form2_p1.png")
        df = df0[df0['Scan'] == 6]
        Ui = df['WE(1).Potential (V)']
        Ii = df['WE(1).Current (A)']
        Ui = np.array(Ui)
        Ii = np.array(Ii)
        upperU, lowerU, upperI, lowerI = separater(Ui, Ii, min(Ui), max(Ui))

        # Apply Gaussian filter(optional)
        apply_gaussian_filter = True  # Set to True to apply the filter, False to not apply the filter

        if apply_gaussian_filter == True:
            # Apply gauplt.savefig(img_path)ssian_filter with sigma
            smoothed_upperI = gaussian_filter(upperI, sigma=sigma)
            smoothed_lowerI = gaussian_filter(lowerI, sigma=sigma)
        else:
            # If not applying the filter, assign the original arrays to the new variables
            smoothed_upperI = upperI
            smoothed_lowerI = lowerI

        plt.scatter(upperU, smoothed_upperI, s=1, c='#1f77b4')
        plt.scatter(lowerU, smoothed_lowerI, s=1, c='#ff7f0e')
        for pp, (Ef1, DelE01, Ea1, Ec1, Ia1, Ic1, Ic1, Scan_Rate1) in enumerate(Ea_res):
            top_x1, top_y1 = find_max(upperU, smoothed_upperI, -1, -0.5)
            bottom_x1, bottom_y1 = find_min(lowerU, smoothed_lowerI, -0.9, -0.75)
            p1_start = pr1[pp][0]
            p1_end = pr1[pp][1]
            p2_start = pr2[pp][0]
            p2_end = pr2[pp][1]

            top_x1, top_y1 = find_max(upperU, smoothed_upperI, p1_start, p1_end)
            bottom_x1, bottom_y1 = find_min(lowerU, smoothed_lowerI, p2_start, p2_end)
            plt.scatter(top_x1, top_y1, s=10, c='r')
            plt.scatter(bottom_x1, bottom_y1, s=10, c='r')

        plt.xlabel('$Applied potential\,(E)\,/\,V$')
        plt.ylabel('$Current\,(I)\,/\,A$')
        # plt.ylim(-2e-5,2e-5)
        # plt.grid()
        # plt.show()
        plt.savefig(img_path)
        plt.close()
        return img_path

    def start2_figure2(self, data, Ea_res, sigma=10, pr1=None, pr2=None):
        """
        Plot full CV curves (smoothed) with red dots showing peak positions.

        Parameters:
            data (dict): Dictionary of scan_rate => DataFrame
            Ea_res (list): List of peak result tuples
            sigma (float): Smoothing factor
            pr1, pr2: Optional peak range data (unused in this version)

        Returns:
            str: Path to saved image
        """
        img_path = os.path.join(self.datapath, "CV_form2_p2.png")

        for jj, df0 in data.items():
            j = int(jj.replace("mVs", ""))
            scan_rate = str(j) + "mV"

            df = df0
            E = df['WE(1).Potential (V)']
            I = df['WE(1).Current (A)']

            # Define the standard deviation (sigma) for the Gaussian filter
            sigma = 10.0  # You can adjust this as needed
            upperE, lowerE, upperI, lowerI = separater(E, I, min(E), max(E))

            # Apply gaussian_filter with sigma=?
            smoothed_upperI = gaussian_filter(upperI, sigma=sigma)
            smoothed_lowerI = gaussian_filter(lowerI, sigma=sigma)

            I = np.concatenate((smoothed_upperI, smoothed_lowerI))
            E = upperE + lowerE

            #         print("length of E:",len(E))
            plt.scatter(E, I, label=scan_rate, s=1)

        for pp, (Ef1, DelE01, Ea1, Ec1, Ia1, Ic1, Ic1, Scan_Rate1) in enumerate(Ea_res):
            # print("===", pp, Ea1, Ia1, Ec1, Ic1)
            plt.scatter(Ea1, Ia1, s=10, c='r')
            plt.scatter(Ec1, Ic1, s=10, c='r')

        plt.xlabel('$Applied potential\,(E)\,/\,V$')
        plt.ylabel('$Current\,(I)\,/\,A$')
        # plt.ylim(-2e-5,2e-5)
        # plt.grid()
        # plt.show()
        plt.legend()
        plt.savefig(img_path)
        plt.close()
        return img_path

    def start2(self, all_params):
        """
        Main function for peak extraction and analysis in CV form2.

        This method:
        1. Parses user-specified peak range and scan cycle settings
        2. Loads CV data files and extracts usable data
        3. Iteratively finds peak oxidation/reduction positions per scan cycle
        4. Stores results in the `peak_info` dictionary

        Parameters:
            all_params (dict): Contains keys:
                - 'peak_range_top': str, e.g., "((-1, -0.7), (0.0, 0.2))"
                - 'peak_range_bottom': str, e.g., "((-0.9, -0.75), ...)"
                - 'scan_rate_from', 'scan_rate_after': list of ints
                - 'cycle_range': [start, end] as list
                - 'example_scan', 'example_cycle': int
                - and others like 'method'

        Returns:
            None (but prints progress and updates internal peak_info state)
        """
        status_msg = ''
        try:
            print(all_params)

            # --- 1. Parse form inputs ---
            method = all_params['method']
            # peak_range_top = all_params['peak_range_top']
            # peak_range_bottom = all_params['peak_range_bottom']

            peak_info = {}
            peak_range_ox = ast.literal_eval(all_params['peak_range_top']) # [(-1, -0.70), (0, 0.2), (0.25, 0.5)]
            peak_range_re = ast.literal_eval(all_params['peak_range_bottom'])  #[(-0.925, -0.75), (0.0, 0.125), (0.125, 0.25)]

            discard_scan_start = ast.literal_eval(all_params['scan_rate_from'])
            discard_scan_end = ast.literal_eval(all_params['scan_rate_after'])

            cycle_range_input = ast.literal_eval(all_params['cycle_range'])
            cycle_range = range(cycle_range_input[0], cycle_range_input[1])

            example_scan_rate = all_params['example_scan'] # default 20
            example_cycle  = all_params['example_cycle'] # default 9

            sigma = float(self.res_data['CV']['form1']['input']['sigma'])

            # --- 2. Read metadata and real data paths ---
            with open(self.files_info, 'r') as f:
                info_list = json.loads(f.read())
            files = []
            real_file_path = {}
            for info in info_list:
                # input your file name here and switch rpm in to %d
                f = info['filename']
                ef = info['existed_filename']
                if not os.path.isfile(ef):
                    continue
                files.append(f)
                real_file_path[f] = ef

            # Sort files by scan rate
            files = sorted(files, key=Search_scan_rate)
            # --- 3. File filtering by device type ---
            device = f'Autolab'
            if device == 'Autolab':
                Filter_files = [file for file in files if file.endswith('.xlsx') or file.endswith('.csv')]
            elif device == 'EClab':
                Filter_files = [file for file in files if file.endswith('.txt')]
            else:
                Filter_files = []
                print('device not found in library')

            # Get filename template like "HDV_G_DMAB0.05gL_%dmVs_CV.csv"
            file_template = os.path.splitext(create_file_template_CV(Filter_files[0]))[0]

            # --- 4. Load all data into memory ---
            data_list = []
            myglobals = {}
            for file in Filter_files:
                scan_rate = Search_scan_rate(file)
                df = read_auto_lab_file(real_file_path[file])
                var_name = file_template % scan_rate
                myglobals[var_name] = df
                data_list.append(var_name)
                print(var_name)

            # --- 5. Peak extraction for each range set ---
            for z in range(len(peak_range_ox)):
                peak_info[f'Ef{z}'] = []
                peak_info[f'DelE0{z}'] = []
                peak_info[f'Ea{z}'] = []
                peak_info[f'Ec{z}'] = []
                peak_info[f'Ia{z}'] = []
                peak_info[f'Ic{z}'] = []
                peak_info[f'Scan_Rate{z}'] = []

                # Create a new figure for each z loop
                print(f'\n\033[1mFigure Set for Peak{z + 1}:\033[0m')
                plt.figure()

                # Determine the slice based on the variable
                selected_data_list = data_list[discard_scan_start[z]:discard_scan_end[z]]
                print("\033[1mGoing to process the following files:\033[0m")
                for file in selected_data_list:
                    print(file)
                print("\n")

                # --- 6. Loop through selected files ---
                for var_name in selected_data_list:
                    df = myglobals[var_name]
                    print(var_name)
                    scan_rate = Search_scan_rate(var_name)
                    name = str(scan_rate) + "mV"

                    # Initialize lists for this file
                    Ea_j = []
                    Ec_j = []
                    Ia_j = []
                    Ic_j = []

                    # --- Loop through scan cycles ---
                    for i in cycle_range:
                        cycle_df = df[df['Scan'] == i]
                        if len(cycle_df) == 0:
                            continue
                        Ui = cycle_df['WE(1).Potential (V)']
                        Ii = cycle_df['WE(1).Current (A)']
                        Ui = np.array(Ui)
                        Ii = np.array(Ii)

                        # Separate top and bottom
                        upperU, lowerU, upperI, lowerI = separater(Ui, Ii, min(Ui), max(Ui))

                        # Apply Gaussian filter (optional)
                        apply_gaussian_filter = False  # Set to True to apply the filter, False to not apply the filter

                        if apply_gaussian_filter:
                            smoothed_upperI = gaussian_filter(upperI, sigma=1)
                            smoothed_lowerI = gaussian_filter(lowerI, sigma=1)
                        else:
                            smoothed_upperI = upperI
                            smoothed_lowerI = lowerI

                        # Input range of first peak
                        top_x, top_y = find_max(upperU, smoothed_upperI, peak_range_ox[z][0], peak_range_ox[z][1])
                        bottom_x, bottom_y = find_min(lowerU, smoothed_lowerI, peak_range_re[z][0], peak_range_re[z][1])
                        DelE02i = top_x - bottom_x
                        Ef2i = (top_x + bottom_x) / 2

                        peak_info[f'Ea{z}'].append(top_x)
                        Ea_j.append(top_x)
                        peak_info[f'Ia{z}'].append(find_y(upperU, smoothed_upperI, top_x))
                        Ia_j.append(find_y(upperU, smoothed_upperI, top_x))
                        peak_info[f'Ec{z}'].append(bottom_x)
                        Ec_j.append(bottom_x)
                        peak_info[f'Ic{z}'].append(find_y(lowerU, smoothed_lowerI, bottom_x))
                        Ic_j.append(find_y(lowerU, smoothed_lowerI, bottom_x))

                        peak_info[f'DelE0{z}'].append(DelE02i)
                        peak_info[f'Ef{z}'].append(Ef2i)

                        peak_info[f'Scan_Rate{z}'].append(scan_rate)



            # ==============================
            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            print("Done:", formatted_time)

            def show_info(peak_info, n=5):
                """
                Utility function to print head of each value list in peak_info.
                Useful for debug/logging.
                """
                for key, values in peak_info.items():
                    # Check if the list is shorter than n, if so, adjust n to the length of the list
                    display_length = min(len(values), n)
                    print(f'{key}: {[len(values)]} {values[:display_length]}')

            # Call the function to print the head of peak_info
            show_info(peak_info)


            # Dictionary to store the mean values of Ef
            mean_Ef = {}

            for i in range(len(peak_range_ox)):
                Ef = np.mean(peak_info[f'Ef{i}'])
                mean_Ef[f'Ef{i + 1}'] = Ef

            # Print the results
            for key, value in mean_Ef.items():
                print(f"{key}: {value}")


            ## show all searched peaks on the CV plot figure
            plt.figure()
            # Plot the CV data
            for data_i in data_list:
                df = myglobals[data_i]  # Access the DataFrame using the variable name
                print(data_i)
                U = df['WE(1).Potential (V)']
                I = df['WE(1).Current (A)']
                scan_rate = Search_scan_rate(data_i)  # Extract scan rate from the variable name
                plt.scatter(U, I, label=f'{scan_rate} mV', s=1, c='#1f77b4')

            # Plot the peak information
            for i in range(len(peak_range_ox)):
                plt_data_Ea = peak_info[f'Ea{i}']
                plt_data_Ec = peak_info[f'Ec{i}']
                plt_data_Ia = peak_info[f'Ia{i}']
                plt_data_Ic = peak_info[f'Ic{i}']
                plt.scatter(plt_data_Ea, plt_data_Ia, s=10, c='r')
                plt.scatter(plt_data_Ec, plt_data_Ic, s=10, c='r')

            plt.xlabel('$Applied potential\,(E)\,/\,V$')
            plt.ylabel('$Current\,(I)\,/\,A$')
            plt.legend()
            # plt.show()
            to_file1 = os.path.join(self.datapath, "CV_step2_p1.png")
            plt.savefig(to_file1)
            plt.close()


            search_key = str(example_scan_rate) + "mV"
            # Find all names containing "10mVs"
            matching_data = [name for name in data_list if search_key in name]
            print(matching_data)
            plt.figure()
            if matching_data:
                df = myglobals[matching_data[0]]
                df = df[df['Scan'] == int(example_cycle)]
                U = df['WE(1).Potential (V)']
                I = df['WE(1).Current (A)']

                # Separate top and bottom
                upperU, lowerU, upperI, lowerI = separater(U, I, min(U), max(U))

                if apply_gaussian_filter:
                    smoothed_upperI = gaussian_filter(upperI, sigma=1)
                    smoothed_lowerI = gaussian_filter(lowerI, sigma=1)
                else:
                    smoothed_upperI = upperI
                    smoothed_lowerI = lowerI

                plt.scatter(upperU, smoothed_upperI, s=1, c='#1f77b4')
                plt.scatter(lowerU, smoothed_lowerI, s=1, c='#ff7f0e')

                for z in range(len(peak_range_ox)):
                    top_x, top_y = find_max(upperU, smoothed_upperI, peak_range_ox[z][0], peak_range_ox[z][1])
                    bottom_x, bottom_y = find_min(lowerU, smoothed_lowerI, peak_range_re[z][0], peak_range_re[z][1])
                    plt.scatter(top_x, top_y, s=20, c='r')
                    plt.scatter(bottom_x, bottom_y, s=20, c='r')

            plt.xlabel('$Applied potential\,(E)\,/\,V$')
            plt.ylabel('$Current\,(I)\,/\,A$')
            # plt.show()
            to_file2 = os.path.join(self.datapath, "CV_step2_p2.png")
            plt.savefig(to_file2)
            plt.close()


            # Save tmp results
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


        data = self.res_data

        if 'CV' not in data.keys():
            data['CV'] = {}

        if status_msg == '':
            data['CV']['form2'] = {
                'status': 'done',
                'input': all_params,
                'output': {
                    # 'file1': to_file if to_file.startswith("/") else '/' + to_file,
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

    def start4(self, all_params):
        """
        Calculate heterogeneous rate constants (k₀) from peak separation and scan rate using a Laviron-type analysis.

        Parameters:
            all_params (dict): Must contain:
                - input_a: transfer coefficient (alpha)
                - input_n: list of number of electrons for each redox event
                - input_d: list of diffusion coefficients (D)
                - input_t: temperature (K)

        Returns:
            dict: Contains status and generated images with Ψ vs ΔEp and Ψ vs 1/√ν
        """
        status_msg = ''
        try:
            form2_res = self.pkl_load("form2_res.pkl")
            peak_info = form2_res['peak_info']

            ## (Function 4)Rate constant module
            # Input calculate parameter
            # a = 0.5
            # n = [1, 1, 1]
            # D = [1.3942717733456817e-06, 3.8616343823150815e-05, 9.283534073717666e-05]
            # T = 298.15  # 25 degrees Celsius in Kelvin
            a = float(all_params['input_a'])
            n = ast.literal_eval(all_params['input_n'])
            D = ast.literal_eval(all_params['input_d'])
            T = float(ast.literal_eval(all_params['input_t']))



            # Constant numbers that don't change
            F = 96485.33212
            R = 8.314462618

            k_list = []
            res = []
            for i in range(len(n)):
                DelE = peak_info[f'DelE0{i}']
                Scan_Rate = peak_info[f'Scan_Rate{i}']
                Scan_Rate_V = np.array(Scan_Rate) / 1000
                DelE_mV = np.array(DelE) * 1000
                print(f"DelE_mV{i}: ", DelE_mV)

                # Define the lambda function, passing the correct n value
                print(f"a: {type(a)}, F: {type(F)}, R: {type(R)}, T: {type(T)}, n[i]: {type(n[0])}")

                fai_lambda = lambda DelEi: 2.18 * ((a / math.pi) ** 0.5) * math.exp(-((a ** 2 * F) / (R * T)) * n[i] * DelEi)

                # Apply the lambda function to the list of DelE values
                fai = list(map(fai_lambda, DelE))

                # Plotting the results
                plt.figure()
                plt.scatter(DelE_mV, fai, s=5)
                plt.xlabel('$\Delta E_p$ (mV)')
                plt.ylabel('$\Psi$')
                # plt.show()
                img_path1 = os.path.join(self.datapath, "CV_step3_func3_p1.png")
                plt.savefig(img_path1)
                plt.close()

                # Calculate the term [πDnF/RT]^{-1/2}
                term = ((math.pi * D[i] * n[i] * F) / (R * T)) ** (-1 / 2)
                # Calculate x-axis values
                x_value = term * (Scan_Rate_V ** (-1 / 2))
                # Perform linear regression
                slope, intercept = np.polyfit(x_value, fai, 1)

                # Plot fai against the term multiplied by v^(-1/2)
                plt.figure()
                plt.scatter(x_value, fai, s=1)
                # Add linear regression line to the plot
                plt.plot(x_value, slope * np.array(x_value) + intercept, color='red')
                # Display the equation of the linear regression line on the plot
                equation = f"$y = {slope:.4f}x + {intercept:.4f}$"
                plt.text(0.1, 0.9, equation, transform=plt.gca().transAxes)
                plt.xlabel('$[πDnνF/RT]^{-1/2}$' + str(term) + '$v^{-1/2}$')
                plt.ylabel('$\Psi$')
                # Display the slope
                print("Slope:", slope)
                k_list.append(slope)
                # plt.show()
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

        data = self.res_data

        if 'CV' not in data.keys():
            data['CV'] = {}

        if status_msg == '':
            data['CV']['form4'] = {
                'status': 'done',
                'input': all_params,
                'output': {
                    'files': res
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
        Compute the Tafel slope and transfer coefficient (α) using two methods.
        Method 1: d(log J)/dE
        Method 2: Modified Laviron method involving peak current I_p

        Parameters:
            all_params (dict):
                - cycle (int): CV scan cycle to analyze
                - input_n (int): Number of electrons transferred
                - input_t (float): Temperature in K
                - electrode_dia (float): Electrode diameter (cm)
                - current_peak (int): Which peak to use (e.g. 1, 2, 3)

        Returns:
            dict: Result structure with saved plots for both methods
        """
        status_msg = ''
        try:
            form2_res = self.pkl_load("form2_res.pkl")
            peak_info = form2_res['peak_info']
            data_list = form2_res['data_list']
            myglobals = form2_res['globals']


            cycle = int(all_params['cycle'])
            n = int(all_params['input_n'])
            T = float(ast.literal_eval(all_params['input_t']))
            electrode_dia = float(ast.literal_eval(all_params['electrode_dia']))
            A_Real = np.pi * (electrode_dia/2)**2
            Which_Current_Peak = int(all_params['current_peak'])
            cycle_range = range(2, 15)

            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            print("Start:", formatted_time)
            # constant number don't change (not input value!!)
            F = 96485.33212
            R = 8.314462618

            print("peak_info[Ea0]:", peak_info['Ea0'])

            m1_files = []
            for i, var_name in enumerate(data_list):
                df = myglobals[var_name]
                print(var_name)
                scan_rate = Search_scan_rate(var_name)
                name = str(scan_rate) + "mV"

                print(peak_info[f'Ea0'][len(cycle_range) * i + (cycle - cycle_range[0])])
                cycle_df = df[df['Scan'] == cycle]
                Ui = cycle_df['WE(1).Potential (V)']
                Ii = cycle_df['WE(1).Current (A)']
                Ui = np.array(Ui)
                Ii = np.array(Ii)
                Ji = Ii / A_Real

                # Separate top and bottom
                upperU, lowerU, upperJ, lowerJ = separater(Ui, Ji, min(Ui), max(Ui))

                # Apply Gaussian filter (optional)
                apply_gaussian_filter = False  # Set to True to apply the filter, False to not apply the filter

                if apply_gaussian_filter:
                    smoothed_upperJ = gaussian_filter(upperJ, sigma=1)
                    smoothed_lowerJ = gaussian_filter(lowerJ, sigma=1)
                else:
                    smoothed_upperJ = upperJ
                    smoothed_lowerJ = lowerJ

                logJ_upper = special_log(smoothed_upperJ)
                dlogJ_dU = np.gradient(logJ_upper, upperU)
                dU_dlogJ = np.gradient(upperU, logJ_upper)
                Tafel_slope = 1 / dlogJ_dU
                # Calculate the transfer coefficient (alpha)
                alpha = (2.303 * R * T) / (Tafel_slope * n * F)


                # Create a figure with dual y-axes
                fig, ax1 = plt.subplots()
                ax1.set_xlabel('$Applied potential\,(E)\,/\,V$')
                ax1.set_ylabel('$Current\,(I)\,/\,A$')
                ax1.scatter(upperU, smoothed_upperJ, s=1, color=colors[0])
                ax1.tick_params(axis='y', labelcolor=colors[0])

                ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
                ax2.set_ylabel('\u0391', color=colors[1])  # we already handled the x-label with ax1
                ax2.scatter(upperU, alpha, s=1, color=colors[1])
                ax2.set_ylim([-1, 1])  # Limit y-axis for transfer coefficient between -1 and 1
                ax2.tick_params(axis='y', labelcolor=colors[1])

                fig.tight_layout()  # otherwise the right y-label is slightly clipped
                plt.title(f'Tafel Plot and \u0391 for {name} (Cycle {cycle})')
                plt.grid(True)
                # plt.show()
                img_path2 = os.path.join(self.datapath, "CV_step3_func5_m1_p{}.png".format(i))
                plt.savefig(img_path2)
                plt.close()
                m1_files.append(img_path2.split("/")[-1])

            # -------------------------------------
            # Method 2
            # -------------------------------------

            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            print("Start:", formatted_time)

            m2_files = []
            for i, var_name in enumerate(data_list):
                df = myglobals[var_name]
                print(var_name)
                scan_rate = Search_scan_rate(var_name)
                name = str(scan_rate) + "mV"

                #         print(peak_info[f'Ea0'][len(cycle_range)*i+(cycle-cycle_range[0])])
                cycle_df = df[df['Scan'] == cycle]
                Ui = cycle_df['WE(1).Potential (V)']
                Ii = cycle_df['WE(1).Current (A)']
                Ui = np.array(Ui)
                Ii = np.array(Ii)
                Ji = Ii / A_Real
                Ji = Ii
                # Separate top and bottom
                upperU, lowerU, upperI, lowerI = separater(Ui, Ii, min(Ui), max(Ui))

                # Apply Gaussian filter (optional)
                apply_gaussian_filter = False  # Set to True to apply the filter, False to not apply the filter

                if apply_gaussian_filter:
                    smoothed_upperI = gaussian_filter(upperI, sigma=1)
                    smoothed_lowerI = gaussian_filter(lowerI, sigma=1)
                else:
                    smoothed_upperI = upperI
                    smoothed_lowerI = lowerI

                smoothed_upperI = np.array(smoothed_upperI)
                smoothed_lowerI = np.array(smoothed_upperI)

                upperU = np.array(upperU)
                lowerU = np.array(lowerU)

                I_Peak = peak_info[f'Ia{Which_Current_Peak - 1}'][i * len(cycle_range) + (cycle - min(cycle_range))]
                I_term = (I_Peak ** 2) / (I_Peak - smoothed_upperI)
                lnI_term = special_ln(I_term)
                upperO = (F / (R * T)) * upperU

                dlnI_term_dU = np.gradient(lnI_term, upperU)
                alpha = (1 / 2) * ((R * T) / F) * dlnI_term_dU

                #         dlnI_term_dO = np.gradient(lnI_term, upperO)
                #         alpha = (1/2)*dlnI_term_dO

                # Create a figure with dual y-axes
                fig, ax1 = plt.subplots()
                ax1.set_xlabel('$Applied potential\,(E)\,/\,V$')
                ax1.set_ylabel('$Current\,(I)\,/\,A$')
                ax1.scatter(upperU, smoothed_upperI, s=1, color=colors[0])
                ax1.tick_params(axis='y', labelcolor=colors[0])

                ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
                ax2.set_ylabel('Transfer coefficient \u03B1', color=colors[1])  # we already handled the x-label with ax1
                ax2.scatter(upperU, alpha, s=1, color=colors[1])
                ax2.set_ylim([-1, 1])  # Limit y-axis for transfer coefficient between -1 and 1
                ax2.tick_params(axis='y', labelcolor=colors[1])

                fig.tight_layout()  # otherwise the right y-label is slightly clipped
                plt.title(f'Tafel Plot and Derivative for {name} (Cycle {cycle})')
                plt.grid(True)
                # plt.show()
                img_path2 = os.path.join(self.datapath, "CV_step3_func5_m2_p{}.png".format(i))
                plt.savefig(img_path2)
                plt.close()
                m2_files.append(img_path2.split("/")[-1])
        except Exception as e:
            status_msg = str(e)

        data = self.res_data

        if 'CV' not in data.keys():
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
    # This block only runs if the script is executed directly (not imported as a module)

    # Initialize an instance of the CV class
    # Parameters:
    # - "version_test_CV": output folder name for saving results
    # - "data/CV_csv": path to the folder containing input data files
    # - sigma=10.0: standard deviation for Gaussian smoothing (used later)
    c = CV("version_test_CV", "data/CV_csv", sigma=10.0)

    # Run Step 2: Peak detection and parameter extraction
    # Arguments:
    # - method='Max': method for peak detection (e.g., use the maximum point)
    # - peak_range_top: potential window(s) for locating anodic (oxidation) peaks
    # - peak_range_bottom: potential window(s) for locating cathodic (reduction) peaks
    # Note: These are string representations of tuples that will be converted internally
    res = c.start2(
        method='Max',
        peak_range_top='(-1,-0.5),(0,0.2),(0.25,0.5)',
        peak_range_bottom='(-0.9,-0.75),(0,0.125),(0.125,0.25)'
    )

    # Print the result returned by the start2 function (usually a status and file paths)
    print(res)
