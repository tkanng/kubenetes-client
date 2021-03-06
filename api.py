#!/usr/bin/python

from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
import utils
import time
import re


config.load_kube_config()
extensions_v1beta1 = client.ExtensionsV1beta1Api()
core_v1 = client.CoreV1Api()

gpu_name = "nvidia.com/gpu"
gpu_memory_name = "nvidia.com/gpu-memory"
shared_gpu_name = "nvidia.com/shared-gpu"
exclusive_gpu_name = "nvidia.com/exclusive-gpu"
gpu_free_memory_name = "nvidia.com/gpu-free-memory"
shared_gpu_memory_name = "nvidia.com/shared-gpu-memory"
shared_gpu_free_memory_name = "nvidia.com/shared-gpu-free-memory"
memory_name = "memory"
cpu_name = "cpu"
gpu_devices_name = "nvidia.com/gpu-devices"
shared_cpu_name ='tusimple.com/shared-cpu'
exclusive_cpu_name = "tusimple.com/exclusive-cpu"

submit_retry_time = 60

# extensionsV1beta1Api
# Tips: Deployment's pod only included 1 container
# def create_deployment(task_info, blocking=False):
#     '''
#     task_info:
#     {
#         'data':{} dict data parsed from yaml file
#         'owner':'hua.li',
#         'namespace':'default',
#         'timestamp':

#     }

#     task_info['data']:
#     {
#         "kind": "Deployment",
#         "spec": {
#             "selector": {
#             "matchLabels": { 
#                 "app": "tensorflow"  # !!! selector
#             }
#             },
#             "template": {
#             "spec": {
#                 "containers": [
#                 {
#                     "image": "tensorflow/tensorflow:latest-gpu",
#                     "name": "tensorflow-container-name",  
#                     "resources": {
#                     "limits": {
#                         "nvidia.com/shared-gpu": "1",
#                         "nvidia.com/gpu-memory": "1Gi",
#                     }
#                     }
#                 }
#                 ]
#             },
#             "metadata": {
#                 "labels": {
#                 "app": "tensorflow"   # !!! pod label
#                 },
#                 "annotations": {
#                 "shared-gpu-max-toleration": "22"
#                 }
#             }
#             },
#             "replicas": 1
#         },
#         "apiVersion": "extensions/v1beta1",
#         "metadata": {
#             "name": "gpu"   # !!!   deployment's name
#         }
#     }
#     return: api_response, is_success(boolean)
#     '''
#     if utils.check(task_info)==False:
#         return None,False
#     owner = task_info.get("owner")
#     namespace  = task_info.get("namespace")
#     data = task_info.get("data") # dict parsed from yaml 
#     name = data.get("metadata").get("name")
#     replicas = int(data.get("spec").get("replicas"))
#     if get_deployment_info(name, namespace)!=None:
#         print("deployment: namespace:{a}, name:{b} has been running. Please change your deployment name.".format(a=namespace, b=name) )
#         return None,False
#     try: 
#         resp = extensions_v1beta1.create_namespaced_deployment(body=data, namespace=namespace)
#         print("Submit deployment {name},  status: {status}" .format(name=name,status=resp.status))
#     except ApiException as e:
#         print(e)
#         return None, False
    
#     if blocking==False:
#         return resp, True
#     else:
#         # get all pod names of this deployment 
#         pod_names = list_deployment_pod_name(namespace, name)
#         n = 0
#         while len(pod_names)!=replicas and n < 30:
#             time.sleep(2)
#             n +=1
#             pod_names = list_deployment_pod_name(namespace, name)
#         if len(pod_names)!=replicas:
#             print("Failed to submit deployment " + name + " ." + str(len(pod_names)) + " pods have been submitted.")
#             print("Begin to delete the deployment: " + name)
#             delete_deployment(task_info, blocking=True)
#             return resp, False
#         print("Deployment: " + name + " has been submitted successfully!")
#         return resp, True


