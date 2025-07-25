# #!/usr/bin/env python3
# """
# AWS Resource Network Topology Visualizer

# This script queries AWS resources and their associated security groups to create
# a network topology diagram showing how resources can communicate with each other.

# Requirements:
#     - AWS CLI configured with appropriate credentials
#     - Python packages: boto3, networkx, matplotlib, argparse

# Install requirements:
#     pip install boto3 networkx matplotlib

# Usage:
#     python aws_resource_topology.py [--region us-east-1] [--output topology.png]
# """

# import argparse
# from collections import defaultdict
# from typing import Dict, List, Set
# import boto3
# import networkx as nx
# import matplotlib.pyplot as plt


# class ResourceNetworkTopology:
#     def __init__(self, region='us-east-1'):
#         self.region = region
#         self.session = boto3.Session(region_name=region)
#         self.ec2 = self.session.client('ec2') # type: ignore
#         self.ecs = self.session.client('ecs') # type: ignore
#         self.rds = self.session.client('rds') # type: ignore
#         self.elb = self.session.client('elbv2') # type: ignore
#         self.elasticache = self.session.client('elasticache') # type: ignore
#         self.lambda_client = self.session.client('lambda') # type: ignore

#         self.security_groups = {}
#         self.resources = {}
#         self.network_components = {}  # For VPC endpoints, NAT gateways, etc.
#         self.route_tables = {}
#         self.network_acls = {}
#         self.graph = nx.DiGraph()

#     def fetch_all_resources(self):
#         """Fetch all AWS resources and their security groups"""
#         print("Fetching AWS resources...")

#         # First, fetch all security groups and network components
#         self._fetch_security_groups()
#         self._fetch_network_acls()
#         self._fetch_route_tables()

#         # Fetch network infrastructure
#         self._fetch_vpc_endpoints()
#         self._fetch_nat_gateways()
#         self._fetch_internet_gateways()
#         self._fetch_vpc_peering_connections()
#         self._fetch_transit_gateways()

#         # Then fetch compute/service resources
#         self._fetch_ec2_instances()
#         self._fetch_rds_instances()
#         self._fetch_ecs_services()
#         self._fetch_load_balancers()
#         self._fetch_elasticache_clusters()
#         self._fetch_lambda_functions()

#         print(f"\nTotal resources found: {len(self.resources)}")
#         print(f"Total network components found: {len(self.network_components)}")

#         all_items = {}
#         all_items.update(self.resources)
#         all_items.update(self.network_components)

#         for rtype, count in self._count_items_by_type(all_items).items():
#             print(f"  {rtype}: {count}")

#     def _fetch_network_acls(self):
#         """Fetch Network ACLs"""
#         try:
#             response = self.ec2.describe_network_acls()
#             for acl in response['NetworkAcls']:
#                 self.network_acls[acl['NetworkAclId']] = {
#                     'vpc_id': acl.get('VpcId'),
#                     'entries': acl.get('Entries', []),
#                     'associations': acl.get('Associations', [])
#                 }
#         except Exception as e:
#             print(f"Error fetching Network ACLs: {e}")

#     def _fetch_route_tables(self):
#         """Fetch Route Tables"""
#         try:
#             response = self.ec2.describe_route_tables()
#             for rt in response['RouteTables']:
#                 self.route_tables[rt['RouteTableId']] = {
#                     'vpc_id': rt.get('VpcId'),
#                     'routes': rt.get('Routes', []),
#                     'associations': rt.get('Associations', [])
#                 }
#         except Exception as e:
#             print(f"Error fetching Route Tables: {e}")

#     def _fetch_vpc_endpoints(self):
#         """Fetch VPC Endpoints (Interface and Gateway)"""
#         try:
#             response = self.ec2.describe_vpc_endpoints()
#             for endpoint in response['VpcEndpoints']:
#                 endpoint_id = endpoint['VpcEndpointId']
#                 endpoint_type = endpoint.get('VpcEndpointType', 'Gateway')

#                 # For interface endpoints, get security groups
#                 security_groups = []
#                 if endpoint_type == 'Interface':
#                     security_groups = endpoint.get('Groups', [])
#                     security_groups = [sg['GroupId'] for sg in security_groups]

