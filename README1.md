
# DevOps Lab – RKE, ArgoCD, MongoDB Deployment

This document describes the steps required to deploy and configure a Kubernetes environment using RKE, Helm, ArgoCD, and MongoDB, along with a simple web application. Follow the instructions below to complete the lab.

---

## Phase 1: Create Kubernetes Cluster

### Prerequisites
1. **Machines Setup**:
   - 1 control plane node
   - 2 worker nodes
   - 1 additional Linux machine to act as a management and storage machine.
2. **Tools Installed**:
   - `rke` (1.2+ only on the management)
   - `kubectl`(1.25+ only on the management)
   - `helm`(3+ only on the menagement)
   - `docker`(Please verify that the Docker version is compatible with the others and install it on all the machines.)
   - SSH access between the management machine and cluster nodes.


---


### Setting Up SSH Access Between the Management and Cluster Nodes

To manage your Kubernetes cluster nodes remotely, you need to establish secure SSH access between the management machine and the cluster nodes. Follow the steps below to configure SSH access:

---

#### 1. **Install and generate SSH Keys on the Management Machine**
Run the following command on the management machine to install ssh:
```
sudo apt install update
```
```
sudo apt install openssh-server
```
Run the following command on the management machine to generate a new SSH key pair:
```
ssh-keygen -t rsa
```

- You will be prompted to specify a file to save the key. Press `Enter` to use the default location (`~/.ssh/id_rsa`).
- Set a passphrase (optional) or press `Enter` to skip.
- Two files will be created:
  - **Private Key**: `~/.ssh/id_rsa` (keep this secure).
  - **Public Key**: `~/.ssh/id_rsa.pub`.

---

#### 2. **Copy the Public Key to Each Cluster Node**
Run the following command to copy the public key to each cluster node:
```
ssh-copy-id <ssh-user>@<node-ip>
```

- Replace `<ssh-user>` with the username you will use to access the node (e.g., `root`, `ubuntu`, `ec2-user`, etc.).
- Replace `<node-ip>` with the IP address of the cluster node.

Run the following command to check the ip address:
```
ip a
```
---

#### 3. **Test SSH Access**
After copying the public key to the nodes, test SSH access from the management machine:
```
ssh <ssh-user>@<node-ip>
```

If successful, you should log in without being prompted for a password.

---

#### 4. **Ensure Firewall Rules Allow SSH**
Make sure the firewall on the nodes allows incoming SSH connections on port `22`. For example, on an Ubuntu node, you can check and update the rules using:
```
sudo ufw allow 22/tcp
sudo ufw enable
```

---

Once these steps are completed, the management machine will have secure SSH access to all cluster nodes, enabling smooth deployment and management of your Kubernetes cluster.
+++

### Deployment Steps

1. **RKE Configuration**:
   - Create an `cluster.yml` file:
### Cluster Nodes

```
nodes:
  - address: <controlplane-node-ip>
    user: <ssh-user>
    role:
      - controlplane
      - etcd
    ssh_key_path: <ssh-key-path>
    docker_socket: /var/run/docker.sock
  - address: <controlplane-node-ip>
    user: <ssh-user>
    role:
      - worker
    ssh_key_path: <ssh-key-path>
    docker_socket: /var/run/docker.sock
  - address: <controlplane-node-ip>
    user: <ssh-user>
    role:
      - worker
    ssh_key_path: <ssh-key-path>
    docker_socket: /var/run/docker.sock

# Name of the K8s Cluster
cluster_name: yuval-cluster

services:
  kube-api:
# IP range for any services created on Kubernetes
# This must match the service-cluster-ip-range in kube-controller
    service_cluster_ip_range: 172.16.0.0/16
# Expose a different port range for NodePort services
    service_node_port_range: 30000-32767
    pod_security_policy: false

  kube-controller:
# CIDR pool used to assign IP addresses to pods in the cluster
    cluster_cidr: 172.15.0.0/16
# IP range for any services created on Kubernetes
# This must match the service-cluster-ip-range in kube-api
    service_cluster_ip_range: 172.16.0.0/16

  kubelet:
# Base domain for the cluster
    cluster_domain: cluster.local
# IP address for the DNS service endpoint
    cluster_dns_server: 172.16.0.10
# Fail if swap is on
    fail_swap_on: false

network:
  plugin: calico

# Specify DNS provider (coredns or kube-dns)
dns:
  provider: coredns

# Kubernetes Authorization mode
# Enable RBAC
authorization:
  mode: rbac

# Specify monitoring provider (metrics-server)
monitoring:
  provider: metrics-server
```

