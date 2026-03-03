"""
Setup script for EarnApp Reviewer
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version
version_file = Path(__file__).parent / 'VERSION'
version = version_file.read_text().strip() if version_file.exists() else '1.0.0'

# Read long description
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

setup(
    name='earnapp-reviewer',
    version=version,
    description='Automated EarnApp URL scanner with keyword detection and removal',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Synyster Rick',
    license='Apache License 2.0',
    url='https://github.com/YOUR_USERNAME/earnapp-reviewer',
    packages=find_packages(),
    python_requires='>=3.9',
    install_requires=[
        'PyQt6>=6.7.0',
        'playwright>=1.45.0',
        'qasync>=0.27.0',
        'requests>=2.32.0',
        'beautifulsoup4>=4.12.0',
    ],
    entry_points={
        'console_scripts': [
            'earnapp-reviewer=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
    ],
    keywords='earnapp scanner automation playwright',
)