# def delete_deployment(task_info,blocking=False):
#     '''
#     return: api_response,  is_success(boolean)
#     '''
#     # Delete deployment
#     if utils.check(task_info)==False:
#         return None,False
#     namespace  = task_info.get("namespace")
#     data = task_info.get("data") # dict parsed from yaml 
#     name = data.get("metadata").get("name")
#     return delete(name, namespace,blocking=blocking)

# def delete(name, namespace, blocking=False):
#     print("Deleting deployment " + name)
#     try:
#         api_response = extensions_v1beta1.delete_namespaced_deployment(
#             name = name,
#             namespace = namespace,
#             body=client.V1DeleteOptions(
#                 propagation_policy='Foreground',
#                 grace_period_seconds=3))
#     except ApiException as e:
#         print(e)
#         return None, False
#     if blocking==False:
#         return api_response, True
#     else:
#         while get_deployment_info(name, namespace)!=None:
#             time.sleep(3)
#         print("Delete deployment " + name  + " successfully!")
#         return api_response,True
    
# def resume_deployment(task_info, blocking=False):
#     '''
#     return: api_response, is_success(boolean)
#     '''
#     if utils.check(task_info)==False:
#         return None,False
#     data = task_info.get("data")
#     namespace = task_info.get("namespace")
#     name = data.get("metadata").get("name")
#     if get_deployment_info(name, namespace)==None:
#         return create_deployment(task_info, blocking)
#     else:
#         print("Current deployment {name} is still running. Can not resume the deployment.".format(name))
#         return None,False


# def replace_deployment(task_info):
#     if utils.check(task_info)==False:
#         return None
#     name = task_info.get('data').get('metadata').get('name')
#     namespace = task_info.get('namespace')
#     data = task_info.get("data") # dict parsed from yaml 
#     try:
#         api_response = extensions_v1beta1.replace_namespaced_deployment(name = name, namespace=namespace, body = data)
#         return api_response
#     except ApiException as e:
#         print(e)
#         return None


def submit_pod(task_info, blocking=False):
    '''
    :return: V1Pod, is_success(boolean)
    '''
    namespace = task_info.get("namespace") if  task_info.get("namespace")!=None else "default"
    owner = task_info.get("owner")
    data = task_info.get("data")
    name = data.get("metadata").get("name")
    try:
        resp = core_v1.create_namespaced_pod(namespace, body=data)
    except ApiException as e:
        print(e)
        return None, False
    pod =None
    n=0
    while pod==None or pod.status.phase !="Running":
        pod = get_pod_info(name, namespace)
        time.sleep(2)
        n+=1
        if n > submit_retry_time:
            print("Failed to start pod " + name)
            delete(name, namespace,blocking=True)
            return None, False
    print("Submit pod " + name + " successfully!")
    return resp, True
    
def delete_pod(task_info, blocking=False):
    '''
    :param name: pod's name
    :param namespace: namespace
    :return: V1Status, is_success(boolean)
    '''
    namespace  = task_info.get("namespace") if task_info.get("namespace")!=None else "default"
    data = task_info.get("data") # dict parsed from yaml 
    name = data.get("metadata").get("name")
    return delete(name, namespace,blocking=blocking)

def delete(name, namespace, blocking=False):
    '''
    :param name: pod's name
    :param namespace: namespace
    :return: V1Status, is_success(boolean)
    '''
    print("Deleting pod " + name)
    try:
        api_response = core_v1.delete_namespaced_pod(
            name = name,
            namespace = namespace,
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=3))
    except ApiException as e:
        print(e)
        return None, False
    if blocking==False:
        return api_response, True
    else:
        while get_pod_info(name, namespace)!=None:
            time.sleep(3)
        print("Delete pod " + name  + " successfully!")
        return api_response,True