2. **Deploy the Cluster**:
   - Run the RKE command:
     ```
     rke up --config cluster.yml
     ```

3. **Verify Node Status**:
   - Copy the generated `kube_config_cluster.yml` to the management machine.
   - Use `kubectl` to verify nodes:
     ```
     export KUBECONFIG=kube_config_cluster.yml
     kubectl get nodes
     ```
   - If the nodes are not showing as 'Ready' status, please restart the machine.

---

## Phase 2: Deploying Applications and Tools


### Step 1: Deploy Ingress Controller

1. Create a namespace ingress-nginx:
    ```
    kubectl create namespace ingress-nginx
    ```

2. witch to a the namespace:
    ```
    kubectl config set-context --current --namespace=ingress-nginx
    ```

3. check the current namespace:
    ```
    kubectl config view --minify --output 'jsonpath={..namespace}'
    ```

4. Add the Nginx Ingress Helm repository:
   ```
   helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
   helm repo update
   ```

5. Install the Nginx Ingress:
   ```
   helm install nginx-ingress ingress-nginx/ingress-nginx
   ```

6. Verify the installation:
   ```
   kubectl get pods -n ingress-nginx
   ```

---

### Step 2: Deploy Dynamic Storage Provisioner

### NFS Server and NFS Client Provisioner Setup Guide

This guide outlines the steps for installing and configuring an NFS Server and an NFS Client Provisioner in a Kubernetes cluster.

---

### Installing the NFS Server

1. **Update the System and Install NFS Server Packages**:
    ```bash
    sudo apt-get update
    sudo apt-get install nfs-common nfs-kernel-server -y
    ```

2. **Create a Directory to Export**:
    ```bash
    sudo mkdir -p /data/nfs
    sudo chown nobody:nogroup /data/nfs
    sudo chmod 2770 /data/nfs
    ```

3. **Export Directory and Restart the NFS Service**:
    ```bash
    echo -e "/data/nfs\t172.15.0.0/16(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

    sudo exportfs -av
    sudo systemctl restart nfs-kernel-server
    sudo systemctl status nfs-kernel-server
    ```

4. **Verify NFS Exports**:
    ```bash
    /sbin/showmount -e <your-ip-address>
    ```

---

### Install NFS Client Packages on Kubernetes Nodes

Ensure all Kubernetes nodes have the NFS client packages installed.

1. **Install NFS Client Packages**:
    ```bash
    sudo apt update
    sudo apt install nfs-common -y
    ```

2. Create a namespace apps:
    ```
    kubectl create namespace apps
    ```

3. witch to a the namespace:
    ```
    kubectl config set-context --current --namespace=apps
    ```

4. check the current namespace:
    ```
    kubectl config view --minify --output 'jsonpath={..namespace}'
    ```
---

### Install and Configure NFS Client Provisioner

The NFS Subdir External Provisioner automates the creation and management of Persistent Volumes (PVs) and Persistent Volume Claims (PVCs).

5. **Install Helm on Debian/Ubuntu**:
    ```bash
    curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
    sudo apt-get install apt-transport-https --yes
    echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
    sudo apt-get update
    sudo apt-get install helm
    ```

6. **Add Helm Repository for NFS Subdir External Provisioner**:
    ```bash
    helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner
    ```

