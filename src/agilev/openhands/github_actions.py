"""
GitHub Actions Workflow Generator

Generates GitHub Actions workflows for Agile-V integration:
- Evidence collection on PR
- Scope validation in CI
- Automated handoff generation
- Evidence bundle artifacts
"""

from pathlib import Path

import yaml


class GitHubActionsGenerator:
    """Generates GitHub Actions workflows for Agile-V."""
    
    def __init__(self, repo_dir: Path):
        """Initialize generator."""
        self.repo_dir = repo_dir
        self.workflows_dir = repo_dir / ".github" / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all(self) -> None:
        """Generate all workflows."""
        self.generate_pr_validation()
        self.generate_evidence_collection()
        self.generate_handoff_generation()
        self.generate_scope_check()
    
    def generate_pr_validation(self) -> Path:
        """
        Generate workflow for PR validation.
        
        This workflow runs on every PR and validates:
        - Task ID is present
        - Scope constraints are met
        - Required evidence exists
        """
        workflow = {
            'name': 'Agile-V PR Validation',
            'on': {
                'pull_request': {
                    'types': ['opened', 'synchronize', 'reopened']
                }
            },
            'jobs': {
                'validate': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'name': 'Checkout code',
                            'uses': 'actions/checkout@v4',
                            'with': {'fetch-depth': 0}
                        },
                        {
                            'name': 'Set up Python',
                            'uses': 'actions/setup-python@v5',
                            'with': {'python-version': '3.11'}
                        },
                        {
                            'name': 'Install Agile-V',
                            'run': 'pip install -e .'
                        },
                        {
                            'name': 'Extract task ID from PR',
                            'id': 'task',
                            'run': '''
                                # Extract task ID from PR title or branch
                                TASK_ID=$(echo "${{ github.event.pull_request.title }}" | grep -oP 'AAV-\\d{4}' | head -1)
                                if [ -z "$TASK_ID" ]; then
                                    TASK_ID=$(echo "${{ github.head_ref }}" | grep -oP 'AAV-\\d{4}' | head -1)
                                fi
                                if [ -z "$TASK_ID" ]; then
                                    echo "::error::No task ID found in PR title or branch name"
                                    exit 1
                                fi
                                echo "task_id=$TASK_ID" >> $GITHUB_OUTPUT
                                echo "Found task ID: $TASK_ID"
                            '''
                        },
                        {
                            'name': 'Validate task brief exists',
                            'run': '''
                                TASK_ID="${{ steps.task.outputs.task_id }}"
                                if [ ! -f ".agentic-agile-v/tasks/$TASK_ID/task_brief.md" ]; then
                                    echo "::error::Task brief not found for $TASK_ID"
                                    exit 1
                                fi
                                echo "✅ Task brief found"
                            '''
                        },
                        {
                            'name': 'Validate scope compliance',
                            'run': '''
                                TASK_ID="${{ steps.task.outputs.task_id }}"
                                export AGILEV_TASK_ID=$TASK_ID
                                agilev openhands validate --scope
                            '''
                        },
                        {
                            'name': 'Check for required evidence',
                            'run': '''
                                TASK_ID="${{ steps.task.outputs.task_id }}"
                                agilev validate || echo "::warning::Evidence validation failed"
                            '''
                        },
                        {
                            'name': 'Post validation summary',
                            'if': 'always()',
                            'uses': 'actions/github-script@v7',
                            'with': {
                                'script': '''
                                    const task_id = '${{ steps.task.outputs.task_id }}';
                                    const conclusion = '${{ job.status }}';
                                    
                                    const body = conclusion === 'success' 
                                        ? `✅ Agile-V validation passed for ${task_id}`
                                        : `❌ Agile-V validation failed for ${task_id}. Check workflow logs.`;
                                    
                                    await github.rest.issues.createComment({
                                        ...context.repo,
                                        issue_number: context.issue.number,
                                        body: body
                                    });
                                '''
                            }
                        }
                    ]
                }
            }
        }
        
        output_file = self.workflows_dir / "agilev-pr-validation.yml"
        with open(output_file, 'w') as f:
            yaml.dump(workflow, f, sort_keys=False, default_flow_style=False)
        
        return output_file
    
    def generate_evidence_collection(self) -> Path:
        """
        Generate workflow for evidence collection.
        
        Runs after PR is merged to collect final evidence.
        """
        workflow = {
            'name': 'Agile-V Evidence Collection',
            'on': {
                'push': {
                    'branches': ['main', 'master']
                }
            },
            'jobs': {
                'collect': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'name': 'Checkout code',
                            'uses': 'actions/checkout@v4',
                            'with': {'fetch-depth': 0}
                        },
                        {
                            'name': 'Set up Python',
                            'uses': 'actions/setup-python@v5',
                            'with': {'python-version': '3.11'}
                        },
                        {
                            'name': 'Install Agile-V',
                            'run': 'pip install -e .'
                        },
                        {
                            'name': 'Extract task IDs from commit messages',
                            'id': 'tasks',
                            'run': '''
                                # Get commit messages from this push
                                TASK_IDS=$(git log --pretty=%B ${{ github.event.before }}..${{ github.event.after }} | grep -oP 'AAV-\\d{4}' | sort -u)
                                
                                if [ -z "$TASK_IDS" ]; then
                                    echo "No task IDs found in commits"
                                    exit 0
                                fi
                                
                                echo "Found tasks: $TASK_IDS"
                                echo "task_ids<<EOF" >> $GITHUB_OUTPUT
                                echo "$TASK_IDS" >> $GITHUB_OUTPUT
                                echo "EOF" >> $GITHUB_OUTPUT
                            '''
                        },
                        {
                            'name': 'Collect evidence for each task',
                            'if': 'steps.tasks.outputs.task_ids != \'\'',
                            'run': '''
                                while IFS= read -r TASK_ID; do
                                    echo "Collecting evidence for $TASK_ID..."
                                    agilev openhands evidence collect --task "$TASK_ID" || echo "Warning: Evidence collection failed for $TASK_ID"
                                done <<< "${{ steps.tasks.outputs.task_ids }}"
                            '''
                        },
                        {
                            'name': 'Upload evidence bundles',
                            'if': 'steps.tasks.outputs.task_ids != \'\'',
                            'uses': 'actions/upload-artifact@v4',
                            'with': {
                                'name': 'evidence-bundles',
                                'path': '.agentic-agile-v/tasks/*/evidence/',
                                'retention-days': 90
                            }
                        },
                        {
                            'name': 'Commit evidence to repository',
                            'if': 'steps.tasks.outputs.task_ids != \'\'',
                            'run': '''
                                git config user.name "Agile-V Bot"
                                git config user.email "agilev-bot@github.com"
                                
                                git add .agentic-agile-v/tasks/*/evidence/
                                
                                if git diff --staged --quiet; then
                                    echo "No evidence changes to commit"
                                else
                                    git commit -m "chore: Update evidence bundles [skip ci]"
                                    git push
                                fi
                            '''
                        }
                    ]
                }
            }
        }
        
        output_file = self.workflows_dir / "agilev-evidence-collection.yml"
        with open(output_file, 'w') as f:
            yaml.dump(workflow, f, sort_keys=False, default_flow_style=False)
        
        return output_file
    
    def generate_handoff_generation(self) -> Path:
        """
        Generate workflow for handoff document generation.
        
        Creates handoff documents and posts to PR.
        """
        workflow = {
            'name': 'Agile-V Handoff Generation',
            'on': {
                'pull_request': {
                    'types': ['opened', 'synchronize']
                }
            },
            'jobs': {
                'handoff': {
                    'runs-on': 'ubuntu-latest',
                    'permissions': {
                        'contents': 'read',
                        'pull-requests': 'write'
                    },
                    'steps': [
                        {
                            'name': 'Checkout code',
                            'uses': 'actions/checkout@v4'
                        },
                        {
                            'name': 'Set up Python',
                            'uses': 'actions/setup-python@v5',
                            'with': {'python-version': '3.11'}
                        },
                        {
                            'name': 'Install Agile-V',
                            'run': 'pip install -e .'
                        },
                        {
                            'name': 'Extract task ID',
                            'id': 'task',
                            'run': '''
                                TASK_ID=$(echo "${{ github.event.pull_request.title }}" | grep -oP 'AAV-\\d{4}' | head -1)
                                if [ -z "$TASK_ID" ]; then
                                    TASK_ID=$(echo "${{ github.head_ref }}" | grep -oP 'AAV-\\d{4}' | head -1)
                                fi
                                if [ -z "$TASK_ID" ]; then
                                    echo "No task ID found"
                                    exit 0
                                fi
                                echo "task_id=$TASK_ID" >> $GITHUB_OUTPUT
                            '''
                        },
                        {
                            'name': 'Generate handoff document',
                            'if': 'steps.task.outputs.task_id != \'\'',
                            'id': 'handoff',
                            'run': '''
                                TASK_ID="${{ steps.task.outputs.task_id }}"
                                agilev openhands handoff --task "$TASK_ID" > handoff.md
                                echo "generated=true" >> $GITHUB_OUTPUT
                            '''
                        },
                        {
                            'name': 'Post handoff to PR',
                            'if': 'steps.handoff.outputs.generated == \'true\'',
                            'uses': 'actions/github-script@v7',
                            'with': {
                                'script': '''
                                    const fs = require('fs');
                                    const handoff = fs.readFileSync('handoff.md', 'utf8');
                                    
                                    // Find existing comment
                                    const { data: comments } = await github.rest.issues.listComments({
                                        ...context.repo,
                                        issue_number: context.issue.number
                                    });
                                    
                                    const botComment = comments.find(comment => 
                                        comment.user.type === 'Bot' && 
                                        comment.body.includes('Agile-V Handoff Report')
                                    );
                                    
                                    const body = `## 📋 Agile-V Handoff Report\\n\\n${handoff}`;
                                    
                                    if (botComment) {
                                        await github.rest.issues.updateComment({
                                            ...context.repo,
                                            comment_id: botComment.id,
                                            body: body
                                        });
                                    } else {
                                        await github.rest.issues.createComment({
                                            ...context.repo,
                                            issue_number: context.issue.number,
                                            body: body
                                        });
                                    }
                                '''
                            }
                        }
                    ]
                }
            }
        }
        
        output_file = self.workflows_dir / "agilev-handoff.yml"
        with open(output_file, 'w') as f:
            yaml.dump(workflow, f, sort_keys=False, default_flow_style=False)
        
        return output_file
    
    def generate_scope_check(self) -> Path:
        """
        Generate workflow for scope compliance checking.
        
        Fast check that runs on every push to ensure scope compliance.
        """
        workflow = {
            'name': 'Agile-V Scope Check',
            'on': ['push', 'pull_request'],
            'jobs': {
                'scope': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'name': 'Checkout code',
                            'uses': 'actions/checkout@v4',
                            'with': {'fetch-depth': 0}
                        },
                        {
                            'name': 'Set up Python',
                            'uses': 'actions/setup-python@v5',
                            'with': {'python-version': '3.11'}
                        },
                        {
                            'name': 'Install Agile-V',
                            'run': 'pip install -e .'
                        },
                        {
                            'name': 'Check scope compliance',
                            'run': '''
                                # Try to detect task ID
                                if [ ! -z "$AGILEV_TASK_ID" ]; then
                                    TASK_ID=$AGILEV_TASK_ID
                                elif [ "${{ github.event_name }}" = "pull_request" ]; then
                                    TASK_ID=$(echo "${{ github.event.pull_request.title }}" | grep -oP 'AAV-\\d{4}' | head -1)
                                fi
                                
                                if [ -z "$TASK_ID" ]; then
                                    echo "No task ID detected, skipping scope check"
                                    exit 0
                                fi
                                
                                echo "Checking scope for task $TASK_ID..."
                                export AGILEV_TASK_ID=$TASK_ID
                                agilev openhands validate --scope
                            '''
                        }
                    ]
                }
            }
        }
        
        output_file = self.workflows_dir / "agilev-scope-check.yml"
        with open(output_file, 'w') as f:
            yaml.dump(workflow, f, sort_keys=False, default_flow_style=False)
        
        return output_file


def generate_github_actions(repo_dir: Path) -> None:
    """Generate all GitHub Actions workflows."""
    generator = GitHubActionsGenerator(repo_dir)
    generator.generate_all()
    
    print("✅ GitHub Actions workflows generated:")
    print(f"   - {generator.workflows_dir / 'agilev-pr-validation.yml'}")
    print(f"   - {generator.workflows_dir / 'agilev-evidence-collection.yml'}")
    print(f"   - {generator.workflows_dir / 'agilev-handoff.yml'}")
    print(f"   - {generator.workflows_dir / 'agilev-scope-check.yml'}")
