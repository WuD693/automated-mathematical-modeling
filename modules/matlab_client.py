"""
MATLAB MCP 客户端 — 通过 stdio JSON-RPC 与 MATLAB MCP Core Server 通信，
实现 Python → MATLAB 的绘图调用。

协议: MCP (Model Context Protocol) over stdio JSON-RPC 2.0
"""

import subprocess
import json
import threading
import queue
import time
import base64
import io
import os
from typing import Optional, Callable


class MatlabMCPClient:
    """
    MATLAB MCP 客户端。

    用法:
        client = MatlabMCPClient("D:\\路径\\matlab-mcp-core-server-win64.exe")
        client.start()
        img_bytes = client.call_tool("plot", {"x": [1,2,3], "y": [4,5,6]})
        client.stop()
    """

    def __init__(self, server_path: str, timeout: float = 60.0):
        self.server_path = server_path
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._pending: dict = {}
        self._response_queue = queue.Queue()
        self._reader_thread: Optional[threading.Thread] = None
        self._initialized = False

    # ---- lifecycle ----

    def start(self) -> bool:
        """启动 MCP 服务器并完成初始化握手"""
        try:
            self.process = subprocess.Popen(
                [self.server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # binary mode for base64 image transfer
                bufsize=0,
            )
        except FileNotFoundError:
            raise RuntimeError(f"找不到 MATLAB MCP 服务器: {self.server_path}")

        self._reader_thread = threading.Thread(target=self._read_responses, daemon=True)
        self._reader_thread.start()

        # MCP 初始化握手
        result = self._send_request("initialize", {
            "protocolVersion": "0.1.0",
            "clientInfo": {"name": "auto-math-model", "version": "1.0.0"},
            "capabilities": {},
        })
        if result is None:
            raise RuntimeError("MATLAB MCP 初始化失败：无响应")

        # 发送 initialized 通知
        self._send_notification("notifications/initialized", {})
        self._initialized = True
        return True

    def stop(self):
        """关闭 MCP 服务器连接"""
        self._initialized = False
        if self.process:
            try:
                self.process.stdin.close()
                self.process.stdout.close()
            except Exception:
                pass
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    # ---- public API ----

    def list_tools(self) -> list:
        """获取 MATLAB MCP 提供的所有工具列表"""
        result = self._send_request("tools/list", {})
        return result.get("tools", []) if result else []

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """调用 MATLAB 工具，返回结果 dict（可能包含 base64 图片数据）"""
        return self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })

    def plot_to_bytes(self, plot_code: str) -> Optional[bytes]:
        """执行 MATLAB 绘图代码并返回图片字节"""
        result = self.call_tool("execute", {"code": plot_code})
        if not result:
            return None

        # 检查是否有 base64 图片返回
        content = result.get("content", [])
        for item in content:
            if isinstance(item, dict) and item.get("type") == "image":
                return base64.b64decode(item["data"])
            if isinstance(item, dict) and "data" in item:
                return base64.b64decode(item["data"])
        return None

    def execute(self, code: str) -> Optional[str]:
        """执行 MATLAB 代码并返回文本输出"""
        result = self.call_tool("execute", {"code": code})
        if not result:
            return None
        content = result.get("content", [])
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return item["text"]
        return json.dumps(result)

    # ---- internals ----

    def _send_request(self, method: str, params: dict) -> Optional[dict]:
        """发送 JSON-RPC 请求并等待响应"""
        self._request_id += 1
        req_id = self._request_id

        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        self._send_message(request)

        # 等待响应
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                msg = self._response_queue.get(timeout=0.1)
                if msg.get("id") == req_id:
                    if "error" in msg:
                        raise RuntimeError(f"MATLAB MCP 错误: {msg['error']}")
                    return msg.get("result", {})
                else:
                    self._response_queue.put(msg)  # 放回队列
            except queue.Empty:
                continue
        raise TimeoutError(f"MATLAB MCP 请求超时: {method}")

    def _send_notification(self, method: str, params: dict):
        """发送 JSON-RPC 通知（无响应）"""
        self._send_message({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        })

    def _send_message(self, msg: dict):
        """发送 JSON-RPC 消息到服务器"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("MATLAB MCP 服务器未启动")
        line = json.dumps(msg, ensure_ascii=False) + "\n"
        self.process.stdin.write(line.encode("utf-8"))
        self.process.stdin.flush()

    def _read_responses(self):
        """后台线程：持续读取服务器 stdout 的响应"""
        if not self.process or not self.process.stdout:
            return
        try:
            for line in self.process.stdout:
                try:
                    msg = json.loads(line.decode("utf-8"))
                    self._response_queue.put(msg)
                except json.JSONDecodeError:
                    continue
        except (ValueError, OSError):
            pass  # 管道关闭


# ============================================================
# 单例工厂（复用进程，避免反复启动 MATLAB）
# ============================================================
_client: Optional[MatlabMCPClient] = None


def get_client(server_path: str | None = None) -> Optional[MatlabMCPClient]:
    """获取或创建 MATLAB MCP 客户端单例"""
    global _client
    if _client is None and server_path:
        _client = MatlabMCPClient(server_path)
        _client.start()
    return _client


def shutdown_client():
    """关闭全局客户端"""
    global _client
    if _client:
        _client.stop()
        _client = None