7. **Install Helm Chart for NFS**:
    Replace `<your-ip-address>` with the IP address of your NFS server.
    ```bash
    helm install nfs-subdir-external-provisioner \
    nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
    --set nfs.server=<your-ip-address> \
    --set nfs.path=/data/nfs \
    --set storageClass.onDelete=true
    ```

8. **Create a `nfs-pvc.yaml` File**:
    ```yaml
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: nfs-pvc
    spec:
      accessModes:
        - ReadWriteOnce
      storageClassName: nfs-client
      resources:
        requests:
          storage: 1Gi
    ```

9. **Apply the PVC Configuration**:
    ```bash
    kubectl apply -f nfs-pvc.yaml
    ```

10. **Verify the PVC Creation**:
    Use the following command to view the status of the PVC:
    ```bash
    kubectl get pvc
    ```

---

**Note**: Adjust configurations and IP addresses as needed to fit your setup.
**Note**: The Persistent Volume (PV) will only be dynamically created once an application pod (e.g., a Deployment) that uses the PVC is deployed. Until then, you can observe the PVC in the `kubectl get pvc` output.

### This concludes the NFS Server and NFS Client Provisioner setup and testing. Adjust configurations as needed for your environment.
---


### Step 3 MetalLB Installation and Configuration Guide

This guide explains how to install and configure MetalLB in Kubernetes for providing a Load Balancer solution in environments that lack native cloud load balancer integrations.

---

#### Prerequisites

- A running Kubernetes cluster.
- `kubectl` installed and configured to interact with your cluster.

---

### Install MetalLB

1. **Apply the MetalLB Manifests**:
    ```bash
    kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.9/config/manifests/metallb-native.yaml
    ```

2. **Verify MetalLB Pods**:
    Check that the pods in the `metallb-system` namespace are running.
    ```bash
    kubectl get pods -n metallb-system
    ```

3. **Verify MetalLB API Resources**:
    Ensure that MetalLB resources are available:
    ```bash
    kubectl api-resources | grep metallb
    ```


---

### Configure IP Address Pool

1. **Create the MetalLB Configuration File**:
    Create a file named `metallb-config.yaml`:
    ```yaml
    apiVersion: metallb.io/v1beta1
    kind: IPAddressPool
    metadata:
      name: my-ip-pool
      namespace: metallb-system
    spec:
      addresses:
      - <your-external-ip-range>
    ```

2. **Apply the IP Address Pool Configuration**:
    ```bash
    kubectl apply -f metallb-config.yaml
    ```

3. **Verify the IP Address Pool**:
    Check that the IPAddressPool resource has been created:
    ```bash
    kubectl get IPAddressPool
    ```

---

### Configure L2 Advertisement

1. **Create the L2Advertisement Configuration File**:
    Create a file named `L2Advertisement.yaml`:
    ```yaml
    apiVersion: metallb.io/v1beta1
    kind: L2Advertisement
    metadata:
      name: my-l2-advertisement
      namespace: metallb-system
    spec:
      ipAddressPools:
        - my-ip-pool
    ```

2. **Apply the L2 Advertisement Configuration**:
    ```bash
    kubectl apply -f L2Advertisement.yaml
    ```

3. **Verify the L2 Advertisement**:
    Ensure the L2Advertisement resource has been created:
    ```bash
    kubectl get L2Advertisement
    ```

---

### Summary

After completing these steps:
1. MetalLB is installed in your Kubernetes cluster.
2. An IP Address Pool <your-external-ip-range> is configured.
3. Layer 2 advertisement is enabled, allowing MetalLB to assign IP addresses from the pool to services of type `LoadBalancer`.

You can now create services of type `LoadBalancer` and observe that IP addresses from the configured pool are allocated.


### Step 4: Deploy Application

