from setuptools import setup, find_packages

setup(
	name = 'wellx',
	version = '0.0.25',
	packages = find_packages(),
	install_requires = [
		'numpy>=1.26.4',
		],
	)

# Run the followings from the command line to test it locally:

# python setup.py sdist bdist_wheel

# pip install dist/wellx-{version}-py3-none-any.whl

# Run the followings from the command line to upload to pypi:

# twine upload dist/*