from setuptools import setup, find_packages

setup(
    name="bitchat",
    version="1.0.0",
    description="Python implementation of the bitchat mesh networking protocol",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Nguyen Truong Long",
    author_email="nguyentruonglongdev@gmail.com",
    url="https://github.com/nguyentruonglong/bitchat-py",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "bleak>=0.21.1",
        "cryptography>=42.0.5",
        "pybloom-live>=4.0.0",
    ],
    python_requires=">=3.8",
    license="Unlicense",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Unlicense",
        "Operating System :: OS Independent",
    ],
)