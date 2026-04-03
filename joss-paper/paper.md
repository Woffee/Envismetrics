---
title: 'Envisimetrics: Automated extraction of kinetic and transport parameters from electrochemical measurements'
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
  - name: Dongxiao Yue
    orcid: 0009-0005-9387-8430
    affiliation: "3"
  - name: Xinxin Zhou
    orcid: 0009-0001-0960-6688
    affiliation: "4"
  - name: Fuqin Zhou
    orcid: 0009-0000-0342-0033
    affiliation: "6"
  - name: Omowunmi Sadik
    orcid: 0000-0001-8514-0608
    corresponding: true
    affiliation: "5"
affiliations:
 - name: New Jersey Institute of Technology, Department of Physics
   index: 1
 - name: New Jersey Institute of Technology, Department of Informatics
   index: 2
 - name: Texas A&M University, Department of Economics
   index: 3
 - name: Independent Researcher
   index: 4
 - name: New Jersey Institute of Technology, Chemistry and Environmental Science
   index: 5
 - name: New Jersey Institute of Technology, Martin Tuchman School of Management
   index: 6

date: "2024-08-30"
bibliography: bibliography.bib
---

# Summary

**Envismetrics** is an open-source, browser-based Python application for automated analysis of electrochemical data. It provides a unified and modular framework for processing, visualization, and parameter extraction across commonly used techniques, including cyclic voltammetry (CV), linear sweep voltammetry at rotating disk electrodes (LSV at RDE), and chronoamperometry (CA). The software integrates established electrochemical models—such as Levich and Koutecký–Levich analysis, Randles–Ševčík relationships, Cottrell diffusion analysis, and Tafel methods—into standardized, automated workflows. These enable extraction of key kinetic and transport parameters, including diffusion coefficients, rate constants, and transfer coefficients, directly from experimental data. Envismetrics supports widely used data formats (.xlsx, .csv, .txt) and operates through a graphical web interface, eliminating the need for manual preprocessing or programming. Its modular architecture allows flexible extension to additional techniques and methods, while its open-source implementation promotes transparency and reproducibility. The platform is designed for both research and teaching applications, providing rapid, consistent, and accessible electrochemical data analysis.

# Statement of Need
**Envismetrics** is an open-source, browser-based Python application for automated analysis of electrochemical data. It provides integrated workflows for processing, visualization, and parameter extraction from commonly used techniques, including cyclic voltammetry (CV), linear sweep voltammetry at rotating disk electrodes (LSV at RDE), and chronoamperometry (CA) [@Bard2022]. The software implements standard electrochemical analyses such as peak detection, Randles–Ševčík analysis [@ElLatif2025; @Leftheriotis2007], Levich and Koutecký–Levich regression [@Bruckenstein1977; @Treimer2002], and Cottrell-based diffusion analysis [@Herath2008; @Gomez2023; @RodriguezLucas2025]. These methods enable extraction of key parameters, including diffusion coefficients, rate constants, and transfer coefficients, which are widely used in electrochemical studies [@SANECKI2003; @wang2020; @WILOCH2024; @XU2010; @Bacil2020].
Users can upload raw experimental data in common formats (.xlsx, .csv, .txt) and obtain visual outputs and tabulated results through a graphical interface, without requiring manual preprocessing or programming. The software is modular and extensible, allowing future integration of additional techniques and analytical methods. It operates entirely in the browser, requiring no installation and supporting cross-platform use.

# State of the Field
Electrochemical data analysis is typically performed using three categories of tools: proprietary instrument software, general-purpose data analysis software, and custom scripting approaches. Proprietary software such as NOVA and EC-Lab is primarily designed for data acquisition and basic visualization, with limited support for automated kinetic analysis [@Garg2021]. General-purpose tools, including Excel, Origin, and SigmaPlot, provide flexible data handling but rely on manual workflows and do not include built-in implementations of electrochemical analysis methods such as Levich, Randles–Ševčík, or Cottrell models. Custom MATLAB or Python scripts can implement these methods, but depend on user expertise and are not standardized or easily reusable. Compared to these approaches, **Envismetrics** provides built-in implementations of commonly used electrochemical analyses within a single platform, supports automated workflows for CV, LSV at RDE, and CA, and offers a graphical interface without requiring programming. Its modular and open-source design further enables extension and reproducibility. A comparison with commonly used tools is provided in Table \ref{table:1}.

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

# Software design:

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

![**Figure 1.** Data Import Window: Users can easily drag and drop or select their experimental data for quick and straightforward import.](Image_Set/1.png){ width=50% }

