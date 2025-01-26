from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="git-acp",
    version="0.13.4",
    author="Elvee",
    author_email="luis@lvalencia.dev",
    description="Git Add-Commit-Push automation tool with AI-powered commit messages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/beecave-homelab/git-acp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "git-acp=git_acp.cli:main",
        ],
    },
    install_requires=[
        "typing;python_version<'3.7'",
        "click==8.1.8",
        "rich==13.9.4",
        "questionary==2.1.0",
        "openai==1.59.3",
        "tqdm==4.67.1",
        "python-dotenv==1.0.1",
    ],
)
