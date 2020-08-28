# A Python-Based k8s Operator

This project demonstrates how you can use plain Python to create a
fully-functional k8s operator. To avoid re-inventing the wheel, Helm 3 is
used internally by the operator to maintain the releases of the
application it manages.

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
2. Helm 3 (v3.2.4 or higher)
3. Docker CE (For building the container images)
4. GNU Make


## Optionally Use Microk8s

Use [microk8s](https://microk8s.io/) for testing this operator. It will
make your life so much easier. Go on, I'll wait!

Once you have microk8s installed, run the following:

```
microk8s.enable dns rbac ingress registry storage
mkdir -p ~/.kube
microk8s.config > ~/.kube/config
```


#### Deploy the Operator

```
make install tag=localhost:32000/prometheus-operator
```

NOTE: The address `localhost:32000` is the address of the microk8s registry
      addon that we enabled in the previous step. If you're not using microk8s,
      just replace that address with either another registry address that you
      have access to, or your Docker Hub username.


#### Create Your First Prometheus Cluster

There are some PrometheusCluster CRDs under the `examples/` directory. After
deploying the operator, create a sample Prometheus cluster via the usual
kubectl commands:

```
kubectl create ns example
kubectl apply -f examples/simple.yaml -n example
```

#### Scale Up Your Prometheus Cluster

```
kubectl edit -f examples/simple.yaml -n example
```

Go to the `replicas:` field and change its value. Quit, save, then see your
number of prometheus pods scale accordingly.


#### Delete the Prometheus Cluster While Retaining its Data

Just run:

```
kubectl delete -f examples/simple.yaml -n example
```

The volumes assocated with the pods will be retained and will be re-attached to
the correct pod later on if you want to revive them.


#### Delete the Operator and Everything in the Example Namespace

```
make uninstall
kubectl delete ns example
```


#### Why a Separate Chart for the PrometheusCluster CRD?

Because of the current limitations imposed by Helm 3 on CRDs as described
[here](https://helm.sh/docs/chart_best_practices/custom_resource_definitions/#install-a-crd-declaration-before-using-the-resource),
we are choosing to use Method 2 instead, allowing us to add new versions
to the CRD as needed.

Also, for development purposes, this makes it easy to clean up the entire
cluster of all operator-related objects.

Of course, in a production environment, be careful when managing the CRD.
Most important: don't delete it once it's been created and in use because
it will also delete the objects based on that CRD.


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


#### Try Your Changes on Microk8s

First, make sure you enable a few important addons:

```
microk8s.enable dns rbac ingress registry storage
```

Build and deploy your work to your local microk8s cluster:

```
make install tag=localhost:32000/prometheus-operator
```

NOTE: The address `localhost:32000` is the address of the microk8s registry
      addon that we enabled in the previous step.


#### Create Your First Prometheus Cluster

Use one of the example PrometheusCluster manifests:

```
microk8s.kubectl create ns example
microk8s.kubectl apply -f examples/simple.yaml -n example
```

#### Uninstall

```
make uninstall
microk8s.kubectl delete ns example && microk8s.kubectl create ns example
```

#### Debugging The Prometheus Operator Helm Chart

Run:

```
make debug
```

This prints out the manifests as they would be generated and submitted to k8s.
Check for any errors and fix them accordingly.


#### More Handy Commands in the Makefile

The above make examples are non-exhaustive. Check out the Makefile for more
info on other available commands.


#### A Faster Development Workflow

After some time, it can get very tiring to test your code in a live environment
by running `make operator ...` then `make clean` then `make operator ...` again
ad nauseam. This is especially annoying if all you're doing is change one or
two lines of code in between `make operator` and `make clean`. To make this
process a little bit easier, there's `make dev-operator`.

To get this to work, first make sure you have your `~/.kube/config` set up properly
to point to your target cluster. It's best that you use microk8s here to keep
things easy:

```
mkdir -p ~/.kube
microk8s.config > ~/.kube/config
```

Next deploy the operator in dev mode:

```
make install tag=localhost:32000/prometheus-operator dev=true
```

Finally, run the operator locally

```
prometheus-operator
```

You should see logs starting to stream into stdout at this point. If you want
to make changes to the python code, make those changes, save them, then kill
and rerun `prometheus-operator`

NOTE: Since the operator is running with the admin role in this case, any RBAC
      changes you make will have no effect. So for debugging RBAC-related issues
      run `make install` without the dev=true option instead.

When done, use the usual uninstall method above.


#### Force Re-Install Depedencies and Uninstall the Operator

Run the following

```
make reset
make dependencies
```

If you want something more thorough (and potentially destructive) than that,
delete your virtual environment. Then start from the beginning of the
Development Guide section.