#                 self.network_components[endpoint_id] = {
#                     'type': f'VPC_Endpoint_{endpoint_type}',
#                     'name': f"{endpoint.get('ServiceName', 'Unknown').split('.')[-1]}",
#                     'service_name': endpoint.get('ServiceName'),
#                     'vpc_id': endpoint.get('VpcId'),
#                     'security_groups': security_groups,
#                     'subnet_ids': endpoint.get('SubnetIds', []),
#                     'route_table_ids': endpoint.get('RouteTableIds', []),
#                     'state': endpoint.get('State')
#                 }
#         except Exception as e:
#             print(f"Error fetching VPC Endpoints: {e}")

#     def _fetch_nat_gateways(self):
#         """Fetch NAT Gateways"""
#         try:
#             response = self.ec2.describe_nat_gateways()
#             for nat in response['NatGateways']:
#                 if nat['State'] in ['available', 'pending']:
#                     nat_id = nat['NatGatewayId']

#                     self.network_components[nat_id] = {
#                         'type': 'NAT_Gateway',
#                         'name': f"NAT-{nat_id[-8:]}",
#                         'vpc_id': nat.get('VpcId'),
#                         'subnet_id': nat.get('SubnetId'),
#                         'security_groups': [],  # NAT Gateways don't have security groups
#                         'connectivity_type': nat.get('ConnectivityType', 'public')
#                     }
#         except Exception as e:
#             print(f"Error fetching NAT Gateways: {e}")

#     def _fetch_internet_gateways(self):
#         """Fetch Internet Gateways"""
#         try:
#             response = self.ec2.describe_internet_gateways()
#             for igw in response['InternetGateways']:
#                 igw_id = igw['InternetGatewayId']

#                 # Get attached VPCs
#                 vpc_ids = [att['VpcId'] for att in igw.get('Attachments', [])]

#                 self.network_components[igw_id] = {
#                     'type': 'Internet_Gateway',
#                     'name': f"IGW-{igw_id[-8:]}",
#                     'vpc_id': vpc_ids[0] if vpc_ids else 'Detached',
#                     'security_groups': [],  # IGWs don't have security groups
#                     'attached_vpcs': vpc_ids
#                 }
#         except Exception as e:
#             print(f"Error fetching Internet Gateways: {e}")

#     def _fetch_vpc_peering_connections(self):
#         """Fetch VPC Peering Connections"""
#         try:
#             response = self.ec2.describe_vpc_peering_connections()
#             for pcx in response['VpcPeeringConnections']:
#                 if pcx['Status']['Code'] == 'active':
#                     pcx_id = pcx['VpcPeeringConnectionId']

#                     self.network_components[pcx_id] = {
#                         'type': 'VPC_Peering',
#                         'name': f"PCX-{pcx_id[-8:]}",
#                         'vpc_id': pcx['RequesterVpcInfo']['VpcId'],
#                         'accepter_vpc_id': pcx['AccepterVpcInfo']['VpcId'],
#                         'security_groups': [],  # Peering connections don't have security groups
#                         'requester_vpc': pcx['RequesterVpcInfo'],
#                         'accepter_vpc': pcx['AccepterVpcInfo']
#                     }
#         except Exception as e:
#             print(f"Error fetching VPC Peering Connections: {e}")

#     def _fetch_transit_gateways(self):
#         """Fetch Transit Gateway Attachments"""
#         try:
#             # First get transit gateways
#             response = self.ec2.describe_transit_gateways()
#             for tgw in response.get('TransitGateways', []):
#                 if tgw['State'] == 'available':
#                     tgw_id = tgw['TransitGatewayId']

#                     self.network_components[tgw_id] = {
#                         'type': 'Transit_Gateway',
#                         'name': f"TGW-{tgw_id[-8:]}",
#                         'vpc_id': 'Multi-VPC',
#                         'security_groups': [],
#                         'description': tgw.get('Description', '')
#                     }

#             # Get attachments
#             response = self.ec2.describe_transit_gateway_attachments()
#             for att in response.get('TransitGatewayAttachments', []):
#                 if att['State'] == 'available':
#                     att_id = att['TransitGatewayAttachmentId']

#                     self.network_components[att_id] = {
#                         'type': 'TGW_Attachment',
#                         'name': f"TGW-Att-{att_id[-8:]}",
#                         'vpc_id': att.get('ResourceId'),  # This is the VPC ID for VPC attachments
#                         'security_groups': [],
#                         'transit_gateway_id': att.get('TransitGatewayId'),
#                         'resource_type': att.get('ResourceType')
#                     }
#         except Exception as e:
#             print(f"Error fetching Transit Gateways: {e}")

