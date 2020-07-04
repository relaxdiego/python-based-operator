Why a Separate Chat for the CRD?
================================

Because of the current limitations imposed by Helm 3 on CRDs as described
here: https://helm.sh/docs/chart_best_practices/custom_resource_definitions/#install-a-crd-declaration-before-using-the-resource,
we are choosing to use Method 2 instead, allowing us to add new versions
to the CRD as needed.

Also, for development purposes, this makes it easy to clean up the entire
cluster of all operator-related objects.
