from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    nebius_project_id: str
    nebius_subnet_id: str
    nebius_security_group_id: str
    nebius_service_account_id: str
    nebius_public_key_id: str
    nebius_private_key: str

    nebius_platform: str
    nebius_preset: str
    nebius_image_family: str
    nebius_disk_type: str
    nebius_boot_disk_gb: int
    nebius_instance_name: str

    k3s_master_ip: str
    k3s_node_token: str
    ssh_public_key: str
    gpu_node_label: str

    max_gpu_nodes: int
    poll_interval_seconds: int
    idle_timeout_seconds: int
    max_lifetime_seconds: int

    namespace: str = "placeframe"
    dry_run: bool = False