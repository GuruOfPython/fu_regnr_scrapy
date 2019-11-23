# Automatically created by: shub deploy

from setuptools import setup, find_packages

setup(
    name='fu-regnr_scrapy',
    version='1.0',
    packages=find_packages(),
    package_data={
        'fu-regnr_scrapy': ['/spiders/*.csv']
    },
    entry_points={'scrapy': ['settings = fu_regnr.settings']},
)
