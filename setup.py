from setuptools import setup, find_packages

setup(
    name="file2md",
    version="0.1.0",
    description="다양한 파일 형식을 마크다운으로 변환하는 라이브러리",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pdfplumber>=0.10.0",
        "python-docx>=0.8.11",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "python-pptx>=0.6.21",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "urllib3>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "file2md=file2md.cli:main",
        ],
    },
)
