from typing import Protocol


class VideoProviderProtocol(Protocol):
    def generate_video(self, prompt: str) -> str:
        ...


class RunwayVideoProvider:
    def generate_video(self, prompt: str) -> str:
        raise NotImplementedError("Runway integration is implemented after the pipeline spine.")

