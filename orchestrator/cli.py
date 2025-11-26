# orchestrator/cli.py — Phase II AdvocAI CLI Runner

import os
import argparse
import sys
from rich import print
from rich.console import Console
from rich.table import Table

from orchestrator.main import orchestrate_advocai_workflow, initialize_gemini_client
from storage.session_manager import SessionManager

console = Console()


# --------------------------------------------------------------
# Utility display functions
# --------------------------------------------------------------
def print_header(title: str):
    console.rule(f"[bold cyan]{title}[/bold cyan]")


def print_error(msg: str):
    console.print(f"[bold red]ERROR:[/bold red] {msg}")


# --------------------------------------------------------------
# ACTION: Start new workflow
# --------------------------------------------------------------
def action_start(case_id: str):
    print_header("Starting New AdvocAI Workflow")

    denial_path = f"data/input/denial_{case_id}.pdf"
    policy_path = f"data/input/policy_{case_id}.pdf"

    if not os.path.exists(denial_path) or not os.path.exists(policy_path):
        print_error(f"Input files missing for case: {case_id}")
        console.print(f"- {denial_path}")
        console.print(f"- {policy_path}")
        sys.exit(1)

    session_id = SessionManager.start_new_session(metadata={"case_id": case_id})

    console.print(f"[green]Session created:[/green] {session_id}")
    console.print("Running workflow...")

    client = initialize_gemini_client()
    orchestrate_advocai_workflow(client, denial_path, policy_path, case_id)

    console.print("\n[bold green]Workflow completed successfully![/bold green]")


# --------------------------------------------------------------
# ACTION: Resume workflow
# --------------------------------------------------------------
def action_resume(session_id: str):
    print_header("Resuming AdvocAI Workflow")

    resume_stage = SessionManager.get_resume_stage(session_id)
    if resume_stage is None:
        print_error("No resumable session found.")
        sys.exit(1)

    console.print(f"[cyan]Resuming session[/cyan]: {session_id}")
    console.print(f"[yellow]Resume from stage[/yellow]: {resume_stage}")

    case_id = f"case_{session_id}"
    denial_path = f"data/input/{case_id}/denial.pdf"
    policy_path = f"data/input/{case_id}/policy.pdf"

    if not os.path.exists(denial_path) or not os.path.exists(policy_path):
        print_error("Input files missing for resume session.")
        sys.exit(1)

    client = initialize_gemini_client()
    orchestrate_advocai_workflow(client, denial_path, policy_path, case_id)

    console.print("[bold green]Resume complete.[/bold green]")


# --------------------------------------------------------------
# ACTION: Status check
# --------------------------------------------------------------
def action_status(session_id: str):
    print_header("AdvocAI Workflow Status")

    stage = SessionManager.get_resume_stage(session_id)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Session ID")
    table.add_column("Last Completed Stage")
    table.add_column("Resumable")

    table.add_row(
        session_id,
        stage if stage else "None",
        "YES" if stage else "NO"
    )

    console.print(table)


# --------------------------------------------------------------
# ACTION: Run directly without sessioning (developer/debug)
# --------------------------------------------------------------
def action_run_local(case_id: str):
    print_header("Running Local Workflow (No Session)")

    denial_path = f"data/input/denial_{case_id}.pdf"
    policy_path = f"data/input/policy_{case_id}.pdf"

    if not os.path.exists(denial_path) or not os.path.exists(policy_path):
        print_error("Missing input files.")
        sys.exit(1)

    client = initialize_gemini_client()
    orchestrate_advocai_workflow(client, denial_path, policy_path, case_id)

    console.print("[bold green]Local run complete.[/bold green]")


# --------------------------------------------------------------
# MAIN CLI ENTRYPOINT
# --------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="AdvocAI Workflow CLI — Phase II",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # start
    p_start = sub.add_parser("start", help="Start a new workflow")
    p_start.add_argument("--case_id", required=True, help="Case ID, e.g., case_1")

    # resume
    p_resume = sub.add_parser("resume", help="Resume an interrupted workflow")
    p_resume.add_argument("--session_id", required=True)

    # status
    p_status = sub.add_parser("status", help="Check workflow status")
    p_status.add_argument("--session_id", required=True)

    # run-local
    p_local = sub.add_parser("run-local", help="Run workflow without session manager")
    p_local.add_argument("--case_id", required=True)

    args = parser.parse_args()

    if args.command == "start":
        action_start(args.case_id)

    elif args.command == "resume":
        action_resume(args.session_id)

    elif args.command == "status":
        action_status(args.session_id)

    elif args.command == "run-local":
        action_run_local(args.case_id)


if __name__ == "__main__":
    main()
