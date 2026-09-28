
from flask import Flask, request, jsonify

import subprocess

import os

import shutil

import git



app = Flask(__name__)



GITHUB_TOKEN = "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"

REPO_URL = f"https://20eva:{GITHUB_TOKEN}@github.com/20eva/pfe-linsoft.git"



@app.route('/health')

def health():

    return jsonify({'status': 'ok', 'model': 'Detection & Recommendation Model'})



@app.route('/scan', methods=['POST'])

def scan():

    data = request.json

    branch = data.get('branch', 'playbooks')

    threshold = data.get('threshold', 0.85)



    # Clone playbooks

    playbooks_path = '/tmp/playbooks-scan'

    try:

        if os.path.exists(playbooks_path):

            shutil.rmtree(playbooks_path)

        git.Repo.clone_from(REPO_URL, playbooks_path, branch=branch)

    except Exception as e:

        return jsonify({'error': f'Clone failed: {e}'}), 500



    # Run scan

    result = subprocess.run(

        ['python', 'scan_playbook.py', playbooks_path, '--model', '/app/detector_model_group_split.joblib', '--vectorizer', '/app/detector_vectorizer_group_split.joblib',

         '--threshold', str(threshold)],

        capture_output=True, text=True, cwd='/app'

    )



    output = result.stdout + result.stderr

    blocked = result.returncode != 0

    findings = []

    current = {}

    issues_count = 0



    for line in output.split('\n'):

        line = line.strip()

        if line.startswith('[') and '% confidence]' in line:

            if current:

                findings.append(current)

            confidence = line.split('%')[0].replace('[','').strip()

            file_info = line.split(']')[1].strip()

            current = {'confidence': confidence, 'file': file_info,

                      'type': '', 'line': '', 'recommendation': ''}

        elif line.startswith('Type:') and current:

            current['type'] = line.replace('Type:','').strip()

        elif line.startswith('Line:') and current:

            current['line'] = line.replace('Line:','').strip()

        elif line.startswith('Recommendation:') and current:

            current['recommendation'] = line.replace('Recommendation:','').strip()

        elif 'BLOCKED:' in line:

            if current:

                findings.append(current)

                current = {}

            try:

                issues_count = int(line.split('BLOCKED:')[1].split('finding')[0].strip())

            except:

                issues_count = len(findings)



    return jsonify({

        'blocked': blocked,

        'issues_count': issues_count,

        'findings': findings,

        'raw_output': output,

        'exit_code': result.returncode

    })



if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)

