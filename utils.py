

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

def check_selector_and_pod_label(task_info):
    try:
        check(task_info)
        return True
    except Exception as e:
        print(e)
        print("Invalid task_info, please check task_info:")
        print(task_info)
        return False
    
def check(task_info):
    data = task_info.get("data") # dict parsed from yaml
    assert data!=None
    metadata = data.get("metadata")
    assert metadata!=None
    name = metadata.get("name") # deployment name !!
    assert name!=None
    deployment_spec = data.get("spec")
    assert deployment_spec !=None
    selector = deployment_spec.get("selector")
    assert selector !=None
    matchLabels = selector.get("matchLabels")
    assert matchLabels!=None
    selector_app = matchLabels.get("app") # !!
    assert selector_app!=None
    pod_metadata = deployment_spec.get("metadata")
    assert pod_metadata !=None
    labels = pod_metadata.get("labels") 
    assert labels!=None
    pod_label_app = labels.get("app") # !!
    assert pod_label_app!=None
    assert pod_label_app==name
    assert selector_app==name 
    assert deployment_spec.get("replicas") !=None