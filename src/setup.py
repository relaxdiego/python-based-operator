from sys import version_info

from setuptools import find_packages, setup

minimum_python_version = (3, 8, 3)

if version_info[:3] < minimum_python_version:
    raise RuntimeError(
        'Unsupported python version {}. Please use {} or newer'.format(
            '.'.join(map(str, version_info[:3])),
            '.'.join(map(str, minimum_python_version)),
        )
    )


_NAME = 'python-based-operator'
setup(
    name=_NAME,
    version='0.2.0',
    packages=find_packages(),
    author='Mark S. Maglana',
    author_email='mmaglana@gmail.com',
    include_package_data=True,
    install_requires=[
        'kubernetes>=11.0.0,<11.1.0',
    ],
    entry_points={
        'console_scripts': [
            f"{_NAME} = {_NAME.replace('-', '_')}.operator:main",
        ]
    },
    # https://pypi.org/classifiers/
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
    ]
)
