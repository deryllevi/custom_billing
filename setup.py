from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="custom_billing",
    version="1.0.0",
    description="Finance-officer reviewed invoice emailing for ERPNext v14",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Your Name / Company",
    author_email="you@example.com",
    license="MIT",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
)
