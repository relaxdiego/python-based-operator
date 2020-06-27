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


_NAME = 'prometheus_operator'
setup(
    name=_NAME,
    version='0.1.0',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.8',
    ],
    author='Mark S. Maglana',
    author_email='mark.maglana@linux.com',
    include_package_data=True,
    install_requires=[
        'kubernetes>=11.0.0,<11.1.0',
    ],
    entry_points={
        'console_scripts': [
            '{0} = {0}.operator:main'.format(_NAME),
        ]
    }
)
