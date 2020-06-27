# bare-python-prometheus-operator

It's a prometheus operator that's built with nothing but Python. This is
not meant for production use.

This project was inspired by https://link.medium.com/rC0Nqcrgw7


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
  helm/
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
echo 'foo' >> dev-requirements.in
make dependencies
```

The `dev-requirements.txt` file should now be updated. Make sure to commit
both files to the repo to let your teammates know of the new dependency.

```
git add dev-requirements.*
git commit -m "Add foo to dev-requirements.txt"
git push origin
```


#### When Adding a Runtime Dependency

Add it to the `install_requires` argument of the `setup()` call. For example:

```
setup(
    name=_NAME,
    version='0.1.0',

    ...

    install_requires=[
        'kubernetes',
        'bar'
    ],

    ...

)
```

After having added the `bar` dependency above, run the following:

```
make dependencies
```

The `requirements.txt` file should now be updated. Make sure to commit
both files to the repo to let your teammates know of the new dependency.

```
git add setup.py requirements.txt
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
make operator tag=<your-docker-hub-username>/prometheus-operator
```

NOTE: If you prefer to push your image to a private container repo and
      you have access to one, then feel free use that instead.


To uninstall, run:

```
make clean
```


#### Force Re-Install Depedencies and Uninstall the Operator

Run the following

```
make clean-all
make dependencies
```

If you want something more thorough (and potentially destructive) than that,
delete your virtual environment. Then start from the beginning of the
Development Guide section.
