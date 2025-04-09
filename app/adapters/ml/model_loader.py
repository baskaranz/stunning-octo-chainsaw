import os
import subprocess
import asyncio
import shutil
import tempfile
from typing import Dict, Any, Optional, List, Tuple
import logging
import docker
import boto3
from pathlib import Path

from app.common.errors.custom_exceptions import ModelError
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ModelLoader:
    """
    Handles loading of models from different sources:
    - Local filesystem (model artifacts)
    - Docker images
    - ECR repositories
    """
    
    def __init__(self):
        """Initialize the model loader."""
        self.loaded_models = {}  # Keep track of loaded models
        self.model_processes = {}  # Keep track of running model processes
        self.docker_client = None  # Docker client, initialized on demand
        self.ecr_client = None  # ECR client, initialized on demand
    
    def _get_docker_client(self) -> docker.DockerClient:
        """Get or initialize the Docker client."""
        if self.docker_client is None:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                raise ModelError(f"Failed to initialize Docker client: {str(e)}")
        return self.docker_client
    
    def _get_ecr_client(self, region: str = "us-east-1") -> boto3.client:
        """Get or initialize the ECR client."""
        if self.ecr_client is None:
            try:
                self.ecr_client = boto3.client('ecr', region_name=region)
            except Exception as e:
                raise ModelError(f"Failed to initialize ECR client: {str(e)}")
        return self.ecr_client
    
    async def load_model(self, model_config: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        """
        Load a model from the specified source based on the configuration.
        
        Args:
            model_config: The model configuration
            source_id: The source identifier
            
        Returns:
            Updated model configuration with runtime information
        """
        model_source = model_config.get("source", {})
        source_type = model_source.get("type", "http")  # Default to HTTP endpoint
        model_id = model_config.get("id", "default")
        
        # Generate a unique key for this model
        model_key = f"{source_id}_{model_id}"
        
        # If model is already loaded, return the cached configuration
        if model_key in self.loaded_models:
            return self.loaded_models[model_key]
        
        # Handle different source types
        if source_type == "local_artifact":
            config = await self._load_from_local_artifact(model_config, model_key)
        elif source_type == "docker":
            config = await self._load_from_docker(model_config, model_key)
        elif source_type == "ecr":
            config = await self._load_from_ecr(model_config, model_key)
        else:
            # For HTTP endpoints, no loading needed
            config = model_config
        
        # Cache the loaded model configuration
        self.loaded_models[model_key] = config
        return config
    
    async def _load_from_local_artifact(self, model_config: Dict[str, Any], model_key: str) -> Dict[str, Any]:
        """
        Load a model from local artifact files.
        
        Args:
            model_config: The model configuration
            model_key: Unique key for the model
            
        Returns:
            Updated model configuration with runtime information
        """
        source = model_config.get("source", {})
        artifact_path = source.get("path")
        
        if not artifact_path:
            raise ModelError("Missing artifact path in model configuration")
        
        if not os.path.exists(artifact_path):
            raise ModelError(f"Model artifact path not found: {artifact_path}")
        
        # Get the startup command for the model
        startup_cmd = source.get("startup_command")
        if not startup_cmd:
            raise ModelError("Missing startup command in model configuration")
        
        # Start the model server process
        try:
            # Create a temporary directory for the model process logs
            log_dir = tempfile.mkdtemp(prefix="model_")
            log_file = os.path.join(log_dir, f"{model_key}.log")
            
            # Start the process
            with open(log_file, "w") as log:
                process = subprocess.Popen(
                    startup_cmd,
                    shell=True,
                    cwd=artifact_path,
                    stdout=log,
                    stderr=log
                )
            
            self.model_processes[model_key] = {
                "process": process,
                "log_file": log_file,
                "log_dir": log_dir
            }
            
            # Wait for the server to start up
            await asyncio.sleep(source.get("startup_delay", 5))
            
            # Check if process is still running
            if process.poll() is not None:
                # Process has terminated
                with open(log_file, "r") as log:
                    log_content = log.read()
                
                raise ModelError(
                    f"Model server process terminated unexpectedly. Exit code: {process.returncode}. "
                    f"Logs: {log_content}"
                )
            
            # Update the model configuration with the host and port
            host = source.get("host", "localhost")
            port = source.get("port", 8000)
            
            # Copy the original model config and update it
            updated_config = model_config.copy()
            updated_config["endpoint"] = f"http://{host}:{port}{updated_config.get('endpoint', '/predict')}"
            
            logger.info(f"Started model server from local artifact at {updated_config['endpoint']}")
            
            return updated_config
            
        except Exception as e:
            logger.error(f"Failed to start model from local artifact: {str(e)}")
            raise ModelError(f"Failed to start model from local artifact: {str(e)}")
    
    async def _load_from_docker(self, model_config: Dict[str, Any], model_key: str) -> Dict[str, Any]:
        """
        Load a model from a Docker image.
        
        Args:
            model_config: The model configuration
            model_key: Unique key for the model
            
        Returns:
            Updated model configuration with runtime information
        """
        source = model_config.get("source", {})
        image = source.get("image")
        
        if not image:
            raise ModelError("Missing Docker image in model configuration")
        
        docker_client = self._get_docker_client()
        
        try:
            # Pull the Docker image if needed
            if source.get("pull", True):
                logger.info(f"Pulling Docker image: {image}")
                docker_client.images.pull(image)
            
            # Set up container configuration
            container_name = f"model_{model_key}_{os.getpid()}"
            host_port = source.get("host_port", 0)  # 0 means use a random port
            container_port = source.get("container_port", 8000)
            environment = source.get("environment", {})
            volumes = source.get("volumes", {})
            
            # Format volumes for Docker
            volume_binds = {}
            if volumes:
                for host_path, container_path in volumes.items():
                    volume_binds[host_path] = {"bind": container_path, "mode": "rw"}
            
            # Start the container
            container = docker_client.containers.run(
                image,
                name=container_name,
                detach=True,
                ports={f"{container_port}/tcp": host_port},
                environment=environment,
                volumes=volume_binds,
                remove=True  # Auto-remove when stopped
            )
            
            # Store the container reference
            self.model_processes[model_key] = {
                "container": container,
                "container_name": container_name
            }
            
            # Wait for the container to start up
            await asyncio.sleep(source.get("startup_delay", 5))
            
            # Get the assigned host port if we requested a random port
            if host_port == 0:
                container_info = docker_client.api.inspect_container(container.id)
                port_bindings = container_info["NetworkSettings"]["Ports"][f"{container_port}/tcp"]
                if port_bindings:
                    host_port = port_bindings[0]["HostPort"]
                else:
                    raise ModelError("Failed to get assigned host port for Docker container")
            
            # Update the model configuration with the host and port
            host = source.get("host", "localhost")
            
            # Copy the original model config and update it
            updated_config = model_config.copy()
            updated_config["endpoint"] = f"http://{host}:{host_port}{updated_config.get('endpoint', '/predict')}"
            
            logger.info(f"Started model server from Docker image at {updated_config['endpoint']}")
            
            return updated_config
            
        except Exception as e:
            logger.error(f"Failed to start model from Docker image: {str(e)}")
            raise ModelError(f"Failed to start model from Docker image: {str(e)}")
    
    async def _load_from_ecr(self, model_config: Dict[str, Any], model_key: str) -> Dict[str, Any]:
        """
        Load a model from an ECR repository.
        
        Args:
            model_config: The model configuration
            model_key: Unique key for the model
            
        Returns:
            Updated model configuration with runtime information
        """
        source = model_config.get("source", {})
        repository = source.get("repository")
        
        if not repository:
            raise ModelError("Missing ECR repository in model configuration")
        
        tag = source.get("tag", "latest")
        region = source.get("region", "us-east-1")
        
        try:
            # Get ECR client
            ecr_client = self._get_ecr_client(region)
            docker_client = self._get_docker_client()
            
            # Get the ECR login token
            token = ecr_client.get_authorization_token()
            username, password = self._decode_ecr_token(token)
            registry = token['authorizationData'][0]['proxyEndpoint']
            
            # Log in to ECR
            docker_client.login(
                username=username,
                password=password,
                registry=registry
            )
            
            # Full image name
            image = f"{registry}/{repository}:{tag}"
            
            # Pull the image
            logger.info(f"Pulling ECR image: {image}")
            docker_client.images.pull(image)
            
            # Now use the Docker loading mechanism
            model_config["source"]["image"] = image
            model_config["source"]["pull"] = False  # Already pulled
            
            return await self._load_from_docker(model_config, model_key)
            
        except Exception as e:
            logger.error(f"Failed to start model from ECR: {str(e)}")
            raise ModelError(f"Failed to start model from ECR: {str(e)}")
    
    def _decode_ecr_token(self, token: Dict[str, Any]) -> Tuple[str, str]:
        """
        Decode the ECR authorization token.
        
        Args:
            token: The authorization token response from ECR
            
        Returns:
            Username and password tuple
        """
        import base64
        auth_token = token['authorizationData'][0]['authorizationToken']
        decoded_token = base64.b64decode(auth_token).decode('utf-8')
        return decoded_token.split(':')
    
    async def unload_model(self, model_key: str) -> None:
        """
        Unload and stop a running model.
        
        Args:
            model_key: The unique key for the model
        """
        if model_key not in self.loaded_models:
            logger.warning(f"Model {model_key} not found in loaded models")
            return
        
        if model_key in self.model_processes:
            process_info = self.model_processes[model_key]
            
            try:
                # Check if it's a local process
                if "process" in process_info:
                    process = process_info["process"]
                    if process.poll() is None:  # Process is still running
                        process.terminate()
                        process.wait(timeout=10)  # Wait up to 10 seconds
                    
                    # Clean up logs
                    if os.path.exists(process_info["log_dir"]):
                        shutil.rmtree(process_info["log_dir"])
                
                # Check if it's a Docker container
                elif "container" in process_info:
                    container = process_info["container"]
                    container.stop(timeout=10)  # Stop with a timeout
            
            except Exception as e:
                logger.error(f"Error stopping model {model_key}: {str(e)}")
            
            # Remove from tracking
            del self.model_processes[model_key]
        
        # Remove from loaded models
        del self.loaded_models[model_key]
        logger.info(f"Unloaded model {model_key}")
    
    async def unload_all_models(self) -> None:
        """Unload and stop all running models."""
        model_keys = list(self.loaded_models.keys())
        for model_key in model_keys:
            await self.unload_model(model_key)