# # common/src/common/session_client_docker.py
# from __future__ import annotations

# import http.client
# from typing import Any, Literal, TypedDict

# from docker.models.containers import Container
# from docker.types import DeviceRequest
# from pydantic import AnyHttpUrl

# import docker

# SESSION_PORT = 8000  # internal port exposed by the session container


# class SessionInfo(TypedDict):
#     container_id: str
#     container_name: str
#     host: str
#     port: int


# class DockerSessionClient:
#     def __init__(self, network_name: str = "plerion_default") -> None:
#         self._docker = docker.from_env()
#         self._network_name = network_name

#     def create_session(
#         self,
#         session_id: str,
#         image: str,
#         *,
#         torch_device: Literal["cpu", "cuda", "rocm"] = "cpu",
#         environment: dict[str, str] | None = None,
#     ) -> tuple[str, AnyHttpUrl]:
#         env: dict[str, str] = dict(environment or {})
#         env.setdefault("SESSION_ID", session_id)

#         name = f"vls-session-{session_id}"

#         # Configure optional host-port publishing
#         ports: dict[str, tuple[str, int]] | None = None

#         run_kwargs: dict[str, Any] = {}
#         if torch_device == "cuda":
#             run_kwargs["device_requests"] = [DeviceRequest(count=-1, capabilities=[["gpu"]])]
#         elif torch_device == "rocm":
#             run_kwargs["devices"] = ["/dev/kfd:/dev/kfd", "/dev/dri:/dev/dri"]

#         container: Container = self._docker.containers.run(
#             image=image,
#             name=name,
#             detach=True,
#             environment=env,
#             labels={"service": "vls-session", "session": session_id},
#             network=self._network_name,
#             ports=ports,
#             **run_kwargs,
#         )

#         # Wait for readiness
#         # self._wait_healthy(container)
#         assert container.id is not None

#         # self._wait_http_ready(name)

#         return container.id, AnyHttpUrl(f"http://{name}:{SESSION_PORT}")

#     def stop_session(self, container_id: str) -> None:
#         c: Container | None = None
#         try:
#             c = self._docker.containers.get(container_id)
#         except Exception:
#             # Already gone
#             return

#         try:
#             c.stop(timeout=10)
#         # Don't remove container, we want to keep logs around for debugging
#         # finally:
#         #     try:
#         #         c.remove(force=True)
#         #     except Exception:
#         #         # best-effort cleanup
#         #         pass
#         except Exception:
#             # best-effort cleanup
#             pass

#     def get_session_status(self, container_id: str) -> str:
#         container = self._docker.containers.get(container_id)
#         container.reload()
#         assert container.name is not None

#         status: str | None = container.attrs.get("State", {}).get("Status")

#         if status is None:
#             return "unknown"
#         if status != "running":
#             return status

#         try:
#             conn = http.client.HTTPConnection(container.name, SESSION_PORT, timeout=2.0)
#             conn.request("GET", "/health")
#             health_status = conn.getresponse().status
#             conn.close()
#             if health_status < 500:
#                 return "ready"
#         except Exception:
#             pass

#         return "starting"
