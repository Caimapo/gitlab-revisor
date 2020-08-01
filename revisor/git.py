import logging
import os
import sys
import subprocess
import git
import yaml
import csv
import random
from gitlab import Gitlab, GitlabError, GitlabAuthenticationError
from progress import ProgressBar
import concurrent.futures

log = logging.getLogger(__name__)

progress = ProgressBar('* syncing projects')
emo = ["\U0001F331",'\U0001F332', '\U0001F333', '\U0001F334', '\U0001F335','\U0001F33E', '\U0001F33F', '\U0001F340', '\U0001F341']
gitlab_keywords = ["image", "services", "stages", "types", "before_script", "after_script", "variables", "cache", "include" ]
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
def dump_to_csv(project, path, url, lang, step):
    try:
      with open(path, newline='', mode='a') as file:
          writer = csv.writer(file, delimiter=',')
          writer.writerow([project, url, lang, step])
    except Exception as e:
        log.info("Error trying to openning the file output\nmsg:{}".format(sys.exc_info()))

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


def alter_cicd(file, url):
    yaml_file=yaml.safe_load(file.decode().decode('utf-8'))
    print("\n")
    if (yaml_file["include"][0]["file"] == "/all-in-one/all-cicd-javaGradle-whmg-on-prem.yml"):
        print("\n+{}".format(url))
        yaml_file=add_security_steps(yaml_file, 'java')

    if (yaml_file["include"][0]["file"] == "/all-in-one/all-cicd-nodejs-npm-whmg-on-prem.yml"):
        print("\n+{}".format(url))
        yaml_file=add_security_steps(yaml_file, 'node')
    if (yaml_file["include"][0]["file"] == "/all-in-one/all-cicd-nodejs-npm-whmg.yml"):
        print("\n+{}".format(url))
        yaml_file=add_security_steps(yaml_file, 'node')
    print("\n ---")
    dump_file=yaml.safe_dump(
        yaml_file, default_flow_style=False, sort_keys=False)
    print(dump_file)
    print("\n ---")
    return dump_file


def add_security_steps(data, lang):
    data["detect_secrets"]={
        'extends': '.detect_secrets_seecas',
        'variables': [
        {
            'SECAAS_PLUGIN_ID': '$SECAAS_PLUGIN_ID',
            'SECAAS_PLUGIN_SECRET': '$SECAAS_PLUGIN_SECRET',
            'BUSINESS': '$SECAAS_BUSINESS_ID',
        }
    ],
        'only': {
            'refs': ['devsecops']
        }
    }
    data["dependency_scanning"]={
    'extends': '.dependency_cli_secaas',
    'variables': [
        {
            'DC_TARGET_LANG': lang,
            'SECAAS_PLUGIN_ID': '$SECAAS_PLUGIN_ID',
            'SECAAS_PLUGIN_SECRET': '$SECAAS_PLUGIN_SECRET',
            'BUSINESS': '$SECAAS_BUSINESS_ID',
        }
    ],
    'only': {
        'refs': ['devsecops']
        }
    }
    data["sast_scanning"]={
    'extends': '.veracode_{lang}'.format(lang=lang),
    'variables': [{
            'DC_TARGET_LANG': lang,
            'VERSION': '$CI_PROJECT_NAME-$CI_PROJECT_NAMESPACE-$CI_JOB_ID',
            'SECAAS_PLUGIN_ID': '$SECAAS_PLUGIN_ID',
            'SECAAS_PLUGIN_SECRET': '$SECAAS_PLUGIN_SECRET',
            'BUSINESS': '$SECAAS_BUSINESS_ID',
            'SANDBOX_NAME': '${CI_PROJECT_NAME}-${CI_PROJECT_NAMESPACE}',
            'PROJECT': '${CI_PROJECT_NAME}-${CI_PROJECT_NAMESPACE}',
            'BRANCH': '$CI_COMMIT_REF_SLUG'
        }],
    'only': {
        'refs': ['devsecops']
        }
    }
    return data

def pull_project_ci_file(action):
    if is_git_repo(action.path):
        '''
        Update existing project
        '''
        log.debug("updating existing project {}".format(action.path))
        progress.show_progress(action.node.name, 'pull')
        try:
            repo=git.Repo(action.path)
            repo.remotes.origin.pull()
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error pulling project {}".format(
                action.path), exc_info=True)


def clone_or_pull_project(action):
    if is_git_repo(action.path):
        '''
        Update existing project
        '''
        log.debug("updating existing project {}".format(action.path))
        progress.show_progress(action.node.name, 'pull')
        try:
            repo=git.Repo(action.path)
            repo.remotes.origin.pull()
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error pulling project {}".format(
                action.path), exc_info=True)
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
            log.debug("Error cloning project {}".format(
                action.path), exc_info=True)