def resume_pod(task_info, blocking=False):
    '''
    return: v1Pod, is_success(boolean)
    '''
    data = task_info.get("data") 
    namespace = task_info.get("namespace") if task_info.get("namespace")!=None else "default"
    name = data.get("metadata").get("name")
    if get_pod_info(name, namespace)==None:
        return submit_pod(task_info, blocking)
    else:
        print("Current pod {name} is still running. Can not resume the pod.".format(name))
        return None,False

def append_or_update_node_label(node_name, label_k, label_v=None):
    '''
    :param label_v: if label_v==None, ===> label_v = label_k
    :return: api_response or None 
    '''    
    if label_v == None:
        label_v = label_k
    label_k = re.sub(r"\s+", "-", label_k)
    label_v = re.sub(r"\s+", "-", label_v)
    body = {
    "metadata": {
        "labels": {
            label_k: label_v}
        }
    }
    print("Appending or updating node's label: " + label_k  + "=" + label_v )
    try:
        api_response = core_v1.patch_node(node_name, body)
        return api_response
    except ApiException as e:
        print(e)
        return None

def remove_node_label(node_name, label_k):
    '''
    :return: api_response or None 
    '''    
    body = {
    "metadata": {
        "labels": {
            label_k: None}
        }
    }
    print("Deleting node's label: " + label_k)
    try:
        api_response = core_v1.patch_node(node_name, body)
        return api_response
    except ApiException as e:
        print(e)
        return None 

def get_node_labels(node_name):
    '''
    get node's labels
    :return: node's labels dict(str, str)
    {
        u'GeForce-GTX-1080': 'GeForce-GTX-1080',  # to satisfy tuyaco's feature, key equals value
        u'beta.kubernetes.io/os': 'linux', 
        u'label-key': 'label-v', 
        u'kubernetes.io/hostname': 'tusimple', 
        u'node-owner': 'kangqiang', 
        u'foo': 'bar2', 
        u'beta.kubernetes.io/arch': 'amd64'
    }
    '''
    v1_node = get_node_info(node_name)
    if v1_node==None:
        return None
    else:
        metadata = v1_node.metadata
        return metadata.labels

# get functions
def get_node_info(node_name):
    '''
    :return: V1Node or None
    '''
    try:
        api_response = core_v1.read_node(node_name, pretty="true")
        return api_response
    except ApiException as e:
        print(e)
        return None

def get_pod_info(name, namespace):
    '''
    :param name: pod name 
    :return: V1Pod
    '''
    try:
        res = core_v1.read_namespaced_pod(name, namespace)
        return res
    except ApiException as e:
        print(e)
        return None
    
def get_pod_log(name, namespace):
    '''
    :parameter:name, pod name
    :return:str, pod'log
    '''
    try:
        pretty = 'true'
        res = core_v1.read_namespaced_pod_log(name, namespace,pretty=pretty)
        return res
    except ApiException as e:
        print(e)
        return None
    
# Get container tty
def get_container_tty(namespace, pod, container=None):
    command = "kubectl -n {namespace} exec -it {pod}  {contianer} /bin/bash".format(namespace=namespace, pod=pod, container="" if container==None else "-c "+container)
    os.system(command)

# list functions 
def list_node():
    '''
    :return: v1NodeList
    '''
    try:
        api_response = core_v1.list_node()
        return api_response
    except ApiException as e:
        print(e)
        return None

