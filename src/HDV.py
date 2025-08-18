"""
HDV.py - Hydrodynamic Voltammetry (HDV) Analysis Module
--------------------------------------------------------

This module is part of the Envismetrics software suite and performs comprehensive
analysis of Hydrodynamic Voltammetry (HDV) data, including both Levich and
Koutecky-Levich plots for determining diffusion coefficients.

Main Features:
--------------
1. **step1(sigma)**:
   - Loads all valid HDV data files (Excel or TXT), sorted by RPM.
   - Visualizes raw and Gaussian-filtered current vs potential curves.
   - Stores PNG figures for raw and smoothed voltammograms.

2. **step2_1(all_params)**:
   - Levich plot analysis for each potential point or interval.
   - Calculates slope (B) and diffusion coefficient (D).
   - Produces:
     - Individual regression plots across rotation rates.
     - Summary slope-D plots vs potential.
     - Exportable CSV file with current vs √ω data.

3. **step2_2(all_params)**:
   - Koutecky-Levich plot analysis for kinetic and diffusion current separation.
   - Estimates diffusion coefficients using inverse current vs ω⁻¹ᐟ².
   - Produces:
     - Regression line plots per potential.
     - Combined B-D dual-axis plots.
     - Exportable CSV of calculated parameters.

Core Utilities:
---------------
- `read_data()`: Handles file parsing, RPM extraction, and CSV caching.
- `rpm_to_rads()`: Converts RPM to angular velocity (rad/s).
- Utility functions: `find_y`, `extract_rpm`, `check_files`, etc.

Inputs:
-------
- User-defined electrochemical parameters: number of electrons (n), area (A), viscosity (ν), and bulk concentration (C).
- Potential range, number of points, and sampling interval.

Output:
-------
- PNG plots, CSV results, and progress tracking in structured JSON.

Dependencies:
-------------
- numpy, pandas, matplotlib, scipy, sklearn
- BaseModule.py
- JSON configuration files

Date: 2025
"""
import re
import numpy as np
import pandas as pd
import os as os
import matplotlib
import matplotlib.pyplot as plt
import math
import json
from BaseModule import BaseModule
from sklearn.linear_model import LinearRegression
from scipy.ndimage import gaussian_filter
matplotlib.use('Agg')

# Function to find y value (I) corresponding to given x value (potential)
# It finds the index of the element in the array x that is closest to the target_x value using

def find_y(x, y, target_x):
    """
    WHAT:
        Given two 1D arrays `x` and `y` (of equal length), return the value in `y`
        that corresponds to the value in `x` closest to `target_x`.

    INPUT:
        x : array-like
            Independent variable array (e.g., time, voltage).
        y : array-like
            Dependent variable array (e.g., current, intensity).
        target_x : float
            The x-value we want to find the closest match for.

    OUTPUT:
        y_value : float
            The corresponding y-value at the nearest x to `target_x`.

    WHY:
        Experimental or simulation data often doesn't have exact x values;
        this allows nearest-neighbor interpolation to approximate the y-value.
    """
    # Find the index of the x-value closest to target_x
    index = np.argmin(np.abs(x - target_x))
    # Return the corresponding y-value
    return y[index]


def find_y_exact(x, y, target_x):
    """
    WHAT:
        Returns the y-values where x matches `target_x` exactly.

    INPUT:
        x : array-like
            Independent variable array.
        y : array-like
            Dependent variable array.
        target_x : float or int
            The x-value to match exactly.

    OUTPUT:
        y_values : array
            All y-values at positions where x == target_x.
            (May be empty if no exact match is found.)

    WHY:
        Use this when exact x-values are expected and meaningful.
        Ensures strict matching, useful for discrete systems.
    """
    # Find indices where x equals target_x
    index = np.where(x == target_x)[0]
    # Return the matching y-values
    return y[index]


def rpm_to_rads(rpm):
    """
    WHAT:
        Convert rotational speed in RPM (revolutions per minute) to angular
        velocity in radians per second.

    INPUT:
        rpm : float or int
            Rotational speed in revolutions per minute.

    OUTPUT:
        rad_per_sec : float
            Angular velocity in radians per second.

    WHY:
        Most physics/engineering formulas involving angular motion
        require radians/sec as standard SI unit.
    """
    rps = rpm / 60              # Convert RPM to RPS (revolutions per second)
    rad_per_sec = 2 * math.pi * rps  # Convert to radians/second
    return rad_per_sec


