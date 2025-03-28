# Code Generator API  

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-High%20Performance-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A FastAPI-powered web service that integrates the `mistralai/Mistral-7B-Instruct-v0.1` model to generate high-quality code in various programming languages based on user prompts.

![System Architecture](https://via.placeholder.com/800x400.png?text=Backend+%2B+Frontend+Architecture)

---

## Table of Contents  

- [Overview](#overview)  
- [Key Features](#key-features)  
- [Project Structure](#project-structure)  
- [Installation & Setup](#installation--setup)  
- [API Endpoints](#api-endpoints)  
- [Deployment](#deployment)  
- [Future Enhancements](#future-enhancements)  
- [Contributing](#contributing)  
- [License](#license)  
- [Contact](#contact)  

---

## Overview  

The **Code Generator API** is a scalable and efficient system for AI-driven code generation, designed for developers, educators, and AI enthusiasts. This system allows users to input prompts and receive corresponding code in multiple programming languages.

---

## Key Features 🚀  

- **FastAPI Backend:** High-performance web API for code generation.  
- **Hugging Face Integration:** Uses the `mistralai/Mistral-7B-Instruct-v0.1` model for text-to-code transformation.  
- **Multi-language Support:** Generates code in various programming languages based on user input.  
- **Efficient API Endpoints:** Well-structured and optimized for easy integration.  
- **Scalable Deployment:** Supports cloud deployment, including AWS, GCP, and Hugging Face Spaces.  

---

## Project Structure  

code-generator/ ├── app/ │ ├── backend.py # FastAPI backend logic │ ├── frontend.py # Streamlit frontend logic (upcoming feature) ├── .gitignore # Files to be ignored by Git ├── requirements.txt # Dependencies ├── README.md # Project documentation


---

## Installation & Setup  

### **Prerequisites**  
- Python 3.8+  
- Virtual environment (recommended)  
- `pip` package manager  

### **Setup Instructions**  
1. **Clone the repository:**  
   ```sh
   https://github.com/Shivadzn/code-generator.git
   cd code-generator
   
2. Create and activate a virtual environment:
- python -m venv venv
- source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:
- pip install -r requirements.txt

4. Run the FastAPI server:
- uvicorn app.backend:app --host 0.0.0.0 --port 8000 --reload

5. Access the API documentation:
**Open http://127.0.0.1:8000/docs in your browser.**

# API Endpoints
- Method	Endpoint	Description
- POST	/generate	Generates code based on the provided prompt.

## Example Request:
curl -X POST "http://127.0.0.1:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Write a Python function to check prime numbers."}'

## Example Response
{
  "generated_code": "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n ** 0.5) + 1):\n        if n % i == 0:\n            return False\n    return True"
}

# Deployment
This project can be deployed using:

- Hugging Face Spaces

- Docker

- Cloud Services (AWS/GCP/Azure)

Future Enhancements
- Streamlit-based frontend integration.

- Support for additional models and fine-tuning.

- Enhanced error handling and logging.

# License
- This project is licensed under the MIT License.

#Contact
For queries or collaborations, feel free to reach out via [www.linkedin.com/in/shiva-gupta-a70190234].
