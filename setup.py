from setuptools import setup, find_packages

setup(
    name='Textwall Monitoring',
    version='0.5.0',
    description='Process Given Texwall CSV Output',
    author='Patrick Roddy',
    author_email='patrickjamesroddy@gmail.com',
    packages=find_packages(),
    install_requires=['datetime', 'numpy', 'pandas', 'argparse'],
    use_2to3=True,
    entry_points={
        'console_scripts': [
            'textwall = attendance.command:main'
        ]
    }
)