## Hydrodynamic Voltammetry (HDV) - Rotating Disc Electrode (RDE) Module

### Function 1: Plotting and Gaussian Filtering

This function sorts experimental data by rotation rate (RPM) and generates the corresponding current–potential plots. An optional Gaussian smoothing can be applied by specifying a **sigma** value: larger sigma values produce smoother curves by attenuating high-frequency noise, while smaller values preserve more detail. To disable smoothing, set `sigma = 0`.

The Gaussian filter operates by convolving the current signal with a Gaussian kernel, enhancing trend visibility in noisy datasets. While smoothing can improve clarity, excessive filtering may suppress genuine electrochemical features—such as sharp peaks or kinetic shoulders—so it should be applied with caution.

### Function 2: Levich and Koutecky–Levich Analysis

Levich and Koutecký–Levich analyses are widely used to study electrochemical reactions under laminar flow convection conditions [@Masa2014]. *Envismetrics* automates these workflows by generating both Levich and KL plots directly from experimental data.

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

![**Figure 2.** Koutecký–Levich plot module (logarithmic scale on the y-axis).](Image_Set/KL_D23.png){ width=80% }

## Cyclic Voltammetry (CV) Module

### Function 1: Plotting and Gaussian Filtering

Plots cyclic voltammetry data and optionally applies Gaussian smoothing. Users can specify the `sigma` value to control smoothing intensity — higher values reduce high-frequency noise but may also attenuate sharp features. Both the raw and smoothed curves are displayed for direct comparison.  
*(Identical in functionality to the HDV Gaussian filtering feature.)*

### Function 2: Peak Searching

Peak identification is essential for calculating formal potentials, peak separations, and performing Randles–Ševčík analysis. *Envismetrics* primarily uses **Max/Min Search** to detect absolute peak positions within user-defined potential ranges. An additional **inflection-point detection** option is available for more complex waveforms. Users can define custom search ranges to target specific redox processes. Multiple peaks can be resolved in multi-step or complex reactions. All detected peak coordinates are stored for downstream analysis and are overlaid on the CV plot for visual verification.


### Function 3: Randles–Ševčík Analysis

The Randles–Ševčík analysis estimates the diffusion coefficient $D$ from the relationship between peak current and scan rate, and can be applied to both reversible and irreversible electrochemical systems [@Gewirth2004]. Peak parameters for this calculation are obtained from **Function 2 (Peak Searching)**.

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

Function 4 implements an advanced, optional method for estimating the standard heterogeneous rate constant $k_0$, using a dimensionless kinetic parameter $\Psi$ that relates $k_0$ to the system’s electrochemical and physical properties. This approach is based on the classical Nicholson model and extended by Lavagnini *et al.* to cover a broader range of peak separations ($\Delta E_p$), with additional support for the Klingler–Kochi formulation in highly irreversible systems [@Nicholson1965; @Lavagnini2004; @Klingler1981].

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

Tafel analysis is used to determine the anodic ($\alpha_a$) and cathodic ($\alpha_c$) transfer coefficients. The International Union of Pure and Applied Chemistry (IUPAC) formally defines these coefficients as experimentally determined values [@Guidelli2014]:

$$
\alpha_a = \frac{RT}{F} \left( \frac{d \ln j_{a, \text{corr}}}{dE} \right)
$$

$$
\alpha_c = -\frac{RT}{F} \left( \frac{d \ln |j_{c, \text{corr}}|}{dE} \right)
$$

A **mass-transport-corrected** version is also implemented in this module [@Li2018]. This approach has been applied in other studies, such as dopamine oxidation at gold electrodes [@Bacil2020]. The corrected anodic transfer coefficient is calculated as:

$$
-\frac{d\ln \left( \frac{1}{I_a} - \frac{1}{I_{\text{peak}}} \right)}{d\theta} = \alpha_a'
$$

> **Usage Note:** The accuracy of Tafel slope and $\alpha$ determination depends strongly on proper baseline correction, mass-transport correction, and the selection of the linear Tafel region.  
> Misidentifying the potential range can lead to significant errors in calculated kinetic parameters.

<!--
![(a) Peak Searching module](Image_Set/CVPS_D.png){ width=45% }
![(b) Randles–Ševčík Analysis Module](Image_Set/RC_DMAB.png){ width=45% }

![Example of figures in Envismetrics(CV Module): (a) Peak Searching module, (b) Randles–Ševčík Analysis Module.]
-->