1. **Write the Application**:
   Create a simple Python app (`app.app`):
   ```python

    from flask import Flask, send_from_directory
    import os

    app = Flask(__name__)

    IMAGE_PATH = "/data/nfs/"

    @app.route('/')
    def home():
        return '<h1 style="color:green;">Task Complete</h1>'

    @app.route('/image')
    def image():
        return send_from_directory(IMAGE_PATH, 'image.jpg')

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)
   ```

2. **Prepare Docker Container**:
   Create a `Dockerfile`:
   ```
    FROM python:3.9-slim

    WORKDIR /app

    COPY app.py /app/app.py

    COPY requirements.txt /app/requirements.txt

    RUN pip install --no-cache-dir -r requirements.txt

    EXPOSE 5000

    CMD ["python", "app.py"]
   ```

3. **Push the Container to a Registry**:
   ```
    create dockerhub account if you don't have one.
    docker build -t <your-dockerhub-user>/python-app:latest .
    docker login 
    docker push <your-dockerhub-user>/python-app:latest
   ```

4. **requirements.txt**:
   - Create a requirements.txt:
     ```
        flask
     ```


**Note**: The requirements.txt file lists a project's Python dependencies, which can be installed using pip install -r requirements.txt.



5.  - Create a Deployment.yaml:
     ```
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: python-app
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: python-app
      template:
        metadata:
          labels:
            app: python-app
        spec:
          containers:
            - name: python-app
              image: <your-dockerhub-user>/python-app:latest
              volumeMounts:
                - name: nfs-storage
                  mountPath: /data/nfs/
          volumes:
            - name: nfs-storage
              persistentVolumeClaim:
                claimName: nfs-pvc
                              
     ```

6.   - Create a service.yaml:

```
    apiVersion: v1 
    # API version
    kind: Service 
    # Resource type
    metadata:
      name: python-app-service 
        # Service name
      namespace: apps  
        # Namespace
    spec:
      selector:
        app: python-app  
        # Pod label selector
      ports:
        - protocol: TCP  
          port: 80  
            # Exposed port
          targetPort: 5000  
            # Container port
      type: LoadBalancer  
        # Expose via load balancer (Metallb)
    ```

7. **Apply the service.yaml Configuration**:
    ```bash
    kubectl apply -f service.yaml
    ```

8. **Apply the deployment.yaml**:
    ```bash
    kubectl apply -f deployment.yaml
    ```

### Step 5 Download and Configure an Image in NFS PV Directory:

This guide explains how to download an image file, rename it, and copy it to the NFS Persistent Volume (PV) directory.

---

**Navigate to the NFS Directory**
Verify that the Persistent Volume (PV) is created using the following command:
```
kubectl get pv
```
Switch to the NFS directory where the Persistent Volume (PV) is mounted:

```bash
cd /data/nfs
```

---

**Download the Image**

Use `wget` to download the image file(use can choose other links):

```bash
sudo wget https://thumbs.dreamstime.com/z/complete-stamp-icon-sign-stock-complete-stamp-icon-sign-161618814.jpg?ct=jpeg
```

---

**Rename the Image File**

The downloaded file contains special characters (`?ct=jpeg`). Rename it to `image.jpg`:

```bash
mv complete-stamp-icon-sign-stock-complete-stamp-icon-sign-161618814.jpg\?ct\=jpeg image.jpg
```

---

**Copy the Image to the PV Directory**
Check the directory of the Persistent Volume (PV) created by the following command:
```
ls
```

Copy the renamed image file to the directory of the Persistent Volume (PV) that was created.

```bash
cp image.jpg <the directory that was created>
```


---

### Summary

- The image file was downloaded and renamed to `image.jpg`.
- The file was copied to the NFS Persistent Volume directory .

You can now use this file within applications that utilize the NFS-mounted Persistent Volume. 



### Accessing the Application and Image

After completing all the setup steps, you can now access your application and the image stored in the NFS Persistent Volume.

---

**Check the External IP**

1. Use the following command to retrieve the `External IP` of your service:
    ```bash
    kubectl get svc
    ```

2. Note the `External IP` assigned to your application.

---

