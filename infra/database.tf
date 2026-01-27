# Cloud SQL Instance (Postgres)
resource "google_sql_database_instance" "postgres" {
  name             = "${var.service_name}-db-${random_id.db_suffix.hex}"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  settings {
    tier = var.db_tier
    
    # MVP Config: Public IP enabled, but require Auth
    ip_configuration {
      ipv4_enabled = true 
    }
  }

  deletion_protection = false # For MVP, easy teardown. Set to true for production.
  depends_on          = [google_project_service.apis]
}

resource "random_id" "db_suffix" {
  byte_length = 4
}

# Database
resource "google_sql_database" "database" {
  name     = "concierge_db"
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
}

# Database User
resource "google_sql_user" "db_user" {
  name     = "${var.service_name}-user"
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
  password = random_password.db_pass.result
}

resource "random_password" "db_pass" {
  length  = 16
  special = false
}

# Store DB Password in Secret Manager
resource "google_secret_manager_secret" "db_pass_secret" {
  secret_id = "${var.service_name}-db-pass"
  project   = var.project_id
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_pass_secret_version" {
  secret      = google_secret_manager_secret.db_pass_secret.id
  secret_data = random_password.db_pass.result
}

# Grant Access to Secret for Backend SA
resource "google_secret_manager_secret_iam_member" "sa_secret_access" {
  secret_id = google_secret_manager_secret.db_pass_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}
