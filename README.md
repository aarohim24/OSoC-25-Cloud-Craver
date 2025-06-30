# 🚀 Cloud Craver

> **Accelerating Infrastructure-as-Code Workflows with Python**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Terraform](https://img.shields.io/badge/Terraform-Compatible-purple.svg)](https://terraform.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)](CONTRIBUTING.md)

**Cloud Craver** is a powerful Python-based CLI tool that streamlines Infrastructure-as-Code (IaC) workflows by generating standardized, production-ready Terraform templates. Built with developer experience in mind, it enforces best practices, modular design, and cross-cloud consistency.

## ✨ Key Features

- 🌐 **Multi-Cloud Support** – Generate templates for AWS, Azure, GCP, and custom providers  
- 📁 **Standardized Project Structure** – Enforces separation of concerns with organized file layouts  
- 🎯 **Interactive Configuration** – Smart prompts for regions, resource types, and naming conventions  
- 🔧 **Modular Design** – Reusable modules for databases, networking, and CI/CD pipelines  
- 📚 **Auto-Documentation** – Generates comprehensive READMEs and setup instructions  
- ⚡ **Rapid Prototyping** – Quickly spin up development and testing environments  

## 🏗️ Architecture

```
┌─────────────────────┐
│  User Interface     │  ← CLI with interactive prompts
├─────────────────────┤
│  Business Logic     │  ← Core template processing
├─────────────────────┤
│  Template Engine    │  ← Jinja2-based rendering
├─────────────────────┤
│  Output Manager     │  ← File operations & structure
└─────────────────────┘
```

## 🛠️ Tech Stack

**Core Technologies:**

- **Python 3.8+** – Cross-platform compatibility and rapid development  
- **Terraform** – Infrastructure provisioning and management  
- **Jinja2** – Powerful template rendering engine  

**Key Libraries:**

| Library         | Purpose                        |
|-----------------|--------------------------------|
| Click           | CLI framework                  |
| Rich            | Beautiful terminal output      |
| Dynaconf        | Configuration management       |
| GitPython       | Git integration                |
| PyInquirer      | Interactive prompts            |
| python-dotenv   | Environment variables          |

## 📂 Project Structure

```
cloud-craver/
├── src/                   # Core application code
│   ├── main.py            # CLI entry point
│   ├── generator.py       # Template generation logic
│   ├── templates/         # Terraform templates by provider
│   │   ├── aws/
│   │   ├── azure/
│   │   └── gcp/
│   ├── config/            # Configuration files
│   ├── utils/             # Helper functions
│   └── cli/               # CLI interface components
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
├── examples/              # Example generated projects
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── setup.py               # Package installation
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher  
- Git  
- Terraform (optional, for testing generated templates)  

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cloud-craver.git
cd cloud-craver

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### Basic Usage

```bash
# Generate a new Terraform project
cloud-craver generate

# Generate project for specific cloud provider
cloud-craver generate --provider aws --region us-west-2

# List available templates
cloud-craver list-templates

# Validate generated templates
cloud-craver validate ./generated-project
```

## 🎯 Use Cases

- **Multi-Cloud Infrastructure** – Standardized templates across AWS, Azure, and GCP  
- **CI/CD Pipeline Setup** – Scaffold infrastructure for automated deployments  
- **Team Standardization** – Enforce consistent IaC patterns across teams  
- **Rapid Prototyping** – Set up development environments quickly  
- **Learning & Training** – Learn Terraform and Python templating best practices  

## 🤝 Contributing

We welcome contributions from the community!

### Getting Started

1. Browse [Issues](https://github.com/yourusername/cloud-craver/issues)  
2. Look for tags like `good first issue`  
3. Read the [Contributing Guide](CONTRIBUTING.md)  

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/cloud-craver.git

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting and formatting
flake8 src/ tests/
black src/ tests/
```

### Contribute To:

- 📦 **New Templates**  
- 🧠 **CLI UX Improvements**  
- 📖 **Docs and Tutorials**  
- 🧪 **Unit/Integration Tests**  
- ⚡ **Optimization & Refactoring**  

## 📊 Roadmap

- [ ] **v1.0** – Full AWS, Azure, GCP template support  
- [ ] **v1.1** – Add Docker and Kubernetes scaffolding  
- [ ] **v1.2** – Plugin system for custom providers  
- [ ] **v1.3** – Visual UI to generate projects  
- [ ] **v2.0** – Terraform state & drift detection  

## 📝 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- 🏗️ **HashiCorp** for Terraform  
- 🐍 **Python** community for open-source excellence  
- 🤝 **Contributors** like you who make this possible  

## 📞 Support

- 📚 [Documentation](docs/)  
- 🐛 [Bug Reports](https://github.com/yourusername/cloud-craver/issues)  
- 💬 [Discussions](https://github.com/yourusername/cloud-craver/discussions)  
- 📧 [Email](mailto:support@yourproject.com)  

---

**Built with 💡 by the Cloud Craver Team**  
⭐ _Star this repo if you like it!_