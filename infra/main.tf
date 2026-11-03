terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
  }
}

provider "kubernetes" {
  config_path    = pathexpand("~/.kube/config")
  config_context = "devops-lab"
}

resource "kubernetes_namespace_v1" "lab_iac" {
  metadata {
    name   = "lab-iac"
    labels = { managed-by = "opentofu" }
  }
}

resource "kubernetes_resource_quota_v1" "lab_iac" {
  metadata {
    name      = "lab-quota"
    namespace = kubernetes_namespace_v1.lab_iac.metadata[0].name
  }
  spec {
    hard = {
      "requests.cpu"    = "2"
      "requests.memory" = "2Gi"
      "pods"            = "10"
    }
  }
}
