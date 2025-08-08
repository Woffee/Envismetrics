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
    index = np.argmin(np.abs(x - target_x))
    return y[index]

def find_y_exact(x,y,target_x):
    index = np.where(x == target_x)[0]
    return y[index]

def rpm_to_rads(rpm):
    rps = rpm / 60  # Convert RPM to RPS (revolutions per second)
    rad_per_sec = 2 * math.pi * rps  # Convert RPS to rad/s
    return rad_per_sec

def reorder(filename):
    match = re.search(r'(\d+)rpm', filename)
    if match:
        return int(match.group(1))
    else:
        # Handle files without RPM values
        return -1  # You can use any default value or treatment

def extract_rpm(filename):
    pattern = r'(?:^|_)(\d+)(?=rpm)(?:rpm)?(?:_|\.|$)'
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    else:
        return None

def check_files(files):
    for f in files:
        ext = f.split('.')[-1].lower()
        if ext not in ['xlsx', 'txt']:
            return False
    return True

class HDV(BaseModule):
    def __init__(self, version):
        super().__init__(version)


    def read_data(self):
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

        data = {}
        for f in files:
            file = real_file_path[f]
            if not os.path.isfile(file):
                continue
            print("filename:", f)
            rpm = extract_rpm(f)
            if rpm is None:
                continue
            print("rpm:", rpm)
            if file.endswith(".xlsx"):
                csv_file = file + ".csv"
                if os.path.exists(csv_file):
                    data[rpm] = pd.read_csv(csv_file, sep=',')
                else:
                    data0 = pd.ExcelFile(file)
                    data[rpm] = data0.parse('Sheet1')
                    data[rpm].to_csv(csv_file, sep=',', index=False)
                    print("saved csv file to {}".format(csv_file))
            elif file.endswith(".txt"):
                df = pd.read_csv(file, delimiter=';')
                data[rpm] = df
        print("data: ", len(data))
        return data

    def check_columns(self, data):
        cols = ['WE(1).Current (A)', 'WE(1).Potential (V)']
        print("check_columns:", cols)
        missing_cols = []
        for rpm, df in data.items():
            for col in cols:
                if col not in df.columns:
                    missing_cols.append(col)
        print("missing_cols:", missing_cols)
        if len(missing_cols) > 0:
            return "error: Missing columns: " + ", ".join(missing_cols)
        return ''

    def step1(self, sigma=10):
        data = self.read_data()
        status_msg = self.check_columns(data)
        if status_msg == '':
            try:
                for rpm, df in data.items():
                    E = df['WE(1).Potential (V)']
                    I = df['WE(1).Current (A)']
                    print("length of E:", len(E))
                    plt.scatter(E, I, label=rpm, s=1)
                plt.xlabel('Applied potential/V')
                plt.ylabel('Current/A')
                plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
                #plt.xlim()
                # plt.ylim(-0.0002,0.0003)
                plt.legend()
                # plt.grid()
                # plt.show()
                to_file1 = os.path.join(self.datapath, "step1_p1.png")
                plt.savefig(to_file1)
                plt.close()

                # plot figure modlue with Gaussian filter

                # Create an empty DataFrame to store the data
                combined_data = pd.DataFrame()

                # Define the standard deviation (sigma) for the Gaussian filter

                for rpm, df in data.items():
                    E = df['Potential applied (V)']
                    I = df['WE(1).Current (A)']

                    # Apply the Gaussian filter to the 'Current (A)'
                    smoothed_I = gaussian_filter(I, sigma=sigma)
                    print("length of E:", len(E))
                    plt.scatter(E, smoothed_I, label=rpm, s=1)

                    # Create a new DataFrame for the current RPM
                    rpm_data = pd.DataFrame({'Potential (V)' + rpm: E, 'Current (A)' + rpm: I})
                    # Concatenate the data for this RPM to the right of the combined_data DataFrame
                    combined_data = pd.concat([combined_data, rpm_data], axis=1)

                plt.xlabel('Applied potential/V')
                plt.ylabel('Current/A')
                plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
                # plt.xlim(-1.0,0.5)
                # plt.ylim(-0.00006, 0.00008)
                plt.legend()
                # plt.grid()
                # plt.show()
                to_file2 = os.path.join(self.datapath, "step1_p2.png")
                plt.savefig(to_file2)
                plt.close()
            except Exception as e:
                status_msg = str(e)

        data = self.res_data
        if 'HDV' not in data.keys():
            data['HDV'] = {}

        if status_msg == '':
            data['HDV']['form1'] = {
                'status': 'done',
                'input': {
                    'sigma': sigma,
                },
                'output': {
                    'file1': to_file1.split("/")[-1],
                    'file2': to_file2.split("/")[-1],
                    # 'img1': '/outputs/version_test_CV/form2.jpg',
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
            data['HDV']['form1'] = {
                'status': status_msg,
                'input': {
                    'sigma': sigma,
                }
            }
            self.save_result_data(data)

            return {
                'status': False,
                'version': self.version,
                'message': status_msg,
                'data': data
            }

    def _step2_1_fig1(self, data, all_params ):
        input_n = int(all_params['input_N'])
        input_a = float(all_params['input_A'])
        input_v = float(all_params['input_V'])
        input_c = float(all_params['input_C'])

        input_range = all_params['input_range'].replace("(", "").replace(")", "").split(",")
        n_points = int(all_params['input_n_points'])  # Number of points to select
        interval = int(all_params['input_interval'])

        # Define constants and parameters_These are setting parameter
        start_value = float(input_range[0])  # Starting value of the range for potential
        end_value = float(input_range[1])  # Ending value of the range for potential

        # These are calculation parameter
        n = input_n
        relectrode = 0.15  # Radius of the rotate electrode
        print('electrode Radius is :', relectrode, 'cm')
        A = np.pi * (relectrode ** 2)
        print('surface area is :', A, 'cm\u00b2')
        v = input_v  # kinematic viscosity of the solution (ν - cm2/s),
        C = input_c  # in mol/cm3

        # Load data
        Levich_plotshow_data = pd.DataFrame()

        data = self.read_data()
        E = None
        for rpm, df in data.items():
            E = df['WE(1).Potential (V)']
            break

        # Calculate the corresponding indices within the range
        if E.iloc[0] < E.iloc[-1]:  # Ascending order
            start_index = E[E >= start_value].idxmin()
            end_index = E[E <= end_value].idxmax()
            print("E in Ascending order")
        else:  # Descending order
            start_index = E[E <= end_value].idxmax()
            end_index = E[E >= start_value].idxmin()
            print("E in Descending order")
        print("start_index:", start_index, "end_index:", end_index)
        points_number = np.linspace(start_index, end_index, n_points, dtype=int)
        E_selected = E.iloc[points_number]
        Levich_slope = []
        Levich_intercept = []
        D = []

        try:
            sigma = self.res_data['HDV']['form1']['input']['sigma']
        except Exception as e:
            sigma = 10.0

        for j, potential in enumerate(E_selected):
            # find the corresponding I
            print(f"potential {j + 1} : {potential:.4f} V")
            I_elected = []
            w_05 = []

            for rpm, df in data.items():
                # x axis（w）
                w_i = rpm_to_rads(int(rpm.replace('rpm', '')))
                w05_i = w_i ** 0.5
                w_05.append(w05_i)

                # y axis (Ii)
                E = df['Potential applied (V)']
                I = df['WE(1).Current (A)']
                # Apply the Gaussian filter to the 'Current (A)'
                smoothed_I = gaussian_filter(I, sigma=sigma)

                I_potential_i = find_y(E, smoothed_I, potential)
                # print(I_potential_i)
                I_elected.append(I_potential_i)

            plt.scatter(w_05, I_elected, s=3)

            # Create a new DataFrame for the current RPM

            potential_data = pd.DataFrame(
                {'w_05' + " {:.2f}".format(potential): w_05, 'Im' + " {:.2f}".format(potential): I_elected})

            # Concatenate the data for this RPM to the right of the combined_data DataFrame
            Levich_plotshow_data = pd.concat([Levich_plotshow_data, potential_data], axis=1)

            # Perform linear regression
            coeffs = np.polyfit(w_05, I_elected, 1)

            # Store the regression information
            Levich_slope_i = coeffs[0]
            Levich_intercept_i = coeffs[1]
            Levich_slope.append(Levich_slope_i)
            Levich_intercept.append(Levich_intercept_i)

            x_regression = np.linspace(min(w_05), max(w_05), 100)
            y_regression = np.polyval(coeffs, x_regression)

            B = np.abs(Levich_slope_i)
            F = 96485.3321
            D23 = B / (0.62 * n * F * A * (v ** -(1 / 6)) * C)
            D_i = D23 ** (3 / 2)

            D.append(D_i)

            # Plot the regression line
            plt.plot(x_regression, y_regression, label=f'{potential:.2f}V')

        plt.xlabel(r'$[Rotation\ Rate\ (\omega)\ /\ \mathrm{rad\cdot s}^{-1}]^{1/2}$')
        plt.ylabel(r'$Limit current\ (I_{\mathrm{lim}})\ /\ \mathrm{A}$')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        plt.legend(loc='upper left', bbox_to_anchor=(1.05, 1), borderaxespad=0.)

        # plt.grid()
        to_file1 = os.path.join(self.datapath, "HDV_step2_1_p1.png")
        plt.savefig(to_file1)
        plt.close()

        to_file2 = os.path.join(self.datapath, "HDV_step2_1_Levich_plotshow_data.csv")
        Levich_plotshow_data.to_csv(to_file2, sep=',', index=False)
        return to_file1, to_file2


    def _step2_1_fig2(self, data, all_params):
        input_n = int(all_params['input_N'])
        input_a = float(all_params['input_A'])
        input_v = float(all_params['input_V'])
        input_c = float(all_params['input_C'])

        input_range = all_params['input_range'].replace("(", "").replace(")", "").split(",")
        n_points = int(all_params['input_n_points'])  # Number of points to select
        interval = int(all_params['input_interval'])

        # Define constants and parameters_These are setting parameter
        start_value = float(input_range[0])  # Starting value of the range for potential
        end_value = float(input_range[1])  # Ending value of the range for potential

        # These are calculation parameter
        n = input_n
        relectrode = 0.15  # Radius of the rotate electrode
        print('electrode Radius is :', relectrode, 'cm')
        A = np.pi * (relectrode ** 2)
        print('surface area is :', A, 'cm\u00b2')
        v = input_v  # kinematic viscosity of the solution (ν - cm2/s),
        C = input_c  # in mol/cm3

        # Load data
        # Levich_plotshow_data = pd.DataFrame()

        data = self.read_data()
        E = None
        for rpm, df in data.items():
            E = df['WE(1).Potential (V)']
            break

        # Calculate the corresponding indices within the range
        if E.iloc[0] < E.iloc[-1]:  # Ascending order
            start_index = E[E >= start_value].idxmin()
            end_index = E[E <= end_value].idxmax()
            print("E in Ascending order")
        else:  # Descending order
            start_index = E[E <= end_value].idxmax()
            end_index = E[E >= start_value].idxmin()
            print("E in Descending order")
        print("start_index:", start_index, "end_index:", end_index)
        E_selected = E.iloc[start_index:end_index + 1]
        print('Number of Selected Potential:', len(E_selected))
        Levich_slope = []
        Levich_intercept = []
        D = []
        E_plot = []

        try:
            sigma = self.res_data['HDV']['form1']['input']['sigma']
        except Exception as e:
            sigma = 10.0

        for j in range(0, len(E_selected), interval):
            potential = E_selected.iloc[j]

            print('now processing', "index:", j, "E:", potential)
            w_05 = []
            Il = []

            for rpm, df in data.items():
                # x axis（w）
                w_i = rpm_to_rads(int(rpm.replace('rpm', '')))
                w05_i = w_i ** 0.5
                w_05.append(w05_i)

                # y axis (Ii)
                E_irpm = df['Potential applied (V)']
                I_irpm = df['WE(1).Current (A)']

                # Apply the Gaussian filter to the 'Current (A)'
                I_irpm = gaussian_filter(I_irpm, sigma=sigma)

                I_potential_i = find_y(E_irpm, I_irpm, potential)
                Il.append(I_potential_i)

            # Perform linear regression
            coeffs = np.polyfit(w_05, Il, 1)
            Bi = coeffs[0]
            intercept_i = coeffs[1]
            Levich_slope.append(Bi)
            Levich_intercept.append(intercept_i)
            E_plot.append(potential)

        # calculate D from B
        # check these parameter
        Levich_slope = np.array(Levich_slope)
        B = np.abs(Levich_slope)
        F = 96485.3321
        D23 = B / (0.62 * n * F * A * (v ** -(1 / 6)) * C)
        D = D23 ** (3 / 2)

        ig, ax1 = plt.subplots()

        # Scatter plot for the first y-axis
        ax1.scatter(E_plot, Levich_slope, s=2, color='#1f77b4')
        ax1.set_xlabel('Applied potential/V')
        ax1.set_ylabel('Corresponding Slope B', color='k')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Create a second y-axis
        ax2 = ax1.twinx()

        # Scatter plot for the second y-axis
        ax2.scatter(E_plot, D, s=2, color='#ff7f0e')
        ax2.set_ylabel('Diffusion coefficient(D)/cm\u00b2/s', color='k')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')

        # plt.grid()
        # plt.show()
        to_file1 = os.path.join(self.datapath, "HDV_step2_1_p2.png")
        plt.savefig(to_file1)
        plt.close()

        return to_file1

    def step2_1(self, all_params):
        """ Step 2 Levich Analysis Moudle V2 """
        data = self.res_data
        status_msg = ''
        try:
            to_file1, excel_file = self._step2_1_fig1(data, all_params)
            to_file2 = self._step2_1_fig2(data, all_params)
        except Exception as e:
            status_msg = str(e)

        if 'HDV' not in data.keys():
            data['HDV'] = {}

        if status_msg == '':
            data['HDV']['form2_1'] = {
                'status': 'done',
                'input': all_params,
                'output': {
                    'file1': to_file1.split("/")[-1],
                    'file2': to_file2.split("/")[-1],
                    'excel_file': excel_file.split("/")[-1],
                    # 'img1': '/outputs/version_test_CV/form2.jpg',
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
            data['HDV']['form2_1'] = {
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

    def _step2_2_fig1(self, data, all_params):
        input_n = int(all_params['input_N'])
        input_a = float(all_params['input_A'])
        input_v = float(all_params['input_V'])
        input_c = float(all_params['input_C'])

        input_range = all_params['input_range'].replace("(","").replace(")", "").split(",")
        n_points = int(all_params['input_n_points']) # Number of points to select
        interval = int(all_params['input_interval'])

        # Define constants and parameters_These are setting parameter
        start_value = float(input_range[0]) # Starting value of the range for potential
        end_value = float(input_range[1])  # Ending value of the range for potential

        # These are calculation parameter
        n = input_n
        relectrode = 0.15  # Radius of the rotate electrode
        print('electrode Radius is :', relectrode, 'cm')
        A = np.pi * (relectrode ** 2)
        print('surface area is :', A, 'cm\u00b2')
        v = input_v  # kinematic viscosity of the solution (ν - cm2/s),
        C = input_c  # in mol/cm3

        # Load data
        Koutecky_Levich_plotshow_data = pd.DataFrame()

        data = self.read_data()
        E = None
        for rpm, df in data.items():
            E = df['Potential applied (V)']
            break

        # Calculate the corresponding indices within the range
        # start_index = E[E >= start_value].idxmin()
        # end_index = E[E <= end_value].idxmax()
        if E.iloc[0] < E.iloc[-1]:  # Ascending order
            start_index = E[E >= start_value].idxmin()
            end_index = E[E <= end_value].idxmax()
            print("E in Ascending order")
        else:  # Descending order
            start_index = E[E <= end_value].idxmax()
            end_index = E[E >= start_value].idxmin()
            print("E in Descending order")
        print("start_index:", start_index, "end_index:", end_index)


        points_number = np.linspace(start_index, end_index, n_points, dtype=int)
        E_selected = E.iloc[points_number]
        Koutecky_Levich_slope = []
        Koutecky_Levich_intercept = []
        D = []

        try:
            sigma = self.res_data['HDV']['form1']['input']['sigma']
        except Exception as e:
            sigma = 10.0

        for j, potential in enumerate(E_selected):
            # find the corresponding I
            print(f"potential {j + 1} : {potential:.4f} V")
            inverse_Im_elected = []
            w_n05 = []

            for rpm, df in data.items():

                # x axis（w）
                w_i = rpm_to_rads(int(rpm.replace('rpm', '')))
                wn05_i = w_i ** -0.5
                w_n05.append(wn05_i)

                # y axis (Ii)
                E = df['Potential applied (V)']
                I = df['WE(1).Current (A)']
                # Apply the Gaussian filter to the 'Current (A)'
                smoothed_I = gaussian_filter(I, sigma=sigma)

                I_potential_i = find_y(E, smoothed_I, potential)

                inverse_Im_elected.append(1 / I_potential_i)

            plt.scatter(w_n05, inverse_Im_elected, s=3)

            # Create a new DataFrame for the current RPM

            potential_data = pd.DataFrame({'w_n05' + " {:.2f}".format(potential): w_n05,
                                           'inverse_Im' + " {:.2f}".format(potential): inverse_Im_elected})

            # Concatenate the data for this E to the right of the DataFrame
            Koutecky_Levich_plotshow_data = pd.concat([Koutecky_Levich_plotshow_data, potential_data], axis=1)

            # Perform linear regression
            coeffs = np.polyfit(w_n05, inverse_Im_elected, 1)

            # Store the regression information
            Koutecky_Levich_slope_i = coeffs[0]
            Koutecky_Levich_intercept_i = coeffs[1]
            Koutecky_Levich_slope.append(Koutecky_Levich_slope_i)
            Koutecky_Levich_intercept.append(Koutecky_Levich_intercept_i)

            x_regression = np.linspace(min(w_n05), max(w_n05), 100)
            y_regression = np.polyval(coeffs, x_regression)

            # Calculate D from Koutecky_Levich_slope_i
            KL_slope = np.array(Koutecky_Levich_slope_i) ** -1
            B = np.abs(KL_slope)
            F = 96485.3321
            D23 = B / (0.62 * n * F * A * (v ** -(1 / 6)) * C)
            D_i = D23 ** (3 / 2)

            D.append(D_i)

            # Plot the regression line
            plt.plot(x_regression, y_regression, label=f'{potential:.2f}V')

        plt.xlabel(r'$[Rotation\ Rate\ (\omega)\ /\ \mathrm{rad\cdot s}^{-1}]^{1/2}$')
        plt.ylabel(r'$Limit current\ (I_{\mathrm{lim}})\ /\ \mathrm{A}$')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        plt.legend(loc='upper left', bbox_to_anchor=(1.05, 1), borderaxespad=0.)

        # plt.grid()

        to_file1 = os.path.join(self.datapath, "HDV_step2_2_p1.png")
        plt.savefig(to_file1)
        plt.close()

        # Create DataFrame
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
        input_n = int(all_params['input_N'])
        input_a = float(all_params['input_A'])
        input_v = float(all_params['input_V'])
        input_c = float(all_params['input_C'])

        input_range = all_params['input_range'].replace("(", "").replace(")", "").split(",")
        n_points = int(all_params['input_n_points'])  # Number of points to select
        interval = int(all_params['input_interval'])

        # Define constants and parameters_These are setting parameter
        start_value = float(input_range[0])  # Starting value of the range for potential
        end_value = float(input_range[1])  # Ending value of the range for potential


        # These are calculation parameter
        n = input_n
        relectrode = 0.15  # Radius of the rotate electrode
        print('electrode Radius is :', relectrode, 'cm')
        A = np.pi * (relectrode ** 2)
        print('surface area is :', A, 'cm\u00b2')
        v = input_v  # kinematic viscosity of the solution (ν - cm2/s),
        C = input_c  # in mol/cm3

        # Load data
        Koutecky_Levich_plotshow_data = pd.DataFrame()

        data = self.read_data()
        E = None
        for rpm, df in data.items():
            E = df['Potential applied (V)']
            break

        # Calculate the corresponding indices within the range
        if E.iloc[0] < E.iloc[-1]:  # Ascending order
            start_index = E[E >= start_value].idxmin()
            end_index = E[E <= end_value].idxmax()
            print("E in Ascending order")
        else:  # Descending order
            start_index = E[E <= end_value].idxmax()
            end_index = E[E >= start_value].idxmin()
            print("E in Descending order")
        print("start_index:", start_index, "end_index:", end_index)
        E_selected = E.iloc[start_index:end_index + 1]
        print('Number of Selected Potential:', len(E_selected))

        Koutecky_Levich_slope = []
        Koutecky_Levich_intercept = []
        D = []
        E_plot = []

        try:
            sigma = self.res_data['HDV']['form1']['input']['sigma']
        except Exception as e:
            sigma = 10.0

        for j in range(0, len(E_selected), interval):
            potential = E_selected.iloc[j]

            print('now processing', "index:", j, "E:", potential)
            wn05 = []
            Iln1 = []

            for rpm, df in data.items():

                # x axis（w）
                w_i = rpm_to_rads(int(rpm.replace('rpm', '')))
                wn05_i = w_i ** -0.5
                wn05.append(wn05_i)

                # y axis (Ii)
                E_irpm = df['WE(1).Potential (V)']
                I_irpm = df['WE(1).Current (A)']
                # Apply the Gaussian filter to the 'Current (A)'
                I_irpm = gaussian_filter(I_irpm, sigma=sigma)

                I_potential_i = find_y(E_irpm, I_irpm, potential)
                Iln1.append(I_potential_i ** -1)

            # Perform linear regression
            coeffs = np.polyfit(wn05, Iln1, 1)
            Bi = coeffs[0]
            Koutecky_Levich_slope.append(Bi)
            E_plot.append(potential)

        # calculate D from B
        # check these parameter
        KL_slope = np.array(Koutecky_Levich_slope) ** -1
        B = np.abs(KL_slope)
        F = 96485.3321
        D23 = B / (0.62 * n * F * A * (v ** -(1 / 6)) * C)
        D = D23 ** (3 / 2)

        ig, ax1 = plt.subplots()

        # Scatter plot for the first y-axis
        ax1.scatter(E_plot, KL_slope, s=2, color='#1f77b4')
        ax1.set_xlabel('$Applied\ potential\ (E)\ /\ V$')
        ax1.set_ylabel('$Corresponding\ Slope\ (B)$', color='k')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Create a second y-axis
        ax2 = ax1.twinx()

        # Scatter plot for the second y-axis
        ax2.scatter(E_plot, D, s=2, color='#ff7f0e')
        ax2.set_ylabel('$Diffusion\ coefficient\ (\mathrm{D})\ /\ \mathrm{cm\cdot s}^{-1}$', color='k')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')

        # plt.grid()

        to_file1 = os.path.join(self.datapath, "HDV_step2_2_p2.png")
        plt.savefig(to_file1)
        plt.close()

        return to_file1

    def step2_2(self, all_params):
        """ Step 2 Koutecky-Levich Analysis Moudle """

        data = self.res_data
        status_msg = ''
        try:
            to_file1, excel_file = self._step2_2_fig1(data, all_params)
            to_file2 = self._step2_2_fig2(data, all_params)
        except Exception as e:
            status_msg = str(e)

        if 'HDV' not in data.keys():
            data['HDV'] = {}

        if status_msg == '':
            data['HDV']['form2_2'] = {
                'status': 'done',
                'input': all_params,
                'output': {
                    'file1': to_file1.split("/")[-1],
                    'file2': to_file2.split("/")[-1],
                    'excel_file': excel_file if excel_file.startswith("/") else '/' + excel_file,
                    # 'img1': '/outputs/version_test_CV/form2.jpg',
                }
            }
            self.save_result_data(data)
            return {
                'status': True,
                'version': self.version,
                'message': status_msg,
                'data': data
            }
        else:
            data['HDV']['form2_2'] = {
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

if __name__ == '__main__':
    hdv = HDV('version_0423_111216', "uploads/version_0423_111216/fileinfo_version_0423_111216.json")
    # hdv.start()
    hdv.start2_1()

