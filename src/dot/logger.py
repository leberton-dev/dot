from dot.link_state import LinkState


class DotLogger:
    @staticmethod
    def error(command: str, cause: str) -> None:
        line = f"{command}.error: {cause}"
        print(line)
        # DotLogger.log_to_file(line, LOG_FILE)

    @staticmethod
    def debug(module: str, dest: str, state: LinkState, action: str) -> None:
        line = f"{f'{module}:':<10}{dest:<50} state={state.name} -> {action}"
        print(f"[DEBUG] {line}")

    @staticmethod
    def debug_line(line: str) -> None:
        print(f"[DEBUG] {line}")
