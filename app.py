
from api2 import *

import yaml

import time

class Tclient(object):

    def __init__(self, submit_retry_time=5):
        self.submit_retry_time = submit_retry_time


    def create_deployment(self, task_info, blocking=False):
        '''
            task_info:
            {
                'data':{} dict data parsed from yaml file
                'owner':'hua.li'
                'namespace':'default'
            }

            task_info['data']:
            {
                "kind": "Deployment",
                "spec": {
                    "selector": {
                    "matchLabels": { 
                        "app": "tensorflow"  # !!! selector
                    }
                    },
                    "template": {
                    "spec": {
                        "containers": [
                        {
                            "image": "tensorflow/tensorflow:latest-gpu",
                            "name": "tensorflow-container-name",  
                            "resources": {
                            "limits": {
                                "nvidia.com/shared-gpu": "1",
                                "nvidia.com/gpu-memory": "1Gi",
                            }
                            }
                        }
                        ]
                    },
                    "metadata": {
                        "labels": {
                        "app": "tensorflow"   # !!! pod label
                        },
                        "annotations": {
                        "shared-gpu-max-toleration": "22"
                        }
                    }
                    },
                    "replicas": 1
                },
                "apiVersion": "extensions/v1beta1",
                "metadata": {
                    "name": "gpu"   # !!!   deployment's name
                }
            }
        '''
        return create_deployment(task_info,blocking)

    def delete_deployment(self,task_info,blocking=False):
        """
            :param name: deploy_name
            {
                namespace: "default"
                name: "redis"
            }
            :return:
        """
        return delete_deployment(task_info, blocking)
    
    def resume_deployment(self, task_info, blocking=False):
        return resume_deployment(task_info, blocking)


    def get_deployment(self, name, namespace):
        """
            :param name namespace: get one deployment
            :return:
            {
                name: "redis"
                namespace: "default"
            }
        """
        return get_deployment_info(name,namespace)
        

    def list_deployments(self, namespace=None):
        """
            :param namespace: None or string. When None, get_all_deployments_for_all_namespaces
            :return: 
        """
        return list_deployments(namespace=namespace)
        
    def list_node(self):
        return list_node()

    def list_node_pod(self, node_name):
        return list_node_pod(node_name)

    def list_node_allocatable_resources(self):
        print("*"*50 + " node allocatable resources: " + "*"*50)
        resp = list_node_allocatable_resources()
        print(resp)
        return resp
        
    def list_node_allocated_resources(self):
        resp = list_node_allocated_resources()
        print("*"*50 + " node allocated resources: " + "*"*50)
        print(resp)
        return resp

    def list_node_labels(self):
        return  list_node_labels()
    
    def list_deployment_pod(self, namespace, deployment_name):
        return list_deployment_pod(namespace, deployment_name)

    def list_deployment_pod_name(self, namespace, deployment_name):
        return list_deployment_pod_name(namespace, deployment_name)
        

def test(counts, memorys,shared,replicas=1):
    test_gpu_name = shared_gpu_name if shared else exclusive_gpu_name
    for i in range(len(counts)):
        resource = {
            "limits":{
                 test_gpu_name: str(counts[i]), 
                 gpu_memory_name: '{}Mi'.format(memorys[i]*1024),
            }
        }
        name = "{mode}-c-{count}-m-{memory}".format(mode="shared" if shared else "exclusive", count=counts[i], memory=memorys[i])
        _, result = tclient.submit(namespace,name,image,resource,replicas,blocking=True)
        if result==False:
            # Failed to start the deployment, delete the deployment
            tclient.delete(name, namespace, blocking=True) 
            continue
        podNames = tclient.list_deployment_pod_name(namespace,name)
        print("PodNames: " + str(podNames))
        phase = get_pod_info(podNames[0],namespace).status.phase
        print("Pods phase: " + phase)
        time.sleep(15)
        tclient.list_node_allocatable_resources()
        tclient.list_node_allocated_resources()      
        tclient.delete(name, namespace,blocking=True)


if __name__ == '__main__':

    tclient = Tclient()
    namespace = "default"
    image = "tensorflow/tensorflow:latest-gpu"
    replicas = 1
    print("initializing test environment")
    shared_name = "shared-gpu"
    resource = {
        "limits":{
             shared_gpu_name: '3', 
        }
    }

    tclient.submit(namespace,shared_name,image,resource,1, blocking=True)
    exclusive_name = "exclusive-gpu"
    resource = {
        "limits":{
             exclusive_gpu_name: '3',
        }
    }
    tclient.submit(namespace,exclusive_name,image,resource,1,blocking=True)

    try:
        print("*"*50+"shared count" +"*"*50)
        print("*"*100)
        counts = [1,5,6]
        test(counts, [0]*len(counts), True)
        
        print("*"*50+"exclusive count"  +"*"*50)
        print("*"*100)
        counts = [2,4,1]
        test(counts, [0]*len(counts), False)
        
        print("*"*50+"shared memory" +"*"*50)
        print("*"*100)
        counts = [2,2,3,5,5]
        memorys = [20,30,30,50,60]
        test(counts, memorys, True)

        print("*"*50+"exclusive memory" +"*"*50)
        print("*"*100)
        counts = [1,1]
        memorys = [10,12]
        test(counts, memorys, False)
    finally:
        tclient.delete(shared_name, namespace)
        tclient.delete(exclusive_name, namespace)


    # while True:
    #     time.sleep(2)
    #     tclient.list_node_allocatable_resources()
    #     tclient.list_node_allocated_resources()
    # print("Deleting deployment")
    # tclient.delete(deploymentName, namespace)
    # print("*"*100)
    # tclient.submit(namespace,deploymentName,containers[0].get("image"),containers[0].get("resources"),replicas)
    # print("*"*100)
    # tclient.list_deployment_pod(namespace, deploymentName)
    # res = tclient.list_deployment_pod_name(namespace, deploymentName)
    # print(res)
    # res = tclient.list_node_pod('tusimple')
    # print(res)
    # tclient.list_node_allocatable_resources()
    # print("*"*100)
    # tclient.list_node_allocatable_resources()
    # print("*"*100)
    # tclient.list_node_allocated_resources()
    # print("Sleep 30s")
    # time.sleep(30)
    # print("Updating deployment")
    # tclient.update_deployment(namespace, deploymentName, containers[0].get("image"),{},replicas)
    # print("Sleep 30s")
    # time.sleep(30)
    # print("Deleting deployment")
    # tclient.delete(deploymentName, namespace)
    # tclient.list_node()
    # tclient.list_node_metadata_and_status()