#     def _fetch_ec2_instances(self):
#         """Fetch EC2 instances"""
#         try:
#             response = self.ec2.describe_instances()
#             for reservation in response['Reservations']:
#                 for instance in reservation['Instances']:
#                     if instance['State']['Name'] in ['running', 'stopped']:
#                         instance_id = instance['InstanceId']
#                         name = self._get_tag_value(instance.get('Tags', []), 'Name') or instance_id

#                         security_groups = [sg['GroupId'] for sg in instance.get('SecurityGroups', [])]

#                         self.resources[instance_id] = {
#                             'type': 'EC2',
#                             'name': name,
#                             'security_groups': security_groups,
#                             'vpc_id': instance.get('VpcId', 'EC2-Classic'),
#                             'private_ip': instance.get('PrivateIpAddress'),
#                             'public_ip': instance.get('PublicIpAddress'),
#                             'state': instance['State']['Name']
#                         }
#         except Exception as e:
#             print(f"Error fetching EC2 instances: {e}")

#     def _fetch_rds_instances(self):
#         """Fetch RDS instances"""
#         try:
#             response = self.rds.describe_db_instances()
#             for db in response['DBInstances']:
#                 db_id = db['DBInstanceIdentifier']
#                 security_groups = [sg['VpcSecurityGroupId'] for sg in db.get('VpcSecurityGroups', [])]

#                 self.resources[db_id] = {
#                     'type': 'RDS',
#                     'name': db_id,
#                     'security_groups': security_groups,
#                     'vpc_id': db.get('DBSubnetGroup', {}).get('VpcId', 'Unknown'),
#                     'engine': db.get('Engine', 'Unknown'),
#                     'endpoint': db.get('Endpoint', {}).get('Address'),
#                     'port': db.get('Endpoint', {}).get('Port')
#                 }
#         except Exception as e:
#             print(f"Error fetching RDS instances: {e}")

#     def _fetch_ecs_services(self):
#         """Fetch ECS services and their tasks"""
#         try:
#             # Get all clusters
#             clusters = self.ecs.list_clusters()

#             for cluster_arn in clusters.get('clusterArns', []):
#                 # Get services in cluster
#                 services = self.ecs.list_services(cluster=cluster_arn)

#                 if services.get('serviceArns'):
#                     # Describe services
#                     service_details = self.ecs.describe_services(
#                         cluster=cluster_arn,
#                         services=services['serviceArns']
#                     )

#                     for service in service_details.get('services', []):
#                         if service['status'] == 'ACTIVE':
#                             service_name = service['serviceName']
#                             service_id = f"ecs-{service_name}"

#                             # Get security groups from network configuration
#                             network_config = service.get('networkConfiguration', {}).get('awsvpcConfiguration', {})
#                             security_groups = network_config.get('securityGroups', [])

#                             self.resources[service_id] = {
#                                 'type': 'ECS_Service',
#                                 'name': service_name,
#                                 'security_groups': security_groups,
#                                 'vpc_id': 'Unknown',  # Would need subnet lookup
#                                 'cluster': cluster_arn.split('/')[-1],
#                                 'launch_type': service.get('launchType', 'Unknown'),
#                                 'desired_count': service.get('desiredCount', 0)
#                             }
#         except Exception as e:
#             print(f"Error fetching ECS services: {e}")

#     def _fetch_load_balancers(self):
#         """Fetch Application and Network Load Balancers"""
#         try:
#             response = self.elb.describe_load_balancers()
#             for lb in response['LoadBalancers']:
#                 lb_name = lb['LoadBalancerName']
#                 lb_id = f"lb-{lb_name}"

#                 self.resources[lb_id] = {
#                     'type': f"{lb['Type'].upper()}_LB",
#                     'name': lb_name,
#                     'security_groups': lb.get('SecurityGroups', []),
#                     'vpc_id': lb.get('VpcId', 'Unknown'),
#                     'scheme': lb.get('Scheme', 'Unknown'),
#                     'dns_name': lb.get('DNSName', 'Unknown')
#                 }
#         except Exception as e:
#             print(f"Error fetching load balancers: {e}")

