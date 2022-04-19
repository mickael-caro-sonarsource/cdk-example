from pathlib import Path

from cdkapp.config.schemas_config import ProjectConfig


class PathHelper:
    """Class helps with managing paths in this environment."""

    def __init__(self, project_config: ProjectConfig):
        """Constructor."""
        self.root_dir = project_config.ROOT_DIR

    def get_root_path(self):
        """Returns the absolute path of the root directory of this project."""
        return Path(self.root_dir).resolve()

    def get_cdk_out_path(self):
        """
        Get the local app / stack path.

        Returns the absolute path of the current app cdk.out directory.
        """
        return Path(".").joinpath("cdk.out").resolve()

    def get_cdk_path(self):
        """Returns the absolute path of the root cdk directory."""
        return self.get_root_path().joinpath("cdk")

    def get_userdata_path(self, file_name: str):
        """Returns the absolute path to directory containing the lambda for the given function."""
        return self.get_root_path().joinpath("files", "userdata", file_name)

    def get_full_path(self, path_from_root: str):
        """Returns the absolute path to directory containing the lambda for the given function."""
        return self.get_root_path().joinpath(path_from_root)

    def get_subdirectories(self, directory: str):
        """Return the sub directories of the given directory."""
        return self.get_root_path().joinpath(directory).glob("./*/")

    @staticmethod
    def get_file_content(file_path):
        """Get the content of a file as a string."""
        return Path(file_path).read_text()
