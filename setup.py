import setuptools

REQUIREMENTS = [line for line in open('requirements.txt').read().split('\n') if line != '']

VERSION = '0.2.0'
AUTHOR = 'Igor Dias, Daniel Henning'
EMAIL = 'igorhenriquedias94@gmail.com, dhenning@hp-jammer.de'



setuptools.setup(
    name='axis_vapix',
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    license='MIT',
    description='Implementation of python functions for control and configuration of Axis cameras using Vapix.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=['axis', 'vapix', 'camera'],
    python_requires='>=3.6',
    install_requires=REQUIREMENTS,
)
