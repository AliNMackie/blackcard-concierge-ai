variable "project_id" {
  description = "The GCP Project ID to deploy to."
  type        = string
}

variable "region" {
  description = "The default GCP region to deploy resources in."
  type        = string
  default     = "europe-west2"
}

variable "service_name" {
  description = "The base name for the service and resources."
  type        = string
  default     = "elite-concierge"
}

variable "db_tier" {
  description = "The machine type for the Cloud SQL instance."
  type        = string
  default     = "db-f1-micro" # MVP friendly
}
