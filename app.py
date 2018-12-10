
from api import *

import yaml
import utils
import time

class Tclient(object):


    def create_container(self,data, blocking=False):
        '''
        :param blocking: blocking API
        :param data: {
            'owner': 'jack.ma',
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
                        'labels': ['GeForce GTX 1080'],
                        'shared': False
                    },
                    'volumes': [
                        '/mnt:/mnt:slave',
                        '/etc/timezone:/etc/timezone:ro',
                        '/etc/localtime:/etc/localtime:ro'
                    ],
                    'image': 'registry.tusimple.ai/dope:lingting',
                    'command': 'echo helloworld',
                    'labels': ['general', 'retired']
                    'hosts': [
                        'super5.sd.tusimple.ai',
                        'super6.sd.tusimple.ai'
                    ],
                    'hostname' = 'octopus3-sliu-0614',
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
        :return: V1Pod, is_success(boolean)
        '''
        task_info = utils.convert_tuyaco_dict_to_task_info(data)
        return self.submit_pod(task_info, blocking)
    
    def kill_container(self, data, blocking=False):
        '''
        data:{
            'owner': 'hua.li',
            'data': {
                'name': 'test',  # container_name 
                'namespace': 'test_namespace'
            }
        }
        '''
        name = data['data']['name']
        namespace = data.get("data").get("namespace") if  data.get("data").get("namespace") else "default"
        return self.delete(name, namespace, blocking)

    def resume_container(self, data, blocking=False):
        task_info = utils.convert_tuyaco_dict_to_task_info(data)
        return resume_pod(task_info, blocking)

    def submit_pod(self, task_info, blocking=False):
        '''
            task_info:
            {
                'data':{} dict data parsed from yaml file
                'owner':'hua.li'
                'namespace':'default'
            }
            task_info['data']:
                {
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
        '''
        return submit_pod(task_info,blocking)

    def delete_pod(self,task_info,blocking=False):
        """
        :param task_info: 
        :return:
        """
        return delete_pod(task_info, blocking)

    def delete(self,name, namespace, blocking=False):
        return delete(name, namespace, blocking=blocking)

    def resume_pod(self, task_info, blocking=False):
        return resume_pod(task_info, blocking)

    def get_pod_info(self, name, namespace):
        return get_pod_info(name, namespace)

    def get_pod_log(self, name, namespace):
        return get_pod_log(name, namespace)
    
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
        return list_node_labels()
    
    def test(self,counts, memorys,shared,task_info,replicas=1):
        test_gpu_name = shared_gpu_name if shared else exclusive_gpu_name
        for i in range(len(counts)):
            resource = {
                    test_gpu_name: str(counts[i]), 
                    gpu_memory_name: '{}Mi'.format(memorys[i]*1024)
            }
            name = "{mode}-c-{count}-m-{memory}".format(mode="shared" if shared else "exclusive", count=counts[i], memory=memorys[i])
            namespace = task_info.get("namespace") if task_info.get("namespace")!=None else "default" 
            utils.set_name(task_info["data"], name)
            utils.set_resources(task_info["data"], resource)
            print("pod " + name)
            print(resource)
            _, result = self.submit_pod(task_info, blocking=True)
            if result==False:
                # Failed to start the deployment, delete the deployment
                self.delete(name, namespace, blocking=True) 
                continue
            pod_status = get_pod_info(name,namespace).status
            phase = pod_status.phase
            container_id = pod_status.container_statuses[0].container_id.split("//")[1]
            r = utils.get_container_GPU(container_id, name)
            print("Pod phase: " + phase)
            print("Pod GPU: " + r)
            self.list_node_allocatable_resources()
            self.list_node_allocated_resources()      
            self.delete(name, namespace,blocking=True)
            
if __name__ == '__main__':
    # tclient = Tclient()
    # task_info = {}
    # namespace = "default"
    # task_info["data"] = utils.pod_template
    # task_info["owner"] = "qiang.kang"
    # task_info["namespace"] = namespace
    # try:     
    #     tclient.create_container(utils.data, blocking=True)
    #     time.sleep(100000)
    # finally:
    #     name = utils.data.get("data").get("config").get("hostname")
    #     data = {
    #         "owner":"qiang.kang",
    #         "data":{
    #             'name':name,
    #             'namespace':"default"
    #         }
    #     }
    #     tclient.kill_container(data, blocking=True)
    
    print(get_node_labels("tusimple"))
    # print("initializing test environment")
    # shared_name = "shared-gpu"
    # resource = {shared_gpu_name: '3'}
    # utils.set_name(task_info,shared_name)
    # utils.set_resource_limits(task_info, resource)
    # print(task_info)
    # tclient.create_deployment(task_info,blocking=True)
    # names = tclient.list_deployment_pod_name(namespace, shared_name)
    # for name in names:
    #     res = tclient.get_pod_info(name, namespace)
    #     print("*"*100)
    #     print(res)
    #     res   = tclient.get_pod_log(name, namespace)
    #     print("*"*100)
    #     print(res)

    # tclient.delete(shared_name, namespace)
    # print(get_node_labels("tusimple"))
    # append_or_update_node_label("tusimple", "foo", "bar1")
    # print(get_node_labels("tusimple"))
    # append_or_update_node_label("tusimple", "foo", "bar2")
    # print(get_node_labels("tusimple"))
    # remove_node_label("tusimple", "foo")
    # print(get_node_labels("tusimple"))
    # remove_node_label("tusimple", "foo")
    # print(get_node_labels("tusimple"))
    # append_or_update_node_label("tusimple", "foo", "bar2")

    # tclient.submit_pod(utils.convert_tuyaco_dict_to_task_info(), True)
    # namespace = "default"
    # image = "tensorflow/tensorflow:latest-gpu"
    # replicas = 1

    # print("initializing test environment")
    # shared_name = "shared-gpu"
    # resource = {shared_gpu_name: '3'}
    # utils.set_name(task_info["data"],shared_name)
    # utils.set_resources(task_info["data"], resource)
    # print(task_info)
    # tclient.submit_pod(task_info,blocking=True)
    # exclusive_name = "exclusive-gpu"
    # resource = {exclusive_gpu_name: '3'}
    # utils.set_name(task_info["data"], exclusive_name)
    # utils.set_resources(task_info["data"], resource)
    # tclient.submit_pod(task_info,blocking=True)
    # try:
    #     print("*"*50+"shared count" +"*"*50)
    #     print("*"*100)
    #     counts = [5,6]
    #     tclient.test(counts, [0]*len(counts), True, task_info)
        
    #     print("*"*50+"exclusive count"  +"*"*50)
    #     print("*"*100)
    #     counts = [2,4,1]
    #     tclient.test(counts, [0]*len(counts), False, task_info)
        
    #     print("*"*50+"shared memory" +"*"*50)
    #     print("*"*100)
    #     counts = [2,2,3,5,5]
    #     memorys = [20,30,30,50,60]
    #     tclient.test(counts, memorys, True,task_info)

    #     print("*"*50+"exclusive memory" +"*"*50)
    #     print("*"*100)
    #     counts = [1,1]
    #     memorys = [10,12]
    #     tclient.test(counts, memorys, False,task_info)
    # finally:
    #     tclient.delete(shared_name, namespace)
    #     tclient.delete(exclusive_name, namespace)

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