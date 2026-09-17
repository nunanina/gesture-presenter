# Gesture Presenter

A real-time hand-gesture presentation control system built with Python, OpenCV, and MediaPipe. The application uses a webcam to recognize predefined hand gestures and maps them to mouse and keyboard actions for presentation control.

## Features

- Move the mouse cursor using a two-finger gesture.
- Perform a left click using a one-finger gesture.
- Move to the next slide with a right-hand three-finger gesture.
- Move to the previous slide with a left-hand three-finger gesture.
- Start presentation mode with a four-finger gesture.
- Exit presentation mode with the configured exit gesture.
- Accept gesture commands only when the hand is detected above the head.
- Smooth cursor movement using an exponential moving average (EMA).
- Display the camera preview as a compact always-on-top Windows window.

## System Architecture

```text
Webcam Input
     |
     v
OpenCV Frame Processing
     |
     +--> Face Detection --> Head-Top Reference
     |
     v
MediaPipe Hand Detection
     |
     v
Hand Landmarks
     |
     v
Finger-State Analysis
     |
     v
Gesture Recognition
     |
     v
Above-Head Validation
     |
     v
Command Mapping
     |
     v
Mouse / Keyboard Presentation Control
```

## Gesture Controls

| Gesture | Action |
|---|---|
| One finger | Left click |
| Two fingers | Move cursor |
| Three fingers - right hand | Next slide |
| Three fingers - left hand | Previous slide |
| Four-finger start gesture | Start presentation mode |
| Exit gesture | Exit presentation mode |

Gesture commands are executed only when the detected index fingertip is above the top boundary of the detected face.

## Technologies

- Python 3.11
- OpenCV
- MediaPipe
- NumPy
- PyAutoGUI
- PyWin32

## Project Structure

```text
gesture-presenter/
|-- src/
|   `-- gesture_presenter.py
|-- .gitignore
|-- requirements.txt
`-- README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/nunanina/gesture-presenter.git
cd gesture-presenter
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment on Windows

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

Run the application with:

```bash
python src/gesture_presenter.py
```

Keep the camera window active and press `Esc` on the keyboard to close the application.

## How It Works

Each webcam frame is processed using OpenCV. MediaPipe Face Detection provides a reference for the top of the user's head, while MediaPipe Hands provides hand landmarks and handedness information. Finger states are derived from landmark positions and matched against predefined gesture patterns.

Before a recognized gesture can trigger an action, the system checks whether the index fingertip is above the detected head boundary. Cursor coordinates are mapped from normalized landmark coordinates to the screen and smoothed using an exponential moving average.

## Platform

The current implementation is designed for Windows because it uses PyWin32 for window management and PyAutoGUI for operating-system input control.

## Author

Tidarut Doo-saard
