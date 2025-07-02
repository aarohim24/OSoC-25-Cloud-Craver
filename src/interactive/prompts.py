from PyInquirer import prompt

def get_user_inputs():
    questions = [
        {
            'type': 'list',
            'name': 'cloud_provider',
            'message': 'Choose cloud provider:',
            'choices': ['AWS', 'Azure']
        },
        {
            'type': 'input',
            'name': 'region',
            'message': 'Enter cloud region:',
        },
        {
            'type': 'checkbox',
            'name': 'resources',
            'message': 'Select resources to generate:',
            'choices': [{'name': r} for r in ['VPC', 'EC2', 'S3', 'RDS']]
        },
        {
            'type': 'input',
            'name': 'prefix',
            'message': 'Enter project name prefix:',
        },
        {
            'type': 'input',
            'name': 'description',
            'message': 'Enter project description:',
        },
        {
            'type': 'input',
            'name': 'team',
            'message': 'Enter team name:',
        },
        {
            'type': 'list',
            'name': 'environment',
            'message': 'Select environment:',
            'choices': ['Development', 'Staging', 'Production']
        }
    ]
    return prompt(questions)
