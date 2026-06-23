# Thai Text Segmenter System

A Thai text segmentation system designed to process Thai text from plain text input and HTML files. The system segments Thai text into more readable word units, making it easier to analyse, display and prepare for web-based content such as landing pages.

Thai text segmentation is challenging because Thai sentences are often written **without spaces between words.** This project addresses that issue by combining **machine learning**, **dictionary-based segmentation** and **custom rule-based processing** to produce more practical segmentation results.

---

## 🎯 Project Purpose and Motivation

This project was developed as my **Final Year Project**, focusing on **Thai text segmentation** and its practical use in **web layouts**.

The idea came from **my experience in frontend development**, where I often had to deal with Thai text wrapping issues in website layouts. Thai text is commonly written without spaces between words, which can cause words to break incorrectly at the end of a line. This creates extra manual work when adjusting landing pages and other web content.

While there are existing open-source Thai NLP tools, I noticed that they can still produce incorrect segmentation for certain words, especially in real website content. Since these tools are not always easy to retrain or customise for a specific frontend use case, manually adding words to a dictionary is often only a temporary solution.

Therefore, the purpose of this project is to **better understand Thai text segmentation** and develop it into a practical **Thai text segmenter system**. The main focus is to identify likely **Thai word boundaries** and group Thai text into **suitable word units**, allowing Thai content to **wrap more naturally in web layouts**.

This project also demonstrates how an **academic Thai text segmentation method** can be adapted into a usable full-stack application with **frontend**, **backend**, and **machine learning components**.

---

## 🎬 Demo
[![YouTube Video qYPyIiI_O9k](https://utfs.io/f/nGnSqDveMsqxfCR27I8SwoegrUBJZjmC8iTa4NsIvbOnMyR6)](https://www.youtube.com/watch?v=qYPyIiI_O9k)

---
## 🔍 Before and After

<p align="center">
  <img width="654" height="979" alt="beforeaftertext" src="https://github.com/user-attachments/assets/f72c9452-6293-4f53-a1e3-4140b641bd54" />
</p>

**Before:**
In the original Thai text, line wrapping often **breaks words incorrectly.** For example, words such as `ภาษา` (*language*) and `รูปแบบ` (*format/pattern*) should stay together, but they may be split across lines in a web layout.

**After:**
The system identifies likely **word boundaries** and inserts spaces between segmented words. This helps the text **wrap more naturally** on websites. While the result is not perfect, achieving **over 70% accuracy** is already useful for improving Thai text readability in web layouts.

---

## Project Background

This project was developed as an AI-assisted software engineering project. I used AI tools extensively throughout the development process, including for code generation, debugging, interface design, refactoring and documentation.

The core segmentation workflow was inspired by an existing academic thesis on Thai text segmentation. The thesis was used as a foundation to understand the overall methodology and processing flow. I then adapted, modified and extended the approach into a working full-stack application with a user interface, file upload support, user history and practical text processing features.

This project is not a direct copy of the thesis implementation. Instead, the thesis served as a conceptual reference for understanding the segmentation process, while the final system was redesigned and implemented into a usable web-based application.

---

## ✨ Key Features

* Thai text segmentation from direct text input
* HTML file upload and processing
* Extraction and segmentation of Thai text from HTML content
* User history for previous segmentation results

---

## ⚙️ How the System Works

The system follows a Thai text segmentation pipeline.

<p align="center">
  <img width="543" height="662" alt="flowchart" src="https://github.com/user-attachments/assets/acb08ed9-b33d-4e74-899c-366493930577" />
</p>

The user can either paste Thai text directly into the text input page or upload an HTML file. For HTML files, the system parses the file, extracts the Thai text and then applies the segmentation pipeline.

The segmentation process uses a combination of machine learning and dictionary-based logic. A custom CRF model is used for syllable and MTU segmentation, while a Viterbi-based approach is used to select the most suitable word segmentation path.

---

## 🧪 Example

### Input

```
วันดีอากาศแจ่มใสสดชื่น แมวรัก สวัสดีปีใหม่
```

### Output

```
วันดี อากาศ แจ่มใส สดชื่น แมวรัก สวัสดี ปีใหม่
```

### Explanation

The original Thai sentence does not contain spaces between words. The system identifies likely word boundaries and groups Thai text into word units, allowing the text to wrap more naturally in web layouts without breaking words incorrectly.


---

## 🛠️ Tech Stack

### Frontend

* React 
* TypeScript

### Backend

* Python
* FastAPI
* Uvicorn
* sklearn-crfsuite
* scikit-learn


### Machine Learning

* Custom CRF model for syllable and MTU segmentation
* Custom k-best word segmentation
* LST20 dictionary support for Thai word segmentation

---


## 📚 Academic Reference

This project was inspired by the following academic work:

**Kannikar Paripremkul.**
*Word Segmentation and Part-of-Speech Tagging for Thai Language Using Minimum Text and Conditional Random Field.*
PhD Dissertation, National Institute of Development Administration, 2020.
DOI: `10.14457/NIDA.the.2020.128`
Retrieved: 15 October 2025.

The thesis was used as a conceptual foundation for understanding Thai word segmentation, Minimum Text Unit segmentation, syllable segmentation, word segmentation, and Conditional Random Field-based processing.

This project does not directly copy the thesis implementation. Instead, the methodology was studied, adapted, modified, and extended into a practical full-stack Thai text segmenter system with a web interface, HTML file processing, user history and custom application-level features.

---

## 🚀 Future Improvements

* Improve segmentation accuracy with a larger training dataset
* Improve HTML text extraction accuracy
* Support batch file processing
* Improve the UI for mobile and tablet screens

---

## 💻 Thai Segmentation System Server - Development

### Backend

To run the backend server, navigate to the `backend` directory and execute:

```bash
uv run main.py
```

### Frontend

To run the frontend development server, navigate to the `frontend` directory and execute:

```bash
npm install # run once
npm run dev
```
