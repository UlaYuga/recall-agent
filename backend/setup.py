from setuptools import setup

setup(
    name="recall-backend",
    version="0.1.0",
    description="FastAPI backend for Recall AI CRM reactivation pipeline",
    packages=[
        "app",
        "app.agent",
        "app.api",
        "app.delivery",
        "app.runway",
        "app.telegram",
        "app.workers",
    ],
    install_requires=[
        "fastapi>=0.115",
        "uvicorn[standard]>=0.32",
        "sqlmodel>=0.0.22",
        "pydantic-settings>=2.6",
        "httpx>=0.27",
        "anthropic>=0.40",
        "runwayml>=3.0",
        "aiogram>=3.13",
        "apscheduler>=3.10",
        "ffmpeg-python>=0.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "ruff>=0.8",
        ]
    },
    python_requires=">=3.11",
)

