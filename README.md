# A Python-Based k8s Operator

This project demonstrates how you can use plain Python to create a
fully-functional k8s operator. To avoid re-inventing the wheel, Helm 3 is
used internally by the operator to maintain the releases of the
application it manages. However, if you want to customize this project
to fit your needs and if your needs don't include Helm 3, you may safely
remove that requirement from the code.

This operator can manage multiple instances of Prometheus. You can modify
it to manage other types of applications if you wish. Prometheus was just
chosen in this case because most engineers in the DevOps space are already
familiar with it.

You instantiate Prometheus in a namespace by creating a PrometheusCluster
custom resource in said namespace. A simple instance with defaults can be
created via the following custom resource:

```yaml
apiVersion: relaxdiego.com/v1alpha1
kind: PrometheusCluster
metadata:
  name: simple-prometheus-instance
spec: {}
```


## Prior Art

Inspired by [this Medium article](https://link.medium.com/rC0Nqcrgw7)


## Dependencies

1. Kubernetes 1.18 or higher
2. [Docker CE](https://docs.docker.com/engine/install/) 17.06 or higher (For building the operator image)
3. GNU Make


## Optionally Use Microk8s

Use [microk8s](https://microk8s.io/) for testing this operator. It will
make your life so much easier. Go on, I'll wait!

Once you have microk8s installed, run the following:

```
microk8s.enable dns rbac ingress registry storage
mkdir -p ~/.kube
microk8s.config > ~/.kube/config
kubectl cluster-info
```


#### Build and Deploy the Operator

The following will build the image and deploy it in the `python-based-operator`
namespace.

```
make image deploy tag=localhost:32000/python-based-operator
```

NOTE: The address `localhost:32000` is the address of the microk8s registry
      addon that we enabled in the previous step. If you're not using microk8s,
      just replace that address with either another registry address that you
      have access to, or your Docker Hub username.


#### Create Your First Prometheus Cluster

There are sample PrometheusCluster files under the `examples/` directory. After
deploying the operator, create a sample Prometheus cluster via kubectl:

```
kubectl create ns simple-prometheus-cluster
kubectl config set-context --current --namespace=simple-prometheus-cluster
kubectl apply -f examples/simple.yaml
```

#### Scale Up Your Prometheus Cluster

```
kubectl edit -f examples/simple.yaml
```

Go to the `replicas:` field and change its value. Quit, save, then see your
number of prometheus pods scale accordingly.


#### Delete the Prometheus Cluster While Retaining its Data

Just run:

```
kubectl delete -f examples/simple.yaml
```

The volumes assocated with the pods will be retained and will be re-attached to
the correct pod later on if you want to revive them.


#### Delete the Operator and Everything in the Example Namespace

```
kubectl delete -f examples/simple.yaml
make uninstall
kubectl delete ns simple-prometheus-cluster
```


## Development Guide


#### Dependencies

1. Python 3.8.x or higher

TIP: Make your life easier by using [pyenv](https://github.com/pyenv/pyenv-installer)


#### Prepare Your Virtualenv (venv style)

```
python3 -m venv --prompt prometheus-operator .venv
source .venv/bin/activate
```

#### Prepare Your Virtualenv (pyenv-virtual style)

```
pyenv virtualenv 3.8.3 prometheus-operator-3.8.3
```

More on [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv):


#### Install Development Dependencies

```
make dependencies
```


#### Add a Development Dependency

```
echo 'foo' >> src/dev-requirements.in
make dependencies
```

The `src/dev-requirements.txt` file should now be updated and the `foo`
package installed in your local machine. Make sure to commit both files
to the repo to let your teammates know of the new dependency.

```
git add src/dev-requirements.*
git commit -m "Add foo to src/dev-requirements.txt"
git push origin
```


#### Add a Runtime Dependency

Add it to the `install_requires` argument of the `setup()` call in
`src/setup.py`. For example:

```
setup(
    name=_NAME,
    version='0.1.0',

    ...

    install_requires=[
        'kubernetes>=11.0.0,<11.1.0',
        'bar>=1.0.0,<2.0.0'
    ],

    ...

)
```

After having added the `bar` dependency above, run the following:

```
make dependencies
```

The `src/requirements.txt` file should now be updated and the bar package
installed in your local machine. Make sure to commit both files to the repo
to let your teammates know of the new dependency.

```
git add src/setup.py src/requirements.txt
git commit -m "Add bar as a runtime dependency"
git push origin
```

#### Force Re-Install Depedencies and Uninstall the Operator

Run the following

```
make reset
make dependencies
```

If you want something more thorough (and potentially destructive) than that,
delete your virtual environment. Then start from the beginning of the
Development Guide section.
