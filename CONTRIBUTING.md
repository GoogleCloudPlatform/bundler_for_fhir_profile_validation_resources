# How to contribute

We'd love to accept your patches and contributions to this project.

## Before you begin

### Sign our Contributor License Agreement

Contributions to this project must be accompanied by a
[Contributor License Agreement](https://cla.developers.google.com/about) (CLA).
You (or your employer) retain the copyright to your contribution; this simply
gives us permission to use and redistribute your contributions as part of the
project.

If you or your current employer have already signed the Google CLA (even if it
was for a different project), you probably don't need to do it again.

Visit <https://cla.developers.google.com/> to see your current agreements or to
sign a new one.

### Review our community guidelines

This project follows
[Google's Open Source Community Guidelines](https://opensource.google/conduct/).

## Contribution process

### Code reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult
[GitHub Help](https://help.github.com/articles/about-pull-requests/) for more
information on using pull requests.

See the [CL author's guide](https://google.github.io/eng-practices/review/developer/)
for best practices on submitting pull requests.

## Style Guide

All code contributions should follow Google language-specific style guides at
<https://google.github.io/styleguide>.

## Usage notes

- The implementation guide feature in Google Cloud Healthcare FHIR stores are
  used for *profile validation*. If you try to create a bundle from a guide
  package that contains a purely descriptive `ImplementationGuide` (i.e. one
  that solely provides textual information without any associated validation
  resources like `StructureDefinition`s, `ValueSet`s, etc.), it will not have
  much effect after upload into a FHIR store.
- `ImplemenationGuide`s may contain `StructureDefinition`s that should not be
  applied to all resources, either because they do not describe a resource
  (`StructureDefinition`s for FHIR data types), or they only apply in specific
  scenarios. To distinguish between these different use cases, the FHIR store
  uses the `ImplementationGuide.global` field to identify resource profiles that
  all incoming resources should be validated against.

  The bundler will help you assemble resource-based `StructureDefinition`s into
  the `ImplementationGuide.global` field, should you instruct it to. You will
  have to ensure other `StructureDefinition`s are referenced appropriately
  according to your use case.