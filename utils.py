

def convert_str_to_num(q_str):
    if q_str.isdigit():
        return int(q_str)
    elif q_str.endswith("m"):
        return float(0.001)*int(q_str[:-1])
    elif q_str.endswith("Ki"):
        return 1024*int(q_str[:-2])
    elif q_str.endswith("K"):
        return 1024*int(q_str[:-1])
    elif q_str.endswith("Mi"):
        return 1024*1024*int(q_str[:-2])
    elif q_str.endswith("M"):
        return 1024*1024*int(q_str[:-1])
    elif q_str.endswith("Gi"):
        return 1024*1024*1024*int(q_str[:-2])
    elif q_str.endswith("G"):
        return 1024*1024*1024*int(q_str[:-1])
    else:
        return 0

def check(task_info):
    try:
        check_selector_and_pod_label(task_info)
        return True
    except Exception as e:
        print(e)
        print("Invalid task_info, please check task_info:")
        print(task_info)
        return False
    
def check_selector_and_pod_label(task_info):
    data = task_info.get("data") # dict parsed from yaml
    metadata = data.get("metadata")
    name = metadata.get("name") # deployment name !!
    deployment_spec = data.get("spec")
    selector = deployment_spec.get("selector")
    matchLabels = selector.get("matchLabels")
    selector_app = matchLabels.get("app") # !!
    pod_metadata = deployment_spec.get("template").get("metadata")
    labels = pod_metadata.get("labels") 
    pod_label_app = labels.get("app") # !!
    if pod_label_app!=name:
        raise ValueError("pod_label_app({a}) doesn't equal deployment's name ({b})".format(a=pod_label_app, b=name))
    if selector_app!=name:
        raise ValueError("selector_app({a}) doesn't equal deployment's name({b})".format(a=pod_label_app, b=name))
    if deployment_spec.get("replicas")==None:
        raise ValueError("deployment's replicas parameter is None")
    
def set_resource_limits(task_info,new_limits):
    data = task_info.get("data")
    containers = data.get("spec").get("template").get("spec").get("containers")
    for c in containers:
        resources = c.get("resources")
        resources["limits"] = new_limits

def set_replicas(task_info, replicas):
    task_info["data"]["spec"]["replicas"] = int(replicas)

def set_name(task_info, new_name):
    if check(task_info)==False:
        return
    data = task_info.get("data") # dict parsed from yaml
    metadata = data.get("metadata")
    deployment_spec = data.get("spec")
    selector = deployment_spec.get("selector")
    matchLabels = selector.get("matchLabels")
    pod_metadata = deployment_spec.get("template").get("metadata")
    labels = pod_metadata.get("labels")
    metadata["name"] = new_name
    matchLabels["app"] = new_name
    labels["app"] = new_name