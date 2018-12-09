import copy

import yaml
import commands
import json
import re
task_info_example =  {
    "kind": "Deployment", 
    "spec": {
        "selector": {
            "matchLabels": {
                "app": "tensorflow"
            }
        }, 
        "template": {
            "spec": {
                "containers": [
                    {
                        "image": "tensorflow/tensorflow:latest-gpu", 
                        "nodeSelector": {
                            "disktype": "ssd"
                        }, 
                        "name": "shared-gp111", 
                        "resources": {
                            "limits": {
                                "nvidia.com/shared-gpu": 3, 
                                "nvidia.com/gpu-memory": "0Mi"
                            }
                        }, 
                        "env": [
                            {
                                "name": "GREETING", 
                                "value": "Warm greetings to"
                            }, 
                            {
                                "name": "HONORIFIC", 
                                "value": "The Most Honorable"
                            }, 
                            {
                                "name": "NAME", 
                                "value": "Kubernetes"
                            }
                        ]
                    }
                ]
            }, 
            "metadata": {
                "labels": {
                    "app": "tensorflow"
                }
            }
        }, 
        "replicas": 1
    }, 
    "apiVersion": "extensions/v1beta1", 
    "metadata": {
        "name": "tensorflow"
    }
}

pod_template = {
    "kind": "Pod", 
    "spec": {
        "containers": [
            {
                "name": "tensorflow", 
                "env": [
                    
                ], 
                "image": "tensorflow/tensorflow:latest-gpu", 
                "volumeMounts": [
                 
                ], 
                "resources": {
                    "limits": {
                    }
                }
            }
        ], 
        "volumes": [
           
        ], 
        "nodeSelector": {
            
        }
    }, 
    "apiVersion": "v1", 
    "metadata": {
        "name": "shared-pod"
    }
}

def get_container_GPU(contianer_id, pod_name):
    return_code, output = commands.getstatusoutput('docker inspect {} | grep NVIDIA_VISIBLE_DEVICES'.format(contianer_id))
    r = pod_name + "\n" + output
    return  r
    
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
    
# def set_resource_limits(task_info,new_limits):
#     data = task_info.get("data")
#     containers = data.get("spec").get("template").get("spec").get("containers")
#     for c in containers:
#         resources = c.get("resources")
#         resources["limits"] = new_limits

# def set_replicas(task_info, replicas):
#     task_info["data"]["spec"]["replicas"] = int(replicas)



def set_name(pod_dict, new_name):
    metadata=pod_dict["metadata"]
    metadata["name"] = new_name
    containers = pod_dict.get("spec").get("containers")
    for i in range(len(containers)):
        containers[i]["name"] = new_name + "-" +str(i)

def set_image(pod_dict, new_image):
    containers = pod_dict.get("spec").get("containers")
    for c in containers:
        c["image"] = new_image

def set_command(pod_dict, command):
    '''
    command: string
    '''
    containers = pod_dict.get("spec").get("containers")
    if command ==None or command.strip()=="":
        return
    else:
        for c in containers:
            c["command"] = ["/bin/sh", "-c", command]

def set_resources(pod_dict, limits):
    '''
    :limits: dict
    {
        "cpu":"1",
        "nvidia.com/gpu":"2",
    }
    '''
    containers = pod_dict.get("spec").get("containers")
    for c in containers:
        c["resources"]["limits"] = limits


def set_volumes(pod_dict, volumes):
    if volumes ==None or len(volumes) ==0:
        return
    hostPaths = []
    containerPaths = []
    readOnly = []
    for v in volumes:
        vs = v.split(":")
        if len(vs)<2:
            continue
        hostPaths.append(vs[0])
        containerPaths.append(vs[1])
        if len(vs)==2:
            readOnly.append(False)
        elif vs[2] =="ro":
            readOnly.append(True)
        else:
            readOnly.append(False)
    pod_volumes = []
    containers_volumeMounts = []
    for i in range(len(hostPaths)):
        vol_name = "vol" + str(i)
        pod_volumes.append(
            {
                "hostPath": {
                    "path": hostPaths[i]
                }, 
                "name": vol_name
            }
        )
        containers_volumeMounts.append(
           {
                "readOnly": readOnly[i], 
                "mountPath": containerPaths[i], 
                "name": vol_name
            }
        )
    pod_dict["spec"]["volumes"] = pod_volumes
    containers = pod_dict.get("spec").get("containers")
    for c in containers:
        c["volumeMounts"] = containers_volumeMounts

