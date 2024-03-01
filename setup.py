from setuptools import setup, find_packages

setup(
    name="moonlander",
    version="0.1.0",
    py_modules=["kb"],  # if it's a single-file script
    # packages=find_packages(),  # if it's a complex project
    install_requires=[
        # "DEPENDENCY"
    ],
    entry_points={
        "console_scripts": [
            "kb = moonlander:main",
            "moonlander = moonlander:main",
        ],
    },
)
