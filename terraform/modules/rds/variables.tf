variable "name_prefix" {
  description = "Prefix for RDS resource name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where RDS will be created"
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "allowed_security_group_id" {
  description = "Security group ID allowed to connect to RDS"
  type        = string
}

variable "db_name" {
  description = "Initial PostgreSQL database name"
  type        = string
}

variable "username" {
  description = "Master username for PostgreSQL"
  type        = string
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "backup_retention_period" {
  description = "Number of days to retain automated backups; zero disables backups"
  type        = number
  default     = 0

  validation {
    condition     = var.backup_retention_period >= 0 && var.backup_retention_period <= 35
    error_message = "backup_retention_period must be between 0 and 35 days."
  }
}

variable "deletion_protection" {
  description = "Prevent deletion of the RDS instance until an operator explicitly disables protection"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Whether deletion skips the final DB snapshot"
  type        = bool
  default     = true
}

variable "final_snapshot_identifier" {
  description = "Unique snapshot name to use when skip_final_snapshot is false"
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = var.skip_final_snapshot || (var.final_snapshot_identifier != null && length(trimspace(var.final_snapshot_identifier)) > 0)
    error_message = "final_snapshot_identifier is required when skip_final_snapshot is false."
  }
}

variable "tags" {
  description = "Common tags for RDS resources"
  type        = map(string)
  default     = {}
}
