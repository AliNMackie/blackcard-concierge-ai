resource "google_sql_database_instance" "master" {
  name             = "elite-concierge-db-prod"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier = "db-f1-micro" # Start small for MVP
    
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
