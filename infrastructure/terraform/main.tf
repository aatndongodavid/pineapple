# infrastructure/terraform/main.tf

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
}

# -----------------------------------------------------------------------------
# 1. Groupe de ressources principal
# -----------------------------------------------------------------------------
resource "azurerm_resource_group" "pineapple_rg" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Project     = "Pineapple OS"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Region      = "South Africa North (Johannesburg)"
  }
}

# -----------------------------------------------------------------------------
# 2. Azure Key Vault (Gestionnaires de secrets)
# -----------------------------------------------------------------------------
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "pineapple_kv" {
  name                        = "kv-pineapple-${var.environment}"
  location                    = azurerm_resource_group.pineapple_rg.location
  resource_group_name         = azurerm_resource_group.pineapple_rg.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false

  sku_name = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Purge", "Recover"
    ]
  }

  tags = azurerm_resource_group.pineapple_rg.tags
}

resource "azurerm_key_vault_secret" "db_password_secret" {
  name         = "database-password"
  value        = var.postgres_admin_password
  key_vault_id = azurerm_key_vault.pineapple_kv.id
}

resource "azurerm_key_vault_secret" "jwt_secret" {
  name         = "jwt-secret-key"
  value        = var.jwt_secret_key
  key_vault_id = azurerm_key_vault.pineapple_kv.id
}

# -----------------------------------------------------------------------------
# 3. Base de données PostgreSQL (Azure Database for PostgreSQL - Flexible Server)
# -----------------------------------------------------------------------------
resource "azurerm_postgresql_flexible_server" "pineapple_postgres" {
  name                   = "psql-pineapple-${var.environment}"
  resource_group_name    = azurerm_resource_group.pineapple_rg.name
  location               = azurerm_resource_group.pineapple_rg.location
  version                = "16"
  administrator_login    = var.postgres_admin_username
  administrator_password = var.postgres_admin_password
  storage_mb             = 32768
  sku_name               = var.postgres_sku_name

  backup_retention_days = 7
  geo_redundant_backup_enabled = false

  tags = azurerm_resource_group.pineapple_rg.tags
}

resource "azurerm_postgresql_flexible_server_database" "pineapple_db" {
  name      = "pineapple_db"
  server_id = azurerm_postgresql_flexible_server.pineapple_postgres.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# -----------------------------------------------------------------------------
# 4. Cache & Broker (Azure Cache for Redis)
# -----------------------------------------------------------------------------
resource "azurerm_redis_cache" "pineapple_redis" {
  name                = "redis-pineapple-${var.environment}"
  location            = azurerm_resource_group.pineapple_rg.location
  resource_group_name = azurerm_resource_group.pineapple_rg.name
  capacity            = var.redis_capacity
  family              = var.redis_family
  sku_name            = var.redis_sku_name
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  tags = azurerm_resource_group.pineapple_rg.tags
}

# -----------------------------------------------------------------------------
# 5. Registre de conteneurs (Azure Container Registry - ACR)
# -----------------------------------------------------------------------------
resource "azurerm_container_registry" "pineapple_acr" {
  name                = "acrpineapple${var.environment}"
  resource_group_name = azurerm_resource_group.pineapple_rg.name
  location            = azurerm_resource_group.pineapple_rg.location
  sku                 = "Standard"
  admin_enabled       = true

  tags = azurerm_resource_group.pineapple_rg.tags
}

# -----------------------------------------------------------------------------
# 6. Stockage d'objets (Azure Blob Storage - 4 Conteneurs)
# -----------------------------------------------------------------------------
resource "azurerm_storage_account" "pineapple_storage" {
  name                     = "stpineapple${var.environment}"
  resource_group_name      = azurerm_resource_group.pineapple_rg.name
  location                 = azurerm_resource_group.pineapple_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = azurerm_resource_group.pineapple_rg.tags
}

resource "azurerm_storage_container" "academy_docs" {
  name                  = "academy-documents"
  storage_account_name  = azurerm_storage_account.pineapple_storage.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "cert_docs" {
  name                  = "certification-documents"
  storage_account_name  = azurerm_storage_account.pineapple_storage.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "tenant_exports" {
  name                  = "tenant-exports"
  storage_account_name  = azurerm_storage_account.pineapple_storage.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "org_logos" {
  name                  = "org-logos"
  storage_account_name  = azurerm_storage_account.pineapple_storage.name
  container_access_type = "private"
}

# -----------------------------------------------------------------------------
# 7. Hébergement du Backend (Azure Container Apps + Environment)
# -----------------------------------------------------------------------------
resource "azurerm_container_app_environment" "pineapple_cae" {
  name                = "cae-pineapple-${var.environment}"
  location            = azurerm_resource_group.pineapple_rg.location
  resource_group_name = azurerm_resource_group.pineapple_rg.name

  tags = azurerm_resource_group.pineapple_rg.tags
}

resource "azurerm_container_app" "pineapple_backend" {
  name                         = "ca-pineapple-backend-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.pineapple_cae.id
  resource_group_name          = azurerm_resource_group.pineapple_rg.name
  revision_mode                = "Single"

  template {
    container {
      name   = "backend"
      image  = "${azurerm_container_registry.pineapple_acr.login_server}/pineapple-backend:latest"
      cpu    = 0.5
      memory = "1.0Gi"

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "AZURE_KEY_VAULT_URL"
        value = azurerm_key_vault.pineapple_kv.vault_uri
      }
      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = azurerm_storage_account.pineapple_storage.name
      }
    }

    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    custom_scale_rule {
      name             = "http-concurrency-rule"
      custom_rule_type = "http"
      metadata = {
        concurrentRequests = tostring(var.http_concurrency_target)
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = azurerm_resource_group.pineapple_rg.tags
}

# -----------------------------------------------------------------------------
# 8. Hébergement du Frontend (Azure Static Web Apps)
# -----------------------------------------------------------------------------
resource "azurerm_static_web_app" "pineapple_frontend" {
  name                = "swa-pineapple-${var.environment}"
  resource_group_name = azurerm_resource_group.pineapple_rg.name
  location            = "westeurope" # Static Web Apps est un service managé mondial

  tags = azurerm_resource_group.pineapple_rg.tags
}

# -----------------------------------------------------------------------------
# 9. CDN & Protection de Périphérie (Azure Front Door)
# -----------------------------------------------------------------------------
resource "azurerm_cdn_frontdoor_profile" "pineapple_fd" {
  name                = "fd-pineapple-${var.environment}"
  resource_group_name = azurerm_resource_group.pineapple_rg.name
  sku_name            = "Standard_AzureFrontDoor"

  tags = azurerm_resource_group.pineapple_rg.tags
}

resource "azurerm_cdn_frontdoor_endpoint" "pineapple_fd_endpoint" {
  name                     = "fde-pineapple-${var.environment}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.pineapple_fd.id
}