| ![**(a)** Peak searching module (CV-2)](Image_Set/CVPS_D.png){ width=48% } | ![**(b)** Randles–Ševčík analysis module (CV-3)](Image_Set/RC_DMAB.png){ width=48% } |
|:--:|:--:|
| (a) Peak searching module (CV-2) | (b) Randles–Ševčík analysis module (CV-3) |

**Figure 3.** Visual outputs from the CV module: (a) Peak searching module (CV-2), (b) Randles–Ševčík analysis module (CV-3; conceptual output shown here, available in local version but not yet on the online platform).

## Step Techniques Structure: CA Module

### Function 1: Plotting and Gaussian Filtering

Plots applied potential vs. time and corresponding current vs. time, with an optional Gaussian filter for smoothing (user-defined $\sigma$). Function operates identically to Gaussian filtering in HDV and CV modules.

### Function 2: Cottrell Equation Plot

This function utilizes the Cottrell equation to calculate the diffusion coefficient from chronoamperometric (CA) data. The Cottrell equation describes the current response of an electrochemical system under planar diffusion control as a function of time:

$$
i(t) = \frac{nFA C_0 D^{1/2}}{\pi^{1/2} t^{1/2}} 
$$

In *Envismetrics*, users can input experimental parameters such as the fitting interval (number of the input files), $n$, $A$, and $C_0$. The software then plots $i(t)$ vs. $\sqrt{nFAC/\pi t}$ and performs linear regression to determine $D$. The outputs include both a regression figure and a summary table of calculated diffusion coefficients.

| ![**(a)** Current–time curve plotting module (CA-1)](Image_Set/CAIt_D.png){ width=48% } | ![**(b)** Diffusion coefficient regression module (CA-2)](Image_Set/CAp2_D.png){ width=48% } |
|:--:|:--:|
| (a) Current–time curve plotting module (CA-1) | (b) Diffusion coefficient regression module (CA-2) |

**Figure 4.** Output visualization from the CA module: (a) Current–time curve plotting module (CA-1), (b) Diffusion coefficient regression module based on Cottrell equation (CA-2).

# Research impact statement

Envismetrics has been employed in various research projects, demonstrating its versatility in the analysis of electrochemical systems. For instance, the software was utilized in the investigation of photocatalytic degradation of perfluorooctanoic acid (PFOA), published in *Chemosphere* [@Osonga2024], where it facilitated the precise analysis of kinetic parameters essential to understanding the degradation mechanisms. Additionally, Envismetrics played a key role in mechanistic studies on the electrochemical oxidation of dimethylamine borane (DMAB), as documented in recent works [@Torabfam2025; XUE2026]. In these studies, Envismetrics enabled the accurate processing of electrochemical data, which was crucial for validating the proposed mechanisms and deriving key kinetic parameters.

# Author Contributions

Huize Xue, Wenbo Wang, and Dongxiao Yue contributed equally to this work.

- **Huize Xue**: Conceptualization, Methodology, Software, Formal Analysis, Visualization, Data Curation, Writing – Original Draft.  
  Led the overall design and development of the electrochemical data analysis pipeline, including core Python-based processing modules and experimental method validation. Responsible for manuscript drafting and figure preparation.

- **Wenbo Wang**: Software, Writing – Review & Editing, Data Curation, Project Administration.  
  Contributed to front-end interface development, online platform integration, and GitHub repository maintenance. Assisted with server deployment and manuscript revision.

- **Dongxiao Yue**: Software, Validation, Debugging, Writing – Review & Editing.  
  Contributed to software revision and debugging, validated core analysis modules, and assisted in improving code robustness and manuscript clarity.

- **Xinxin Zhou**: Validation, Testing, Documentation.  
  Performed internal software testing and contributed to documentation and usability feedback.

- **Fuqin Zhou**: Investigation, Data Curation.  
  Supported data formatting and assisted with exploratory testing of selected modules.

- **Omowunmi Sadik**: Supervision, Project Administration, Funding Acquisition.  
  Provided scientific oversight and strategic guidance throughout the project, and contributed to refinement of the analysis direction and manuscript review.

# Acknowledgments
The authors acknowledge the NJIT Start-ups (172803) and the Bill Melinda Gates Foundation for funding.

# Conflict of Interest
The authors confirm that we have read the JOSS conflict of interest policy, that we have no COIs related to reviewing this work, and that JOSS has waived any perceived COIs for the purpose of this review.

# AI usage disclosure
Generative AI tools were used only to correct grammar and improve language clarity. The software design, implementation, and all technical contributions are entirely the work of the authors.

# References
