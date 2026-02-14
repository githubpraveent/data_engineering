"""
Setup file for Dataflow pipelines.
"""

from setuptools import setup, find_packages

setup(
    name='retail-dataflow-pipelines',
    version='1.0.0',
    description='Dataflow pipelines for retail data lake',
    packages=find_packages(),
    install_requires=[
        'apache-beam[gcp]==2.50.0',
        'google-cloud-bigquery==3.11.0',
        'google-cloud-storage==2.10.0',
        'google-cloud-pubsub==2.18.0',
    ],
)

