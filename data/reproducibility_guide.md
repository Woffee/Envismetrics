# Reproducing Manuscript Figures

This guide explains how to reproduce all four subplots in **Figure 2** of the *Envismetrics* manuscript using the online tool(http://34.162.1.1:8080/).

All required input files are included in this GitHub folder:  
🔗 [`/data/test_data/`](https://github.com/Woffee/Envismetrics/tree/main/data/test_data)

---
## 1. Figure 2a and 2b: Hydrodynamic Voltammetry (HDV Module)

**Dataset location:**  
[`data/test_data/05202024_HDV_D40_A1`](https://github.com/Woffee/Envismetrics/tree/main/data/test_data/05202024_HDV_D40_A1)

**Files used:**
- `HDV_G_DMAB0.05gL_10mVs_200rpm.xlsx`  
- `HDV_G_DMAB0.05gL_10mVs_400rpm.xlsx`  
- `HDV_G_DMAB0.05gL_10mVs_600rpm.xlsx`  
- `HDV_G_DMAB0.05gL_10mVs_800rpm.xlsx`  
- `HDV_G_DMAB0.05gL_10mVs_1000rpm.xlsx`  
- `HDV_G_DMAB0.05gL_10mVs_1200rpm.xlsx`  
- `HDV_G_DMAB0.05gL_10mVs_1400rpm.xlsx`  
- `HDV_G_DMAB0.05gL_10mVs_1600rpm.xlsx`  
- `HDV_G_DMAB0.05gL_10mVs_1800rpm.xlsx`  
- `HDV_G_DMAB0.05gL_10mVs_2000rpm.xlsx`

Each file contains a linear sweep voltammetry (LSV) curve recorded at a specific electrode rotation speed. These data are used to generate the **Levich plot** and compute the **diffusion coefficient** for DMAB.

---

### Reproduction Steps

1. Visit the [Envismetrics HDV module](http://34.162.1.1:8080/hyd_elec)  
2. Upload **all 10 HDV files** listed above  
3. Set the **Smoothing Level (σ):** `10`  
4. Click **Submit** to proceed to **HDV-2**  
5. Enter the following parameters:

| Parameter                           | Value                             | Description                                                                 |
|-------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| **Concentration of solute (C)**     | `0.004e-3 mol/cm³`                | Bulk concentration of DMAB                                                 |
| **Electrode surface area (A)**      | `0.07068583470577035 cm²`         | Geometric surface area of the working electrode                            |
| **Kinematic viscosity (ν)**         | `0.01 cm²/s`                      | For aqueous systems near room temperature                                  |
| **Number of electrons (n)**         | `1`                               | Number of electrons involved in oxidation                                  |
| **Method**                          | `Levich plot and Levich analysis` | Enables linear fit and diffusion coefficient calculation                    |
| **Applied potential range (V)**     | `(-0.12, 0.2)`                    | Region for identifying limiting current                                     |
| **Number of potentials to display** | `6`                               | Number of points selected for Levich plot                                   |
| **Potential step interval (mV)**    | `37`                              | Controls resolution of the dot plot                                         |

6. Click **Next** to enter **HDV-3.1**  
7. The tool will generate:
   - **Figure 2**: Koutecky-Levich plot
---

## Notes

- These example files are pre-calibrated to match the tool’s default settings — **no manual adjustments needed**  
- When using custom HDV data:
  - Provide at least **5 rotation speeds**
  - Use the `?` tooltips for parameter guidance
- If the tool becomes unresponsive:
  - Refresh your browser and re-enter the settings


---
## 2. Figure 3a and 3b: Cyclic Voltammetry (CV Module)

**Folder used:**  
[`data/test_data/01112023_CV_DMAB`](https://github.com/Woffee/Envismetrics/tree/main/data/test_data/01112023_CV_DMAB)

**Files:**
- `G_P_KOH40.0032gL_DMAB0.0475gL_100mVs_CV.xlsx`
- `G_P_KOH40.0032gL_DMAB0.0475gL_10mVs_CV.xlsx`
- `G_P_KOH40.0032gL_DMAB0.0475gL_20mVs_CV.xlsx`
- `G_P_KOH40.0032gL_DMAB0.0475gL_30mVs_CV.xlsx`
- `G_P_KOH40.0032gL_DMAB0.0475gL_40mVs_CV.xlsx`
- `G_P_KOH40.0032gL_DMAB0.0475gL_50mVs_CV.xlsx`
- `G_P_KOH40.0032gL_DMAB0.0475gL_60mVs_CV.xlsx`
- `G_P_KOH40.0032gL_DMAB0.0475gL_70mVs_CV.xlsx`
- `G_P_KOH40.0032gL_DMAB0.0475gL_80mVs_CV.xlsx`
- `G_P_KOH40.0032gL_DMAB0.0475gL_90mVs_CV.xlsx`

Each file contains a cyclic voltammetry (CV) curve of DMAB oxidation recorded at a different scan rate. These are required for **Randles–Ševčík analysis** and **standard rate constant estimation**.

---

### Steps to Reproduce

1. Go to the [CV module](http://34.162.1.1:8080/cv) to open the **CV-1** page  
2. Upload **all 10 files** listed above  
3. Keep default settings:  
   - **Gaussian filter sigma**: `10`  
   - **Cycle of representative**: `6` (for this dataset, any cycle between 1–12 is acceptable)  
4. Click **Submit** to proceed to the **CV-2.1** page  
5. In **Function 2: Peak searching**, use the following settings:

| Parameter                        | Value                                              | Explanation                                                                  |
|----------------------------------|----------------------------------------------------|------------------------------------------------------------------------------|
| **Peak range (top)**             | `(-1, -0.70), (0, 0.2), (0.25, 0.5)`               | Voltage ranges where oxidation peaks are expected                            |
| **Peak range (bottom)**          | `(-0.925, -0.75), (0.0, 0.125), (0.125, 0.25)`     | Voltage ranges where reduction peaks are expected                            |
| **Peak 1 – Scan Rate Range**     | `10 to 100 mV/s`                                   | Scan rates used for Peak 1 analysis (via slider)                             |
| **Peak 2 – Scan Rate Range**     | `10 to 100 mV/s`                                   | Scan rates used for Peak 2 analysis (via slider)                             |
| **Peak 3 – Scan Rate Range**     | `20 to 80 mV/s`                                    | Scan rates used for Peak 3 analysis (via slider)                             |
| **Cycle range**                  | `2 to 100`                                         | Only cycles within this range are used in the peak analysis                  |
| **Scan rate to display**         | `20 mV/s`                                          | Highlights the curve at 20 mV/s in the display                               |
| **Cycle number to display**      | `9`                                                | The 9th cycle will be shown in the figure                                    |
| **Which method to use**          | `Max`                                              | Peak current is determined by the maximum value within the selected range    |


6. Click **Submit** to proceed to the **CV-2.2** page  
7. The results generated correspond to:
   - **Figure 3a**: Peak overlay plot and scan rate-dependent peak current curves

---

8. Then, click **Function 3: Randles–Ševčík Analysis** to enter the **CV-3.1** page  
9. Use the following parameter settings:

| Parameter                                | Value                         | Explanation                                                                 |
|------------------------------------------|-------------------------------|-----------------------------------------------------------------------------|
| **Number of electron transfer (n)**      | `1`                           | Number of electrons involved in redox reaction                             |
| **Concentration of material (C)**        | `0.000806e-3 mol/cm³`         | Bulk concentration of DMAB used in the CV test                             |
| **Temperature (T)**                      | `298.15 K`                    | Standard room temperature in Kelvin                                         |
| **Electrode diameter**                   | `0.16 cm`                     | Diameter of the glassy carbon disk electrode used in this setup            |

10. Click **Submit** to view the results

---

### Output

- **Figure 3a**: Peak current vs. scan rate from Function 2  
- **Figure 3b**: Randles–Ševčík plot (Ip vs. √v) including linear regression  
  - A **simulated data point** (▲) is also shown for theoretical comparison

> ⚠️ **Important Note on Figure 3b:**  
> The triangular simulated peak current shown in Figure 3b is generated using a **newly implemented feature in the local (Python) version** of Envismetrics.  
> This feature is **not yet available** in the web-based version at the time of submission.  
> To reproduce Figure 3b exactly, please refer to the local codebase on GitHub. The web version currently supports only experimental data fitting and linear regression.  
> For precise reproduction, see:  
> [`CV_General.ipynb`](https://github.com/Woffee/Envismetrics/blob/main/src/CV_General.ipynb), section: **`## (Function 3) 3.2 Randles–Ševčík analysis module – mechanism verification module`**
---

### Additional Notes

- When using your own CV dataset, ensure it includes **at least 3 different scan rates**  
- You can hover over the `?` icons for helpful guidance in the web tool  
- These settings were calibrated to reproduce the manuscript figures exactly  

## 3. Figure 4a and 4b: Step Techniques (Chronoamperometry Module)

**Dataset location:**  
[`data/test_data/05132024_CA_D`](https://github.com/Woffee/Envismetrics/tree/main/data/test_data/05132024_CA_D)

**Files used:**
- `1_DMAB_120s_CA.xlsx`  
- `2_DMAB_120s_CA.xlsx`  
- `3_DMAB_120s_CA.xlsx`  
- `4_DMAB_120s_CA.xlsx`  
- `5_DMAB_120s_CA.xlsx`  
- `6_DMAB_120s_CA.xlsx`  
- `7_DMAB_120s_CA.xlsx`  

Each file contains a current–time response (i–t curve) recorded during chronoamperometry (CA) for DMAB at different applied potentials. These are used for **Cottrell-based diffusion coefficient analysis**.

---

### Steps to Reproduce

1. Go to the [CA module](http://34.162.1.1:8080/step_methods)  
2. Upload all **7 files** listed above  
3. Click **Submit** to access **CA-1** (current–time visualization)  
   - This corresponds to **Figure 4a**: Overlay of i–t curves  
4. Click **Next** to proceed to **CA-2** (Diffusion Coefficient Analysis)  
5. Use the following parameter settings:

| Parameter                                | Value                            | Explanation                                                                |
|------------------------------------------|----------------------------------|----------------------------------------------------------------------------|
| **Number of electrons (n)**              | `1`                              | Number of electrons transferred in the DMAB oxidation                      |
| **Concentration of solute (C)**          | `0.000848608e-3 mol/cm³`         | Bulk concentration of DMAB                                                 |
| **Electrode surface area (A)**           | `0.07068583470577035 cm²`        | Geometric area of the gold working electrode                               |
| **Regression time range (s)**            | `[0, 1]`                          | Time window used for Cottrell regression (linear fit of I vs. t⁻¹ᐟ²)       |

6. Click **Submit** to generate results  
   - This corresponds to **Figure 4b**: Linear regression for diffusion coefficient extraction

---

### Output

- **Figure 4a:** Overlay of current vs. time curves from all input files  
- **Figure 4b:** Diffusion coefficient fitting using the Cottrell equation

---

### Notes

- All data files record current for 120 seconds at a fixed potential, under identical experimental conditions  
- The chosen regression time range `[0, 1]` seconds captures the early diffusion-controlled regime, minimizing capacitive current effects  
