from setuptools import setup, find_packages

setup(
    name="sql-server-compare",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyodbc",
        "ttkbootstrap",
        "pillow",
    ],
    entry_points={
        "console_scripts": [
            "sqlcompare=sql_compare.main:main",
        ],
    },
    author="Jose Freitas",
    description="A tool for comparing and synchronizing SQL Server database schemas",
    keywords="sql-server, database, schema, comparison",
    python_requires=">=3.7",
)
