import os.path
import re
import setuptools


def get_package_variable(name, rel_path="receipt_parser/__init__.py"):
    path = os.path.join(os.path.abspath(os.path.dirname(name)), rel_path)

    pattern = re.compile(r'^{}.*?([\'"])(?P<value>.+)\1.*$'.format(re.escape(name)))

    with open(path, "r", encoding="UTF-8") as fh:
        for line in fh:
            match = pattern.match(line)

            if match:
                return match.group("value")
        raise RuntimeError("Unable to find variable: " + name)


__version__ = get_package_variable("__version__")


with open("README.md", "r", encoding="UTF-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="UTF-8") as fh:
    install_requires = fh.read()


setuptools.setup(
    name="receipt_parser",
    version=__version__,
    author="Savvov Sergey",
    author_email="sersavvov@yandex.ru",
    description="Allow receipt parsing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/slgero/receipt_parser",
    packages=setuptools.find_packages(include=["receipt_parser", "receipt_parser.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Natural Language :: Russian",
    ],
    install_requires=install_requires,
    python_requires=">=3.6",
    keywords=["receipt parser", "product parser", "nlp"],
)
