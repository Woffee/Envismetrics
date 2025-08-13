<a name="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Woffee/Envismetrics">
    <img src="src/static/imgs/logo.png" alt="Logo"  height="80">
  </a>
  <h3 align="center">Envismetrics</h3>
  <h6 align="center">http://34.162.1.1:8080<a href="http://34.162.1.1:8080"></a></h6>


  <p align="center">
    A comprehensive toolbox for the interpretation of results across various electrochemical techniques.
  </p>
</div>


## About The Project

### Built With

* [Flask][Flask-url]
* [JQuery][JQuery-url]
* [Bootstrap][Bootstrap-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## System Requirements

To run Envismetrics locally, you will need:

- Python 3.8 or higher: [Check here](https://www.python.org/downloads/)
- Git: [Install Git](https://git-scm.com/)
- (Optional) Anaconda: [Install Anaconda](https://www.anaconda.com/download)

To check if Git and Python are installed:
```sh
git --version
python --version
```

<!-- GETTING STARTED -->
## Getting Started


You can use Envismetrics **online** without installation:  
➡️ [Click here to use the online version](http://34.162.1.1:8080)  

Or, for local use (recommended for developers or offline analysis), follow the steps below.

### 1. Clone the Repository

```sh
git clone https://github.com/Woffee/Envismetrics.git
cd Envismetrics
```

### 2. Create a Virtual Environment and Install Required Packages

💻 Linux / macOS

```sh
python3 -m venv myenv
source myenv/bin/activate
```

🖥 Windows (Command Prompt)

```sh
python -m venv myenv
myenv\Scripts\activate
```

🖥 Windows (PowerShell)

```
python -m venv myenv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
myenv\Scripts\Activate.ps1
```

🔰 We recommend keeping the virtual environment inside the local repository for simplicity, especially for beginners. Advanced users may choose a centralized folder for their environments.

Install Required Packages

```sh
pip install -r requirements.txt
```

### Alternatively, Anaconda users can create a new environment:

```sh
conda create -n envismetrics python=3.9
conda activate envismetrics
pip install -r requirements.txt
```

### 4. Run the Application

💻 Linux / macOS

```sh
python src/app.py
```

🖥 Windows (Command Prompt)

```sh
python src\app.py
```

Then visit http://localhost:8080/ in your browser.

### 📁 Project Directory Overview

The Envismetrics repository is organized as follows:

```plaintext
Envismetrics/
├── app/                    # Web app interface (Flask-based backend logic)
├── data/
│   ├── example_files/      # Example .xlsx files showing required data formats for CV, CA, HDV
│   └── test_data/          # Full experimental datasets used for testing
├── src/                    # Core electrochemical analysis modules (CV.py, CA.py, HDV.py, etc.)
├── tests/                  # Unit tests for validating module functions
├── static/                 # Static web resources (CSS, JS, images)
├── templates/              # HTML templates for web UI
├── paper/
│   ├── paper.md            # JOSS manuscript source
│   ├── bibliography.bib    # BibTeX-formatted references
│   └── Image_Set/          # Figures used in the manuscript
├── LICENSE
├── README.md
└── requirements.txt        # Python dependencies
```

- **`data/example_files/`**: Provides sample `.xlsx` templates to help users format input files correctly (e.g., column headers for potential and current).
- **`data/test_data/`**: Contains real experimental datasets to test and validate the software functionality.


### Test data

The test data is now available in the [`data/test_data`](https://github.com/Woffee/Envismetrics/tree/main/data/test_data) folder.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Data Privacy and Retention

When using the online version of Envismetrics, uploaded data is stored temporarily to allow users to revisit their analysis via a unique session link. For example:

`http://34.162.1.1:8080/step_methods/version_0627_040023?step=2`

This link is automatically generated after uploading data and can be bookmarked for future access.

To protect user privacy:
- Uploaded files are **not publicly listed**, and links are sufficiently unique to prevent accidental discovery.
- **All stored data is automatically deleted on the 1st of each month**.
- Currently, there is **no login or authentication system**, as this is an early-stage prototype intended for demonstration and testing purposes.

**Please do not upload sensitive or confidential data at this time.** We plan to introduce access control and permanent storage options in future releases.


## Statement of Need

In terms of data handling, typical electrochemical kinetic analysis solutions have relied on instrument-specific proprietary software provided with potentiostats, homemade scripts for specific data, or manual processing in Excel. Compared with the proprietary tools available from potentiostat manufacturers, these often lack the flexibility, cross-platform support, and comprehensive functionality that Envismetrics offers. Compared with homegrown solutions and packages, Envismetrics provides a more general function that saves time and eliminates the need to re-edit code when changing potentiostats or experimental methods in kinetic analysis. Users can rely on Envismetrics to streamline their workflow and enhance efficiency.

Envismetrics provides an open-source, cross-platform (Windows, MacOS, and Linux) online software focused on electrochemical kinetic analysis. No installation or updates are required, making it convenient and always up-to-date. Envismetrics offers a full toolbox for processing raw voltammogram data, extracting parameters, and generating publication-ready figures. The analysis can be applied to any scan, cycle, or range of voltammogram data. At any stage of the analysis, users can export the results for further use or to create new figures. Whether users are professional researchers seeking to save time or individuals lacking basic knowledge of the relevant equations, Envismetrics encourages reproducible, easy-to-use, and transparent analysis.

Envismetrics not only facilitates data collection and analysis from electrochemical experiments but also provides educational resources to help users understand the terminology and concepts they encounter. This dual approach ensures that both seasoned researchers and newcomers can effectively utilize the software.

Envismetrics is dedicated to continuous improvement and innovation. Future plans include incorporating widely used kinetic electrochemical analysis methods and expanding support for additional data formats from various potentiostat brands. The software's modular design enables the seamless integration of new features and methods, ensuring Envismetrics remains a leading tool in electrochemical analysis.


<!-- USAGE EXAMPLES -->
## Usage

Envismetrics is an online tool ([click here](http://34.74.47.99:8080/)) that requires no download or installation. The software updates automatically whenever new modules are released, ensuring you always have access to the latest features.

1. Access the Software
	- Visit Envismetrics Online.
2. Select the Module
	- Choose the module that corresponds to your experiment from the list of available options.
3. Upload Your Data
	- Select or drag and drop your data files from a folder into the designated area. The software supports various file formats such as XLSX, TXT, and CSV.
4. Input Parameters
	- Enter your desired figure settings and initial experimental parameters. This ensures that the analysis is tailored to your specific needs.
5. Submit for Analysis
	- Press the "Submit" button to start the analysis. The software will process your data and generate the results based on the selected module and input parameters.
6. Review and Adjust Parameters
	- If you need to edit any parameters from the previous page, press the "Go Back" button to make the necessary adjustments.
7. Analyze New Data
	- If you want to analyze a new set of data, press the "Try Again" button to restart the process.

By following these simple steps, you can efficiently utilize Envismetrics for your electrochemical kinetic analysis, ensuring accurate and reproducible results. 


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap


### Hydrodynamic Voltammetry (HDV) Module

1. Data Import, Plotting, and Gaussian Filtering
    - Data Import: Supports importing data from various potentiostats and file formats.
    - Plotting: Visualizes the imported data sorted by RPM (rotations per minute).
    - Gaussian Filtering: Applies a Gaussian filter to smooth the plotted data.
2. Levich and Koutecky-Levich Analysis
	- Levich Plot and Analysis:
		- Generates Levich plots directly from the data.
		- Calculates the diffusion coefficient from the slope of the plot.
	- Koutecky-Levich Plot and Analysis:
		- Produces Koutecky-Levich plots.
		- Performs linear regression to analyze the diffusion coefficient at various potentials.

### Cyclic Voltammetry (CV) Module

1. Plotting and Gaussian Filtering
	- Plotting: Visualizes cyclic voltammetry data sorted by rate constant value.
	- Gaussian Filtering: Applies a Gaussian filter to smooth the data, with user-defined sigma values.
2. Peak Searching
	- Identifies peak points within specific ranges using various methods (max/min, knee/elbow detection).
	- Records peak information for use in subsequent analyses.
3. Randles–Ševčík Analysis
	- Calculates the diffusion coefficient from peak current and scan rate.
4. Rate Constant Calculation
	- Calculates the rate constant using peak separation
5. Tafel Analysis Module
    - Determines anodic and cathodic transfer coefficients.
    - Implements mass-transport corrected methods for enhanced accuracy.

### Step Techniques Module

1. CA Module
   - Plotting: Generates plots of applied potential vs. time and corresponding current vs. time.
   - Gaussian Filtering: Smooths data for clearer visualization, with adjustable sigma values.
   - Cottrell Equation Plot: Utilizes the Cottrell equation to calculate the diffusion coefficient.


<p align="right">(<a href="#readme-top">back to top</a>)</p>






<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Conflict of interest

I confirm that I have read the [JOSS conflict of interest policy](https://joss.readthedocs.io/en/latest/reviewer_guidelines.html#joss-conflict-of-interest-policy) and that: I have no COIs with reviewing this work or that any perceived COIs have been waived by JOSS for the purpose of this review.


## Code of Conduct

I confirm that I read and will adhere to the [JOSS code of conduct](https://joss.theoj.org/about#code_of_conduct).


<!-- CONTACT -->
## Contact

Huize Xue - email@example.com

Project Link: [https://github.com/Woffee/Envismetrics](https://github.com/Woffee/Envismetrics)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments


* [Grant Xue](#)
* [Wenbo Wang](#)
* [Omowunmi Sadik](#)
* [Xinxin Zhou](#)
* [Fuqin Zhou](#)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=for-the-badge
[contributors-url]: https://github.com/othneildrew/Best-README-Template/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/othneildrew/Best-README-Template.svg?style=for-the-badge
[forks-url]: https://github.com/othneildrew/Best-README-Template/network/members
[stars-shield]: https://img.shields.io/github/stars/othneildrew/Best-README-Template.svg?style=for-the-badge
[stars-url]: https://github.com/othneildrew/Best-README-Template/stargazers
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/othneildrew/Best-README-Template/issues
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/othneildrew
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
[Flask.com]: https://flask.palletsprojects.com/en/3.0.x/_static/shortcut-icon.png
[Flask-url]: https://flask.palletsprojects.com/

