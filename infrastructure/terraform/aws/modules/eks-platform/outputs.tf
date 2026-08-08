output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_arn" {
  value = aws_eks_cluster.this.arn
}

output "node_role_arn" {
  value = aws_iam_role.node.arn
}
