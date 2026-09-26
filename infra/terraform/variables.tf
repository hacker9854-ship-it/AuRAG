variable "aws_region" {
  description = "AWS region for production deployment (Mumbai)"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project namespace"
  type        = string
  default     = "aurag"
}

variable "site_id" {
  description = "Initial single-plant site identifier"
  type        = string
  default     = "plant-mumbai-01"
}

variable "vpc_cidr" {
  description = "CIDR block for the plant VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "backend_cpu" {
  description = "ECS Fargate CPU units for backend API task (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "backend_memory" {
  description = "ECS Fargate Memory for backend API task (MB)"
  type        = number
  default     = 2048
}

variable "frontend_cpu" {
  description = "ECS Fargate CPU units for Next.js frontend task"
  type        = number
  default     = 512
}

variable "frontend_memory" {
  description = "ECS Fargate Memory for Next.js frontend task (MB)"
  type        = number
  default     = 1024
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "aurag_enterprise"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "aurag_admin"
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
  default     = "ChangeMeInProductionVault123!"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t4g.medium"
}

variable "entra_tenant_id" {
  description = "Microsoft Entra ID Tenant ID for RS256 JWT validation"
  type        = string
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "entra_client_id" {
  description = "Microsoft Entra ID Application Client ID"
  type        = string
  default     = "aurag-enterprise-app"
}
