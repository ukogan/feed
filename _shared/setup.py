from setuptools import setup, find_packages

setup(
    name="feed-shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.34.0",
        "httpx>=0.28.0",
        "jinja2>=3.1.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
)
