# Locals for regional scaling
locals {
  regions = ["europe-west2", "us-central1"]
}

# Artifact Registry Repo is global/regional - we keep one for now or mirror
resource "google_artifact_registry_repository" "repo" {
  location      = "europe-west2" # Primary repo
  repository_id = "${var.service_name}-repo"
  description   = "Docker repository for Elite Concierge services"
  format        = "DOCKER"
  project       = var.project_id
}

# Cloud Run v2 Services (Multi-Region)
resource "google_cloud_run_v2_service" "api" {
  for_each = toset(local.regions)
  
  name     = "${var.service_name}-api-${each.key}"
  location = each.key
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER" # Restrict to LB

  template {
    service_account = google_service_account.backend_sa.email

    max_instance_request_concurrency = 80
    session_affinity                = true

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" 
      
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "DB_INSTANCE_CONNECTION_NAME"
        value = google_sql_database_instance.master.connection_name
      }
      
      env {
        name = "DB_PASS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_pass.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "DB_USER"
        value = google_sql_user.users.name
      }

      env {
        name  = "DB_NAME"
        value = google_sql_database.database.name
      }

      env {
        name  = "ENV"
        value = "production"
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version
    ]
  }
}

# --- GLOBAL LOAD BALANCING (Autonomous Scale) ---

# Serverless NEGs
resource "google_compute_region_network_endpoint_group" "serverless_neg" {
  for_each              = toset(local.regions)
  name                  = "${var.service_name}-neg-${each.key}"
  network_endpoint_type = "SERVERLESS"
  region                = each.key
  project               = var.project_id
  cloud_run {
    service = google_cloud_run_v2_service.api[each.key].name
  }
}

# Backend Service
resource "google_compute_backend_service" "default" {
  name                  = "${var.service_name}-backend"
  project               = var.project_id
  protocol              = "HTTP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  locality_lb_policy    = "ROUND_ROBIN"

  # Enterprise Hardening: Automatic Failover & Outlier Detection
  outlier_detection {
    consecutive_errors = 5
    base_ejection_time {
      seconds = 30
    }
    interval {
      seconds = 1
    }
    max_ejection_percent = 50 # If one region fails, 50% ejection allows failover to the other
  }

  circuit_breakers {
    max_requests_per_connection = 100
  }

  dynamic "backend" {
    for_each = toset(local.regions)
    content {
      group = google_compute_region_network_endpoint_group.serverless_neg[backend.key].id
      balancing_mode = "UTILIZATION" # Required for some LB types, helps with failover
      capacity_scaler = 1.0 
    }
  }

  security_policy = google_compute_security_policy.policy.id
}

# URL Map
resource "google_compute_url_map" "default" {
  name            = "${var.service_name}-url-map"
  project         = var.project_id
  default_service = google_compute_backend_service.default.id
}

# HTTP Target Proxy
resource "google_compute_target_http_proxy" "default" {
  name    = "${var.service_name}-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.default.id
}

# Forwarding Rule (Global IP)
resource "google_compute_global_forwarding_rule" "default" {
  name                  = "${var.service_name}-forwarding-rule"
  project               = var.project_id
  target                = google_compute_target_http_proxy.default.id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# --- CLOUD ARMOR WAF (Security Hardening) ---
resource "google_compute_security_policy" "policy" {
  name    = "${var.service_name}-waf-policy"
  project = var.project_id

  # Default rule (Allow all, then apply filters)
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default rule"
  }

  # Block SQL Injection
  rule {
    action   = "deny(403)"
    priority = "1000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
    description = "SQLi protection"
  }

  # Block XSS
  rule {
    action   = "deny(403)"
    priority = "1001"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
    description = "XSS protection"
  }
}
