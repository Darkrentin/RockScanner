<img src="https://raw.githubusercontent.com/Darkrentin/RockScanner/refs/heads/main/screen/logoRockScanner.png" alt="RockScanner Logo" width="100">

# RockScanner

RockScanner is a specialized tool for Star Citizen designed to provide additional data on scanned mineral signatures.

In Star Citizen, scanning a rock signature provides a numerical value that can reveal the mineral type and the number of rocks through simple division. RockScanner simply automates this manual calculation.

> Since it only captures and processes visual data available to the player, it does not violate Cloud Imperium Games' policies regarding third-party external tools.

## Installation

To install or update RockScanner, download the latest version below:

[**Download RockScanner for Windows**](https://github.com/Darkrentin/RockScanner/releases/latest/download/RockScannerSetup.exe)

Run the installer and follow the on-screen instructions.

## How to Use

**RockScanner features 4 distinct states:**

### IDLE State
In this state, the tool is inactive. This allows you to keep the application open without it scanning your screen.

You can enable scanning by toggling the button in the top-left corner when you are ready to mine.

![IDLE](https://raw.githubusercontent.com/Darkrentin/RockScanner/refs/heads/main/screen/IDLE.png)

### SCANNING State
While scanning, the tool monitors the center of your screen to locate the scanned signature UI.

The tool may stay in this state if:
- No signature is currently displayed on your screen.
- The UI cannot be detected. **(Detection may struggle with overly bright backgrounds; it performs best in space.)**
- The detected signature does not match any known minerals. **(e.g., if you scan a ship or multiple overlapping rocks.)**

![SCANNING](https://raw.githubusercontent.com/Darkrentin/RockScanner/refs/heads/main/screen/SCANNING.png)

### LOCKED State
This state is reached when a valid mineral signature is detected and identified.

- **Upper Right Image:** Shows the specific screen region being analyzed.
- **Upper Left Number:** Displays the value extracted via OCR (Optical Character Recognition).

> **Note:** The program may occasionally misread the number. Please verify that the OCR value matches the image preview.

- **Results:** The identified mineral type and the number of rocks present are displayed below.

> If multiple combinations match the signature, all possibilities will be listed.

![LOCKED](https://raw.githubusercontent.com/Darkrentin/RockScanner/refs/heads/main/screen/LOCKED.png)

### PAUSED State
To prevent visual stuttering or freezing, the program automatically pauses while the window is being moved.

![PAUSED](https://raw.githubusercontent.com/Darkrentin/RockScanner/refs/heads/main/screen/PAUSED.png)

## How it works

The program captures screenshots of the center of your screen at regular intervals, specifically targeting the signature UI.

It processes these images using various binarization levels and OCR to extract numerical data. Once a number is found, the tool validates it: a valid signature must be a multiple of the base signatures of known Star Citizen minerals.

Signature data is based on the research and charts provided by **MrKraken**.

![MrKrakenSigChart](https://raw.githubusercontent.com/Darkrentin/RockScanner/refs/heads/main/screen/MrKrakenSig.png)

---

### /!\ WARNING

- **Low Contrast:** The tool may fail if the color difference between the background (e.g., snow planets) and the signature UI is too low.
- **Compatibility:** Not all ships have been tested. If the tool fails on a specific ship, please contact me.
- **Stability:** Capture may take a few moments. Try to keep your view steady to assist the detection process.