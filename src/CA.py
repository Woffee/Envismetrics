"""
CA.py - Chronoamperometry (CA) Analysis Module
----------------------------------------------

This module is part of the Envismetrics software suite and provides both visualization
and diffusion coefficient analysis for Chronoamperometry (CA) data. It reads time-dependent
potential and current measurements from electrochemical experiments and offers a standardized
approach to visualize raw signals and compute key kinetic parameters using the Cottrell equation.

Core Functions:
---------------
1. `step1()`: Raw Data Visualization
   - Generates two plots per dataset:
     - A: Applied Potential vs Time
     - B: Current vs Time
   - Useful for preliminary data inspection and quality control.

2. `step2(inter, n, a, c, x_range)`: Diffusion Coefficient Calculation
   - Applies the Cottrell equation to estimate diffusion coefficients (D) from current-time curves.
   - Performs linear regression on transformed data (Bt vs I), where Bt ~ t^(-1/2).
   - Produces:
     - Plot of raw current vs time.
     - Plot of regression used to extract D.
     - Summary table (CSV) with slope, D, and R² for each dataset.

Features:
---------
- Supports batch processing of multiple CA files.
- Configurable analysis range (`x_range`) for linear regression.
- Automatically handles file saving, figure generation, and output management.
- Saves intermediate results and metadata to `data.json` and CSV for reproducibility.

Dependencies:
-------------
- numpy, pandas, matplotlib, scipy, sklearn
- config.py
- BaseModule.py

Date: 2025
"""


import os
import json
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from BaseModule import BaseModule

