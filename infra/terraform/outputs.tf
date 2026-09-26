output "alb_dns_name" {
  description = "Public Application Load Balancer DNS name for AuRAG console"
  value       = aws_lb.main.dns_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL database endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "s3_document_bucket" {
  description = "S3 bucket for document ingestion and drawings"
  value       = aws_s3_bucket.documents.id
}

output "ecs_cluster_name" {
  description = "ECS cluster identifier"
  value       = aws_ecs_cluster.main.name
}

output "vpc_id" {
  description = "VPC identifier"
  value       = aws_vpc.main.id
}
