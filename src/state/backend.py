def configure_remote_backend(provider: str, bucket: str, region: str = None):
    print(f"Configuring backend for provider: {provider}")
    print(f"Bucket: {bucket}")
    if region:
        print(f"Region: {region}")