class CA(BaseModule):
    def __init__(self, version):
        """
        Initialize the Chronoamperometry (CA) module.

        This class inherits from BaseModule and sets up the environment
        for processing CA data associated with a given analysis version.

        Args:
            version (str): Unique identifier for this session/run.
                           Used to organize output directories and results.
        """
        super().__init__(version)

    def _save_metadata(self, todata, status_msg=''):
        """
        Helper method to save metadata and return standardized response.
        
        Args:
            todata (dict): Metadata dictionary to save
            status_msg (str): Error message if any, empty string for success
            
        Returns:
            dict: Standardized response with status, version, message, and data
        """
        data_file = os.path.join(self.datapath, 'data.json')
        with open(data_file, 'w') as f:
            json.dump(todata, f)
            print(f"saved to: {data_file}")
        
        return {
            'status': status_msg == '',
            'version': self.version,
            'message': 'Success' if status_msg == '' else status_msg,
            'data': todata
        }

    def check_columns(self, data):
        """
        Validate that all required columns are present in the input DataFrames.
        Uses intelligent column detection to support multiple file formats.

        Args:
            data (list): List of dictionaries, each containing a 'df' key with a pandas DataFrame.

        Returns:
            str: Empty string if all columns are present; otherwise, returns an error message
                 listing all missing columns.
        """
        missing_cols = set()
        for d in data:
            df = d['df']
            detected = self.detect_column_names(df)
            
            # Check if essential columns were detected
            if detected['time'] is None:
                missing_cols.add('Time column (e.g., "Time (s)" or "time/s")')
            if detected['current'] is None:
                missing_cols.add('Current column (e.g., "WE(1).Current (A)" or "current/A")')
            if detected['potential'] is None:
                missing_cols.add('Potential column (e.g., "WE(1).Potential (V)" or "potential/V")')
        
        return f"error: Missing columns: {', '.join(missing_cols)}" if missing_cols else ''

    def step1(self):
        """
        Step 1: Visualization of raw Chronoamperometry data.

        This method:
        1. Loads pre-processed CA data using `read_data()`.
        2. Verifies required columns using `check_columns()`.
        3. Generates and saves two plots:
            - Plot A: Applied potential (V) vs. time (s)
            - Plot B: Current (A) vs. time (s)
        4. Saves output metadata to a JSON file (`data.json`) for reproducibility.

        Output Files:
            - CA_form1_p1.png: Potential vs Time
            - CA_form1_p2.png: Current vs Time

        Returns:
            dict: A structured response containing success status, version, result paths,
                  or error message if any step fails.
        """
        todata = self.res_data.copy()
        if 'CA' not in todata:
            todata['CA'] = {}

        status_msg = ''
        try:
            data = self.read_data()
            status_msg = self.check_columns(data)
            
            if status_msg == '':
                # Plot A: Potential vs Time
                for d in data:
                    df = d['df']
                    plt.plot(df['Time (s)'], df['WE(1).Potential (V)'], 
                            linestyle='-', linewidth=1, color='#1f77b4')

                plt.title('A', loc='left', bbox=dict(facecolor='white', edgecolor='black'))
                to_file1 = self.save_plot("CA_form1_p1.png", 
                                         xlabel='time/s', 
                                         ylabel='Applied potential/V',
                                         legend=False)

                # Plot B: Current vs Time
                for d in data:
                    df = d['df']
                    plt.scatter(df['Time (s)'], df['WE(1).Current (A)'], s=1, c='#1f77b4')

                plt.title('B', loc='right', bbox=dict(facecolor='white', edgecolor='black'))
                plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
                to_file2 = self.save_plot("CA_form1_p2.png",
                                         xlabel='time/s',
                                         ylabel='Current/A',
                                         legend=False)

                todata['CA']['form1'] = {
                    'status': 'done',
                    'input': {'uploaded_files': []},
                    'output': {
                        'file1': os.path.basename(to_file1),
                        'file2': os.path.basename(to_file2),
                    }
                }

        except Exception as e:
            status_msg = str(e)
            todata['CA']['form1'] = {
                'status': status_msg,
                'input': {'uploaded_files': []}
            }

        return self._save_metadata(todata, status_msg)

    def step2(self, inter, n, a, c, x_range=''):
        """
        Step 2: Calculate diffusion coefficient (D) from chronoamperometric data using the Cottrell equation.

        WHAT:
            This function applies the Cottrell equation to estimate the diffusion coefficient (D)
            from current-time (I-t) chronoamperometry data. The Cottrell equation states:

                I(t) = (nFAc) / (π^0.5 * t^0.5)

            which can be transformed into a linear relationship:
                I ∝ t^(-1/2)

            By computing a transformation Bt = (nFAc/π^0.5)·t^(-1/2), and performing linear regression
            of I vs Bt, we obtain the slope. The diffusion coefficient is then calculated as D = slope².

        INPUT:
            inter (int): Reserved for future use (currently unused).
            n (int): Number of electrons involved in the redox process.
            a (float): Electrode area in cm².
            c (float): Bulk concentration of electroactive species in mol/cm³.
            x_range (str): Optional string in format "[start, end]", specifying Bt range used for regression.

        OUTPUT:
            dict: Dictionary with:
                - status (True/False)
                - generated image file names (current vs time and regression)
                - calculated slope, diffusion coefficient D, and R² in a CSV

        WHY:
            This step enables quantitative kinetic analysis of mass transport during electrochemical reactions,
            using the well-established Cottrell equation. It is particularly valuable for estimating D in
            systems involving diffusion-limited processes.
        """
        data = self.read_data()
        interval = len(data)
        status_msg = ''
        
        todata = self.res_data.copy()
        if 'CA' not in todata:
            todata['CA'] = {}
            
        try:
            F = 96485  # Faraday constant in C/mol
            print('electrode area (cm2):', a)

            # Parse x_range input string into numerical range
            range_start, range_end = x_range.replace("[", "").replace("]", "").split(',')
            range_start = float(range_start)
            range_end = float(range_end)

            slope_set = []
            D_set = []
            R2_set = []
            to_files = []

            for d in data:
                filename = d['filename']
                df = d['df']
                j = self.get_num(filename)  # Extract index from filename for plotting/tracking

                if j > interval:
                    continue

                # Extract relevant columns
                t = df['Time (s)'] - df['Time (s)'].iloc[0]  # Normalize time (start from 0)
                I = df['WE(1).Current (A)']

                # Compute transformed Bt term based on Cottrell equation
                Bt = ((n * F * a * c) / (math.pi ** 0.5)) * (t ** (-0.5))

                # Plot 1: Raw current vs time
                plt.scatter(t, I, s=2, color='#1f77b4')
                plt.xlabel('Time (s)')
                plt.ylabel('Current (A)')
                plt.subplots_adjust(left=0.2)
                to_file1 = os.path.join(self.datapath, f"CA_form2_p{j}_1.png")
                plt.savefig(to_file1)
                plt.close()

                # Trim unstable initial points (first 2) and apply Bt window range
                Bt = Bt[2:]
                I = I[2:]
                regression_mask = (Bt >= range_start) & (Bt <= range_end)
                Bt = Bt[regression_mask]
                I = I[regression_mask]

                # Linear regression: I = slope * Bt + intercept
                slope, intercept = np.polyfit(Bt, I, 1)
                D = slope ** 2  # Based on squared slope per Cottrell derivation

                slope_set.append(slope)
                D_set.append(D)

                # Calculate R² value
                residuals = I - (slope * Bt + intercept)
                ss_residuals = np.sum(residuals ** 2)
                ss_total = np.sum((I - np.mean(I)) ** 2)
                r_squared = 1 - (ss_residuals / ss_total)
                R2_set.append(r_squared)

                # Plot 2: Regression Bt vs I with best-fit line
                plt.scatter(Bt, I, s=2, color='#1f77b4')
                plt.plot(Bt, slope * Bt + intercept, color='red', label='Regression Line')
                plt.xlabel('nFAC₀ π⁻¹/² t⁻¹/²')
                plt.ylabel('Current (A)')
                plt.legend()
                plt.subplots_adjust(left=0.2)
                to_file2 = os.path.join(self.datapath, f"CA_form2_p{j}_2.png")
                plt.savefig(to_file2)
                plt.close()

                print(j, "Slope:", slope)
                print(j, "R-squared:", r_squared)
                print(j, "D:", D)
                to_files.append([os.path.basename(to_file1), os.path.basename(to_file2)])

            # Assemble CSV table
            table = pd.DataFrame([slope_set, D_set, R2_set], index=['slope', 'D', 'R2'])
            table.columns = [f'interval{i+2}' for i in range(len(D_set))]
            to_file_csv = os.path.join(self.datapath, "CA_form2.csv")
            table.to_csv(to_file_csv, index=True, sep=',')
            print("saved to:", to_file_csv)

            todata['CA']['form2'] = {
                'status': 'done',
                'input': {'uploaded_files': []},
                'output': {
                    'files': to_files,
                    'D_set': D_set,
                    'csv_file': os.path.basename(to_file_csv),
                }
            }

        except Exception as e:
            status_msg = str(e)
            todata['CA']['form2'] = {
                'status': status_msg,
                'input': {'uploaded_files': []}
            }

        self.save_result_data(todata)
        return {
            'status': status_msg == '',
            'version': self.version,
            'message': 'Success' if status_msg == '' else status_msg,
            'data': todata
        }

if __name__ == '__main__':
    # === Entry point for direct execution ===
    # WHAT:
    #   When this script (CA.py) is executed directly (not imported as a module),
    #   this block will be triggered to test or demonstrate core functionality.
    #
    # WHY:
    #   Useful for debugging, local testing, or demonstrating CA class behavior.
    #   This can be extended to run step1() or step2() with test inputs.

    # Initialize the CA module with a version tag.
    # INPUT:
    #   - "version_test_CV": Used as folder name under /outputs for saving figures and results.
    c = CA("version_test_CV")

    # Optional: Run example analysis
    # Example (uncomment to run step1 visualization):
    # res = c.step1()
    # print(res)

    # Example (uncomment to run step2 with dummy params):
    # res = c.step2(
    #     inter=1,
    #     n=1,
    #     a=0.07,  # electrode area in cm²
    #     c=1e-6,  # analyte concentration in mol/cm³
    #     x_range='[0, 1e-3]'  # Bt range for regression
    # )
    # print(res)

