from transformers import pipeline

def generate_template(prompt):
    generator = pipeline("text-generation", model="gpt2")
    result = generator(prompt, max_length=200, truncation=True)[0]['generated_text']
    return result