def reorder(filename):
    """
    WHAT:
        Extract an integer RPM value from a filename string (e.g., 'test_500rpm.xlsx').

    INPUT:
        filename : str
            The name of the file containing an RPM tag like '1000rpm'.

    OUTPUT:
        rpm : int
            Extracted RPM as integer, or -1 if not found.

    WHY:
        Used to numerically sort or organize files based on RPM value.
        Returns -1 for filenames without valid RPM to handle edge cases safely.
    """
    match = re.search(r'(\d+)rpm', filename)
    if match:
        return int(match.group(1))  # Extract numeric portion of 'xxxrpm'
    else:
        return -1  # Fallback value when RPM is missing


def extract_rpm(filename):
    """
    WHAT:
        Extract the string label (e.g., '1200rpm') from the filename for labeling purposes.

    INPUT:
        filename : str
            Filename including RPM tag, like 'data_1200rpm.txt'.

    OUTPUT:
        rpm_label : str or None
            The full RPM label (e.g., '1200rpm') or None if not found.

    WHY:
        Useful for adding readable RPM tags to plots, legends, logs, etc.
        Uses a regex pattern that works with or without underscores before the RPM.
    """
    pattern = r'(?:^|_)(\d+rpm)\.'  # Matches 'xxxrpm.' optionally preceded by underscore or start
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    else:
        return None


def check_files(files):
    """
    WHAT:
        Verify that all files in the list have supported extensions (.xlsx or .txt).

    INPUT:
        files : list of str
            List of filenames to validate.

    OUTPUT:
        is_valid : bool
            True if all files are .xlsx or .txt; False otherwise.

    WHY:
        Prevents downstream processing errors by filtering out unsupported file types.
        Acts as an early safeguard during batch processing.
    """
    for f in files:
        ext = f.split('.')[-1].lower()  # Extract file extension
        if ext not in ['xlsx', 'txt']:
            return False  # Invalid file type found
    return True  # All files passed