def list_node_allocated_resources():
    '''
    :return: dict(str(node_name), dict(resource_info))
    'nvidia.com/gpu-memory': pods on this node gpu memory request sum
    'current_used_gpu_memory': node 
    {'tusimple': {u'nvidia.com/gpu-memory': 0 , u'nvidia.com/shared-gpu': 3, 'current_shared_physical_gpu': 3, 'current_used_gpu_memory': 0, 'current_exclusive_physical_gpu': 0}}
    '''
    try:
        nodes = core_v1.list_node()
        allocated  = {}
        current_shared_gpu_num = 0
        for item in nodes.items:
            one_allocated={}
            node_name = item.metadata.name
            podList = list_node_pod(node_name)
            for pod in podList.items:
                containers = pod.spec.containers
                for c in containers:
                    resources_limits = c.resources.limits  # type: dict(str, str)
                    if resources_limits is not None:
                        for k in resources_limits:
                            if one_allocated.get(k)!=None:
                                one_allocated[k] = one_allocated[k] + utils.convert_str_to_num(resources_limits[k])
                            else:
                                one_allocated[k] = utils.convert_str_to_num(resources_limits[k])
                            if k==shared_gpu_name and utils.convert_str_to_num(resources_limits[k]) > current_shared_gpu_num:
                                current_shared_gpu_num = utils.convert_str_to_num(resources_limits[k])
            r = item.status.allocatable
            gpu_memory_capacity = utils.convert_str_to_num(r[gpu_memory_name]) if r.get(gpu_memory_name)!=None else 0
            gpu_free_memory = utils.convert_str_to_num(r[gpu_free_memory_name]) if r.get(gpu_free_memory_name)!=None else 0
            # used gpu memory
            current_used_gpu_memory = gpu_memory_capacity - gpu_free_memory
            one_allocated["current_shared_physical_gpu"] = current_shared_gpu_num
            one_allocated["current_exclusive_physical_gpu"] = one_allocated[exclusive_gpu_name] if one_allocated.get(exclusive_gpu_name)!=None else 0
            one_allocated["current_used_gpu_memory"] = current_used_gpu_memory
            allocated[node_name] = one_allocated
        return allocated
    except ApiException as e:
        print(e)
        return None

# return dict{k:node_name, v:dict{}}
def list_node_allocatable_resources():
    '''
    :return: dict(str(node_name), dict(resource_info))
    {'tusimple': {u'ephemeral-storage': 37925506191, u'hugepages-1Gi': 0, u'tusimple.com/shared-cpu': 0, u'nvidia.com/gpu': 8, u'nvidia.com/gpu-memory': 93767860224, u'hugepages-2Mi': 0, u'tusimple.com/exclusive-cpu': 0, u'memory': 236562677760, u'GPU': 8, u'GPUMemory': 93767860224, u'pods': 110, u'cpu': 56}}
    '''
    try:
        nodes = core_v1.list_node()
        allocatable = {}
        delete_key_list = [shared_gpu_name,exclusive_gpu_name,gpu_free_memory_name,shared_gpu_memory_name,shared_gpu_free_memory_name,shared_cpu_name,exclusive_cpu_name,"GPU","GPUMemory"]
        for item in nodes.items:
            r = item.status.allocatable
            for k in delete_key_list:
                if k in r:
                    del r[k]
            for k in r:
               r[k] = utils.convert_str_to_num(r[k])  # Convert quantity str to num 
            # Get GPU device detail
            gpus = item.metadata.annotations.get("GPUs")
            if gpus==None:
                r[gpu_devices_name] = ""
            else:
                r[gpu_devices_name] = gpus
            allocatable[item.metadata.name] = r
        return allocatable
    except ApiException as e:
        print(e)
        return None

def list_node_labels():
    '''
    :return: dict(node_name:string , labels:dict)  or None
    '''
    try:
        nodes = core_v1.list_node()
        labels = {}
        for node in nodes.items:
            metadata = node.metadata
            label = metadata.labels
            labels[metadata.name] = label
        return labels
    except ApiException as e:
        print(e)
        return None

def list_node_names():
    '''
    :return: list(str)
    '''
    try:
        nodes = core_v1.list_node()
        names = []
        for node in nodes.items:
            metadata = node.metadata
            names.append(metadata.name)
        return names
    except ApiException as e:
        print(e)
        return None 

def list_node_pod(node_name):
    '''
    :return: v1PodList or None
    '''
    field_selector = "spec.nodeName="+node_name
    try:
        res = core_v1.list_pod_for_all_namespaces(include_uninitialized=True, field_selector=field_selector)
        return res
    except ApiException as e:
        print(e)
        return None
