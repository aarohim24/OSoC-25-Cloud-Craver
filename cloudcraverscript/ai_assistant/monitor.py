def generate_monitoring_config(resources):
    config = {}
    for r in resources:
        config[r] = {
            "cpu_alarm": "trigger if CPU > 80% for 5 mins",
            "memory_alarm": "trigger if RAM > 75%"
        }
    return config