#     def _fetch_elasticache_clusters(self):
#         """Fetch ElastiCache clusters"""
#         try:
#             response = self.elasticache.describe_cache_clusters()
#             for cluster in response['CacheClusters']:
#                 cluster_id = cluster['CacheClusterId']

#                 # Get security groups
#                 security_groups = []
#                 for sg in cluster.get('SecurityGroups', []):
#                     security_groups.append(sg['SecurityGroupId'])

#                 self.resources[cluster_id] = {
#                     'type': 'ElastiCache',
#                     'name': cluster_id,
#                     'security_groups': security_groups,
#                     'vpc_id': 'Unknown',  # Would need subnet lookup
#                     'engine': cluster.get('Engine', 'Unknown'),
#                     'cache_node_type': cluster.get('CacheNodeType', 'Unknown')
#                 }
#         except Exception as e:
#             print(f"Error fetching ElastiCache clusters: {e}")

#     def _fetch_lambda_functions(self):
#         """Fetch Lambda functions with VPC configuration"""
#         try:
#             response = self.lambda_client.list_functions()
#             for func in response.get('Functions', []):
#                 vpc_config = func.get('VpcConfig', {})
#                 security_groups = vpc_config.get('SecurityGroupIds', [])

#                 if security_groups:  # Only include Lambda functions in VPCs
#                     func_name = func['FunctionName']
#                     func_id = f"lambda-{func_name}"

#                     self.resources[func_id] = {
#                         'type': 'Lambda',
#                         'name': func_name,
#                         'security_groups': security_groups,
#                         'vpc_id': vpc_config.get('VpcId', 'Unknown'),
#                         'runtime': func.get('Runtime', 'Unknown')
#                     }
#         except Exception as e:
#             print(f"Error fetching Lambda functions: {e}")

#     def _get_tag_value(self, tags: List[Dict], key: str) -> str:
#         """Extract tag value by key"""
#         for tag in tags:
#             if tag.get('Key') == key:
#                 return tag.get('Value', '')
#         return ''

#     def _count_items_by_type(self, items: Dict) -> Dict[str, int]:
#         """Count items by type"""
#         counts = defaultdict(int)
#         for item in items.values():
#             counts[item['type']] += 1
#         return dict(counts)

#     def build_graph(self):
#         """Build a directed graph from resources and their security group rules"""
#         # Combine all items (resources + network components)
#         all_items = {}
#         all_items.update(self.resources)
#         all_items.update(self.network_components)

#         # Add nodes for each item
#         for item_id, item_data in all_items.items():
#             label = f"{item_data['name']}\n({item_data['type']})"
#             self.graph.add_node(
#                 item_id,
#                 label=label,
#                 type=item_data['type'],
#                 vpc=item_data.get('vpc_id', 'Unknown')
#             )

#         # Add edges based on various connection types
#         self._add_security_group_connections(all_items)
#         self._add_vpc_endpoint_connections()
#         self._add_nat_gateway_connections()
#         self._add_internet_gateway_connections()
#         self._add_vpc_peering_connections()
#         self._add_transit_gateway_connections()

#     def _add_security_group_connections(self, all_items):
#         """Add connections based on security group rules"""
#         for src_id, src_data in all_items.items():
#             src_security_groups = set(src_data.get('security_groups', []))

#             for dst_id, dst_data in all_items.items():
#                 if src_id == dst_id:
#                     continue

#                 dst_security_groups = set(dst_data.get('security_groups', []))

#                 # Check if source can connect to destination
#                 connections = self._check_connection(src_security_groups, dst_security_groups)

#                 if connections:
#                     # Aggregate all connection rules
#                     edge_label = self._format_connections(connections)
#                     self.graph.add_edge(src_id, dst_id, label=edge_label, rules=connections)

#     def _add_vpc_endpoint_connections(self):
#         """Add connections for VPC endpoints"""
#         for endpoint_id, endpoint_data in self.network_components.items():
#             if not endpoint_data['type'].startswith('VPC_Endpoint'):
#                 continue

#             # Interface endpoints can be accessed by resources in the same VPC
#             if endpoint_data['type'] == 'VPC_Endpoint_Interface':
#                 vpc_id = endpoint_data['vpc_id']
#                 service_name = endpoint_data['name']

#                 # Find resources in the same VPC that might use this endpoint
#                 for resource_id, resource_data in self.resources.items():
#                     if resource_data.get('vpc_id') == vpc_id:
#                         # Check if they share security groups or if the endpoint allows the resource's SGs
#                         endpoint_sgs = set(endpoint_data.get('security_groups', []))
#                         resource_sgs = set(resource_data.get('security_groups', []))