### Open the Application in a Browser

1. Open your browser.
2. Navigate to:
    ```
    http://<External-IP>/
    ```
    or to
    ```
    http://<External-IP>/image
    ```
    Replace `<External-IP>` with the IP retrieved in the previous step.

---

### Expected Result

- The application will load in your browser.
- The image stored in the NFS Persistent Volume will be displayed.

**Congratulations!** The setup is complete, and your application is successfully serving the image from the NFS PV.


### Step 5: Deploy ArgoCD


1. Create a namespace argocd:
    ```
    kubectl create namespace arogcd
    ```

2. witch to a the namespace:
    ```
    kubectl config set-context --current --namespace=argocd
    ```

3. check the current namespace:
    ```
    kubectl config view --minify --output 'jsonpath={..namespace}'
    ```
4. Add the ArgoCD Helm repository:
   ```
   helm repo add argo https://argoproj.github.io/argo-helm
   helm repo update
   ```

5. Install ArgoCD:
   ```
   helm install argocd argo/argo-cd --namespace argocd --create-namespace
   ```

6. Expose ArgoCD via Metallb (change the argocd-server type to LoadBalancer):
    ```
    kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
    ```

7.  Verify that the argocd-server has an external IP:
    ```
    kubectl get svc    
    ```

8. check the argocd password:
    ```
    kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
    ```

9. open a web browser and execute the following commands:
    ```
    Connect to http://<argocd-server-external-ip>
    ```
10. connect to the argocd web browser:
    ```
    insert   username=admin    and    password = from the output of the password command
    ```

11. **To deploy MongoDB using ArgoCD, please refer to the link and follow the instructions provided**:
   - browse https://github.com/yuvallinik/mongodb-manifest/blob/main/README.md

12. **Deploy with ArgoCD**:
   - Create an ArgoCD application pointing to the GitHub repo containing the MongoDB manifest.

13. **Test MongoDB**:
   - Access the database using MongoDB Compass or write a Mongoose-based script.


### Verifying MongoDB Connectivity and Creating a Collection

This guide explains how to verify MongoDB connectivity, connect to your database, and create a new collection using MongoDB Compass.

---

#### Step 1: Retrieve MongoDB External IP

1. Run the following command to get the `External IP` of the MongoDB service:
    ```bash
    kubectl get svc --namespace=mongo-namespace
    ```
2. Note the `External IP` assigned to your MongoDB service.

---

#### Step 2: Install MongoDB Compass

1. Download and install **MongoDB Compass** from the official MongoDB website:  
   [https://www.mongodb.com/try/download/compass](https://www.mongodb.com/try/download/compass)
2. Launch MongoDB Compass after installation.

---

#### Step 3: Connect to MongoDB

1. In MongoDB Compass, enter the connection string in the following format:
    ```
    mongodb://<External-IP>:27017
    ```
    Replace `<External-IP>` with the IP you retrieved earlier.
2. Click on **Connect**.

---

#### Step 4: Create a New Collection

1. Once connected, navigate to your database.
2. Click on **Create Collection**.
3. Provide a name for your collection and save.

---

#### Step 5: Verify Persistent Volume Claim (PVC)

1. Check the PVC associated with your MongoDB deployment:
    ```bash
    kubectl get pvc --namespace=mongo-namespace
    ```
2. Ensure the PVC is bound and the Persistent Volume (PV) is properly attached.

---

### Summary

After completing these steps:
- You have verified connectivity to app.
- Successfully verifed the "Task Complete" message and image display.
- You have Verifed MongoDB connectivity and create a new collection.
- Successfully connected using MongoDB Compass.
- Created a new collection within your MongoDB database. 

Well done! You’ve successfully completed the steps, and everything is working as expected!

---

### Conclusion
By completing these steps, you have successfully:
- Set up a Kubernetes cluster using RKE.
- Deployed applications using Helm.
- Integrated ArgoCD for GitOps.
- Verified application and database functionality.


