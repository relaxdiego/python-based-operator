# Prometheus Operator (Python Based)

It's a prometheus operator that's built with nothing but Python. This is
not meant for production use. This project was inspired by
https://link.medium.com/rC0Nqcrgw7

See the quick demo on [YouTube](https://youtu.be/RlhLFxOGE_E).

## Dependencies

1. Kubernetes 1.18 or higher
2. Helm 3
3. Docker CE
4. GNU Make


## Make Your Life Easier

If you just want to kick the tires a bit, use [microk8s](https://microk8s.io/)
to get Kubernetes and Helm 3 up and running in no time!

```
microk8s.enable helm3
```


## Usage


#### Build the Container Image

```
docker build -t <your-docker-hub-username>/prometheus-operator .
docker push <your-docker-hub-username>/prometheus-operator
```

NOTE: If you prefer to push your image to a private container repo and
      you have access to one, then feel free use that instead.


#### Deploy the Operator

```
helm install --atomic \
  --set image.repository=<your-docker-hub-username>/prometheus-operator \
  <name-of-this-prometheus-operator> \
  charts/prometheus-operator/
```

#### Need Some Sample PrometheusCluster manifests?

There's some under the `examples/` directory. After deploying the operator,
create some sample PrometheusClusters via the usual kubectl command:

```
kubectl apply -f examples/simple.yaml
```

#### Clean Up

```
helm uninstall <name-of-this-prometheus-operator>
```


## Development Guide


#### Dependencies

1. Python 3.8.x or higher

TIP: Make your life easier by using [pyenv](https://github.com/pyenv/pyenv-installer)


#### Prepare Your Virtualenv

```
python3 -m venv --prompt prometheus-operator .venv
source .venv/bin/activate
```

TIP: Make your life easier by using [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv):

```
pyenv virtualenv 3.8.3 prometheus-operator-3.8.3
```


#### Install Development Dependencies For the First Time

```
python3 -m pip install --upgrade pip
python3 -m pip install "pip-tools>=5.2.1,<5.3"
make dependencies
```

#### Subsequent Installation of Development Dependencies

```
make dependencies
```

#### When Adding a Development Dependency

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


#### When Adding a Runtime Dependency

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


#### Trying Your Changes on Microk8s

First, make sure you enable a few important addons:

```
microk8s.enable dns helm3 ingress registry storage
```

Build and deploy your work to your local microk8s cluster:

```
make operator tag=localhost:32000/prometheus-operator
```

NOTE: The address `localhost:32000` is the address of the microk8s registry
      addon that we enabled in the previous step.

To uninstall, run:

```
make clean
```

You can optionally deploy the operator to its own namespace (recommended).
For example, if you want to deploy to a namespace named prometheus-operator
in a microk8s cluster with its registry addon enabled, run:

```
microk8s.kubectl create ns prometheus-operator
make operator tag=localhost:32000/prometheus-operator ns=prometheus-operator
```

#### Debugging The Prometheus Operator Helm Chart

Run:

```
make debug
```

Checkout stdout for any inaccuracies or errors.


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
make dev-operator
```

Finally, run the operator locally

```
prometheus-operator
```

You should see logs starting to stream into stdout at this point. If you want
to make changes to the python code, make those changes, save them, then kill
and rerun `prometheus-operator`

To clean up, use the same `make clean` command. Enjoy!


#### Force Re-Install Depedencies and Uninstall the Operator

Run the following

```
make clean-all
make dependencies
```

If you want something more thorough (and potentially destructive) than that,
delete your virtual environment. Then start from the beginning of the
Development Guide section.
