from pathlib import Path

from invoke import task, Context


class Paths:
    repo_root = Path(__file__).parent
    infra_dir = repo_root / "infra_package"
    flet_app = repo_root / "flet_app"

    compiled_flet_src = flet_app / "build" / "web"
    compiled_flet_dest = repo_root / "lambda" / "flet_app"
    stack_output_file = repo_root / "stack_output.json"


@task
def build_flet_web_app(c: Context):
    with c.cd(Paths.repo_root):
        c.run("flet build web flet_app --base-url flet")
        c.run(f"rm -rf {Paths.compiled_flet_dest}")
        c.run(f"mv {Paths.compiled_flet_src} {Paths.compiled_flet_dest}")


@task
def deploy_infra(c: Context):
    if not Paths.compiled_flet_dest.exists():
        print("Must run the task `build-flet-web-app` at least once before deploy")
        raise RuntimeError(
            "Must run the task `build-flet-web-app` at least once before deploy"
        )

    with c.cd(Paths.infra_dir):
        c.run(
            f"cdk deploy --require-approval never --outputs-file {Paths.stack_output_file.absolute()}"
        )