#                         if self._check_connection(resource_sgs, endpoint_sgs):
#                             self.graph.add_edge(resource_id, endpoint_id,
#                                               label=f"via SG\n{service_name}")

#             # Gateway endpoints are accessed via route tables
#             elif endpoint_data['type'] == 'VPC_Endpoint_Gateway':
#                 # This would need route table analysis to be fully accurate
#                 # For now, show potential connections
#                 vpc_id = endpoint_data['vpc_id']
#                 service_name = endpoint_data['name']

#                 for resource_id, resource_data in self.resources.items():
#                     if resource_data.get('vpc_id') == vpc_id:
#                         self.graph.add_edge(resource_id, endpoint_id,
#                                           label=f"via Route\n{service_name}",
#                                           style='dashed')

#     def _add_nat_gateway_connections(self):
#         """Add connections through NAT gateways"""
#         for nat_id, nat_data in self.network_components.items():
#             if nat_data['type'] != 'NAT_Gateway':
#                 continue

#             vpc_id = nat_data['vpc_id']

#             # Find private resources in the same VPC that might use NAT
#             for resource_id, resource_data in self.resources.items():
#                 if resource_data.get('vpc_id') == vpc_id:
#                     # Check if resource is in a private subnet (simplified check)
#                     if not resource_data.get('public_ip'):
#                         self.graph.add_edge(resource_id, nat_id,
#                                           label="Outbound",
#                                           style='dashed')

#     def _add_internet_gateway_connections(self):
#         """Add connections through Internet gateways"""
#         for igw_id, igw_data in self.network_components.items():
#             if igw_data['type'] != 'Internet_Gateway':
#                 continue

#             attached_vpcs = igw_data.get('attached_vpcs', [])

#             # Find public resources in attached VPCs
#             for resource_id, resource_data in self.resources.items():
#                 if resource_data.get('vpc_id') in attached_vpcs:
#                     # Check if resource has a public IP
#                     if resource_data.get('public_ip') or resource_data['type'] in ['APPLICATION_LB', 'NETWORK_LB']:
#                         self.graph.add_edge(resource_id, igw_id,
#                                           label="Internet",
#                                           style='dashed')

#     def _add_vpc_peering_connections(self):
#         """Add VPC peering connections"""
#         for pcx_id, pcx_data in self.network_components.items():
#             if pcx_data['type'] != 'VPC_Peering':
#                 continue

#             requester_vpc = pcx_data['vpc_id']
#             accepter_vpc = pcx_data['accepter_vpc_id']

#             # Show potential connections between resources in peered VPCs
#             requester_resources = [r for r, d in self.resources.items()
#                                  if d.get('vpc_id') == requester_vpc]
#             accepter_resources = [r for r, d in self.resources.items()
#                                 if d.get('vpc_id') == accepter_vpc]

#             # Add edges to show peering relationship
#             for r_resource in requester_resources[:2]:  # Limit to avoid clutter
#                 self.graph.add_edge(r_resource, pcx_id,
#                                   label="Peering",
#                                   style='dotted')
#             for a_resource in accepter_resources[:2]:
#                 self.graph.add_edge(pcx_id, a_resource,
#                                   label="Peering",
#                                   style='dotted')

#     def _add_transit_gateway_connections(self):
#         """Add Transit Gateway connections"""
#         for tgw_att_id, tgw_att_data in self.network_components.items():
#             if tgw_att_data['type'] != 'TGW_Attachment':
#                 continue

#             vpc_id = tgw_att_data['vpc_id']
#             tgw_id = tgw_att_data['transit_gateway_id']

#             # Connect VPC resources to TGW via attachment
#             vpc_resources = [r for r, d in self.resources.items()
#                            if d.get('vpc_id') == vpc_id]

#             for resource in vpc_resources[:3]:  # Limit to avoid clutter
#                 self.graph.add_edge(resource, tgw_att_id,
#                                   label="TGW Route",
#                                   style='dotted')

#             # Connect attachment to TGW
#             if tgw_id in self.network_components:
#                 self.graph.add_edge(tgw_att_id, tgw_id,
#                                   label="Attached",
#                                   style='dotted')

