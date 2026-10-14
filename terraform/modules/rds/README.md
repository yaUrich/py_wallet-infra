# Module: rds

Creates a private PostgreSQL RDS instance with DB subnet group, SG-to-SG ingress, and a generated master password.

The module exposes explicit backup, deletion-protection and final-snapshot
controls. Its defaults remain suitable for ephemeral environments. Long-lived
environments must set a non-zero retention period, enable deletion protection,
and provide a unique final snapshot identifier.

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.6 |
| aws | ~> 5.0 |
| random | ~> 3.6 |

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.6.0, < 2.0.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 5.0 |
| <a name="requirement_random"></a> [random](#requirement\_random) | ~> 3.6 |

## Providers

| Name | Version |
| ---- | ------- |
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 5.0 |
| <a name="provider_random"></a> [random](#provider\_random) | ~> 3.6 |

## Modules

No modules.

## Resources

| Name | Type |
| ---- | ---- |
| [aws_db_instance.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance) | resource |
| [aws_db_subnet_group.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_subnet_group) | resource |
| [aws_security_group.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [random_password.master](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/password) | resource |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_allocated_storage"></a> [allocated\_storage](#input\_allocated\_storage) | Allocated storage in GB | `number` | `20` | no |
| <a name="input_backup_retention_period"></a> [backup\_retention\_period](#input\_backup\_retention\_period) | Number of days to retain automated backups; zero disables backups | `number` | `0` | no |
| <a name="input_allowed_security_group_id"></a> [allowed\_security\_group\_id](#input\_allowed\_security\_group\_id) | Security group ID allowed to connect to RDS | `string` | n/a | yes |
| <a name="input_db_name"></a> [db\_name](#input\_db\_name) | Initial PostgreSQL database name | `string` | n/a | yes |
| <a name="input_deletion_protection"></a> [deletion\_protection](#input\_deletion\_protection) | Prevent deletion of the RDS instance until an operator explicitly disables protection | `bool` | `false` | no |
| <a name="input_final_snapshot_identifier"></a> [final\_snapshot\_identifier](#input\_final\_snapshot\_identifier) | Unique snapshot name to use when skip_final_snapshot is false | `string` | `null` | no |
| <a name="input_instance_class"></a> [instance\_class](#input\_instance\_class) | RDS instance class | `string` | `"db.t4g.micro"` | no |
| <a name="input_name_prefix"></a> [name\_prefix](#input\_name\_prefix) | Prefix for RDS resource name | `string` | n/a | yes |
| <a name="input_skip_final_snapshot"></a> [skip\_final\_snapshot](#input\_skip\_final\_snapshot) | Whether deletion skips the final DB snapshot | `bool` | `true` | no |
| <a name="input_subnet_ids"></a> [subnet\_ids](#input\_subnet\_ids) | Private subnet IDs for the DB subnet group | `list(string)` | n/a | yes |
| <a name="input_tags"></a> [tags](#input\_tags) | Common tags for RDS resources | `map(string)` | `{}` | no |
| <a name="input_username"></a> [username](#input\_username) | Master username for PostgreSQL | `string` | n/a | yes |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | VPC ID where RDS will be created | `string` | n/a | yes |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_db_name"></a> [db\_name](#output\_db\_name) | PostgreSQL database name |
| <a name="output_endpoint"></a> [endpoint](#output\_endpoint) | RDS connection endpoint (host:port) |
| <a name="output_password"></a> [password](#output\_password) | Master password |
| <a name="output_port"></a> [port](#output\_port) | RDS port |
| <a name="output_username"></a> [username](#output\_username) | Master username |
<!-- END_TF_DOCS -->
