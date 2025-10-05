import os
import structlog

log = structlog.get_logger()

# Detect Render or any environment where Docker isn’t available
IN_RENDER = os.getenv("RENDER", "false").lower() == "true"

if not IN_RENDER:
    import docker
    client = docker.from_env()
else:
    client = None
    log.warning("Docker not available — running in Render environment")

IMAGE_MAP = {
    "cerebras": "tessera-cerebras-capsule:latest",
    "hf": "tessera-hf-capsule:latest",
}


def _get_image_type(model_name: str) -> str:
    return "cerebras" if "cerebras" in model_name.lower() else "hf"


def spawn_capsule(model_name: str, role: str) -> str:
    """Spin up a Docker container for attacker/defender capsule."""
    if IN_RENDER:
        log.warning("spawn_capsule called in Render — returning mock URL")
        return f"https://mock-{role}.render-app.local"

    image_type = _get_image_type(model_name)
    image = IMAGE_MAP[image_type]
    short_id = os.urandom(3).hex()
    container_name = f"{role}-{model_name.replace('/', '-')}-{short_id}"

    log.info("spawning_capsule", model=model_name, image=image, role=role)
    container = client.containers.run(
        image,
        detach=True,
        name=container_name,
        environment={"MODEL_NAME": model_name, "ROLE": role},
        ports={"8080/tcp": None},
    )
    container.reload()
    port = container.attrs["NetworkSettings"]["Ports"]["8080/tcp"][0]["HostPort"]
    url = f"http://localhost:{port}"
    log.info("capsule_started", container=container_name, url=url)
    return url


def stop_capsule(container_name: str):
    """Stop Docker container if available."""
    if IN_RENDER:
        log.warning(f"stop_capsule skipped in Render for {container_name}")
        return
    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
        log.info("capsule_removed", name=container_name)
    except Exception as e:
        log.warning("capsule_stop_failed", error=str(e))
