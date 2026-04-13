"""
seed_jobs.py — Populates the database with sample job postings for the demo.

WHY THIS EXISTS:
For a demo or professor presentation, you don't want to manually enter jobs.
Run this script ONCE after starting the server to add realistic job postings.

Usage:
  python seed_jobs.py

This calls the /jobs API endpoint to create jobs, so the server must be running.
"""

import httpx
import json

API_URL = "http://localhost:8000/jobs"

SAMPLE_JOBS = [
    {
        "title": "Machine Learning Engineer",
        "company": "DeepMind Technologies",
        "skills": "Python, TensorFlow, PyTorch, Scikit-learn, NLP, Computer Vision",
        "experience": "3-5 years",
        "description": (
            "We are looking for a Machine Learning Engineer to design and implement "
            "production-grade ML models. You will work on natural language processing, "
            "deep learning architectures, and MLOps pipelines. Expertise in Python, "
            "TensorFlow or PyTorch is essential. Experience with transformer models, "
            "BERT, and large language models is a strong advantage. You will collaborate "
            "with research scientists to deploy models at scale using Docker and Kubernetes."
        )
    },
    {
        "title": "Data Scientist",
        "company": "Spotify",
        "skills": "Python, R, SQL, Statistics, A/B Testing, Pandas, Data Visualization",
        "experience": "2-4 years",
        "description": (
            "Join our data science team to drive data-driven product decisions. "
            "You will conduct statistical analysis, build predictive models, and "
            "design A/B experiments to improve user engagement. Strong proficiency "
            "in Python and SQL is required. You will use tools like Databricks, Spark, "
            "and Tableau. Experience in recommendation systems or audio feature analysis "
            "is a bonus. You must be comfortable presenting insights to non-technical stakeholders."
        )
    },
    {
        "title": "NLP Research Engineer",
        "company": "Hugging Face",
        "skills": "NLP, Transformers, BERT, Python, Hugging Face, PyTorch, Linguistics",
        "experience": "2-5 years",
        "description": (
            "We are hiring an NLP Research Engineer to advance our open-source transformer "
            "library. You will implement state-of-the-art NLP models including BERT, GPT, "
            "T5, and LLaMA architectures. Deep knowledge of tokenization, attention mechanisms, "
            "and fine-tuning is essential. You'll contribute to the Hugging Face Transformers "
            "library, write technical documentation, and collaborate on NLP benchmarks. "
            "Experience with semantic similarity, text classification, and named entity "
            "recognition is highly valued."
        )
    },
    {
        "title": "Backend Python Developer",
        "company": "Stripe",
        "skills": "Python, FastAPI, Django, PostgreSQL, Redis, Docker, REST APIs",
        "experience": "2-4 years",
        "description": (
            "We need a Backend Developer to build and maintain robust APIs for our "
            "payments infrastructure. You will design RESTful services using FastAPI or Django, "
            "write clean and testable Python code, and work closely with frontend engineers. "
            "Strong understanding of databases (PostgreSQL, Redis), caching strategies, "
            "and async programming is required. Experience with Docker, CI/CD pipelines, "
            "and microservices architecture is a plus."
        )
    },
    {
        "title": "Data Analyst",
        "company": "Airbnb",
        "skills": "SQL, Excel, Tableau, Python, Business Intelligence, Reporting",
        "experience": "1-3 years",
        "description": (
            "As a Data Analyst, you will extract insights from large datasets to inform "
            "business strategy. You will write complex SQL queries, build dashboards in "
            "Tableau and Looker, and prepare reports for leadership. Comfort with Python "
            "for data cleaning and analysis is expected. You'll work with cross-functional "
            "teams including product, marketing, and finance. Excellent communication and "
            "storytelling with data skills are essential."
        )
    },
    {
        "title": "Computer Vision Engineer",
        "company": "Tesla AI",
        "skills": "Python, OpenCV, PyTorch, CNNs, Object Detection, YOLO, CUDA",
        "experience": "3-6 years",
        "description": (
            "Tesla's Autopilot team is hiring a Computer Vision Engineer. You will develop "
            "real-time object detection, lane recognition, and depth estimation systems. "
            "Strong experience with convolutional neural networks, YOLO, and OpenCV is "
            "required. You must be proficient with GPU computing (CUDA) and PyTorch. "
            "Experience with autonomous driving datasets, sensor fusion, and model "
            "optimization for embedded systems is highly desirable."
        )
    },
    {
        "title": "Full Stack Developer",
        "company": "Notion",
        "skills": "React, Node.js, TypeScript, PostgreSQL, GraphQL, AWS",
        "experience": "2-5 years",
        "description": (
            "We are looking for a Full Stack Developer to build features for our "
            "productivity platform. You will work with React on the frontend and "
            "Node.js/TypeScript on the backend. Experience with PostgreSQL, GraphQL APIs, "
            "and AWS services is expected. You will participate in architecture decisions, "
            "code reviews, and agile sprint planning. A love for clean UX and performance "
            "optimization is important. Prior experience with real-time collaboration "
            "features using WebSockets is a plus."
        )
    },
    {
        "title": "AI Product Manager",
        "company": "Microsoft",
        "skills": "Product Management, AI/ML Knowledge, Agile, User Research, Roadmapping",
        "experience": "4-7 years",
        "description": (
            "Microsoft is seeking an AI Product Manager to lead AI-powered product features. "
            "You will work at the intersection of business, design, and engineering, "
            "defining product strategy for machine learning features in Microsoft 365. "
            "A solid understanding of AI/ML capabilities, limitations, and ethics is "
            "required. You should have experience with agile methodologies, user research, "
            "and cross-functional leadership. Ability to write clear PRDs and communicate "
            "technical trade-offs to executives is essential."
        )
    },
]


def seed():
    print("🌱 Seeding sample jobs into the database...\n")
    for i, job in enumerate(SAMPLE_JOBS, 1):
        try:
            r = httpx.post(API_URL, json=job, timeout=30)
            r.raise_for_status()
            data = r.json()
            print(f"  ✅ [{i}/{len(SAMPLE_JOBS)}] Created: \"{data['title']}\" (ID: {data['id']})")
        except Exception as e:
            print(f"  ❌ Failed to create \"{job['title']}\": {e}")

    print(f"\n🎉 Done! {len(SAMPLE_JOBS)} jobs added. Visit http://localhost:8000 to use the platform.")


if __name__ == "__main__":
    seed()
