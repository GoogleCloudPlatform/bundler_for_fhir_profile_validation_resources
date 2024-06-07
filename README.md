# Bundler for FHIR profile validation resources

## Summary

This is a utility that helps create a FHIR `transaction` [Bundle](https://build.fhir.org/bundle.html) of a set of profile validation resources, such that execution of the bundle can load the resources atomically into a FHIR store.

## Getting Started

Being a Python-based utility, you will have to have [Python](https://www.python.org/downloads/) installed.

Otherwise, the utility uses libraries that are part of the Python [standard library](https://docs.python.org/3/library/index.html) - `argparse`, `hashlib`, `json`, `os` and `uuid`.

### Details

You'll need to run the utility with these input arguments:

- `--input_dir`: the directory containing all of the loose FHIR profile validation resource JSONs.
- `--output_dir`: the directory into which to output the bundle of profile validation resources.
- `--generate_global_array`: optional boolean flag to indicate whether or not you'd like the utility to populate the `global` array in the `ImplementationGuide` resource containing references to all `StructureDefinition` resources in the inputs, which is [needed by the Google Cloud Healthcare API](https://cloud.google.com/healthcare-api/docs/how-tos/fhir-profiles#configure_your_implementation_guide). The default value is True. If you've already done this yourself, you can pass `--no-generate_global_array`.

### Feedback/contributions

We welcome any help with improving the tool! Please see the CONTRIBUTING file for guidelines.

## License

Apache License, Version 2.0