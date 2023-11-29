# Bundler for FHIR profile validation resources

## Summary

This is a utility that helps create a FHIR `transaction` [Bundle](https://build.fhir.org/bundle.html) of a set of profile validation resources, such that execution of the bundle can load the resources atomically into a FHIR store.

## Getting Started

Being a Python-based utility, you will have to have [Python](https://www.python.org/downloads/) installed.

Otherwise, the utility uses libraries that are part of the Python [standard library](https://docs.python.org/3/library/index.html) - `argparse`, `hashlib`, `json`, `os` and `uuid`.

### Details

Place the utility file in a directory where one of its subfolders contains all the profile validation resources you'd like to bundle. Follow the prompts once you trigger the script to enter the path to those resources relative to the CWD of the utility file. Once run, a new folder will be created in the utility file's CWD along with the bundled output.

### Feedback/contributions

We welcome any help with improving the tool! Please see the CONTRIBUTING file for guidelines.

## License

Apache License, Version 2.0