class HDV(BaseModule):
    """
    HDV (Hydrodynamic Voltammetry) module for data preprocessing and visualization.

    This module reads electrochemical data files tagged with RPM values,
    converts them into a unified format, applies optional Gaussian smoothing,
    and generates potential-current plots for exploratory analysis.

    Attributes:
        version (str): current analysis version, inherited from BaseModule
        files_info (str): path to JSON file containing info about input data files
        datapath (str): folder to save output images
        res_data (dict): internal result dictionary updated with each step
    """

    def __init__(self, version):
        """
        Initialize HDV module by setting version and base attributes.

        Parameters:
            version (str): version string to organize outputs
        """
        super().__init__(version)

    def read_data(self):
        """
        Read all valid data files listed in the self.files_info JSON file.

        WHAT:
            - Extracts file names and corresponding RPM tags
            - Sorts files by RPM numerically
            - Reads data from .xlsx (or cached .csv) and .txt files
            - Returns a dictionary mapping RPM → DataFrame

        RETURNS:
            dict: { '1000rpm': DataFrame, '1500rpm': DataFrame, ... }

        WHY:
            Standardizes data format and ensures all input files are
            accessible and numerically sorted for analysis.
        """
        with open(self.files_info, 'r') as f:
            info_list = json.loads(f.read())

        files = []
        real_file_path = {}
        for info in info_list:
            # 'filename' is the display name (used as key), 'existed_filename' is the actual path
            f = info['filename']
            file = info['existed_filename']
            if not os.path.isfile(file):
                continue  # Skip missing files
            files.append(f)
            real_file_path[f] = file

        # Sort files numerically by RPM extracted from filename
        files = sorted(files, key=reorder)

        data = {}
        for f in files:
            file = real_file_path[f]
            if not os.path.isfile(file):
                continue
            print(f)

            rpm = extract_rpm(f)
            if rpm is None:
                continue
            print(rpm)

            if file.endswith(".xlsx"):
                csv_file = file + ".csv"
                if os.path.exists(csv_file):
                    # Use cached CSV version if available
                    data[rpm] = pd.read_csv(csv_file, sep=',')
                else:
                    # Parse Excel file and cache as CSV
                    data0 = pd.ExcelFile(file)
                    data[rpm] = data0.parse('Sheet1')
                    data[rpm].to_csv(csv_file, sep=',', index=False)
                    print("saved csv file to {}".format(csv_file))
            elif file.endswith(".txt"):
                # .txt files are assumed to be semicolon-separated
                df = pd.read_csv(file, delimiter=';')
                data[rpm] = df

        print("data: ", len(data))
        return data

    def step1(self, sigma=10):
        """
        Visualize raw and smoothed current-potential curves for all RPM files.

        WHAT:
            - Reads experimental data for each RPM
            - Generates two figures:
              1) Raw current vs. potential scatter plot
              2) Smoothed current (Gaussian filter) vs. potential
            - Saves both plots as PNG images
            - Stores result metadata in self.res_data['HDV']['form1']

        PARAMETERS:
            sigma (float): standard deviation for Gaussian smoothing

        RETURNS:
            dict: {
                'status': True,
                'version': self.version,
                'message': 'Success',
                'data': res_data
            }

        WHY:
            Provides visual feedback and preprocessing validation for HDV experiments.
        """
        data = self.read_data()

        # ---- Figure 1: Raw current vs potential ----
        for rpm, df in data.items():
            E = df['WE(1).Potential (V)']     # Extract potential column
            I = df['WE(1).Current (A)']       # Extract current column
            print("length of E:", len(E))
            plt.scatter(E, I, label=rpm, s=1)  # Scatter plot per RPM
        plt.xlabel('Applied potential/V')
        plt.ylabel('Current/A')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        plt.legend()

        # Save raw scatter plot
        to_file1 = os.path.join(self.datapath, "step1_p1.png")
        plt.savefig(to_file1)
        plt.close()

        # ---- Figure 2: Smoothed current (Gaussian filter) ----
        combined_data = pd.DataFrame()  # Container for all RPM columns (side-by-side)

        for rpm, df in data.items():
            E = df['Potential applied (V)']       # Note: different column name
            I = df['WE(1).Current (A)']

            # Apply Gaussian filter to smooth current
            smoothed_I = gaussian_filter(I, sigma=sigma)
            print("length of E:", len(E))
            plt.scatter(E, smoothed_I, label=rpm, s=1)

            # Append E and I for this RPM to combined_data
            rpm_data = pd.DataFrame({
                'Potential (V)' + rpm: E,
                'Current (A)' + rpm: I
            })
            combined_data = pd.concat([combined_data, rpm_data], axis=1)

        plt.xlabel('Applied potential/V')
        plt.ylabel('Current/A')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        plt.legend()

        # Save smoothed plot
        to_file2 = os.path.join(self.datapath, "step1_p2.png")
        plt.savefig(to_file2)
        plt.close()

        # ---- Save results ----
        data = self.res_data
        if 'HDV' not in data.keys():
            data['HDV'] = {}
        data['HDV']['form1'] = {
            'status': 'done',
            'input': {
                'sigma': sigma,
            },
            'output': {
                'file1': os.path.basename(to_file1),
                'file2': os.path.basename(to_file2),
            }
        }
        self.save_result_data(data)

        # Return result metadata
        return {
            'status': True,
            'version': self.version,
            'message': 'Success',
            'data': data
        }


    def _step2_1_fig1(self, data, all_params ):
        """
        WHAT:
            Generate multiple Levich plots based on selected potentials from RDE data.
            Each plot corresponds to one potential value, showing the linear relationship
            between limiting current and square root of rotation rate.

        INPUT:
            data (dict): RPM-tagged DataFrames, usually from read_data()
            all_params (dict): analysis parameters from GUI or user config, including:
                - input_N: number of electrons
                - input_A: electrode area (cm^2)
                - input_V: kinematic viscosity (cm^2/s)
                - input_C: concentration (mol/cm^3)
                - input_range: potential range to extract (e.g. "(0.1,0.4)")
                - input_n_points: number of potential points to sample in range
                - input_interval: unused in this function but parsed

        OUTPUT:
            tuple:
                to_file1 (str): path to saved plot image (Levich lines)
                to_file2 (str): path to saved CSV of underlying w^0.5 vs I data

        WHY:
            Levich analysis quantifies diffusion behavior in hydrodynamic voltammetry.
            Linear fits across RPMs at each potential yield diffusion coefficients D.
        """

        # Parse electrochemical input parameters
        input_n = int(all_params['input_N'])          # number of electrons (n)
        input_v = float(all_params['input_V'])        # kinematic viscosity (ν)
        input_c = float(all_params['input_C'])        # analyte concentration (mol/cm^3)

        # Extract and parse potential range string into float bounds
        input_range = all_params['input_range'].replace("(", "").replace(")", "").split(",")
        n_points = int(all_params['input_n_points'])  # number of potential points to analyze

        # Define potential window
        start_value = float(input_range[0])
        end_value = float(input_range[1])

        # Constants for electrode geometry and calculation
        n = input_n
        relectrode = 0.15  # Radius of RDE electrode (cm)
        print('electrode Radius is :', relectrode, 'cm')
        A = np.pi * (relectrode ** 2)  # Electrode area (cm²)
        print('surface area is :', A, 'cm²')
        v = input_v
        C = input_c

        Levich_plotshow_data = pd.DataFrame()  # Stores combined w^0.5 and current data

        # Re-read raw data internally (ignores passed-in `data`)
        data = self.read_data()

        # Extract reference potential column from first dataset (any RPM)
        E = None
        for rpm, df in data.items():
            E = df['WE(1).Potential (V)']
            break

        # Determine index range corresponding to [start_value, end_value]
        if E.iloc[0] < E.iloc[-1]:  # Ascending sweep
            start_index = E[E >= start_value].idxmin()
            end_index = E[E <= end_value].idxmax()
            print("E in Ascending order")
        else:  # Descending sweep
            start_index = E[E <= end_value].idxmax()
            end_index = E[E >= start_value].idxmin()
            print("E in Descending order")

        print("start_index:", start_index, "end_index:", end_index)

        # Sample `n_points` uniformly within [start_index, end_index]
        points_number = np.linspace(start_index, end_index, n_points, dtype=int)
        E_selected = E.iloc[points_number]  # Selected potentials to analyze

        Levich_slope = []      # Store slope (for D calculation)
        Levich_intercept = []  # Store intercept
        D = []                 # Store estimated diffusion coefficients

        # Retrieve Gaussian filter sigma from step1 results (if available)
        try:
            sigma = self.res_data['HDV']['form1']['input']['sigma']
        except Exception as e:
            sigma = 10.0  # Default smoothing factor

        # Loop through each selected potential to generate individual Levich plots
        for j, potential in enumerate(E_selected):
            print(f"potential {j + 1} : {potential:.4f} V")
            I_elected = []  # Stores smoothed current values at this potential
            w_05 = []       # Stores sqrt(angular rotation rate)

            for rpm, df in data.items():
                # Convert RPM to angular velocity in rad/s and then sqrt(w)
                w_i = rpm_to_rads(int(rpm.replace('rpm', '')))
                w05_i = w_i ** 0.5
                w_05.append(w05_i)

                # Extract smoothed current at given potential
                E = df['Potential applied (V)']
                I = df['WE(1).Current (A)']
                smoothed_I = gaussian_filter(I, sigma=sigma)
                I_potential_i = find_y(E, smoothed_I, potential)
                I_elected.append(I_potential_i)

            # Plot experimental points: current vs sqrt(angular velocity)
            plt.scatter(w_05, I_elected, s=3)

            # Save data to DataFrame for export
            potential_data = pd.DataFrame({
                'w_05' + " {:.2f}".format(potential): w_05,
                'Im' + " {:.2f}".format(potential): I_elected
            })
            Levich_plotshow_data = pd.concat([Levich_plotshow_data, potential_data], axis=1)

            # Fit linear model: I = k·w^0.5 + b
            coeffs = np.polyfit(w_05, I_elected, 1)
            Levich_slope_i = coeffs[0]
            Levich_intercept_i = coeffs[1]
            Levich_slope.append(Levich_slope_i)
            Levich_intercept.append(Levich_intercept_i)

            # Generate regression line for plot
            x_regression = np.linspace(min(w_05), max(w_05), 100)
            y_regression = np.polyval(coeffs, x_regression)

            # Estimate diffusion coefficient D from Levich slope
            B = np.abs(Levich_slope_i)
            F = 96485.3321  # Faraday constant (C/mol)
            D23 = B / (0.62 * n * F * A * (v ** -(1 / 6)) * C)
            D_i = D23 ** (3 / 2)
            D.append(D_i)

            # Plot regression line
            plt.plot(x_regression, y_regression, label=f'{potential:.2f}V')

        # Finalize and save figure
        plt.xlabel('$[Rotation Rate/(Rad/s)]^{1/2}$')
        plt.ylabel('Limit current/A')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        plt.legend(loc='lower left')

        to_file1 = os.path.join(self.datapath, "HDV_step2_1_p1.png")
        plt.savefig(to_file1)
        plt.close()

        # Export numeric data as CSV
        to_file2 = os.path.join(self.datapath, "HDV_step2_1_Levich_plotshow_data.csv")
        Levich_plotshow_data.to_csv(to_file2, sep=',', index=False)

        return to_file1, to_file2



    def _step2_1_fig2(self, data, all_params):
        """
        WHAT:
            Perform Levich analysis over a continuous range of potentials using a specified interval.
            For each selected potential, perform linear regression of limiting current (Il) vs. sqrt(angular velocity).
            Plot the resulting Levich slope (B) and calculated diffusion coefficient (D) vs. potential.

        INPUT:
            data (dict): Experimental datasets keyed by RPM, each as a DataFrame.
            all_params (dict): User-defined analysis parameters, including:
                - input_N: number of electrons
                - input_A: electrode area (unused in this function, overridden internally)
                - input_V: kinematic viscosity (cm^2/s)
                - input_C: analyte concentration (mol/cm^3)
                - input_range: potential range string, e.g. "(0.1, 0.4)"
                - input_n_points: number of points to sample (used in fig1 only)
                - input_interval: step size in number of points between selected potentials

        OUTPUT:
            to_file1 (str): File path of saved dual-axis plot image (.png), showing:
                - B vs. potential (left y-axis)
                - D vs. potential (right y-axis)

        WHY:
            This function provides a more continuous, fine-grained Levich analysis than fig1,
            helping to visualize how transport properties evolve across a potential sweep.
        """
        # === Parse user input parameters ===
        input_n = int(all_params['input_N'])       # Number of electrons transferred
        input_v = float(all_params['input_V'])     # Kinematic viscosity
        input_c = float(all_params['input_C'])     # Reactant concentration

        # Parse potential range from string to float
        input_range = all_params['input_range'].replace("(", "").replace(")", "").split(",")
        interval = int(all_params['input_interval'])    # Sampling interval (e.g., every 3rd point)

        # Define bounds of potential range
        start_value = float(input_range[0])
        end_value = float(input_range[1])

        # === Define constants ===
        n = input_n
        relectrode = 0.15  # Radius of RDE electrode (cm)
        print('electrode Radius is :', relectrode, 'cm')
        A = np.pi * (relectrode ** 2)  # Electrode area (cm^2)
        print('surface area is :', A, 'cm²')
        v = input_v
        C = input_c

        # === Load data ===
        data = self.read_data()
        E = None
        for rpm, df in data.items():
            E = df['WE(1).Potential (V)']  # Use potential from first RPM
            break

        # === Determine potential indices ===
        if E.iloc[0] < E.iloc[-1]:  # Ascending order
            start_index = E[E >= start_value].idxmin()
            end_index = E[E <= end_value].idxmax()
            print("E in Ascending order")
        else:  # Descending order
            start_index = E[E <= end_value].idxmax()
            end_index = E[E >= start_value].idxmin()
            print("E in Descending order")

        print("start_index:", start_index, "end_index:", end_index)
        E_selected = E.iloc[start_index:end_index + 1]  # Full range of potentials in that region
        print('Number of Selected Potential:', len(E_selected))

        # === Initialize result containers ===
        Levich_slope = []      # Linear fit slopes (B) at each potential
        Levich_intercept = []  # Linear fit intercepts (not used)
        E_plot = []            # Store potential values plotted

        # Try to retrieve Gaussian smoothing sigma from step1
        try:
            sigma = self.res_data['HDV']['form1']['input']['sigma']
        except Exception as e:
            sigma = 10.0  # Default fallback

        # === Main loop: sample points from E_selected every 'interval' steps ===
        for j in range(0, len(E_selected), interval):
            potential = E_selected.iloc[j]
            print('now processing', "index:", j, "E:", potential)

            w_05 = []  # Square root of angular velocity (x-axis for Levich plot)
            Il = []    # Limiting current at selected potential

            for rpm, df in data.items():
                # Convert rpm to sqrt(angular velocity)
                w_i = rpm_to_rads(int(rpm.replace('rpm', '')))
                w05_i = w_i ** 0.5
                w_05.append(w05_i)

                # Get smoothed current value at this potential
                E_irpm = df['Potential applied (V)']
                I_irpm = df['WE(1).Current (A)']
                I_irpm = gaussian_filter(I_irpm, sigma=sigma)

                I_potential_i = find_y(E_irpm, I_irpm, potential)
                Il.append(I_potential_i)

            # === Linear regression: I = B·w^0.5 + intercept ===
            coeffs = np.polyfit(w_05, Il, 1)
            Bi = coeffs[0]             # Slope
            intercept_i = coeffs[1]   # Intercept

            # Append results for plotting
            Levich_slope.append(Bi)
            Levich_intercept.append(intercept_i)
            E_plot.append(potential)

        # === Calculate diffusion coefficient D from Levich slope B ===
        Levich_slope = np.array(Levich_slope)
        B = np.abs(Levich_slope)
        F = 96485.3321  # Faraday constant
        D23 = B / (0.62 * n * F * A * (v ** -(1 / 6)) * C)
        D = D23 ** (3 / 2)

        # === Plot B and D vs potential on dual Y-axes ===
        ig, ax1 = plt.subplots()

        # First Y-axis: Slope B
        ax1.scatter(E_plot, Levich_slope, s=2, color='#1f77b4')
        ax1.set_xlabel('Applied potential/V')
        ax1.set_ylabel('Corresponding Slope B', color='k')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Second Y-axis: Diffusion Coefficient D
        ax2 = ax1.twinx()
        ax2.scatter(E_plot, D, s=2, color='#ff7f0e')
        ax2.set_ylabel('Diffusion coefficient(D)/cm²/s', color='k')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')

        to_file1 = os.path.join(self.datapath, "HDV_step2_1_p2.png")
        plt.savefig(to_file1)
        plt.close()

        return to_file1

    def step2_1(self, all_params):
        """
        WHAT:
            Wrapper function to perform Levich analysis (version 2) and generate visual outputs.

        INPUT:
            all_params (dict): All parameters for analysis, including:
                - Electrode and solution parameters (n, A, v, C)
                - Potential range and point selection settings
                - Gaussian smoothing sigma (loaded from step1 result)

        OUTPUT:
            Saves:
              - PNG: scatter plots of current vs sqrt(ω), regression lines
              - CSV: raw current values for each potential
              - PNG: slope and diffusion coefficient vs potential
            And records all outputs into self.res_data for further use.

        WHY:
            To automate multi-point Levich analysis for a rotating disk electrode,
            and record all result files and parameters in a unified JSON-style result structure.
        """
        data = self.res_data  # Load result container from previous steps

        # Call the figure subfunctions (each returns a file path)
        to_file1, excel_file = self._step2_1_fig1(data, all_params)
        to_file2 = self._step2_1_fig2(data, all_params)

        # Save results in structured JSON format
        if 'HDV' not in data.keys():
            data['HDV'] = {}
        data['HDV']['form2_1'] = {
            'status': 'done',
            'input': all_params,
            'output': {
                'file1': os.path.basename(to_file1),
                'file2': os.path.basename(to_file2),
                'excel_file': os.path.basename(excel_file),
            }
        }
        self.save_result_data(data)


    def _step2_2_fig1(self, data, all_params):
        """
        WHAT:
            Perform Koutecky-Levich analysis at selected potentials.
            Plot inverse current vs inverse sqrt(angular velocity), extract kinetic current and diffusion coefficient.

        INPUT:
            data (dict): Dictionary of RPM-tagged experimental data.
            all_params (dict): User-defined parameters:
                - input_N: number of electrons
                - input_A: electrode area
                - input_V: viscosity
                - input_C: concentration
                - input_range: potential range to analyze
                - input_n_points: number of potential points to select
                - input_interval: spacing between each selected point

        OUTPUT:
            Returns:
                - to_file1: path to PNG file of regression plot
                - to_file2: path to CSV with extracted parameters (slope, D)
            Also logs all intermediate data into a CSV file.

        WHY:
            Koutecky-Levich analysis allows separation of kinetic and diffusion-limited current
            in rotating disk electrode measurements. This function automates multi-point extraction and fitting.
        """
        # === Parse input parameters ===
        input_n = int(all_params['input_N'])
        input_v = float(all_params['input_V'])
        input_c = float(all_params['input_C'])

        input_range = all_params['input_range'].replace("(","").replace(")", "").split(",")
        n_points = int(all_params['input_n_points'])

        # === Define physical constants ===
        start_value = float(input_range[0])
        end_value = float(input_range[1])

        n = input_n
        relectrode = 0.15  # RDE radius (cm)
        print('electrode Radius is :', relectrode, 'cm')
        A = np.pi * (relectrode ** 2)
        print('surface area is :', A, 'cm²')
        v = input_v
        C = input_c

        # === Read experimental data ===
        Koutecky_Levich_plotshow_data = pd.DataFrame()
        data = self.read_data()
        E = None
        for rpm, df in data.items():
            E = df['Potential applied (V)']
            break

        # === Determine potential range index ===
        if E.iloc[0] < E.iloc[-1]:  # Ascending
            start_index = E[E >= start_value].idxmin()
            end_index = E[E <= end_value].idxmax()
            print("E in Ascending order")
        else:
            start_index = E[E <= end_value].idxmax()
            end_index = E[E >= start_value].idxmin()
            print("E in Descending order")
        print("start_index:", start_index, "end_index:", end_index)

        points_number = np.linspace(start_index, end_index, n_points, dtype=int)
        E_selected = E.iloc[points_number]

        # === Result containers ===
        Koutecky_Levich_slope = []
        Koutecky_Levich_intercept = []
        D = []

        # Get sigma for smoothing
        try:
            sigma = self.res_data['HDV']['form1']['input']['sigma']
        except Exception as e:
            sigma = 10.0

        # === Main loop over selected potentials ===
        for j, potential in enumerate(E_selected):
            print(f"potential {j + 1} : {potential:.4f} V")
            inverse_Im_elected = []
            w_n05 = []

            for rpm, df in data.items():
                w_i = rpm_to_rads(int(rpm.replace('rpm', '')))
                wn05_i = w_i ** -0.5  # x-axis: w^-0.5
                w_n05.append(wn05_i)

                E = df['Potential applied (V)']
                I = df['WE(1).Current (A)']
                smoothed_I = gaussian_filter(I, sigma=sigma)
                I_potential_i = find_y(E, smoothed_I, potential)

                inverse_Im_elected.append(1 / I_potential_i)

            plt.scatter(w_n05, inverse_Im_elected, s=3)

            # Save raw data for each potential into DataFrame
            potential_data = pd.DataFrame({
                'w_n05' + " {:.2f}".format(potential): w_n05,
                'inverse_Im' + " {:.2f}".format(potential): inverse_Im_elected
            })
            Koutecky_Levich_plotshow_data = pd.concat([Koutecky_Levich_plotshow_data, potential_data], axis=1)

            # === Linear regression ===
            coeffs = np.polyfit(w_n05, inverse_Im_elected, 1)
            slope_i = coeffs[0]
            intercept_i = coeffs[1]

            Koutecky_Levich_slope.append(slope_i)
            Koutecky_Levich_intercept.append(intercept_i)

            x_regression = np.linspace(min(w_n05), max(w_n05), 100)
            y_regression = np.polyval(coeffs, x_regression)
            plt.plot(x_regression, y_regression, label=f'{potential:.2f}V')

            # === Calculate D from slope ===
            KL_slope = slope_i ** -1
            B = np.abs(KL_slope)
            F = 96485.3321
            D23 = B / (0.62 * n * F * A * (v ** -(1 / 6)) * C)
            D_i = D23 ** (3 / 2)
            D.append(D_i)

        # === Finalize plot ===
        plt.xlabel('$[Rotation Rate/(Rad/s)]^{-1/2}$')
        plt.ylabel('$[measured current/A]^{-1}$')
        plt.yscale('log')  # Log scale for better separation
        plt.legend(loc='upper left')

        to_file1 = os.path.join(self.datapath, "HDV_step2_2_p1.png")
        plt.savefig(to_file1)
        plt.close()

        # === Save parameters to CSV ===
        table_content = {
            'Potential': E_selected,
            'Koutecky Levich slope': Koutecky_Levich_slope,
            'Diffusion Coefficient': D
        }
        table = pd.DataFrame(table_content)
        to_file2 = os.path.join(self.datapath, "HDV_step2_2_Calculated_Parameters.csv")
        table.to_csv(to_file2, sep=',', index=False)

        return to_file1, to_file2


    def _step2_2_fig2(self, data, all_params):
        """
        WHAT:
            Plot the inverse slope (B) and calculated diffusion coefficient (D)
            as a function of applied potential using Koutecky–Levich theory.

        INPUT:
            data (dict): Dictionary containing RPM-tagged experimental datasets.
            all_params (dict): Dictionary of user input parameters:
                - input_N: number of electrons transferred
                - input_A: electrode area
                - input_V: kinematic viscosity of solution (cm²/s)
                - input_C: concentration of reactant (mol/cm³)
                - input_range: tuple-like string defining potential window
                - input_n_points: number of total points to scan
                - input_interval: index interval between selected points

        OUTPUT:
            to_file1 (str): File path to saved PNG plot of B vs E and D vs E (dual-axis figure)

        WHY:
            This figure summarizes how mass transport behavior (via D) and reaction
            control (via B) vary with applied potential, offering mechanistic insight.
        """
        # === Parse parameters ===
        input_n = int(all_params['input_N'])
        input_v = float(all_params['input_V'])
        input_c = float(all_params['input_C'])

        input_range = all_params['input_range'].replace("(", "").replace(")", "").split(",")
        interval = int(all_params['input_interval'])

        # === Range for potential axis ===
        start_value = float(input_range[0])
        end_value = float(input_range[1])

        # === Physical constants ===
        n = input_n
        relectrode = 0.15  # cm, radius of rotating electrode
        print('electrode Radius is :', relectrode, 'cm')
        A = np.pi * (relectrode ** 2)
        print('surface area is :', A, 'cm²')
        v = input_v
        C = input_c

        # === Read data and extract potential axis ===
        data = self.read_data()
        E = None
        for rpm, df in data.items():
            E = df['Potential applied (V)']
            break

        # === Locate index bounds in potential window ===
        if E.iloc[0] < E.iloc[-1]:  # Ascending scan
            start_index = E[E >= start_value].idxmin()
            end_index = E[E <= end_value].idxmax()
            print("E in Ascending order")
        else:  # Descending scan
            start_index = E[E <= end_value].idxmax()
            end_index = E[E >= start_value].idxmin()
            print("E in Descending order")
        print("start_index:", start_index, "end_index:", end_index)

        E_selected = E.iloc[start_index:end_index + 1]
        print('Number of Selected Potential:', len(E_selected))

        # === Initialize containers for output values ===
        Koutecky_Levich_slope = []
        E_plot = []

        # === Gaussian smoothing sigma from previous step ===
        try:
            sigma = self.res_data['HDV']['form1']['input']['sigma']
        except Exception as e:
            sigma = 10.0

        # === Main loop: step through selected potentials ===
        for j in range(0, len(E_selected), interval):
            potential = E_selected.iloc[j]
            print('now processing', "index:", j, "E:", potential)

            wn05 = []   # x-axis: ω^{-1/2}
            Iln1 = []   # y-axis: 1/I (from smoothed current)

            for rpm, df in data.items():
                # Compute angular velocity and its inverse square root
                w_i = rpm_to_rads(int(rpm.replace('rpm', '')))
                wn05_i = w_i ** -0.5
                wn05.append(wn05_i)

                # Extract smoothed current at matched potential
                E_irpm = df['WE(1).Potential (V)']
                I_irpm = df['WE(1).Current (A)']
                I_irpm = gaussian_filter(I_irpm, sigma=sigma)
                I_potential_i = find_y(E_irpm, I_irpm, potential)
                Iln1.append(I_potential_i ** -1)

            # === Linear regression: 1/I vs ω^{-1/2} ===
            coeffs = np.polyfit(wn05, Iln1, 1)
            Bi = coeffs[0]
            Koutecky_Levich_slope.append(Bi)
            E_plot.append(potential)

        # === Calculate diffusion coefficient from B ===
        KL_slope = np.array(Koutecky_Levich_slope) ** -1
        B = np.abs(KL_slope)
        F = 96485.3321
        D23 = B / (0.62 * n * F * A * (v ** -(1 / 6)) * C)
        D = D23 ** (3 / 2)

        # === Dual-axis plot: B and D vs potential ===
        fig, ax1 = plt.subplots()

        ax1.scatter(E_plot, KL_slope, s=2, color='#1f77b4')
        ax1.set_xlabel('Applied potential/V')
        ax1.set_ylabel('Corresponding Slope B', color='k')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Create secondary y-axis for D
        ax2 = ax1.twinx()
        ax2.scatter(E_plot, D, s=2, color='#ff7f0e')
        ax2.set_yscale('log')  # Log scale better captures D variation
        ax2.set_ylabel('Diffusion coefficient(D)/cm²/s', color='k')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')

        # Save figure
        to_file1 = os.path.join(self.datapath, "HDV_step2_2_p2.png")
        plt.savefig(to_file1)
        plt.close()

        return to_file1


    def step2_2(self, all_params):
        """
        WHAT:
            Step 2.2: Perform Koutecky-Levich (K-L) analysis, including two main plots:
                (1) 1/I vs ω⁻¹ᐟ² with linear regression to extract kinetic current
                (2) B vs E and D vs E (slope and diffusion coefficient vs potential)

        INPUT:
            all_params (dict): Dictionary of parameters provided by the user interface, including:
                - input_N: electron transfer number
                - input_A: electrode area (cm²)
                - input_V: kinematic viscosity (cm²/s)
                - input_C: reactant concentration (mol/cm³)
                - input_range: potential range string "(E_start, E_end)"
                - input_n_points: number of evenly spaced points to scan in potential range
                - input_interval: interval of selection across potential array

        OUTPUT:
            Saves two figure files and one CSV data file for analysis results.
            Updates `self.res_data['HDV']['form2_2']` with input/output tracking.

        WHY:
            Koutecky–Levich analysis enables decoupling of kinetic and diffusion-limited currents.
            Plotting the results helps interpret rate control behavior and quantify transport properties.
        """
        data = self.res_data

        # === Call internal figure generation methods ===
        to_file1, excel_file = self._step2_2_fig1(data, all_params)  # 1/I vs w⁻¹/² + slope + D
        to_file2 = self._step2_2_fig2(data, all_params)              # Slope/D vs E plot

        # === Store output file references into result data dictionary ===
        if 'HDV' not in data.keys():
            data['HDV'] = {}

        data['HDV']['form2_2'] = {
            'status': 'done',
            'input': all_params,
            'output': {
                'file1': os.path.basename(to_file1),  # Only save the filename
                'file2': os.path.basename(to_file2),
                'excel_file': os.path.basename(excel_file),
            }
        }

        # === Save results to disk ===
        self.save_result_data(data)


# === Entry point for debugging or direct execution ===
if __name__ == '__main__':
    # Initialize the HDV class with working folder and metadata file path
    hdv = HDV('version_0423_111216', "uploads/version_0423_111216/fileinfo_version_0423_111216.json")

    # Run the HDV Step 2.1 module (Levich analysis)
    # You may replace with `hdv.step2_2()` to run Koutecky-Levich instead
    hdv.start2_1()

