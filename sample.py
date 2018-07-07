import os
import json

from os import listdir
from os.path import isdir, isfile, join
from github import Github

repo = 'test-repo'
token = '586a50c289209e7996877bec419c042ddfdbf4d6'


def update_repo(scraper_name='Buildings'):
    gh = Github(token)
    user = gh.get_user()
    # repo = user.get_repo('test-repo')
    repo = None

    for r in user.get_repos():
        repo = r

    files = merge_files(scraper_name)

    for merged_file in files:
        # file = repo.get_file_contents('coastal.json')
        file = repo.get_file_contents(merged_file)

        # now we can manipulate like a regular JSON object
        data = json.loads(file.decoded_content)
        data['name'] = "Look at me, look at me. *I* am the captain now!"
        dc_new = json.dumps(data, indent=2, ensure_ascii=False)

        repo.update_file('/coastal.json', 'Bot commit', dc_new, file.sha)


def merge_files(filename, filepath='./dumps'):
    filepaths = []
    file_dir = './data'
    filepath = '{}/{}'.format(filepath, filename.lower())

    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    # checks if the filepath has any subdirectories or files.
    _, directories, files = next(os.walk(filepath))

    if directories:
        for directory in directories:
            path_in = '{}/{}'.format(filepath, directory)
            path_out = '{}/{}.json'.format(file_dir, directory)
            filepaths.append(path_out)

            files = [f for f in listdir(path_in) if isfile(join(path_in, f))]

            with open(path_out, 'w') as merged_file:
                for file in files:
                    with open('{}/{}'.format(path_in, file), 'r') as f:
                        merged_file.write(f.read())
    else:
        path_in = filepath
        path_out = '{}/{}.json'.format(file_dir, filename.lower())
        filepaths.append(path_out)

        with open(path_out, 'w') as merged_file:
            for file in files:
                with open('{}/{}'.format(path_in, file), 'r') as f:
                    merged_file.write(f.read())

    return filepaths


if __name__ == '__main__':
    update_repo('Courses')
    print('Done. Check your repo')