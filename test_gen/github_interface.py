from dataclasses import dataclass

from github import Github


@dataclass
class GitHubInterface:
    """Wrapper for GitHub API."""

    github: Github
    github_repository: str
    github_branch: str | None = None
    github_base_branch: str | None = None
    
    def get_status(self) -> str:
        """
        Gets the status of the GitHub interface. 
        This method is not for the model to be used but its for giving the assistant 
        the context at the start of the conversation.
        Returns:
            str: The status of the GitHub interface
        """
        try:
            commits = list(self.github_repo_instance.get_commits())
        except Exception as e:
            print(e)
            commits = []
        
        if len(commits) > 10:
            commits = commits[-10:]
        
        return {
            "github_repository": self.github_repository,
            "github_branch": self.github_branch,
            "github_base_branch": self.github_base_branch,
            "files": self.get_files(),
            "commit_history": commits,
        }
        
    def get_files(self, path=""):
        """
        Gets all the files in the repository, including those in subdirectories.
        Returns:
            List[str]: The files in the repository
        """
        files = []
        try:
            contents = self.github_repo_instance.get_contents(path)
        except Exception as e:
            print(e)
            contents = []

        for content in contents:
            if content.type == "dir":
                files.extend(self.get_files(content.path))
            else:
                files.append(content.path)

        return files
    
    @classmethod
    def from_github_token(cls, github_token: str, repository: str, **kwargs) -> "GitHubInterface":
        """
        Creates a GitHubInterface from a GitHub token
        Parameters:
            github_token(str): The GitHub token
        Returns:
            GitHubInterface: The GitHubInterface object
        """
        github = Github(github_token)
        return cls(github=github, github_repository=repository, **kwargs)
    
    def __post_init__(self):
        self.github_repo_instance = self.github.get_repo(self.github_repository)
        # default value for branch is main
        if self.github_branch is None:
            self.github_branch = "main"
        # default value for base branch is main
        if self.github_base_branch is None:
            self.github_base_branch = "main"
        
    def create_branch(self, branch_name: str) -> str:
        """
        Creates a new branch from the working branch
        Parameters:
            branch_name(str): The name of the new branch
        Returns:
            str: A success or failure message
        """
        # check if branch exists
        try:
            self.github_repo_instance.get_branch(branch_name)
            return f"Branch {branch_name} already exists"
        except Exception as e:
            # create branch
            self.github_repo_instance.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=self.github_repo_instance.get_branch(self.github_branch).commit.sha,
            )
            self.github_branch = branch_name
            return f"Successfully created branch {branch_name}"
    
    def get_current_branch(self) -> str:
        """
        Gets the current branch
        Returns:
            str: The current branch
        """
        return self.github_branch

    def create_pull_request(self, pr_query: str) -> str:
        """
        Makes a pull request from the bot's branch to the base branch
        Parameters:
            pr_query(str): a string which contains the PR title
            and the PR body. The title is the first line
            in the string, and the body are the rest of the string.
            For example, "Updated README\nmade changes to add info"
        Returns:
            str: A success or failure message
        """
        if self.github_base_branch == self.github_branch:
            return """Cannot make a pull request because 
            commits are already in the master branch"""
        else:
            try:
                title = pr_query.split("\n")[0]
                body = pr_query[len(title) + 2 :]
                pr = self.github_repo_instance.create_pull(
                    title=title,
                    body=body,
                    head=self.github_branch,
                    base=self.github_base_branch,
                )
                return f"Successfully created PR number {pr.number}"
            except Exception as e:
                return "Unable to make pull request due to error:\n" + str(e)
    
    def file_exists(self, file_path):
        try:
            self.github_repo_instance.get_contents(file_path)
            return True
        except Exception as e:
            print(type(e))
            return False

    def create_file(self, file_path: str, file_contents: str) -> str:
        """
        Creates a new file on the Github repo
        Parameters:
            file_path (str): The path to the file to be created
            file_contents (str): The contents of the file
        Returns:
            str: A success or failure message
        """
        try:
            if not self.file_exists(file_path):
                self.github_repo_instance.create_file(
                    path=file_path,
                    message="Create " + file_path,
                    content=file_contents,
                    branch=self.github_branch,
                )
                return "Created file " + file_path
            else:
                return f"File already exists at {file_path}. Use update_file instead"
        except Exception as e:
            print(e)
            return "Unable to make file due to error:\n" + str(e)

    def read_file(self, file_path: str) -> str:
        """
        Reads a file from the github repo
        Parameters:
            file_path(str): the file path
        Returns:
            str: The file decoded as a string
        """
        try:
            file = self.github_repo_instance.get_contents(file_path)
        except Exception as e:
            print(e)
            return "Unable to read file due to error:\n" + str(e)
        return file.decoded_content.decode("utf-8")

    def update_file(self, file_path: str, file_contents: dict[str, str], **kwargs) -> str:
        """
        Updates a file with new content.
        Parameters:
            file_path(str): The path to the file to be updated
            file_contents(docs): The file contents.
                The old file contents is the dict key
                The new file contents is associated with the dict value.
                If no replacement is needed the key will be empty.
                For example:
                /test/hello.txt
                { "Hello Earth!": "Hello Mars!" }
                it will replace "Hello Earth!" with "Hello Mars!"
        Returns:
            A success or failure message
        """
        if kwargs:
            print(f"Warning: extra kwargs detected: {kwargs}")
        try:
            if not self.file_exists(file_path):
                raise FileExistsError(f"File does not exist at {file_path}. Use create_file instead")
            file_content = self.read_file(file_path)

            for old_file_contents, new_file_contents in file_contents.items():
                if old_file_contents:
                    updated_file_content = file_content.replace(
                        old_file_contents, new_file_contents
                    )
                else:
                    updated_file_content = file_content + "\n\n" + new_file_contents

                self.github_repo_instance.update_file(
                    path=file_path,
                    message="Update " + file_path,
                    content=updated_file_content,
                    branch=self.github_branch,
                    sha=self.github_repo_instance.get_contents(file_path).sha,
                )
            
            if not self.file_exists(file_path):
                return f"File does not exist at {file_path}. Use create_file instead"
            
            file_content = self.read_file(file_path)
            updated_file_content = file_content.replace(
                old_file_contents, new_file_contents
            )

            if file_content == updated_file_content:
                return (
                    "File content was not updated because old content was not found."
                    "It may be helpful to use the read_file action to get "
                    "the current file contents."
                )

            self.github_repo_instance.update_file(
                path=file_path,
                message="Update " + file_path,
                content=updated_file_content,
                branch=self.github_branch,
                sha=self.github_repo_instance.get_contents(file_path).sha,
            )
            return "Updated file " + file_path
        except IndexError:
            print(file_contents)
            return "Unable to update file because the file contents were not formatted correctly."
        except Exception as e:
            print(e)
            return "Unable to update file due to error:\n" + str(e)
