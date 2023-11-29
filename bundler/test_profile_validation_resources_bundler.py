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

"""Tests for the bundler for FHIR profile validation resources."""

import os
import sys
import unittest
from unittest import mock
from . import profile_validation_resources_bundler


class TestFhirProfileValidationResourcesBundler(unittest.TestCase):
  """Test class for FhirProfileValidationResourcesBundler."""

  def setUp(self):
    super().setUp()
    self.bundler = (
        profile_validation_resources_bundler.FhirProfileValidationResourcesBundler()
    )

  @mock.patch.object(
      sys,
      'argv',
      [
          'profile_validation_resources_bundler.py',
          '--input_dir=/an/absolute/directory/path/to/individual/validation/resources',
          '--output_dir=/an/absolute/directory/path/to/store/output/resource/bundle',
      ],
  )
  @mock.patch.object(os.path, 'exists', return_value=True)
  def test_get_attribute_flags_returns_user_inputs_with_abs_paths_create_global_array(
      self, unused_os_path_mock
  ):
    """Test ensuring that absolute directory path inputs are processed correctly."""
    source_dir, target_dir, do_construct_global_array = (
        self.bundler.GetAttributeFlags()
    )
    self.assertEqual(
        source_dir,
        '/an/absolute/directory/path/to/individual/validation/resources',
        'Expected source_dir to be set to'
        ' /an/absolute/directory/path/to/individual/validation/resources',
    )
    self.assertEqual(
        target_dir,
        '/an/absolute/directory/path/to/store/output/resource/bundle',
        'Expected target_dir to be set to'
        ' /an/absolute/directory/path/to/store/output/resource/bundle',
    )
    self.assertEqual(
        do_construct_global_array,
        True,
        'Expected do_construct_global_array to be set to true',
    )

  @mock.patch.object(
      sys,
      'argv',
      [
          'profile_validation_resources_bundler.py',
          '--input_dir=./a/relavtive/directory/path/to/individual/validation/resources',
          '--output_dir=a/relavate/directory/path/to/store/output/resource/bundle',
          '--no-generate_global_array',
      ],
  )
  @mock.patch.object(os.path, 'exists', return_value=True)
  @mock.patch.object(os, 'getcwd', return_value='/usr/')
  def test_get_attribute_flags_returns_user_inputs_rel_paths_no_global_array(
      self, unused_os_path_mock, unused_os_getcwd_mock
  ):
    """Test ensuring that relative directory paths and the boolean generate global array inputs are processed correctly."""
    source_dir, target_dir, do_construct_global_array = (
        self.bundler.GetAttributeFlags()
    )
    self.assertEqual(
        source_dir,
        '/usr/a/relavtive/directory/path/to/individual/validation/resources',
        'Expected source_dir to be set to'
        ' /usr/a/relavtive/directory/path/to/individual/validation/resources',
    )
    self.assertEqual(
        target_dir,
        '/usr/a/relavate/directory/path/to/store/output/resource/bundle',
        'Expected target_dir to be set to'
        ' /usr/a/relavate/directory/path/to/store/output/resource/bundle',
    )
    self.assertEqual(
        do_construct_global_array,
        False,
        'Expected do_construct_global_array to be set to false',
    )

  def test_process_profile_validation_resource_populates_global_array_with_structuredefinition(
      self,
  ):
    """Test ensuring that references to StructureDefinitions are properly generated should the user want it."""
    resource = {
        'resourceType': 'StructureDefinition',
        'url': (
            'http://www.hl7.org/some/structure/definition/resource/for/patient'
        ),
        'id': 'sd-1',
        'version': '1.0.0',
        'type': 'Patient',
    }
    _, global_array = self.bundler.ProcessProfileValidationResource(
        resource, True, []
    )
    self.assertIn(
        {
            'type': 'Patient',
            'profile': 'http://www.hl7.org/some/structure/definition/resource/for/patient',
        },
        global_array,
        'Given IG global reference not found in the global array',
    )

  def test_process_profile_validation_resource_does_not_populate_global_array_not_structuredefinition(
      self,
  ):
    """Test ensuring that the global array does not include non-StructureDefinition resources."""
    resource = {
        'resourceType': 'ValueSet',
        'url': 'http://www.hl7.org/some/value/set/resource',
        'id': 'vs-1',
        'version': '1.0.0',
    }
    _, global_array = self.bundler.ProcessProfileValidationResource(
        resource, True, []
    )
    self.assertEqual(global_array, [], 'Expected global array to be empty!')

  def test_process_profile_validation_resource_generates_and_assigns_fullurl(
      self,
  ):
    """Test ensuring UUIDs are generated and populated in the fullUrl field of each resource bundle entry."""
    resource = {
        'resourceType': 'ValueSet',
        'url': 'http://www.hl7.org/some/value/set/resource',
        'id': 'vs-1',
        'version': '1.0.0',
    }
    bundle_entry, _ = self.bundler.ProcessProfileValidationResource(
        resource, True, []
    )
    resource_uuid = bundle_entry['fullUrl']
    # Entry should be assigned a UUID that's also cached to be inserted as a
    # reference in the ImplementationGuide resource
    self.assertEqual(
        self.bundler.resource_id_to_uuid_map['ValueSet/vs-1'],
        resource_uuid,
        'Expected the appropriate fullUrl to have been assigned to the bundle'
        ' entry',
    )

  def test_process_implementation_guide_resource_should_include_global_array_if_flag_on(
      self,
  ):
    """Test ensuring that a generated global array is inserted into the IG resource should the user signaled for it."""
    resource = {
        'resourceType': 'ImplementationGuide',
        'url': 'http://www.hl7.org/some/implementation/guide/resource',
        'id': 'ig-1',
        'version': '1.0.0',
    }
    profile = {
        'profile': 'http://www.hl7.org/some/structured/definition/for/patients',
        'type': 'Patient',
    }
    bundle_entry = self.bundler.ProcessImplementationGuideResource(
        resource, True, [profile]
    )
    bundled_guide = bundle_entry['resource']
    self.assertEqual(
        bundled_guide['global'],
        [profile],
        'Expected global array to be populated!',
    )

  def test_process_implementation_guide_resource_should_not_include_global_array_if_flag_off(
      self,
  ):
    """Test ensuring that the global array is not inserted into the IG resource should the generate_global_array setting be false."""
    resource = {
        'resourceType': 'ImplementationGuide',
        'url': 'http://www.hl7.org/some/implementation/guide/resource',
        'id': 'ig-1',
        'version': '1.0.0',
    }
    profile = {
        'profile': 'http://www.hl7.org/some/structured/definition/for/patients',
        'type': 'Patient',
    }
    bundle_entry = self.bundler.ProcessImplementationGuideResource(
        resource, False, [profile]
    )
    bundled_guide = bundle_entry['resource']
    self.assertEqual(
        bundled_guide.get('global', []),
        [],
        'Expected global array to be empty!',
    )

  def test_process_implementation_guide_resource_updates_resource_references_in_definitions(
      self,
  ):
    """Test ensuring resource references in IG definitions are replaced with the correct UUIDs."""
    guide_resource = {
        'resourceType': 'ImplementationGuide',
        'url': 'http://www.hl7.org/some/implementation/guide/resource',
        'id': 'ig-1',
        'version': '1.0.0',
        'definition': {
            'resource': [{
                'reference': {'reference': 'Patient/1'},
                'exampleBoolean': False,
            }]
        },
    }
    patient_resource = {
        'resourceType': 'Patient',
        'url': 'http://www.hl7.org/some/structured/definition/for/patients',
        'id': '1',
        'version': '1.0.0',
    }
    # Generates and caches the fullUrl for the patient
    self.bundler.ProcessProfileValidationResource(patient_resource, False, [])
    bundle_entry = self.bundler.ProcessImplementationGuideResource(
        guide_resource, False, []
    )
    bundled_guide = bundle_entry['resource']
    definition_resource_reference = bundled_guide['definition']['resource'][0][
        'reference'
    ]['reference']
    self.assertNotEqual(
        definition_resource_reference,
        'Patient/1',
        'Expected definition resource reference to have been reassigned!',
    )

  def test_process_implementation_guide_resource_should_skip_example_definition_resources(
      self,
  ):
    """Test ensuring example definitions should not be included in the final IG."""
    guide_resource = {
        'resourceType': 'ImplementationGuide',
        'url': 'http://www.hl7.org/some/implementation/guide/resource',
        'id': 'ig-1',
        'version': '1.0.0',
        'definition': {
            'resource': [{
                'reference': {'reference': 'Patient/1'},
                'exampleBoolean': True,
            }]
        },
    }
    bundle_entry = self.bundler.ProcessImplementationGuideResource(
        guide_resource, False, []
    )
    bundled_guide = bundle_entry['resource']
    definition_resources = bundled_guide['definition']['resource']
    self.assertEqual(
        definition_resources, [], 'Expected definition resources to be empty!'
    )


if __name__ == '__main__':
  unittest.main()