def set_envs(pod_dict, envs):
    if envs==None:
        return
    Envs = []
    for env in envs:
        Envs.append({"name":env.split("=")[0], "value":env.split("=")[1]})
    containers = pod_dict.get("spec").get("containers")
    for c in containers:
        c["env"] =  Envs

def set_node_selector(pod_dict, node_selector):
    '''
    node_selector: dict{}
    '''
    if node_selector==None:
        return
    pod_dict["spec"]["nodeSelector"] = node_selector


def convert_tuyaco_dict_to_task_info():
    data={
        'owner': 'jack.ma',
        'namespace':'default',
        'data': {
            'config': {
                'cpu': {
                    'count': 8,
                    'shared': True
                },
                'mem': {
                    'amount': 8192,
                    'shared': True
                },
                'gpu': {
                    'count': 4,
                    'mem': 4096,
                    'labels': ['GeForce GTX 1080'],  # labels
                    'shared': False
                },
                'volumes': [
                    "/home/tusimple/my_k8s/k8s-client/kuyaco:/notebooks:ro"
                ],
                'image': 'tensorflow/tensorflow:latest-gpu',
                'labels': [],     
                'hosts': [
                    "tusimple"
                ],
                'hostname':'octopus3-sliu-0614',
                'allocate_ip': True,
                'environments': [
                    'NAME=VALUE'
                ],
                'shm_size': '8G',
                'ipc_mode': 'host',
                'waiting': False,
                'reschedule': 0
            },
        }
    }

    configs = data["data"]["config"]
    cpu = configs.get("cpu")
    mem = configs.get("mem")
    gpu = configs.get("gpu")
    volumes = configs.get("volumes")
    image = configs.get("image")  
    command = configs.get("command")
    labels = configs.get("labels") if configs.get("labels")!=None else [] # ==> k8s node_selector + gpu label
    hosts = configs.get("hosts")  # node_selector ===> "kubernetes.io/hostname=gke-x1"
    name = configs.get("hostname")
    environment = configs.get("environments") # []

    # gpu data structure has gpu's label
    # 'required': ['cpu', 'mem', 'image', 'hostname', 'allocate_ip']
    # hostname is deployment name
    pod_dict = copy.deepcopy(pod_template)

    set_name(pod_dict, name)
    set_image(pod_dict,image)
    set_command(pod_dict, command)
    limits = {}
    if cpu!=None:
        limits["cpu"] = str(cpu.get("count") if cpu.get("count") > 0 else 0)
    if mem!=None:
        limits["memory"] = str(mem.get("amount") if mem.get("amount") >0  else 0) + "Mi"
    if gpu!=None:
        if gpu.get("shared"):
            limits["nvidia.com/shared-gpu"] = str(gpu.get("count") if gpu.get("count") >0 else 0)
        else:
            limits["nvidia.com/exclusive-gpu"] = str(gpu.get("count") if gpu.get("count") >0 else 0)
        limits["nvidia.com/gpu-memory"] = str(gpu.get("mem") if gpu.get("mem") >0  else 0) + "Mi"
        if gpu.get("labels"):
            # node's gpu labels 
            labels = labels + gpu.get("labels")

    set_resources(pod_dict, limits)
    set_volumes(pod_dict, volumes)
    set_envs(pod_dict, environment)
    node_selector = {}

    for label in labels:
        # replace all blank character with '-'
        k = re.sub(r"\s+", "-", label)
        node_selector[k]=k
    if hosts!=None and len(hosts) >0:
        node_selector ["kubernetes.io/hostname"] = hosts[0]
    set_node_selector(pod_dict, node_selector)

    task_info = {}
    task_info["data"] = pod_dict
    task_info["owner"] = data["owner"]
    task_info["namespace"] =data.get("namespace")
    task_info["allocate_ip"] = configs.get("allocate_ip")
    task_info["shm_size"] = configs.get("shm_size")
    task_info["ipc_mode"] = configs.get("ipc_mode")
    task_info["protective"] = configs.get("protective")
    task_info["tmpfs"] = configs.get("tmpfs")
    task_info["waiting"] = configs.get("waiting")
    task_info["reschedule"] = configs.get("reschedule")
    task_info["push_after_finish"] = configs.get("push_after_finish")
    return task_info


# a = convert_tuyaco_dict_to_task_info()
# print(a["data"])
# print(pod_template)