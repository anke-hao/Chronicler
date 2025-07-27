from setuptools import setup, find_packages

setup(
    name="changelog-gen",
    version="1.0.0",
    description="AI-powered changelog generator CLI tool",
    author="Your Name",
    author_email="your.email@example.com",
    py_modules=["changelog_gen"],
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "changelog-gen=changelog_gen:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)