#     def _check_connection(self, src_sgs: Set[str], dst_sgs: Set[str]) -> List[Dict]:
#         """Check if source security groups can connect to destination security groups"""
#         connections = []

#         for dst_sg in dst_sgs:
#             if dst_sg not in self.security_groups:
#                 continue

#             dst_sg_data = self.security_groups[dst_sg]

#             # Check ingress rules of destination
#             for rule in dst_sg_data['ingress']:
#                 # Check if any source security group is allowed
#                 for user_group in rule.get('UserIdGroupPairs', []):
#                     allowed_sg = user_group.get('GroupId')
#                     if allowed_sg in src_sgs:
#                         connections.append({
#                             'protocol': rule.get('IpProtocol', 'all'),
#                             'from_port': rule.get('FromPort', 0),
#                             'to_port': rule.get('ToPort', 65535),
#                             'source_sg': allowed_sg,
#                             'dest_sg': dst_sg
#                         })

#         return connections

#     def _format_connections(self, connections: List[Dict]) -> str:
#         """Format connection rules for edge labels"""
#         # Group by protocol and ports
#         rule_strings = set()

#         for conn in connections:
#             protocol = conn['protocol']
#             if protocol == '-1':
#                 protocol = 'all'

#             from_port = conn['from_port']
#             to_port = conn['to_port']

#             if from_port == to_port:
#                 ports = str(from_port) if from_port != 0 else 'all'
#             elif from_port == 0 and to_port == 65535:
#                 ports = 'all'
#             else:
#                 ports = f"{from_port}-{to_port}"

#             rule_strings.add(f"{protocol}/{ports}")

#         return '\n'.join(sorted(rule_strings))

#     def visualize(self, output_file='topology.png', show_labels=True):
#         """Create and save the network topology diagram"""
#         if not self.graph.nodes():
#             print("No resources to visualize")
#             return

#         plt.figure(figsize=(20, 16))

#         # Group nodes by type and VPC
#         type_groups = defaultdict(list)
#         for node in self.graph.nodes():
#             node_type = self.graph.nodes[node].get('type', 'Unknown')
#             type_groups[node_type].append(node)

#         # Define colors for different resource types
#         type_colors = {
#             'EC2': '#FF9900',  # AWS Orange
#             'RDS': '#1B660F',  # Dark Green
#             'ECS_Service': '#FF9900',  # Orange
#             'APPLICATION_LB': '#F58536',  # Light Orange
#             'NETWORK_LB': '#F58536',  # Light Orange
#             'ElastiCache': '#C925D1',  # Purple
#             'Lambda': '#FF9900',  # Orange
#             'VPC_Endpoint_Interface': '#4B9CD3',  # Blue
#             'VPC_Endpoint_Gateway': '#4B9CD3',  # Blue
#             'NAT_Gateway': '#759EEA',  # Light Blue
#             'Internet_Gateway': '#FF0000',  # Red
#             'VPC_Peering': '#00C49F',  # Teal
#             'Transit_Gateway': '#FFBB28',  # Yellow
#             'TGW_Attachment': '#FFBB28'  # Yellow
#         }

#         # Use hierarchical layout
#         pos = self._hierarchical_layout_by_type(type_groups)

#         # Draw nodes by type with different shapes
#         for node_type, nodes in type_groups.items():
#             node_positions = {n: pos[n] for n in nodes if n in pos}

#             # Determine node shape based on type
#             if node_type == 'RDS':
#                 node_shape = 's'  # square for databases
#             elif node_type in ['APPLICATION_LB', 'NETWORK_LB']:
#                 node_shape = 'h'  # hexagon for load balancers
#             elif node_type == 'Lambda':
#                 node_shape = '^'  # triangle for Lambda
#             elif node_type in ['VPC_Endpoint_Interface', 'VPC_Endpoint_Gateway']:
#                 node_shape = 'd'  # diamond for endpoints
#             elif node_type in ['NAT_Gateway', 'Internet_Gateway']:
#                 node_shape = 'p'  # pentagon for gateways
#             elif node_type in ['VPC_Peering', 'Transit_Gateway', 'TGW_Attachment']:
#                 node_shape = '*'  # star for cross-VPC connectivity
#             else:
#                 node_shape = 'o'  # circle for others

#             nx.draw_networkx_nodes(
#                 self.graph, node_positions,
#                 nodelist=nodes,
#                 node_color=type_colors.get(node_type, '#cccccc'),
#                 node_shape=node_shape,
#                 node_size=3000,
#                 alpha=0.8
#             )

