#!/usr/bin/env python3
"""
DockerClient Docker控制工具 - 镜像构建、容器管理、编排部署
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import subprocess
import json


class ContainerStatus(Enum):
    """容器状态"""
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    RESTARTING = "restarting"
    EXITED = "exited"
    DEAD = "dead"


@dataclass
class ContainerInfo:
    """容器信息"""
    id: str
    name: str
    image: str
    status: ContainerStatus
    ports: List[str]
    created: str


@dataclass
class ImageInfo:
    """镜像信息"""
    id: str
    tags: List[str]
    size: str
    created: str


class DockerClient:
    """Docker 客户端封装"""
    
    def __init__(self):
        self.name = "docker_client"
        self.description = "Docker 容器管理：镜像构建、容器编排、部署运维"
        self.docker_executable = "docker"
        self.compose_executable = "docker-compose"
    
    def run_command(self, executable: str, *args, timeout: int = 60) -> tuple[int, str, str]:
        """执行 Docker 命令
        
        Args:
            executable: docker 或 docker-compose
            args: 命令参数
            timeout: 超时时间
            
        Returns:
            (exit_code, stdout, stderr)
        """
        cmd = [executable] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except FileNotFoundError:
            return -1, "", f"{executable} not found. Is Docker installed?"
        except Exception as e:
            return -1, "", str(e)
    
    def is_docker_running(self) -> bool:
        """检查 Docker 是否运行"""
        exit_code, _, _ = self.run_command(self.docker_executable, "info")
        return exit_code == 0
    
    # ==================== 镜像操作 ====================
    
    def image_list(self, all: bool = False) -> List[ImageInfo]:
        """列出镜像"""
        args = ["images", "--format", "{{.ID}}|{{.Repository}}:{{.Tag}}|{{.Size}}|{{.CreatedAt}}"]
        if all:
            args.append("-a")
        
        exit_code, stdout, stderr = self.run_command(self.docker_executable, *args)
        if exit_code != 0:
            return []
        
        images = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            
            parts = line.split("|")
            if len(parts) >= 4:
                tags = parts[1].split(",") if "," in parts[1] else [parts[1]]
                images.append(ImageInfo(
                    id=parts[0],
                    tags=tags,
                    size=parts[2],
                    created=parts[3]
                ))
        
        return images
    
    def build_image(self, tag: str, path: str = ".", 
                    dockerfile: str = None, no_cache: bool = False,
                    pull: bool = False) -> Dict:
        """构建镜像
        
        Args:
            tag: 镜像标签，如 'myapp:v1.0'
            path: 构建上下文路径
            dockerfile: Dockerfile 路径
            no_cache: 不使用缓存
            pull: 总是拉取基础镜像
        """
        args = ["build"]
        if no_cache:
            args.append("--no-cache")
        if pull:
            args.append("--pull")
        if dockerfile:
            args.extend(["-f", dockerfile])
        args.extend(["-t", tag, path])
        
        exit_code, stdout, stderr = self.run_command(self.docker_executable, *args, timeout=300)
        return {
            "status": "success" if exit_code == 0 else "error",
            "output": stdout,
            "error": stderr if exit_code != 0 else None,
            "image_tag": tag
        }
    
    def pull_image(self, image: str) -> Dict:
        """拉取镜像"""
        exit_code, stdout, stderr = self.run_command(
            self.docker_executable, "pull", image, timeout=120
        )
        return {
            "status": "success" if exit_code == 0 else "error",
            "output": stdout,
            "error": stderr if exit_code != 0 else None
        }
    
    def push_image(self, image: str) -> Dict:
        """推送镜像"""
        exit_code, stdout, stderr = self.run_command(
            self.docker_executable, "push", image, timeout=180
        )
        return {
            "status": "success" if exit_code == 0 else "error",
            "output": stdout,
            "error": stderr if exit_code != 0 else None
        }
    
    def remove_image(self, image: str, force: bool = False) -> Dict:
        """删除镜像"""
        args = ["rmi", image]
        if force:
            args.insert(1, "-f")
        
        exit_code, stdout, stderr = self.run_command(self.docker_executable, *args)
        return {
            "status": "success" if exit_code == 0 else "error",
            "message": stdout if exit_code == 0 else stderr
        }
    
    # ==================== 容器操作 ====================
    
    def container_list(self, all: bool = True) -> List[ContainerInfo]:
        """列出容器"""
        args = ["ps", "--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.CreatedAt}}"]
        if all:
            args.insert(1, "-a")
        
        exit_code, stdout, stderr = self.run_command(self.docker_executable, *args)
        if exit_code != 0:
            return []
        
        containers = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            
            parts = line.split("|")
            if len(parts) >= 5:
                status_str = parts[3].lower()
                if "up" in status_str:
                    status = ContainerStatus.RUNNING
                elif "exited" in status_str:
                    status = ContainerStatus.EXITED
                elif "paused" in status_str:
                    status = ContainerStatus.PAUSED
                else:
                    status = ContainerStatus.STOPPED
                
                containers.append(ContainerInfo(
                    id=parts[0][:12],
                    name=parts[1],
                    image=parts[2],
                    status=status,
                    ports=parts[4].split(",") if parts[4] else [],
                    created=parts[5]
                ))
        
        return containers
    
    def run_container(self, image: str, name: str = None,
                       ports: Dict[str, str] = None,
                       volumes: Dict[str, str] = None,
                       env: Dict[str, str] = None,
                       detach: bool = True,
                       remove: bool = False,
                       command: str = None) -> Dict:
        """运行容器
        
        Args:
            image: 镜像名称
            name: 容器名称
            ports: 端口映射 {'8080': '80'}
            volumes: 卷映射 {'/host/path': '/container/path'}
            env: 环境变量
            detach: 后台运行
            remove: 停止后删除
            command: 启动命令
        """
        args = ["run", "-d"] if detach else ["run"]
        
        if name:
            args.extend(["--name", name])
        if remove:
            args.append("--rm")
        
        for host_port, container_port in (ports or {}).items():
            args.extend(["-p", f"{host_port}:{container_port}"])
        
        for host_path, container_path in (volumes or {}).items():
            args.extend(["-v", f"{host_path}:{container_path}"])
        
        for key, value in (env or {}).items():
            args.extend(["-e", f"{key}={value}"])
        
        args.append(image)
        if command:
            args.extend(command.split())
        
        exit_code, stdout, stderr = self.run_command(self.docker_executable, *args, timeout=60)
        return {
            "status": "success" if exit_code == 0 else "error",
            "container_id": stdout.strip()[:12] if exit_code == 0 else None,
            "error": stderr if exit_code != 0 else None
        }
    
    def stop_container(self, container: str, timeout: int = 10) -> Dict:
        """停止容器"""
        exit_code, stdout, stderr = self.run_command(
            self.docker_executable, "stop", "-t", str(timeout), container
        )
        return {
            "status": "success" if exit_code == 0 else "error",
            "message": stdout if exit_code == 0 else stderr
        }
    
    def start_container(self, container: str) -> Dict:
        """启动容器"""
        exit_code, stdout, stderr = self.run_command(
            self.docker_executable, "start", container
        )
        return {
            "status": "success" if exit_code == 0 else "error",
            "message": stdout if exit_code == 0 else stderr
        }
    
    def remove_container(self, container: str, force: bool = False) -> Dict:
        """删除容器"""
        args = ["rm"]
        if force:
            args.append("-f")
        args.append(container)
        
        exit_code, stdout, stderr = self.run_command(self.docker_executable, *args)
        return {
            "status": "success" if exit_code == 0 else "error",
            "message": stdout if exit_code == 0 else stderr
        }
    
    def logs(self, container: str, tail: int = 100, follow: bool = False) -> str:
        """查看容器日志"""
        args = ["logs"]
        args.extend(["--tail", str(tail)])
        if follow:
            args.append("-f")
        args.append(container)
        
        exit_code, stdout, stderr = self.run_command(self.docker_executable, *args)
        return stdout + stderr
    
    def inspect(self, container: str) -> Dict:
        """获取容器详情"""
        exit_code, stdout, stderr = self.run_command(
            self.docker_executable, "inspect", container
        )
        if exit_code == 0 and stdout:
            try:
                return {"status": "success", "data": json.loads(stdout)[0]}
            except:
                pass
        return {"status": "error", "message": stderr}
    
    # ==================== Docker Compose ====================
    
    def compose_up(self, file: str = None, detach: bool = True,
                   scale: Dict[str, int] = None) -> Dict:
        """启动 Compose 服务"""
        args = ["-f", file] if file else []
        args.append("up")
        if detach:
            args.append("-d")
        if scale:
            for service, count in scale.items():
                args.extend(["--scale", f"{service}={count}"])
        
        exit_code, stdout, stderr = self.run_command(
            self.compose_executable, *args, timeout=120
        )
        return {
            "status": "success" if exit_code == 0 else "error",
            "output": stdout,
            "error": stderr if exit_code != 0 else None
        }
    
    def compose_down(self, file: str = None, remove_volumes: bool = False) -> Dict:
        """停止 Compose 服务"""
        args = ["-f", file] if file else []
        args.append("down")
        if remove_volumes:
            args.append("-v")
        
        exit_code, stdout, stderr = self.run_command(
            self.compose_executable, *args, timeout=60
        )
        return {
            "status": "success" if exit_code == 0 else "error",
            "output": stdout,
            "error": stderr if exit_code != 0 else None
        }
    
    def compose_ps(self, file: str = None) -> List[Dict]:
        """查看 Compose 服务状态"""
        args = ["-f", file] if file else []
        args.extend(["ps", "--format", "json"])
        
        exit_code, stdout, stderr = self.run_command(
            self.compose_executable, *args
        )
        if exit_code == 0 and stdout:
            try:
                # 每行一个 JSON 对象
                return [json.loads(line) for line in stdout.strip().split("\n") if line]
            except:
                pass
        return []


def main(action: str, **kwargs) -> Dict:
    """主入口函数"""
    client = DockerClient()
    
    # 检查 Docker 是否运行
    if not kwargs.get("skip_check") and not client.is_docker_running():
        return {"status": "error", "message": "Docker is not running"}
    
    handlers = {
        # 镜像操作
        "image_list": lambda: {"images": [
            {"id": i.id, "tags": i.tags, "size": i.size}
            for i in client.image_list()
        ]},
        "build": lambda: client.build_image(
            kwargs.get("tag"), kwargs.get("path", "."),
            kwargs.get("dockerfile"), kwargs.get("no_cache", False)
        ),
        "pull": lambda: client.pull_image(kwargs.get("image")),
        "push": lambda: client.push_image(kwargs.get("image")),
        "rmi": lambda: client.remove_image(kwargs.get("image"), kwargs.get("force", False)),
        
        # 容器操作
        "ps": lambda: {"containers": [
            {"id": c.id, "name": c.name, "image": c.image, "status": c.status.value}
            for c in client.container_list()
        ]},
        "run": lambda: client.run_container(
            kwargs.get("image"), kwargs.get("name"),
            kwargs.get("ports"), kwargs.get("volumes"),
            kwargs.get("env"), kwargs.get("detach", True),
            kwargs.get("remove", False), kwargs.get("command")
        ),
        "stop": lambda: client.stop_container(kwargs.get("container"), kwargs.get("timeout", 10)),
        "start": lambda: client.start_container(kwargs.get("container")),
        "rm": lambda: client.remove_container(kwargs.get("container"), kwargs.get("force", False)),
        "logs": lambda: {"logs": client.logs(kwargs.get("container"), kwargs.get("tail", 100))},
        "inspect": lambda: client.inspect(kwargs.get("container")),
        
        # Compose 操作
        "compose_up": lambda: client.compose_up(kwargs.get("file"), kwargs.get("detach", True)),
        "compose_down": lambda: client.compose_down(kwargs.get("file"), kwargs.get("remove_volumes", False)),
        "compose_ps": lambda: {"services": client.compose_ps(kwargs.get("file"))},
    }
    
    if action not in handlers:
        return {"status": "error", "message": f"Unknown action: {action}"}
    
    return handlers[action]()


if __name__ == "__main__":
    # 测试代码
    result = main("ps", skip_check=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
