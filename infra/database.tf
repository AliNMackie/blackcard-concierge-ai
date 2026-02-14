resource "google_sql_database_instance" "master" {
  name             = "elite-concierge-db-prod"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier = "db-f1-micro" # Start small for MVP
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"  # 3 AM UTC
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 4
      }
    }

    ip_configuration {
      ipv4_enabled    = true
      # authorized_networks = [] # Add CI IP if needed, or use Proxy
    }
    
    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }
  }

  deletion_protection  = true # Prevent accidental data loss
}

resource "google_sql_database" "database" {
  name     = "elite_concierge"
  instance = google_sql_database_instance.master.name
}

resource "google_sql_user" "users" {
  name     = "elite_api"
  instance = google_sql_database_instance.master.name
  password = var.db_password # Variable needs to be defined
}
