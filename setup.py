from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="git-acp",
    version="0.9.2",
    author="elvee",
    author_email="",
    description="A tool to automate Git add, commit, and push with AI-powered commit messages",
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
        "click>=8.0.0",
        "rich>=10.0.0",
        "questionary>=1.10.0",
        "typing;python_version<'3.7'",
    ],
)