# Copyright 2023 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Bundles FHIR profile validation resources.

This script helps create a transaction FHIR bundle out of a set of profile
validation resources including an ImplementationGuide resource that can be
executed atomically in a FHIR store. Specify both the folder where the profile
validation resources are stored, and an output directory for the bundle.
Directories can be specified both as absolute paths or relative to the cwd.
"""

import argparse
import hashlib
import json
import os
import uuid


class FhirProfileValidationResourcesBundler:
  """Wraps FHIR profile validation resources into a FHIR transaction bundle."""

  def __init__(self):
    # In order to ensure that resource references within the IG are maintained
    # when the server processes the bundle, we need to assign each resource a
    # UUID:
    # https://cloud.google.com/healthcare-api/docs/how-tos/fhir-bundles#resolving_references_to_resources_created_in_a_bundle
    # The dict maps resourceType/resourceID references that the IG currently has
    # to UUIDs that will be generated, and the set helps prevent dupes.
    self.resource_id_to_uuid_map = {}
    self.uuid_tracker = set()

  def GetAttributeFlags(self):
    """Gets attributes passed in by the user via the command line.

    User inputs include the directory containing all the raw profile validation
    resource files, the directory to output the final bundle, and whether or not
    the user needs the global array with the ImplementationGuide resource to be
    constructed.

    Returns:
      A tuple of the inputs directory, output directory, and boolean of whether
      or not to construct the global array.

    Raises:
      ValueError: if the input directory provided does not exist.
    """
    parser = argparse.ArgumentParser(
        prog='Bundler for FHIR profile validation resources',
        description=(
            'Utility that helps create a transaction FHIR bundle from a set of'
            ' profile validation resources'
        ),
    )
    parser.add_argument(
        '--input_dir',
        help=(
            'Please enter the name of the folder containing all IG-relevant'
            ' files. You can either an absolute path, or one that is relative'
            ' to the current working directory e.g. if the cwd is foo and'
            ' subdir is bar, type bar'
        ),
    )
    parser.add_argument(
        '--output_dir',
        help=(
            'Please enter the name of the folder to which the bundle will be'
            ' written. You can either an absolute path, or one that is relative'
            ' to the current working directory e.g. if the cwd is foo and'
            ' subdir is bar, type bar'
        ),
    )
    parser.add_argument(
        '--generate_global_array',
        default=True,
        action=argparse.BooleanOptionalAction,
        help=(
            'Please indicate whether or not you would like this utility to'
            ' generate `global` array of references to all StructureDefinitions'
            ' and insert it for you into the ImplementationGuide resource.'
            ' Defaults to true. If the global array already exists in your IG'
            ' resource, please input --no-generate_global_array.'
        ),
    )
    args = parser.parse_args()

    ig_folder = args.input_dir
    is_ig_dir_abs_path = os.path.isabs(ig_folder)
    if is_ig_dir_abs_path:
      source_dir = ig_folder
    else:
      source_dir = os.path.join(os.getcwd(), os.path.relpath(ig_folder))

    if not os.path.exists(source_dir):
      raise ValueError('Given directory does not exist!')

    bundle_dest_folder = args.output_dir
    is_bundle_dest_dir_abs_path = os.path.isabs(bundle_dest_folder)
    if is_bundle_dest_dir_abs_path:
      target_dir = bundle_dest_folder
    else:
      target_dir = os.path.join(
          os.getcwd(), os.path.relpath(bundle_dest_folder)
      )

    if not os.path.exists(target_dir):
      os.mkdir(target_dir)

    do_construct_global_array = args.generate_global_array
    return source_dir, target_dir, do_construct_global_array

  def ProcessProfileValidationResourcesAt(
      self, source_dir, do_construct_global_array
  ):
    """Reads in profile validation resource files at a given input directory and wraps them into a FHIR transaction bundle.

    Args:
      source_dir: directory containing all the input profile validation resource
        files.
      do_construct_global_array: whether or not to construct the
        ImplementationGuide resource's global array.

    Returns:
      A FHIR transaction bundle containing all the profile validation resources.
    """
    for child in os.listdir(source_dir):
      global_array = []
      bundle_entries = []
      bundle = {
          'resourceType': 'Bundle',
          'type': 'transaction',
          'entry': bundle_entries,
      }
      ig_resource = {}

      file_path = os.path.join(source_dir, child)
      if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
          resource = json.load(f)
          resource_type = resource['resourceType']
          if resource_type != 'ImplementationGuide':
            # Process these first
            bundle_entry, global_array = self.ProcessProfileValidationResource(
                resource, do_construct_global_array, global_array
            )
            bundle_entries.append(bundle_entry)
          else:
            ig_resource = resource

          ig_bundle_entry = self.ProcessImplementationGuideResource(
              ig_resource, do_construct_global_array, global_array
          )
          bundle_entries.append(ig_bundle_entry)
          return bundle

  def ProcessProfileValidationResource(
      self, resource, do_construct_global_array, global_array
  ):
    """Helps process all non-ImplementationGuide profile validation resources.

    Args:
      resource: the profile validation resource.
      do_construct_global_array: whether or not to populate the given global
        array with this resource's type and URL. This is only done for
        StructureDefinitions.
      global_array: array containing accumulating all StructureDefinition
        references.

    Returns:
      A bundle entry representing the resource in the bundle and the
      global_array.
    """
    resource_type = resource['resourceType']
    # See
    # https://cloud.google.com/healthcare-api/docs/how-tos/fhir-profiles#configure_your_implementation_guide
    resource_uuid = self.__generate_uuid__(resource_type, resource['id'])
    # Please ensure that each profile validation resource has a unique url and
    # version combination - among your own custom resources, and Google's
    # provided default profile validation resources.
    # Here, we try to assign to each resource an ID that's as unique as
    # possible across different profile validation resource sets, while
    # conforming to FHIR's format requirements for resource IDs.
    resource_url = resource['url']
    resource_version = resource['version']
    if resource_url and resource_version:
      m = hashlib.sha256()
      m.update(bytes(resource_url + '|' + resource_version, 'utf-8'))
      resource['id'] = m.hexdigest()

    # Refer to cloud.google.com/healthcare-api/docs/how-tos/fhir-profiles
    if do_construct_global_array and resource_type == 'StructureDefinition':
      sd_targeted_resource_type = resource['type']
      global_array.append(
          {'type': sd_targeted_resource_type, 'profile': resource_url}
      )
    resource_bundle_entry = {
        'resource': resource,
        'fullUrl': resource_uuid,
        'request': {
            'method': 'POST',
            'url': resource_type,
        },
    }
    return resource_bundle_entry, global_array

  def ProcessImplementationGuideResource(
      self, resource, do_construct_global_array, global_array
  ):
    """Helps process the ImplementationGuide resources.

    Args:
      resource: the ImplementationGuide resource.
      do_construct_global_array: whether or not to set the IG resource's global
        array field with the given global_array.
      global_array: array containing accumulating all StructureDefinition
        references.

    Returns:
      A bundle entry representing the IG resource.
    """
    definition = resource.get('definition')
    if definition:
      definition_resources = definition.get('resource')
      if definition_resources:
        final_definition_resources = []
        for definition_resource in definition_resources:
          # Example resources do not actually exist in the IG set; the IG just
          # has references to them that lead nowhere
          if (
              'exampleBoolean' in definition_resource
              and not definition_resource['exampleBoolean']
          ) and 'exampleCanonical' not in definition_resource:
            referenced_resource_identifier = definition_resource['reference'][
                'reference'
            ]
            referenced_resource_uuid = self.resource_id_to_uuid_map[
                referenced_resource_identifier
            ]
            definition_resource['reference'][
                'reference'
            ] = referenced_resource_uuid
            final_definition_resources.append(definition_resource)

        resource['definition']['resource'] = final_definition_resources

    resource_uuid = self.__generate_uuid__(
        'ImplementationGuide', resource['id']
    )
    if do_construct_global_array:
      resource['global'] = global_array

    ig_bundle_entries = {
        'resource': resource,
        'fullUrl': resource_uuid,
        'request': {
            'method': 'POST',
            'url': 'ImplementationGuide',
        },
    }
    return ig_bundle_entries

  def OutputProfileValidationResourceBundle(self, target_dir, bundle):
    """Outputs the given bundle as a JSON in the target_dir.

    Args:
      target_dir: directory into which to write the final bundle JSON.
      bundle: the bundle to write out.
    """
    output_file = os.path.join(target_dir, 'bundle.json')
    with open(output_file, 'w') as f:
      json.dump(bundle, f, indent=2)

  def __generate_uuid__(self, resource_type, resource_id):
    uuid_str = 'urn:uuid:' + str(uuid.uuid4())
    while uuid_str in self.uuid_tracker:
      uuid_str = 'urn:uuid:' + str(uuid.uuid4())
    self.uuid_tracker.add(uuid_str)
    resource_identifier = resource_type + '/' + resource_id
    self.resource_id_to_uuid_map[resource_identifier] = uuid_str
    return uuid_str

  def CreateProfileValidationResourcesBundle(self):
    """Helps create a FHIR transaction bundle from a set of profile validation resources."""
    source_dir, target_dir, do_construct_global_array = self.GetAttributeFlags()
    bundle = self.ProcessProfileValidationResourcesAt(
        source_dir, do_construct_global_array
    )
    self.OutputProfileValidationResourceBundle(target_dir, bundle)


if __name__ == '__main__':
  bundler = FhirProfileValidationResourcesBundler()
  bundler.CreateProfileValidationResourcesBundle()
