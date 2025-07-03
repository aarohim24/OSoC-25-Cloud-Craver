def recommend_resource_sizes(usage_metrics):
    recs = []
    for res_id, metrics in usage_metrics.items():
        if metrics['cpu'] > 70:
            recs.append(f"Resource {res_id} is overutilized. Recommend a larger instance.")
    return recs

def recommend_cost_saving(current_resources):
    recs = []
    for res_id, info in current_resources.items():
        if info.get('uptime', 0) < 10:
            recs.append(f"{res_id} has low uptime. Consider using spot instances.")
    return recs

def recommend_scaling(traffic_data):
    if max(traffic_data) > 80:
        return "Enable predictive auto-scaling for spikes."
    return "No predictive scaling needed currently."
