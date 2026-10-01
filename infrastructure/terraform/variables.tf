# infrastructure/terraform/variables.tf

variable "environment" {
  type        = string
  description = "Environnement de déploiement (dev, staging, prod)"
  default     = "prod"
}

variable "location" {
  type        = string
  description = "Région Azure sélectionnée. South Africa North retenue pour latence minimale vers le Cameroun & Afrique Centrale (Partie BA)."
  default     = "southafricanorth"
}

variable "resource_group_name" {
  type        = string
  description = "Nom du groupe de ressources Azure"
  default     = "rg-pineapple-prod"
}

variable "postgres_sku_name" {
  type        = string
  description = "SKU pour Azure Database for PostgreSQL Flexible Server"
  default     = "GP_Standard_D2ds_v5"
}

variable "postgres_admin_username" {
  type        = string
  description = "Nom d'utilisateur administrateur PostgreSQL"
  default     = "pineapple_admin"
}

variable "postgres_admin_password" {
  type        = string
  description = "Mot de passe administrateur PostgreSQL"
  sensitive   = true
}

variable "redis_sku_name" {
  type        = string
  description = "SKU pour Azure Cache for Redis"
  default     = "Standard"
}

variable "redis_family" {
  type        = string
  description = "Famille de SKU pour Azure Cache for Redis"
  default     = "C"
}

variable "redis_capacity" {
  type        = number
  description = "Capacité Azure Cache for Redis"
  default     = 1
}

variable "min_replicas" {
  type        = number
  description = "Nombre minimal de réplicas pour Azure Container Apps (backend)"
  default     = 2
}

variable "max_replicas" {
  type        = number
  description = "Nombre maximal de réplicas pour Azure Container Apps (backend)"
  default     = 10
}

variable "http_concurrency_target" {
  type        = number
  description = "Seuil de concurrence HTTP par réplica pour le déclenchement de l'auto-scaling Container Apps (KEDA)"
  default     = 100
}

variable "jwt_secret_key" {
  type        = string
  description = "Clé secrète de signature des jetons JWT"
  sensitive   = true
}
