"""LLM Agent 配置管理"""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentConfig:
    """Agent配置类"""
    # OpenAI配置
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    base_url: str = ""  # 自定义API地址，用于本地部署的LLM
    temperature: float = 0.2
    max_tokens: int = 8000  # 输出token限制，充分利用模型能力
    max_context_tokens: int = 128000  # 最大上下文token数，支持大上下文模型

    # Agent行为
    enabled: bool = True
    decision_interval: int = 300
    max_decisions_per_run: int = 5

    # 风控
    max_position_per_stock: float = 0.15
    min_confidence_threshold: float = 0.7

    @classmethod
    def from_env(cls, env_file: str = None) -> "AgentConfig":
        """从环境变量加载配置"""
        # 尝试加载.env文件
        if env_file and Path(env_file).exists():
            _load_env_file(env_file)
        else:
            # 尝试加载默认位置的.env
            default_env = Path(__file__).parent.parent.parent / ".env"
            if default_env.exists():
                _load_env_file(str(default_env))

        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            base_url=os.getenv("OPENAI_BASE_URL", ""),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "8000")),
            # 支持自定义最大token数（本地LLM通常需要更大）
            max_context_tokens=int(os.getenv("AGENT_MAX_CONTEXT_TOKENS", "128000")),
            enabled=os.getenv("AGENT_ENABLED", "false").lower() == "true",
            decision_interval=int(os.getenv("AGENT_DECISION_INTERVAL", "300")),
            max_decisions_per_run=int(os.getenv("AGENT_MAX_DECISIONS_PER_RUN", "5")),
            max_position_per_stock=float(os.getenv("AGENT_MAX_POSITION_PER_STOCK", "0.15")),
            min_confidence_threshold=float(os.getenv("AGENT_MIN_CONFIDENCE_THRESHOLD", "0.7"))
        )

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")
        return True

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "openai_model": self.openai_model,
            "base_url": self.base_url if self.base_url else "https://api.openai.com/v1",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_context_tokens": self.max_context_tokens,
            "enabled": self.enabled,
            "decision_interval": self.decision_interval,
            "max_decisions_per_run": self.max_decisions_per_run,
            "max_position_per_stock": self.max_position_per_stock,
            "min_confidence_threshold": self.min_confidence_threshold
        }


def _load_env_file(filepath: str):
    """手动加载.env文件（不依赖python-dotenv）"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                os.environ[key] = value.strip().strip('"').strip("'")
    except Exception as e:
        print(f"Warning: Failed to load env file {filepath}: {e}")
