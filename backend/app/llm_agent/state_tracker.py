"""
工作流状态追踪器

用于实时追踪AI分析工作流的执行状态，包括当前阶段、工具调用、详细响应等。
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import json


class WorkflowStatus(str, Enum):
    """工作流状态"""
    IDLE = "idle"           # 空闲
    RUNNING = "running"     # 运行中
    PAUSED = "paused"       # 已暂停
    COMPLETED = "completed" # 已完成
    FAILED = "failed"       # 失败


class PhaseStatus(str, Enum):
    """阶段状态"""
    PENDING = "pending"     # 待执行
    RUNNING = "running"     # 执行中
    COMPLETED = "completed" # 已完成
    SKIPPED = "skipped"     # 已跳过
    FAILED = "failed"       # 失败


@dataclass
class ToolCall:
    """工具调用记录"""
    tool_name: str
    parameters: Dict[str, Any]
    status: str = "pending"  # pending, running, success, failed
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms
        }


@dataclass
class PhaseExecution:
    """阶段执行记录"""
    phase: str
    status: PhaseStatus = PhaseStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: Optional[int] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    summary: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "phase": self.phase,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "summary": self.summary,
            "error": self.error
        }


@dataclass
class WorkflowRun:
    """工作流运行记录"""
    run_id: str
    status: WorkflowStatus = WorkflowStatus.IDLE
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[int] = None
    phases: Dict[str, PhaseExecution] = field(default_factory=dict)
    current_phase: Optional[str] = None
    current_tool: Optional[str] = None
    total_tokens: int = 0
    total_cost: float = 0.0
    decisions: List[Dict] = field(default_factory=list)
    llm_responses: List[Dict] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "phases": {k: v.to_dict() for k, v in self.phases.items()},
            "current_phase": self.current_phase,
            "current_tool": self.current_tool,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "decisions": self.decisions,
            "llm_responses": self.llm_responses,
            "error": self.error
        }


class WorkflowStateTracker:
    """工作流状态追踪器（单例模式）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.current_run: Optional[WorkflowRun] = None
        self.run_history: List[WorkflowRun] = []
        self.max_history = 10
        self._state_lock = threading.Lock()

    def start_run(self, run_id: Optional[str] = None) -> str:
        """开始新的工作流运行"""
        with self._state_lock:
            if run_id is None:
                run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.current_run = WorkflowRun(run_id=run_id)
            self.current_run.status = WorkflowStatus.RUNNING

            # 初始化三个阶段
            for phase in ["explore", "decide", "evaluate"]:
                self.current_run.phases[phase] = PhaseExecution(phase=phase)

            return run_id

    def end_run(self, status: WorkflowStatus = WorkflowStatus.COMPLETED, error: Optional[str] = None):
        """结束当前运行"""
        with self._state_lock:
            if self.current_run is None:
                return

            self.current_run.status = status
            self.current_run.end_time = time.time()
            self.current_run.duration_ms = int((self.current_run.end_time - self.current_run.start_time) * 1000)

            if error:
                self.current_run.error = error

            # 添加到历史记录
            self.run_history.append(self.current_run)
            if len(self.run_history) > self.max_history:
                self.run_history.pop(0)

            self.current_run = None

    def start_phase(self, phase: str):
        """开始执行阶段"""
        with self._state_lock:
            if self.current_run is None:
                return

            self.current_run.current_phase = phase
            if phase in self.current_run.phases:
                self.current_run.phases[phase].status = PhaseStatus.RUNNING
                self.current_run.phases[phase].start_time = time.time()

    def end_phase(self, phase: str, status: PhaseStatus = PhaseStatus.COMPLETED,
                  summary: Optional[str] = None, error: Optional[str] = None):
        """结束阶段执行"""
        with self._state_lock:
            if self.current_run is None:
                return

            if phase in self.current_run.phases:
                phase_exec = self.current_run.phases[phase]
                phase_exec.status = status
                phase_exec.end_time = time.time()
                phase_exec.duration_ms = int((phase_exec.end_time - phase_exec.start_time) * 1000) if phase_exec.start_time else None
                phase_exec.summary = summary
                phase_exec.error = error

    def start_tool(self, phase: str, tool_name: str, parameters: Dict) -> ToolCall:
        """开始工具调用"""
        with self._state_lock:
            if self.current_run is None:
                return ToolCall(tool_name=tool_name, parameters=parameters)

            self.current_run.current_tool = tool_name

            if phase in self.current_run.phases:
                tool_call = ToolCall(tool_name=tool_name, parameters=parameters)
                tool_call.status = "running"
                self.current_run.phases[phase].tool_calls.append(tool_call)
                return tool_call

            return ToolCall(tool_name=tool_name, parameters=parameters)

    def end_tool(self, phase: str, tool_name: str, result: Optional[Dict] = None,
                 error: Optional[str] = None):
        """结束工具调用"""
        with self._state_lock:
            if self.current_run is None:
                return

            if phase in self.current_run.phases:
                for tool_call in reversed(self.current_run.phases[phase].tool_calls):
                    if tool_call.tool_name == tool_name and tool_call.status == "running":
                        tool_call.end_time = time.time()
                        tool_call.duration_ms = int((tool_call.end_time - tool_call.start_time) * 1000)
                        tool_call.result = result
                        tool_call.error = error
                        tool_call.status = "success" if error is None else "failed"
                        break

            self.current_run.current_tool = None

    def add_llm_response(self, phase: str, response: Dict):
        """添加LLM响应记录"""
        with self._state_lock:
            if self.current_run is None:
                return

            self.current_run.llm_responses.append({
                "phase": phase,
                "timestamp": time.time(),
                **response
            })

    def add_decision(self, decision: Dict):
        """添加决策记录"""
        with self._state_lock:
            if self.current_run is None:
                return

            self.current_run.decisions.append(decision)

    def update_tokens(self, prompt_tokens: int, completion_tokens: int, cost: float):
        """更新Token统计"""
        with self._state_lock:
            if self.current_run is None:
                return

            self.current_run.total_tokens += prompt_tokens + completion_tokens
            self.current_run.total_cost += cost

    def get_state(self) -> Dict:
        """获取当前状态"""
        with self._state_lock:
            if self.current_run is None:
                return {
                    "status": "idle",
                    "current_run": None,
                    "recent_runs": [r.to_dict() for r in self.run_history[-5:]]
                }

            return {
                "status": "running",
                "current_run": self.current_run.to_dict(),
                "recent_runs": [r.to_dict() for r in self.run_history[-5:]]
            }

    def get_current_run(self) -> Optional[WorkflowRun]:
        """获取当前运行"""
        with self._state_lock:
            return self.current_run

    def is_running(self) -> bool:
        """检查是否有运行中的工作流"""
        with self._state_lock:
            return self.current_run is not None and self.current_run.status == WorkflowStatus.RUNNING


# 全局状态追踪器实例
workflow_tracker = WorkflowStateTracker()