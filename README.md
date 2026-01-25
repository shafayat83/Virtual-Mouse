##Structure (suggested)**

```
Hand-Controlled-Cursor/
│
├── main.py
├── requirements.txt
└── README.md
```

* **main.py** → Your Python code.
* **requirements.txt** → List of required packages.
* **README.md** → Setup and usage guide.

---

## **requirements.txt**

```
opencv-python
mediapipe
pyautogui
```

---

## **README.md

# Hand-Controlled Cursor Project 🖐️🖱️

This project allows you to control your mouse cursor using hand gestures via your webcam. You can move the cursor, click, scroll, and even perform drag-and-drop—all using your hands, without a physical mouse.

---

## Features

- ✌️ Move mouse with index finger  
- 🤏 Click with pinch (thumb + index)  
- ✋ Scroll up/down  
- 🎮 Smooth AI-like movement for games and applications  
- Works on Windows and Linux (Python 3.9+)  

---

## Setup Guide in VS Code

Follow these steps to get this project running on your system:

### 1. Install Python
Make sure Python 3.9+ is installed. You can download it from [python.org](https://www.python.org/downloads/).

Check the version in terminal:

```bash
python --version
````

---

### 2. Clone the Repository

Open VS Code terminal and run:

```bash
git clone https://github.com/YOUR_USERNAME/Hand-Controlled-Cursor.git
cd Hand-Controlled-Cursor
```

---

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

This will install:

* OpenCV (`opencv-python`)
* Mediapipe (`mediapipe`)
* PyAutoGUI (`pyautogui`)

---

### 4. Open the Project in VS Code

1. Open VS Code.
2. Go to **File → Open Folder** and select the project folder.
3. Ensure the **Python interpreter** in VS Code is set to the Python version you installed (3.9+).
   Check in bottom-right corner → select Python 3.9.x.

---

### 5. Run the Program

1. Open `main.py`.
2. Press `F5` or run in terminal:

```bash
python main.py
```

3. A window will open showing your webcam feed.

   * Move your **index finger** → cursor moves.
   * Pinch **thumb + index** → click.
   * Press `ESC` → exit program.

---

### 6. Optional: Customize Gestures

* You can add gestures for:

  * Right-click
  * Drag & drop
  * Scroll
* Adjust distances in code for sensitivity and smoothness.

---

### Troubleshooting

* If you get errors like `module 'mediapipe' has no attribute 'solutions'` → Make sure **mediapipe is updated**:

```bash
pip install --upgrade mediapipe
```

* If cursor jitters → increase smoothing by adding a moving average for coordinates.
* Ensure no other program is using the webcam.

---

### License

This project is open-source. Feel free to use and modify it.
