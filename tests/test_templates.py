import unittest
from unittest.mock import MagicMock
from src.templates.base import BaseTemplate, TemplateMetadata, AWSTemplate, AzureTemplate, GCPTemplate

class TestTemplateMetadata(unittest.TestCase):
    def test_metadata_creation(self):
        metadata = TemplateMetadata(version="1.0", description="Test template", tags=["test", "example"])
        self.assertEqual(metadata.version, "1.0")
        self.assertEqual(metadata.description, "Test template")
        self.assertEqual(metadata.tags, ["test", "example"])

    def test_metadata_creation_no_tags(self):
        metadata = TemplateMetadata(version="1.0", description="Test template")
        self.assertEqual(metadata.tags, [])

class TestBaseTemplate(unittest.TestCase):
    def setUp(self):
        self.metadata = TemplateMetadata(version="1.0", description="Test template")
        # Create a concrete implementation for testing abstract BaseTemplate methods
        class ConcreteTemplate(BaseTemplate):
            def generate(self) -> str:
                return "Generated Content"

            def validate(self) -> bool:
                return True

            def render(self) -> str:
                return "Rendered Content"
        self.ConcreteTemplate = ConcreteTemplate

    def test_base_template_initialization(self):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata)
        self.assertEqual(template.name, "MyTemplate")
        self.assertEqual(template.metadata.version, "1.0")
        self.assertEqual(template.get_all_variables(), {})
        self.assertIsNone(template.get_output())

    def test_base_template_initialization_with_variables(self):
        initial_vars = {"region": "us-east-1", "env": "dev"}
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata, variables=initial_vars)
        self.assertEqual(template.get_all_variables(), initial_vars)

    def test_set_and_get_variable(self):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata)
        template.set_variable("key1", "value1")
        self.assertEqual(template.get_variable("key1"), "value1")

    def test_get_non_existent_variable(self):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata)
        with self.assertRaises(KeyError):
            template.get_variable("non_existent_key")

    def test_get_all_variables(self):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata)
        template.set_variable("key1", "value1")
        template.set_variable("key2", 123)
        self.assertEqual(template.get_all_variables(), {"key1": "value1", "key2": 123})

    def test_abstract_methods_called(self):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata)
        self.assertEqual(template.generate(), "Generated Content")
        self.assertTrue(template.validate())
        self.assertEqual(template.render(), "Rendered Content")

class TestProviderTemplates(unittest.TestCase):
    def setUp(self):
        self.metadata = TemplateMetadata(version="1.0", description="Provider test template")
        self.variables = {"project": "my-app"}

    def test_aws_template(self):
        aws_template = AWSTemplate(name="MyAWSTemplate", metadata=self.metadata, variables=self.variables)
        self.assertEqual(aws_template.name, "MyAWSTemplate")
        self.assertTrue(aws_template.validate())
        generated_content = aws_template.generate()
        self.assertIn("AWS CloudFormation Template", generated_content)
        self.assertIn("project': 'my-app", generated_content)
        self.assertEqual(aws_template.render(), generated_content)
        self.assertIsNotNone(aws_template.get_output())

    def test_azure_template(self):
        azure_template = AzureTemplate(name="MyAzureTemplate", metadata=self.metadata, variables=self.variables)
        self.assertEqual(azure_template.name, "MyAzureTemplate")
        self.assertTrue(azure_template.validate())
        generated_content = azure_template.generate()
        self.assertIn("Azure ARM Template", generated_content)
        self.assertIn("project': 'my-app", generated_content)
        self.assertEqual(azure_template.render(), generated_content)
        self.assertIsNotNone(azure_template.get_output())

    def test_gcp_template(self):
        gcp_template = GCPTemplate(name="MyGCPTemplate", metadata=self.metadata, variables=self.variables)
        self.assertEqual(gcp_template.name, "MyGCPTemplate")
        self.assertTrue(gcp_template.validate())
        generated_content = gcp_template.generate()
        self.assertIn("GCP Deployment Manager Template", generated_content)
        self.assertIn("project': 'my-app", generated_content)
        self.assertEqual(gcp_template.render(), generated_content)
        self.assertIsNotNone(gcp_template.get_output())

if __name__ == '__main__':
    unittest.main()
