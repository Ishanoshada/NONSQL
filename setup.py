from setuptools import setup, find_packages

setup(
    name="nonsql",
    version="1.1.2",
    packages=find_packages(),
    install_requires=[
        'click>=7.0',
        'pyyaml>=5.4.0'
    ],
    author="Ishan Osahda",
    author_email="ishan.kodithuwakku.offical@gmail.com",
    description="A NoSQL database management tool",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ishanoshada/nonsql",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'nonsql=nonsql.cli:main',
        ],
    },
)
