# bare-python-prometheus-operator

It's a prometheus operator that's built with nothing but Python. This is
not meant for production use.

This project was inspired by https://link.medium.com/rC0Nqcrgw7


## Dependencies

1. Kubernetes 1.18 or higher
2. Helm 3
3. Docker CE


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
python3 -m venv --promp prometheus-operator .venv
source .venv/bin/activate
```

TIP: Make your life easier by using [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

#### Install Development Dependencies For the First Time

```
python3 -m pip install --upgrade pip
python3 -m pip install "pip-tools>=5.2.1,<5.3"
pip-sync dev-requirements.txt --pip-args '--require-hashes'
```

#### Subsequent Installation of Development Dependencies

```
pip-sync dev-requirements.txt --pip-args '--require-hashes'
```

#### When Adding a Development Dependency

```
echo 'a-dependency==1.0.0' >> dev-requirements.in
pip-compile --generate-hashes dev-requirements.in
```

The `dev-requirements.txt` file should now be updated. Make sure to commit
that to the repo:

```
git add dev-requirements.*
git commit -m "Add a-dependency to dev-requirements.txt"
git push origin
```

Then install the dev dependencies using `pip-sync` as illustrated above.

#### When Adding a Runtime Dependency

```
echo 'a-dependency==1.0.0' >> requirements.in
pip-compile --generate-hashes requirements.in
```

The `requirements.txt` file should now be updated. Make sure to commit
that to the repo:

```
git add requirements.*
git commit -m "Add a-dependency to requirements.txt"
git push origin
```

Then install the dev dependencies using `pip-sync` as illustrated above.