---
title: 'Envismetrics: A Python-based software for electrochemical kinetic analysis'
tags:
  - Python
  - electrochemistry
  - kinetic analysis
  - online software
  - data analysis
authors:
  - name: Huize Xue
    orcid: 0000-0001-7537-2173
    affiliation: "1"
  - name: Wenbo Wang
    orcid: 0000-0002-0784-7509
    affiliation: "2"
  - name: Xinxin Zhou
    orcid: 0009-0001-0960-6688
    affiliation: "3"
  - name: Fuqin Zhou
    orcid: 0009-0000-0342-0033
    affiliation: "5"
  - name: Omowunmi Sadik
    orcid: 0000-0001-8514-0608
    corresponding: true
    affiliation: "4"
affiliations:
 - name: New Jersey Institute of Technology, Department of Physics
   index: 1
 - name: New Jersey Institute of Technology, Department of Informatics
   index: 2
 - name: Independent Researcher
   index: 3
 - name: New Jersey Institute of Technology, Chemistry and Environmental Science
   index: 4
 - name: New Jersey Institute of Technology, Martin Tuchman School of Management
   index: 5

date: "2024-08-30"
bibliography: bibliography.bib
---

# Abstract
Envismetrics is an open-source, cross-platform Python application designed to assist researchers in the automated analysis of electrochemical data. It provides a modular toolbox for processing, visualization, and parameter extraction from techniques such as cyclic voltammetry, chronoamperometry, and hydrodynamic voltammetry. The software supports data input from selected potentiostat platforms (e.g., Autolab) and automates routine analytical steps — including peak identification, Randles–Ševčík plots, diffusion coefficient estimation, rate constant calculations, and Tafel analysis — all of which are widely used and generally essential in electrochemical analysis and simulation. Envismetrics features a graphical web interface that minimizes the need for coding and enhances accessibility for researchers across disciplines. By focusing on automation and reproducibility, Envismetrics reduces the manual workload associated with electrochemical data interpretation and promotes transparent research workflows. Its open design also allows for adaptation and further development by the community, supporting a wide range of research needs. The source code is available at [https://github.com/Woffee/Envismetrics](https://github.com/Woffee/Envismetrics).

# Summary

Accurate determination of kinetic parameters and thermodynamic properties from electrochemical data is fundamental for understanding redox reactions used in diverse applications [@SANECKI2003109, @wang2020redox, @WILOCH2024144089, @XU20106366]. These values — including diffusion coefficients, standard rate constants, transfer coefficients, and formal potentials — provide mechanistic insight and are commonly used to validate reaction pathways and simulate electrochemical behavior under various conditions [@C9CP05527D].

Although literature values exist for some well-studied redox systems, the evaluation of new analytes or experimental conditions typically requires experimental determination. Techniques such as cyclic voltammetry (CV), linear sweep voltammetry using a rotating disk electrode (LSV at RDE, under laminar flow and planar diffusion conditions), and step methods like chronoamperometry (CA) offer quantitative frameworks for extracting these parameters [@bard2022electrochemical].

Each technique supports specific analyses and is widely adopted in electrochemical research:

- **LSV at RDE**: Levich and Koutecký–Levich analysis [@doi:10.1021/ar50110a004; @treimer2002koutecky],
- **CV**: Randles–Ševčík plots, standard rate constant estimation, and transfer coefficient analysis [@doi:10.1002/adts.202500346; @LEFTHERIOTIS2007259],
- **CA**: Cottrell-based diffusion coefficient estimation [@HERATH20084324; @GOMEZ2023143400; @RODRIGUEZLUCAS2025145648].

While these methods are widely accepted, manual analysis can be labor-intensive and prone to inconsistency. To address this, **Envismetrics** is introduced as an open-source, browser-based Python application that automates data processing and analysis workflows for CV, LSV (RDE), and CA. It provides modules for filtering, peak detection, Levich regression, Randles–Ševčík analysis, and chronoamperometric fitting—offering visual outputs and tabulated results. By focusing on automation and reproducibility, Envismetrics lowers the barrier for electrochemical researchers—especially those dealing with large datasets or requiring rapid feedback—while preserving methodological rigor and transparency.

## Statement of Need

Electrochemical researchers often rely on a patchwork of tools for data analysis and visualization, each with significant limitations. Manual spreadsheet workflows (e.g., Excel) and general-purpose plotting software (e.g., Origin, SigmaPlot) are flexible but require labor-intensive preprocessing, repeated formatting, and substantial domain expertise for kinetic modeling. Proprietary instrument software (e.g., EC-lab & NOVA) is primarily designed for device control and data acquisition; its built-in plotting is basic, vendor-specific, and rarely used for advanced kinetic analysis [@Garg2021].

Envismetrics directly addresses these limitations by offering automated, reproducible workflows for key electrochemical analyses—including peak detection, Levich and Randles–Ševčík analysis, diffusion coefficient and rate constant estimation—without requiring coding. Researchers with raw data from cyclic voltammetry (CV), rotating disk electrode linear sweep voltammetry (LSV at RDE), or chronoamperometry (CA) can obtain visual plots and tabulated results in minutes, avoiding the repetitive manual steps typical of Excel/Origin pipelines or custom MATLAB/Python scripts.

The platform currently supports cyclic voltammetry (CV) data exported in widely used plaintext formats (.xlsx, .csv, .txt) from NOVA and EC-Lab software—reflecting the developer’s available instrumentation. Its modular architecture, however, is designed for both platform expansion (adding compatibility with additional electrochemical workstations) and method expansion (future integration of techniques such as electrochemical impedance spectroscopy).

Envismetrics runs entirely in the browser—requiring no installation or updates—and works seamlessly on Windows, macOS, and Linux. Its guided, user-friendly interface makes it equally well-suited for research laboratories and instructional settings. A direct feature comparison with other commonly used tools is provided in Table \ref{table:1}.


| **Aspect**             | **Proprietary Instrument Software (e.g., NOVA)** | **Envismetrics**                                                                                   | **General Tools (Excel / Origin)**               |
|------------------------|--------------------------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------|
| **Data Format Support**| Vendor-specific native formats                   | `.xlsx`, `.csv`, `.txt` (plaintext from workstation)                                               | Multiple formats, manual setup required          |
| **Analysis Features**  | Basic plotting, smoothing, baseline correction   | Automated Levich/Randles–Ševčík, peak detection, rate fitting, **batch processing**                 | Manual curve fitting, limited built-in models    |
| **Reproducibility & Transparency** |   algorithms not disclosed           | **Fully open-source**; documented methods; reproducible workflows                                   | Depends on user; no built-in workflow tracking   |
| **Extensibility**      | Limited                                           | Modular architecture; easily adds new methods                                                       | Requires manual scripting                        |
| **Ease of Use**        | Steep learning curve; instrument-specific menus  | Intuitive GUI with guided steps                                                                     | Manual data cleaning and formatting required     |
| **Output Quality**     | Basic plots                                       | **Clean, close publication ready, exportable plots**                                                       | Depends on user formatting skills                |
| **Installation & Platform Support** | Windows-only; local install                 | **Web-based; no installation; works on Windows, macOS, Linux**                                       | Local install; Windows, macOS, Linux             |


[Comparison of Electrochemical Data Analysis Software]\label{table:1}

# Current Functions of Envismetrics Toolbox

To aid in interpreting the equations below, Table 2 summarizes commonly used electrochemical parameters along with their meanings and corresponding units.

> **Note**:  
> • The symbol $\nu$ appears twice in the table with different meanings:  
> &nbsp;&nbsp;&nbsp;&nbsp;– In **CV**, it denotes the *scan rate*, with units of $\mathrm{V/s}$.  
> &nbsp;&nbsp;&nbsp;&nbsp;– In **HDV (RDE)**, it denotes the *kinematic viscosity*, with units of $\mathrm{cm^2/s}$.  
> • Both the *diffusion coefficient* $D$ and *kinematic viscosity* $\nu$ share the unit $\mathrm{cm^2/s}$, but represent distinct physical phenomena—molecular diffusion and fluid flow, respectively.

| **Symbol**          | **Meaning**                                       | **Unit**               | **Context**       |
| ------------------- | ------------------------------------------------- | ---------------------- | ----------------- |
| $n$                 | Number of electrons transferred in redox reaction | —                      | All methods       |
| $n'$                | Number of electrons in preceding equilibrium      | —                      | CV (irreversible) |
| $F$                 | Faraday constant                                  | $\text{C/mol}$         | All methods       |
| $R$                 | Ideal gas constant                                | $\text{J/mol·K}$       | All methods       |
| $T$                 | Temperature                                       | $\text{K}$             | All methods       |
| $\nu$               | Scan rate (CV)                                    | $\text{V/s}$           | CV                |
| $\nu$               | Kinematic viscosity (HDV)                         | $\text{cm}^2/\text{s}$ | HDV (RDE)         |
| $D$                 | Diffusion coefficient                             | $\text{cm}^2/\text{s}$ | All methods       |
| $A$                 | Electrode area                                    | $\text{cm}^2$          | All methods       |
| $C$, $C_0$          | Concentration of electroactive species            | $\text{mol/cm}^3$      | All methods       |
| $I_{\text{peak}}$   | Peak current                                      | $\text{A}$             | CV                |
| $j$                 | Current density                                   | $\text{A/cm}^2$        | CV                |
| $\theta$            | Dimensionless overpotential                       | —                      | CV                |
| $\alpha$, $\alpha'$ | (Apparent) transfer coefficient                   | —                      | CV                |
| $k_0$               | Standard rate constant                            | $\text{cm/s}$          | CV                |
| $\Psi$              | Dimensionless kinetic parameter                   | —                      | CV                |

[Summary of parameters used in electrochemical equations]\label{table:2}

## Data Processing

Envismetrics supports plain-text electrochemical data formats (.xlsx, .csv, .txt) exported from potentiostat software. In the current release, compatibility has been validated for Autolab’s NOVA and BioLogic’s EC-Lab (CV analysis), reflecting the instruments available during development. Support for additional formats will be added as needed, leveraging the modular file-parsing architecture.

Users can upload exported files directly to the web-based interface without manual preprocessing, provided they follow the standard export structures of the supported software. The parser automatically detects key experimental parameters—such as scan rate, rotation speed, time, current, and potential—performs file name and format validation, and alerts users to any compatibility or formatting issues, ensuring smooth integration into the downstream analysis workflow.

![Data Import Window: Users can easily drag and drop or select their experimental data for quick and straightforward import.](Image_Set/1.png){ width=80% }

## Hydrodynamic Voltammetry (HDV) - Rotating Disc Electrode (RDE) Module

### Function 1: Plotting and Gaussian Filtering

This function sorts experimental data by rotation rate (RPM) and generates the corresponding current–potential plots. An optional Gaussian smoothing can be applied by specifying a **sigma** value: larger sigma values produce smoother curves by attenuating high-frequency noise, while smaller values preserve more detail. To disable smoothing, set `sigma = 0`.

The Gaussian filter operates by convolving the current signal with a Gaussian kernel, enhancing trend visibility in noisy datasets. While smoothing can improve clarity, excessive filtering may suppress genuine electrochemical features—such as sharp peaks or kinetic shoulders—so it should be applied with caution.

### Function 2: Levich and Koutecky–Levich Analysis

Levich and Koutecký–Levich analyses are widely used to study electrochemical reactions under laminar flow convection conditions [@masa2014koutecky]. *Envismetrics* automates these workflows by generating both Levich and KL plots directly from experimental data.

**Levich analysis** estimates the diffusion coefficient $D$ under mass-transport-limited conditions, based on:

Levich analysis is primarily used to determine the diffusion coefficient $D$ under mass-transport-limited conditions. The classical Levich equation is:

$$
i_L = 0.62\, n F A D^{2/3} \omega^{1/2} \nu^{-1/6} C
$$

**Koutecký–Levich analysis** accounts for kinetic limitations and is often used to estimate the standard rate constant $k_0$ and charge-transfer coefficient $\alpha$. It retains the same diffusion-related slope as the Levich:

$$
\frac{1}{i} = \frac{1}{i_k} + \frac{1}{i_L}
$$

Or explicitly:

$$
\frac{1}{i} = \frac{1}{n F A k^0 C} + \frac{1}{0.62\, n F A D^{2/3} \omega^{1/2} \nu^{-1/6} C}
$$

In *Envismetrics*, users can select potential values to automatically generate these plots, with slopes and derived kinetic parameters $D$ calculated dynamically for each potential. This feature enables users to explore the potential dependence of apparent kinetics and identify plateaus where mass transport dominates. Users should apply Levich/KL analyses only in regions where steady-state limiting currents are observed. *Envismetrics* allows flexible selection of such regions, but interpretation should follow electrochemical theory to avoid applying these models in inappropriate potential windows. The Koutecky–Levich analysis module is under active development to support the calculation of kinetic parameters, including the standard heterogeneous rate constant $k_0$ and the charge-transfer coefficient $\alpha$.

> **Important Note:** These models are only valid in the steady-state limiting-current region. Values of $D$ shown at other potentials **do not indicate a physical change in diffusion coefficient**, but simply reflect the **definitional form** of the equations applied at that potential. Users should select only plateau potentials for quantitative analysis.
> 
<figure style="width: 100%; margin: auto; text-align: center;">
  <img src="Image_Set/KL_D23.png" alt="Koutecky–Levich plot module" style="width: 100%;" />
  <figcaption><strong>Figure 2.</strong> Koutecky–Levich plot module (logarithmic scale on the y-axis).</figcaption>
</figure>

## Cyclic Voltammetry (CV) Module

### Function 1: Plotting and Gaussian Filtering

Plots cyclic voltammetry data and optionally applies Gaussian smoothing. Users can specify the `sigma` value to control smoothing intensity — higher values reduce high-frequency noise but may also attenuate sharp features. Both the raw and smoothed curves are displayed for direct comparison.  
*(Identical in functionality to the HDV Gaussian filtering feature.)*

### Function 2: Peak Searching

Peak identification is essential for calculating formal potentials, peak separations, and performing Randles–Ševčík analysis. *Envismetrics* primarily uses **Max/Min Search** to detect absolute peak positions within user-defined potential ranges. An additional **inflection-point detection** option is available for more complex waveforms. Users can define custom search ranges to target specific redox processes. Multiple peaks can be resolved in multi-step or complex reactions. All detected peak coordinates are stored for downstream analysis and are overlaid on the CV plot for visual verification.


### Function 3: Randles–Ševčík Analysis

The Randles–Ševčík analysis estimates the diffusion coefficient $D$ from the relationship between peak current and scan rate, and can be applied to both reversible and irreversible electrochemical systems [@zanello2019inorganic]. Peak parameters for this calculation are obtained from **Function 2 (Peak Searching)**.

For a **reversible** redox process, the Randles–Ševčík equation is:  

$$
I_{\text{peak}} = 0.4463 \ n \ F \ C \ A \sqrt{\frac{n F \nu D}{R T}}
$$

For an **irreversible** process, the equation becomes:  

$$
I_{\text{peak}} = 0.4463 \sqrt{n^{\prime} + \beta} \ n \ F \ C \ A \sqrt{\frac{n F \nu D}{R T}}
$$

In *Envismetrics*, setting $\sqrt{n' + \beta} = 1$ yields the reversible case. For irreversible systems, $\sqrt{n' + \beta}$ is calculated from the user-specified $\alpha$ and $n'$, allowing both scenarios to be handled within a single computational workflow while keeping full control over input parameters.

### Function 4: Standard Rate Constant Calculation (Experimental Method)

Function 4 implements an advanced, optional method for estimating the standard heterogeneous rate constant $k_0$, using a dimensionless kinetic parameter $\Psi$ that relates $k_0$ to the system’s electrochemical and physical properties. This approach is based on the classical Nicholson model and extended by Lavagnini *et al.* to cover a broader range of peak separations ($\Delta E_p$), with additional support for the Klingler–Kochi formulation in highly irreversible systems [@nicholson1965theory; @lavagnini2004extended; @Klingler1981].

$$
\Psi = \frac{0.6288 + 0.0021 \cdot X}{1 - 0.017 \cdot X}, \quad X = \Delta E_p \cdot n \ \ (\text{in mV})
$$

where $X$ is normalized to millivolts to maintain the dimensionless nature of $\Psi$.

For systems with large $\Delta E_p$ or highly irreversible behavior, the Klingler–Kochi expression is applied:  

$$
\Psi = \frac{2.18}{\alpha \pi} \exp\left(-\frac{\alpha n \Delta E_p F}{2RT}\right)
$$

The standard rate constant is then obtained from:  

$$
k^0 = \Psi \cdot \left(\frac{D \cdot n \cdot F}{R \cdot T}\right)^{1/2}
$$

> ⚠ **Usage Note:** This method is sensitive to experimental noise and the accurate determination of $\Delta E_p$.  
> It should only be applied under conditions that satisfy the theoretical assumptions of the Nicholson or Klingler–Kochi models.  
> Users are advised to cross-check results with alternative approaches where possible.

### Function 5: Tafel Analysis Module

Tafel analysis is used to determine the anodic ($\alpha_a$) and cathodic ($\alpha_c$) transfer coefficients. The International Union of Pure and Applied Chemistry (IUPAC) formally defines these coefficients as experimentally determined values [@guidelli2014defining]:

$$
\alpha_a = \frac{RT}{F} \left( \frac{d \ln j_{a, \text{corr}}}{dE} \right)
$$

$$
\alpha_c = -\frac{RT}{F} \left( \frac{d \ln |j_{c, \text{corr}}|}{dE} \right)
$$

A **mass-transport-corrected** version, proposed by Li *et al.* [@LI2018117], is also implemented in this module. This approach has been applied in other studies, such as dopamine oxidation at gold electrodes by Bacil *et al.* [@C9CP05527D]. The corrected anodic transfer coefficient is calculated as:

$$
-\frac{d\ln \left( \frac{1}{I_a} - \frac{1}{I_{\text{peak}}} \right)}{d\theta} = \alpha_a'
$$

> ⚠ **Usage Note:** The accuracy of Tafel slope and $\alpha$ determination depends strongly on proper baseline correction, mass-transport correction, and the selection of the linear Tafel region.  
> Misidentifying the potential range can lead to significant errors in calculated kinetic parameters.

<!--
![(a) Peak Searching module](Image_Set/CVPS_D.png){ width=45% }
![(b) Randles–Ševčík Analysis Module](Image_Set/RC_DMAB.png){ width=45% }

![Example of figures in Envismetrics(CV Module): (a) Peak Searching module, (b) Randles–Ševčík Analysis Module.]
-->

<div style="display: flex; gap: 10px;">
  <figure style="width: 49%;">
    <img src="Image_Set/CVPS_D.png" alt="(a) Peak searching module (CV-2)">
    <figcaption><strong>(a)</strong> Peak searching module (CV-2)</figcaption>
  </figure>
  <figure style="width: 49%;">
    <img src="Image_Set/RC_DMAB.png" alt="(b) Randles–Ševčík analysis module (CV-3)">
    <figcaption><strong>(b)</strong> Randles–Ševčík analysis module (CV-3)</figcaption>
  </figure>
</div>

<figcaption style="width: 100%; text-align: center; margin-top: 10px;">
  <strong>Figure 3.</strong> Visual outputs from the CV module: (a) Peak searching module (CV-2), (b) Randles–Ševčík analysis module (CV-3; conceptual output shown here, available in local version but not yet on the online platform).
</figcaption>


## Step Techniques Structure: CA Module

### Function 1: Plotting and Gaussian Filtering

Plots applied potential vs. time and corresponding current vs. time, with an optional Gaussian filter for smoothing (user-defined $\sigma$). Function operates identically to Gaussian filtering in HDV and CV modules.

### Function 2: Cottrell Equation Plot

This function utilizes the Cottrell equation to calculate the diffusion coefficient from chronoamperometric (CA) data. The Cottrell equation describes the current response of an electrochemical system under planar diffusion control as a function of time:

$$
i(t) = \frac{nFA C_0 D^{1/2}}{\pi^{1/2} t^{1/2}} 
$$

In *Envismetrics*, users can input experimental parameters such as the fitting interval (number of the input files), $n$, $A$, and $C_0$. The software then plots $i(t)$ vs. $\sqrt{nFAC/\pi t}$ and performs linear regression to determine $D$. The outputs include both a regression figure and a summary table of calculated diffusion coefficients.

<!--
![(a) Plotting and Gaussian Filtering I vs t](Image_Set/CAIt_D.png){ width=45% }
![(b) Diffusion coefficient regression section](Image_Set/CAp2_D.png){ width=45% }

![Example of figures in Envismetrics(CA Module): (a) , (b).]
-->

<div style="display: flex; gap: 10px;">
  <figure style="width: 49%;">
    <img src="Image_Set/CAIt_D.png" alt="(a) Current-time curve plotting (CA-1)">
    <figcaption><strong>(a)</strong> Current–time curve plotting module (CA-1)</figcaption>
  </figure>
  <figure style="width: 49%;">
    <img src="Image_Set/CAp2_D.png" alt="(b) Diffusion coefficient regression module (CA-2)">
    <figcaption><strong>(b)</strong> Diffusion coefficient regression module (CA-2)</figcaption>
  </figure>
</div>

<figcaption style="width: 100%; text-align: center; margin-top: 10px;">
  <strong>Figure 4.</strong> Output visualization from the CA module: (a) Current–time curve plotting module (CA-1), (b) Diffusion coefficient regression module based on Cottrell equation (CA-2).
</figcaption>

## Applications in Research

Envismetrics has been employed in various research projects, demonstrating its versatility in the analysis of electrochemical systems. For instance, the software was utilized in the investigation of photocatalytic degradation of perfluorooctanoic acid (PFOA), published in *Chemosphere* [@OSONGA2024143057], where it facilitated the precise analysis of kinetic parameters essential to understanding the degradation mechanisms. Additionally, Envismetrics played a key role in mechanistic studies on the electrochemical oxidation of dimethylamine borane (DMAB), as documented in recent works [@Xue_2023,@TORABFAM2025107950]. In these studies, Envismetrics enabled the accurate processing of electrochemical data, which was crucial for validating the proposed mechanisms and deriving key kinetic parameters.

## Author Contributions (CRediT Taxonomy)

- **Huize Xue**: Conceptualization, Methodology, Software, Formal Analysis, Visualization, Data Curation, Writing – Original Draft.  
  Led the design and development of the electrochemical analysis pipeline, including Python-based processing tools and experimental method validation. Also responsible for manuscript writing and figure preparation.
- **Wenbo Wang**: Software, Writing – Review & Editing, Data Curation, Project Administration.  
  Contributed to the front-end interface, online platform development, and GitHub repository maintenance. Assisted in server deployment and manuscript refinement.
- **Xinxin Zhou**: Validation, Testing, Documentation.  
  Performed internal testing of the software and contributed to documentation and usability feedback.
- **Fuqin Zhou**: Investigation, Data Curation.  
  Supported data formatting and assisted with exploratory testing of selected modules.
- **Omowunmi Sadik**: Supervision, Project Administration, Funding Acquisition.  
  Provided scientific oversight and strategic guidance throughout the project. Contributed to the refinement of analysis direction and manuscript review.

# Technology Stack

The online platform is primarily built with Python, leveraging the Flask framework. JQuery is employed for real-time features and asynchronous tasks. More details can be found on our GitHub repo.

# Acknowledgments
The authors acknowledge the NJIT Start-ups (172803) and the Bill Melinda Gates Foundation for funding.


# Conflict of Interest
The authors confirm that we have read the JOSS conflict of interest policy, that we have no COIs related to reviewing this work, and that JOSS has waived any perceived COIs for the purpose of this review.

# Code of Conduct
The authors confirm that we read and will adhere to the JOSS code of conduct.

# References
