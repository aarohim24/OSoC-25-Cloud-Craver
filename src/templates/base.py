import abc
from typing import Any, Dict, List, Optional

class TemplateMetadata:
    """
    Represents metadata for a cloud template.

    Attributes:
        version (str): The version of the template.
        description (str): A brief description of the template.
        tags (List[str]): A list of tags associated with the template.
    """
    def __init__(self, version: str, description: str, tags: Optional[List[str]] = None):
        self.version = version
        self.description = description
        self.tags = tags if tags is not None else []

class BaseTemplate(abc.ABC):
    """
    Abstract base class for cloud template management.

    Defines the interface for template generation, validation, and rendering,
    along with methods for variable handling and output management.
    """

    def __init__(self, name: str, metadata: TemplateMetadata, variables: Optional[Dict[str, Any]] = None):
        """
        Initializes the BaseTemplate with a name, metadata, and optional variables.

        Args:
            name (str): The name of the template.
            metadata (TemplateMetadata): Metadata for the template.
            variables (Optional[Dict[str, Any]]): Initial template variables.
        """
        self.name = name
        self.metadata = metadata
        self._variables = variables if variables is not None else {}
        self._output = None

    @abc.abstractmethod
    def generate(self) -> str:
        """
        Generates the cloud template content.

        This method should be implemented by subclasses to produce the
        provider-specific template (e.g., CloudFormation, ARM, Terraform).

        Returns:
            str: The generated template content as a string.
        """
        pass

    @abc.abstractmethod
    def validate(self) -> bool:
        """
        Validates the generated template content against provider-specific rules.

        Returns:
            bool: True if the template is valid, False otherwise.
        """
        pass

    @abc.abstractmethod
    def render(self) -> str:
        """
        Renders the template, applying variables and producing the final output.

        Returns:
            str: The rendered template content.
        """
        pass

    def set_variable(self, key: str, value: Any) -> None:
        """
        Sets a single variable for the template.

        Args:
            key (str): The name of the variable.
            value (Any): The value of the variable.
        """
        self._variables[key] = value

    def get_variable(self, key: str) -> Any:
        """
        Retrieves the value of a template variable.

        Args:
            key (str): The name of the variable.

        Returns:
            Any: The value of the variable.

        Raises:
            KeyError: If the variable is not found.
        """
        if key not in self._variables:
            raise KeyError(f"Variable '{key}' not found.")
        return self._variables[key]

    def get_all_variables(self) -> Dict[str, Any]:
        """
        Retrieves all variables set for the template.

        Returns:
            Dict[str, Any]: A dictionary of all template variables.
        """
        return self._variables

    def get_output(self) -> Optional[str]:
        """
        Retrieves the last generated or rendered output of the template.

        Returns:
            Optional[str]: The template output, or None if not yet generated/rendered.
        """
        return self._output


class AWSTemplate(BaseTemplate):
    """
    AWS-specific implementation of BaseTemplate for CloudFormation templates.
    """
    def __init__(self, name: str, metadata: TemplateMetadata, variables: Optional[Dict[str, Any]] = None):
        super().__init__(name, metadata, variables)

    def generate(self) -> str:
        # Placeholder for AWS CloudFormation template generation logic
        template_content = f"AWS CloudFormation Template for {self.name}\n"
        template_content += f"Description: {self.metadata.description}\n"
        template_content += f"Variables: {self._variables}\n"
        self._output = template_content
        return template_content

    def validate(self) -> bool:
        # Placeholder for AWS CloudFormation validation logic
        print(f"Validating AWS template {self.name}...")
        return True  # Simulate successful validation

    def render(self) -> str:
        # For CloudFormation, generate might be the primary rendering step
        if not self._output:
            self.generate()
        return self._output


class AzureTemplate(BaseTemplate):
    """
    Azure-specific implementation of BaseTemplate for ARM templates.
    """
    def __init__(self, name: str, metadata: TemplateMetadata, variables: Optional[Dict[str, Any]] = None):
        super().__init__(name, metadata, variables)

    def generate(self) -> str:
        # Placeholder for Azure ARM template generation logic
        template_content = f"Azure ARM Template for {self.name}\n"
        template_content += f"Description: {self.metadata.description}\n"
        template_content += f"Variables: {self._variables}\n"
        self._output = template_content
        return template_content

    def validate(self) -> bool:
        # Placeholder for Azure ARM validation logic
        print(f"Validating Azure template {self.name}...")
        return True  # Simulate successful validation

    def render(self) -> str:
        # For ARM, generate might be the primary rendering step
        if not self._output:
            self.generate()
        return self._output


class GCPTemplate(BaseTemplate):
    """
    GCP-specific implementation of BaseTemplate for Deployment Manager templates.
    """
    def __init__(self, name: str, metadata: TemplateMetadata, variables: Optional[Dict[str, Any]] = None):
        super().__init__(name, metadata, variables)

    def generate(self) -> str:
        # Placeholder for GCP Deployment Manager template generation logic
        template_content = f"GCP Deployment Manager Template for {self.name}\n"
        template_content += f"Description: {self.metadata.description}\n"
        template_content += f"Variables: {self._variables}\n"
        self._output = template_content
        return template_content

    def validate(self) -> bool:
        # Placeholder for GCP Deployment Manager validation logic
        print(f"Validating GCP template {self.name}...")
        return True  # Simulate successful validation

    def render(self) -> str:
        # For Deployment Manager, generate might be the primary rendering step
        if not self._output:
            self.generate()
        return self._output
