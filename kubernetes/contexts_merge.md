# Merging Multiple Kubernetes kubeconfig Files

It is common to work with multiple Kubernetes clusters, where each cluster has its own `kubeconfig` file.

Instead of switching files manually, you can merge multiple kubeconfig files into a single configuration.

---

## Example

In this example, we have two kubeconfig files:

| kubeconfig | Description |
|------------|-------------|
| `config-lenovo-laptop` | Remote Kubernetes cluster |
| `config-local-docker-desktop` | Local Docker Desktop Kubernetes cluster |

After merging, both contexts become available from the default kubeconfig file.

---

## Step 1 - Temporarily set the KUBECONFIG environment variable

```powershell
$env:KUBECONFIG="$HOME\.kube\config-lenovo-laptop;$HOME\.kube\config-local-docker-desktop"
```

> **Note (Windows):**
> Multiple kubeconfig files are separated with a semicolon (`;`).

On Linux/macOS, use a colon (`:`) instead.

Example:

```bash
export KUBECONFIG=$HOME/.kube/config-work:$HOME/.kube/config-minikube
```

---

## Step 2 - Merge the kubeconfig files

```powershell
kubectl config view --merge --flatten > "$HOME\.kube\config"
```

### What these options do

| Option | Meaning |
|---------|---------|
| `--merge` | Merge all kubeconfig files specified in `KUBECONFIG` |
| `--flatten` | Produce a self-contained kubeconfig with all referenced information embedded |

The merged configuration is written to:

```
$HOME\.kube\config
```

This becomes the default kubeconfig used by `kubectl`.

---

## Step 3 - Remove the temporary environment variable

```powershell
Remove-Item Env:\KUBECONFIG
```

This ensures future `kubectl` commands use the default merged configuration.

---

## Step 4 - Verify the available contexts

```powershell
kubectl config get-contexts
```

Example output:

```text
CURRENT   NAME                                       CLUSTER              AUTHINFO                NAMESPACE
          docker-desktop                             docker-desktop       docker-desktop
*         kubernetes-admin-user@kubernetes-lenonvo   kubernetes-lenonvo   kubernetes-admin-user
```

The `*` indicates the current active context.

---

## Switch Between Contexts

List available contexts:

```powershell
kubectl config get-contexts
```

Switch to Docker Desktop:

```powershell
kubectl config use-context docker-desktop
```

Switch back to the remote cluster:

```powershell
kubectl config use-context kubernetes-admin-user@kubernetes-lenonvo
```

Verify the current context:

```powershell
kubectl config current-context
```

---

## View Cluster Information

Show cluster information:

```powershell
kubectl cluster-info
```

Show nodes:

```powershell
kubectl get nodes
```

---

## Tips

- Keep a separate kubeconfig file for each cluster.
- Merge them only when needed.
- Give contexts meaningful names.
- Avoid manually editing merged kubeconfig files.
- Store backup copies of your original kubeconfig files.

---

## Result

After merging, you can seamlessly switch between clusters using:

```powershell
kubectl config use-context <context-name>
```

without changing the `KUBECONFIG` environment variable again.