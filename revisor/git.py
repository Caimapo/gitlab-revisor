import logging
import os
import sys
import subprocess
import git
import yaml
from gitlab import Gitlab, GitlabError, GitlabAuthenticationError
from progress import ProgressBar
import concurrent.futures

log = logging.getLogger(__name__)

progress = ProgressBar('* syncing projects')


class GitAction:
    def __init__(self, node, path):
        self.node = node
        self.path = path


def sync_action(root, action, dest, concurrency=1, disable_progress=False):
    if not disable_progress:
        progress.init_progress(len(root.leaves))
    actions = get_git_actions(root, dest)
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        if action == 'print':
            executor.map(PRINT, actions)
        if action == 'create_branch':
            executor.map(create_security_branch, actions)
        if action == 'clone':
            executor.map(clone_or_pull_project, actions)
        else:
            executor.map(PRINT, actions)

    elapsed = progress.finish_progress()
    log.debug("Syncing projects took [{}]".format(elapsed))


def PRINT():
    print("To do")


def get_git_actions(root, dest):
    actions = []
    for child in root.children:
        path = "{0}{1}".format(dest, child.root_path)
        if not os.path.exists(path):
            os.makedirs(path)
        if child.is_leaf:
            actions.append(GitAction(child, path))
        if not child.is_leaf:
            actions.extend(get_git_actions(child, dest))
    return actions


def is_git_repo(path):
    try:
        x = git.Repo(path).git_dir
        print(x)
        return True
    except git.InvalidGitRepositoryError:
        print('ero')
        return False


def is_gitlab_project(node):
    return True if node.id > 0 else False


def create_security_branch(action):
    if is_gitlab_project(action.node):
        '''
        Update existing project with a new branch in site
        '''
        gitlab = Gitlab(os.environ.get('GITLAB_URL'), private_token=os.environ.get('GITLAB_URL'))
        ref = 'master'
        log.debug("updating existing project {}".format(action.path))
        progress.show_progress(action.node.name, 'creating branch')
        try:
            gitlab = Gitlab(os.environ.get('GITLAB_URL'), private_token=os.environ.get('GITLAB_TOKEN'))
            log.debug("Creating branch security in project id: [{}]".format(action.node.id))
            project = gitlab.projects.get(action.node.id)
            # repo = project.branches.create(
            #     {'branch': 'security', 'ref': ref})
            # project.branches.delete('security')
            try:
                try:
                    cicd = project.files.get(file_path='.gitlab-ci.yml', ref=ref)
                except:
                    log.info("file doesnt exist {}".format(sys.exc_info()))
                     
                cicd.content = alter_cicd(cicd.content)
                cicd.save(branch='security', commit_message='Update testfile .gitlab-ci.yml from batch update')
                log.debug(cicd)
            except :
                log.fatal(sys.exc_info())
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except :
            log.fatal(sys.exc_info())    

def alter_cicd(file):
    return file

def pull_project_ci_file(action):
    if is_git_repo(action.path):
        '''
        Update existing project
        '''
        log.debug("updating existing project {}".format(action.path))
        progress.show_progress(action.node.name, 'pull')
        try:
            repo = git.Repo(action.path)
            repo.remotes.origin.pull()
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error pulling project {}".format(action.path), exc_info=True)

def clone_or_pull_project(action):
    if is_git_repo(action.path):
        '''
        Update existing project
        '''
        log.debug("updating existing project {}".format(action.path))
        progress.show_progress(action.node.name, 'pull')
        try:
            repo = git.Repo(action.path)
            repo.remotes.origin.pull()
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error pulling project {}".format(action.path), exc_info=True)
    else:
        '''
        Clone new project
        '''
        log.debug("cloning new project {}".format(action.path))
        progress.show_progress(action.node.name, 'clone')
        try:
            git.Repo.clone_from(action.node.url, action.path)
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error cloning project {}".format(action.path), exc_info=True)