#         # Draw edges with different styles based on protocol
#         edges = self.graph.edges(data=True)
#         if edges:
#             # Separate edges by style
#             solid_edges = [(u, v) for u, v, d in edges if d.get('style') != 'dashed' and d.get('style') != 'dotted']
#             dashed_edges = [(u, v) for u, v, d in edges if d.get('style') == 'dashed']
#             dotted_edges = [(u, v) for u, v, d in edges if d.get('style') == 'dotted']

#             # Draw solid edges (security group connections)
#             if solid_edges:
#                 nx.draw_networkx_edges(
#                     self.graph, pos,
#                     edgelist=solid_edges,
#                     edge_color='gray',
#                     arrows=True,
#                     arrowsize=20,
#                     arrowstyle='-|>',
#                     connectionstyle='arc3,rad=0.1',
#                     alpha=0.6,
#                     width=2
#                 )

#             # Draw dashed edges (routing connections)
#             if dashed_edges:
#                 nx.draw_networkx_edges(
#                     self.graph, pos,
#                     edgelist=dashed_edges,
#                     edge_color='blue',
#                     arrows=True,
#                     arrowsize=20,
#                     arrowstyle='-|>',
#                     connectionstyle='arc3,rad=0.1',
#                     alpha=0.4,
#                     width=1,
#                     style='dashed'
#                 )

#             # Draw dotted edges (peering/transit connections)
#             if dotted_edges:
#                 nx.draw_networkx_edges(
#                     self.graph, pos,
#                     edgelist=dotted_edges,
#                     edge_color='green',
#                     arrows=True,
#                     arrowsize=20,
#                     arrowstyle='-|>',
#                     connectionstyle='arc3,rad=0.1',
#                     alpha=0.4,
#                     width=1,
#                     style='dotted'
#                 )

#         # Draw labels
#         if show_labels:
#             labels = nx.get_node_attributes(self.graph, 'label')
#             nx.draw_networkx_labels(
#                 self.graph, pos, labels,
#                 font_size=8,
#                 font_weight='bold'
#             )

#             # Draw edge labels
#             edge_labels = nx.get_edge_attributes(self.graph, 'label')
#             nx.draw_networkx_edge_labels(
#                 self.graph, pos, edge_labels,
#                 font_size=6,
#                 font_color='red',
#                 bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3)
#             )

#         # Create legend
#         legend_elements = []
#         for rtype, color in type_colors.items():
#             if rtype in type_groups:
#                 if rtype == 'RDS':
#                     marker = 's'
#                 elif rtype in ['APPLICATION_LB', 'NETWORK_LB']:
#                     marker = 'h'
#                 elif rtype == 'Lambda':
#                     marker = '^'
#                 elif rtype in ['VPC_Endpoint_Interface', 'VPC_Endpoint_Gateway']:
#                     marker = 'd'
#                 elif rtype in ['NAT_Gateway', 'Internet_Gateway']:
#                     marker = 'p'
#                 elif rtype in ['VPC_Peering', 'Transit_Gateway', 'TGW_Attachment']:
#                     marker = '*' 'TGW_Attachment']:
#                     marker = '*'
#                 else:
#                     marker = 'o'

#                 element = plt.Line2D([0], [0], marker=marker, color='w',
#                                    markerfacecolor=color, markersize=10,
#                                    label=rtype.replace('_', ' '))
#                 legend_elements.append(element)

#         plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))

#         plt.title(f'AWS Resource Network Topology - {self.region}', fontsize=18, fontweight='bold')
#         plt.axis('off')
#         plt.tight_layout()

#         # Save the diagram
#         plt.savefig(output_file, dpi=300, bbox_inches='tight')
#         print(f"\nNetwork topology diagram saved to: {output_file}")

#         # Also show the diagram
#         plt.show()

#     def _hierarchical_layout_by_type(self, type_groups: Dict[str, List[str]]) -> Dict:
#         """Create a hierarchical layout grouped by resource type"""
#         pos = {}
#         y_offset = 0

#         # Define the order of resource types (top to bottom)
#         type_order = [
#             'Internet_Gateway',
#             'APPLICATION_LB', 'NETWORK_LB',
#             'NAT_Gateway',
#             'ECS_Service', 'EC2', 'Lambda',
#             'VPC_Endpoint_Interface', 'VPC_Endpoint_Gateway',
#             'RDS', 'ElastiCache',
#             'VPC_Peering', 'Transit_Gateway', 'TGW_Attachment'
#         ]

