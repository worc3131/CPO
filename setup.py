from setuptools import setup

import cpo

setup(
    name='CPO',
    packages=['cpo'],
    description='Communication Python Objects',
    version=cpo.__version__,
    author='George Harding',
    author_email='work.gwh@gmail.com',
    keywords=['python', 'cpo', 'cso', 'occam'],
    install_requires=[],
    python_requires='>=3.7'
    )
