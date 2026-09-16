import shlex
from pathlib import Path, PurePosixPath

from harbor.agents.installed.base import BaseInstalledAgent, with_prompt_template
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trial.paths import EnvironmentPaths


class MyInstalledAgent(BaseInstalledAgent):
    REMOTE_DIR = "/opt/harbor/local-agent"
    OUTPUT_FILENAME = "local-agent.txt"
    SETUP_LOG_FILENAME = "setup.log"

    @staticmethod
    def name() -> str:
        return "local-openrouter-agent"

    def _logged_setup_command(self, command: str) -> str:
        setup_log_path = (
            PurePosixPath(EnvironmentPaths.agent_dir) / self.SETUP_LOG_FILENAME
        )
        quoted_log_path = shlex.quote(setup_log_path.as_posix())
        return (
            f"mkdir -p {shlex.quote(EnvironmentPaths.agent_dir.as_posix())} && "
            f"printf '\\n[setup] started_at: %s\\n' \"$(date -Iseconds)\" >> {quoted_log_path} && "
            f"printf '[setup] cwd: %s\\n' \"$PWD\" >> {quoted_log_path} && "
            f"printf '[setup] command: %s\\n' {shlex.quote(command)} >> {quoted_log_path} && "
            f"stdbuf -oL -eL sh -c {shlex.quote(command)} 2>&1 | tee -a {quoted_log_path}"
        )

    async def install(self, environment: BaseEnvironment) -> None:
        local_agent_dir = Path(__file__).parent

        await self.exec_as_root(environment, command=f"mkdir -p {self.REMOTE_DIR}")
        await environment.upload_dir(
            source_dir=local_agent_dir, target_dir=self.REMOTE_DIR
        )
        await self.exec_as_root(
            environment, command=f"chmod +x {self.REMOTE_DIR}/run.sh"
        )

    @with_prompt_template
    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        output_path = PurePosixPath(EnvironmentPaths.agent_dir) / self.OUTPUT_FILENAME
        env = {}
        if self.model_name:
            env["LOCAL_AGENT_MODEL"] = self.model_name

        openai_base_url = self._get_env("OPENAI_BASE_URL")
        if openai_base_url:
            env["OPENAI_BASE_URL"] = openai_base_url

        openai_api_key = self._get_env("OPENAI_API_KEY")
        if openai_api_key:
            env["OPENAI_API_KEY"] = openai_api_key

        await self.exec_as_agent(
            environment,
            command=(
                f"./run.sh {shlex.quote(instruction)} "
                f"2>&1 | tee {shlex.quote(output_path.as_posix())}"
            ),
            env=env,
            cwd=self.REMOTE_DIR,
        )

        context.metadata = {
            "remote_dir": self.REMOTE_DIR,
            "output_file": output_path.as_posix(),
        }

    def populate_context_post_run(self, context: AgentContext) -> None:
        pass