#         for resource_type in type_order:
#             if resource_type not in type_groups:
#                 continue

#             nodes = type_groups[resource_type]

#             # Arrange nodes of the same type horizontally
#             x_spacing = 4
#             x_offset = -(len(nodes) - 1) * x_spacing / 2  # Center the row

#             for i, node in enumerate(nodes):
#                 pos[node] = (x_offset + i * x_spacing, y_offset)

#             y_offset -= 3  # Move down for next type

#         # Handle any remaining types not in the order
#         for resource_type, nodes in type_groups.items():
#             if resource_type not in type_order:
#                 x_spacing = 4
#                 x_offset = -(len(nodes) - 1) * x_spacing / 2

#                 for i, node in enumerate(nodes):
#                     pos[node] = (x_offset + i * x_spacing, y_offset)

#                 y_offset -= 3

#         return pos

#     def print_summary(self):
#         """Print a summary of the resources and connections"""
#         print("\n=== Resource Network Summary ===")

#         all_items = {}
#         all_items.update(self.resources)
#         all_items.update(self.network_components)

#         print(f"Total Resources: {len(self.resources)}")
#         print(f"Total Network Components: {len(self.network_components)}")
#         print(f"Total Connections: {self.graph.number_of_edges()}")

#         # Items by type
#         print("\nComponents by Type:")
#         for rtype, count in sorted(self._count_items_by_type(all_items).items()):
#             print(f"  {rtype}: {count}")

#         # Find isolated resources
#         isolated = [r for r in self.resources.keys()
#                    if self.graph.in_degree(r) == 0 and self.graph.out_degree(r) == 0]
#         if isolated:
#             print(f"\nIsolated Resources (no connections): {len(isolated)}")
#             for resource_id in isolated[:5]:
#                 resource = self.resources[resource_id]
#                 print(f"  - {resource['name']} ({resource['type']})")
#             if len(isolated) > 5:
#                 print(f"  ... and {len(isolated) - 5} more")

#         # VPC Endpoints summary
#         vpc_endpoints = [e for e, d in self.network_components.items()
#                         if d['type'].startswith('VPC_Endpoint')]
#         if vpc_endpoints:
#             print(f"\nVPC Endpoints: {len(vpc_endpoints)}")
#             for endpoint_id in vpc_endpoints[:5]:
#                 endpoint = self.network_components[endpoint_id]
#                 print(f"  - {endpoint['service_name']} ({endpoint['type']})")

#         # Resources with most connections
#         print("\nMost Connected Components:")
#         node_connections = [(n, self.graph.in_degree(n) + self.graph.out_degree(n))
#                            for n in self.graph.nodes()]
#         node_connections.sort(key=lambda x: x[1], reverse=True)

#         for item_id, conn_count in node_connections[:5]:
#             if conn_count > 0:
#                 item = all_items.get(item_id, {})
#                 print(f"  - {item.get('name', 'Unknown')} ({item.get('type', 'Unknown')}): {conn_count} connections")


# def main():
#     parser = argparse.ArgumentParser(
#         description='Generate AWS resource network topology diagram based on security groups'
#     )
#     parser.add_argument('--region', '-r', default='us-east-1',
#                        help='AWS region (default: us-east-1)')
#     parser.add_argument('--output', '-o', default='resource_topology.png',
#                        help='Output file name (default: resource_topology.png)')
#     parser.add_argument('--no-labels', action='store_true',
#                        help='Hide labels in the diagram')
#     parser.add_argument('--profile', '-p', default=None,
#                        help='AWS profile to use')

#     args = parser.parse_args()

#     # Set AWS profile if specified
#     if args.profile:
#         boto3.setup_default_session(profile_name=args.profile)

#     # Create topology analyzer
#     topology = ResourceNetworkTopology(region=args.region)

#     print(f"Analyzing AWS resources in region: {args.region}")
#     topology.fetch_all_resources()

#     print("\nBuilding network graph based on security group rules...")
#     topology.build_graph()

#     topology.print_summary()

#     print("\nGenerating visualization...")
#     topology.visualize(output_file=args.output, show_labels=not args.no_labels)


# if __name__ == '__main__':
#     main()
