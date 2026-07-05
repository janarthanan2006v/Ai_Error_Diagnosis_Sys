# AI Error Diagnosis System using Gemini Vision + RAG + FAISS

## C — Context

You are a Senior AI Engineer, Full-Stack Engineer, ML Engineer, Prompt Engineer, and Software Architect.

Your task is to build a production-ready end-to-end application that diagnoses software errors from screenshots.

The application allows users to upload screenshots containing programming errors, stack traces, terminal outputs, IDE errors, runtime exceptions, compiler errors, or deployment issues.

The system must:

1. Accept image uploads.
2. Analyze screenshots using Google Gemini Vision.
3. Extract error information.
4. Generate embeddings using Sentence Transformers.
5. Retrieve similar historical errors using FAISS.
6. Augment diagnosis with retrieved knowledge.
7. Generate expert troubleshooting recommendations using Gemini.
8. Return structured JSON.
9. Generate a downloadable PDF report.
10. Provide a clean modern frontend.

---

## O — Objective

Build a complete AI-powered Error Diagnosis Assistant with:

### Frontend

* HTML
* CSS
* JavaScript

### Backend

* FastAPI
* Uvicorn

### AI Layer

Google Gemini API

### RAG Layer

Sentence Transformers

Model:

all-MiniLM-L6-v2

Vector Database:

FAISS

### Output

* Structured JSON
* PDF Report

---

## S — Scope

The system must include:

### Module 1

Image Upload Interface

Features:

* Drag and Drop
* File Picker
* Upload Preview
* Upload Validation

Supported Formats:

* PNG
* JPG
* JPEG
* WEBP

---

### Module 2

Gemini Vision Analysis

Tasks:

* OCR
* Error Detection
* Stack Trace Extraction
* Programming Language Detection
* Environment Detection

Output:

{
"error_title": "",
"error_message": "",
"language": "",
"framework": "",
"environment": "",
"raw_stacktrace": ""
}

---

### Module 3

Knowledge Base

Knowledge Categories:

* Python Errors
* FastAPI Errors
* Flask Errors
* Django Errors
* JavaScript Errors
* React Errors
* NodeJS Errors
* Database Errors
* Deployment Errors

Each record contains:

{
"error_name": "",
"description": "",
"root_cause": "",
"solution": "",
"troubleshooting_steps": []
}

Store as JSON files.

---

### Module 4

Embedding Pipeline

Use:

SentenceTransformer

Model:

all-MiniLM-L6-v2

Tasks:

* Encode Knowledge Base
* Generate Embeddings
* Save Vector Index

---

### Module 5

FAISS Retrieval

Tasks:

* Load Vector Index
* Search Similar Errors
* Return Top K Results

Default:

K = 5

---

### Module 6

Prompt Augmentation

Combine:

* Extracted Error
* Similar Errors
* Solutions
* Troubleshooting Steps

Create enriched context for Gemini.

---

### Module 7

Gemini Diagnosis

Generate:

* Root Cause
* Explanation
* Confidence Score
* Resolution Steps
* Preventive Measures
* Best Practices

---

### Module 8

JSON Output

Return:

{
"error_summary":"",
"root_cause":"",
"confidence_score":"",
"recommended_fix":"",
"step_by_step_solution":[],
"prevention_tips":[],
"related_errors":[]
}

---

### Module 9

PDF Generator

Generate professional report containing:

1. Error Screenshot
2. Error Summary
3. Root Cause
4. Diagnosis
5. Fix Recommendations
6. Troubleshooting Steps
7. Prevention Tips

Export:

report.pdf

---

### Module 10

Frontend Dashboard

Pages:

* Upload Page
* Processing Page
* Results Page
* PDF Download

UI Requirements:

* Responsive
* Clean
* Modern
* Minimal
* Mobile Friendly

---

## T — Technical Requirements

Backend:

FastAPI
Uvicorn

AI:

Google Gemini API

RAG:

Sentence Transformers
all-MiniLM-L6-v2

Vector DB:

FAISS

PDF:

ReportLab

Frontend:

HTML
CSS
JavaScript

Configuration:

.env

Secrets:

Never hardcode API keys.

---

## A — Actions

Implement in the following sequence:

1. Project Setup
2. Backend Architecture
3. Gemini Vision Integration
4. Knowledge Base Creation
5. Embedding Generation
6. FAISS Index Creation
7. Retrieval Layer
8. Prompt Engineering
9. Diagnosis Engine
10. JSON Formatter
11. PDF Generator
12. Frontend Dashboard
13. API Integration
14. Error Handling
15. Logging
16. Testing
17. Documentation

---

## R — Result

Deliver a complete production-ready application with:

* Clean Architecture
* Modular Code
* Type Hints
* Pydantic Models
* Environment Configuration
* Unit Tests
* API Documentation
* README
* Deployment Guide

The final application should run using:

uvicorn app.main:app --reload

and provide an end-to-end AI-powered error diagnosis workflow from screenshot upload to PDF report generation.

---

# RISE EXECUTION STRATEGY

## R — Role

Act as:

* Principal Software Architect
* Senior AI Engineer
* Senior FastAPI Engineer
* Senior RAG Engineer
* Senior Prompt Engineer

---

## I — Input

Input:

Screenshot containing software error.

Possible Sources:

* VS Code
* PyCharm
* IntelliJ
* Browser Console
* Terminal
* Docker Logs
* CI/CD Logs

---

## S — Steps

1. Receive Screenshot
2. Run Gemini Vision
3. Extract Error Details
4. Generate Query Embedding
5. Search FAISS
6. Retrieve Similar Errors
7. Augment Prompt
8. Generate Diagnosis
9. Format JSON
10. Generate PDF
11. Return Response

---

## E — Expected Output

Provide:

* Source Code
* APIs
* Models
* Services
* Utilities
* Frontend
* Tests
* Documentation
* Deployment Configuration

All code must be production-grade, maintainable, scalable, and well documented.
