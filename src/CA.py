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

def get_num(filename):
    """
    Extracts the first number found in the filename using regex.

    Args:
        filename (str): File name string (e.g., '3PFOA400ppm_75075_CA.xlsx')

    Returns:
        int or None: Extracted number, or None if no match found.

    """
    match = re.search(r'(\d+)', filename)

    if match:
        result = match.group(1)
        return int(result)
    else:
        return None


class CA(BaseModule):
    def __init__(self, version):
        """
        Initialize the CA module with a version identifier.

        Args:
            version (str): Version name or ID for the run.
        """
        super().__init__(version)

    def check_columns(self, data):
        cols = ['Time (s)', 'WE(1).Current (A)', 'WE(1).Potential (V)']
        missing_cols = []
        for d in data:
            df = d['df']
            for col in cols:
                if col not in df.columns:
                    missing_cols.append(col)
        if len(missing_cols) > 0:
            return "error: Missing columns: " + ", ".join(missing_cols)
        return ''

    def step1(self):
        """
        Step 1: Load CA data files, plot potential and current over time, and save outputs.

        Outputs:
            - CA_form1_p1.png: Potential vs Time for all files
            - CA_form1_p2.png: Current vs Time for all files
            - data.json: Metadata and output file paths

        Returns:
            dict: Status and result metadata
        """
        data_file = os.path.join(self.datapath, 'data.json')
        if os.path.exists(data_file):
            todata = json.loads(open(data_file, 'r').read())
        else:
            todata = {'version': self.version}

        if 'CA' not in todata.keys():
            todata['CA'] = {}

        status_msg = ''
        try:
            data = self.read_data()
            status_msg = self.check_columns(data)
            if status_msg == '':
                for d in data:
                    filename = d['filename']
                    df = d['df']

                    t = df['Time (s)']
                    I = df['WE(1).Current (A)']
                    U = df['WE(1).Potential (V)']
                    plt.plot(t, U, linestyle='-', linewidth=1, color='#1f77b4')

                plt.xlabel(r'$\mathit{Time} \,(t) \,/\, \mathrm{s} $')
                plt.ylabel(r'$\mathit{Current} \,(I) \,/\, \mathrm{A}$')
                plt.title('A', loc='left', bbox=dict(facecolor='white', edgecolor='black'))
                # plt.ylim(-2e-5,2e-5)
                # plt.grid()
                # plt.show()
                to_file1 = os.path.join(self.datapath, "CA_form1_p1.png")
                plt.savefig(to_file1)
                plt.close()


                for d in data:
                    filename = d['filename']
                    df = d['df']

                    t = df['Time (s)']
                    I = df['WE(1).Current (A)']
                    U = df['WE(1).Potential (V)']

                    plt.scatter(t, I, s=1, c='#1f77b4')

                plt.xlabel(r'$\mathit{Time} \,(t) \,/\, \mathrm{s} $')
                plt.ylabel(r'$\mathit{Current} \,(I) \,/\, \mathrm{A}$')
                plt.title('B', loc='right', bbox=dict(facecolor='white', edgecolor='black'))
                # plt.ylim(-2e-5,2e-5)
                # plt.grid()
                plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

                to_file2 = os.path.join(self.datapath, "CA_form1_p2.png")
                plt.savefig(to_file2)
                plt.close()

                todata['CA']['form1'] = {
                    'status': 'done',
                    'input': {
                        'uploaded_files': [],
                        # 'sigma': self.sigma
                    },
                    'output': {
                        'file1': to_file1.split("/")[-1],
                        'file2': to_file2.split("/")[-1],
                    }
                }

        except Exception as e:
            status_msg = str(e)

        if status_msg == '':
            with open(data_file, 'w') as f:
                f.write(json.dumps(todata))
                print("saved to: {}".format(data_file))
            return {
                'status': True,
                'version': self.version,
                'message': 'Success',
                'data': todata
            }
        else:
            todata['CA']['form1'] = {
                'status': status_msg,
                'input': {
                    'uploaded_files': [],
                }
            }
            with open(data_file, 'w') as f:
                f.write(json.dumps(todata))
                print("saved to: {}".format(data_file))
            return {
                'status': False,
                'version': self.version,
                'message': status_msg,
                'data': todata
            }


    def step2(self, inter, n, a, c, x_range=''):
        """
        Step 2: Calculate diffusion coefficient D from chronoamperometric data using Cottrell equation.

        Args:
            inter (int): Not used in current implementation.
            n (int): Number of electrons transferred in the reaction.
            a (float): Electrode surface area in cm².
            c (float): Initial analyte concentration in mol/cm³.
            x_range (str): A string specifying the range for regression in the form '[start, end]'.

        Returns:
            dict: A dictionary with image files, regression output, and calculated D values.
        """
        data = self.read_data()
        interval = len(data)
        status_msg = ''
        try:

            # n = 1
            F = 96485
            d_electrode = 0.3
            # A = math.pi * ((d_electrode / 2) ** 2)
            A = a
            print('electrode area (cm2):', A)

            # C0 = 0.000966e-3  # in (mol/cm3)
            C0 = c

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
                j = get_num(filename)

                if j > interval:
                    continue

                t = df['Time (s)'] - df['Time (s)'].iloc[0]
                I = df['WE(1).Current (A)']
                U = df['WE(1).Potential (V)']

                t_inverse_05 = t ** (-0.5)
                Bt = ((n * F * A * C0) / (math.pi ** 0.5)) * t_inverse_05

                # Plot t vs I
                plt.scatter(t, I, s=2, color='#1f77b4')
                plt.xlabel(r'$\mathit{Time} \,(t) \,/\, \mathrm{s} $')
                plt.ylabel(r'$\mathit{Current} \,(I) \,/\, \mathrm{A}$')
                plt.subplots_adjust(left=0.2)  # 将左边距设置为 0.2，单位是相对于图像宽度的比例
                # plt.grid()
                # plt.show()
                to_file1 = os.path.join(self.datapath, "CA_form2_p{}_1.png".format(j))
                plt.savefig(to_file1)
                plt.close()

                Bt = Bt[2:]
                I = I[2:]

                regression_mask = (Bt >= range_start) & (Bt <= range_end)
                Bt = Bt[regression_mask]
                I = I[regression_mask]

                # Perform linear regression Bt vs I
                slope, intercept = np.polyfit(Bt, I, 1)
                D = slope ** 2

                slope_set.append(slope)
                D_set.append(D)

                # Calculate R-squared value
                residuals = I - (slope * Bt + intercept)
                ss_residuals = np.sum(residuals ** 2)
                ss_total = np.sum((I - np.mean(I)) ** 2)
                r_squared = 1 - (ss_residuals / ss_total)

                R2_set.append(r_squared)

                # Plot Bt vs I with the regression line
                plt.scatter(Bt, I, s=2, color='#1f77b4')
                plt.plot(Bt, slope * Bt + intercept, color='red', label='Regression Line')
                plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
                plt.xlabel('$\mathrm{[n \cdot F \cdot A \cdot C_0 \cdot π^{-1/2}]\ t^{-1/2}}$')
                plt.ylabel('$Current\ (\mathrm{I})\ /\ \mathrm{A}$')

                # plt.grid()
                plt.legend()
                plt.subplots_adjust(left=0.2)  # 将左边距设置为 0.2，单位是相对于图像宽度的比例
                # plt.show()
                to_file2 = os.path.join(self.datapath, "CA_form2_p{}_2.png".format(j))
                plt.savefig(to_file2)
                plt.close()

                print(j, "Slope:", slope)
                print(j, "R-squared:", r_squared)
                print(j, "D:", D)
                to_files.append( [
                    to_file1.split("/")[-1],
                    to_file2.split("/")[-1],
                ])

            table = pd.DataFrame([slope_set, D_set, R2_set], index=['slope', 'D', 'R2'])
            # New column names starting from 'interval2'
            length_of_D_set = len(table.loc['D'])
            new_column_names = ['interval{}'.format(i + 2) for i in range(length_of_D_set)]
            # Assign the new column names to the DataFrame
            table.columns = new_column_names
            to_file_csv = os.path.join(self.datapath, "CA_form2.csv")
            table.to_csv(to_file_csv, index=True, sep=',')
            print("saved to: {}".format(to_file_csv))
        except Exception as e:
            status_msg = str(e)


        todata = self.res_data
        if 'CA' not in todata.keys():
            todata['CA'] = {}

        if status_msg == '':
            todata['CA']['form2'] = {
                'status': 'done',
                'input': {
                    'uploaded_files': [],
                    # 'sigma': self.sigma
                },
                'output': {
                    'files': to_files,
                    'csv_file': to_file_csv.split("/")[-1],
                }
            }
            self.save_result_data(todata)
            return {
                'status': True,
                'version': self.version,
                'message': 'Success',
                'data': todata
            }
        else:
            todata['CA']['form2'] = {
                'status': status_msg,
                'input': {
                    'uploaded_files': [],
                    # 'sigma': self.sigma
                }
            }
            self.save_result_data(todata)
            return {
                'status': False,
                'version': self.version,
                'message': 'Success',
                'data': todata
            }



if __name__ == '__main__':
    c = CA("version_test_CV")


