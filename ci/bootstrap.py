#!/usr/bin/env python

import os
import sys
from os.path import abspath, dirname, exists, join

if __name__ == "__main__":
    base_path = dirname(dirname(abspath(__file__)))
    print(f"Project path: {base_path}")
    env_path = join(base_path, ".tox", "bootstrap")
    if sys.platform == "win32":
        bin_path = join(env_path, "Scripts")
    else:
        bin_path = join(env_path, "bin")
    if not exists(env_path):
        import subprocess

        print(f"Making bootstrap env in: {env_path} ...")
        try:
            subprocess.check_call(["virtualenv", env_path])
        except subprocess.CalledProcessError:
            subprocess.check_call([sys.executable, "-m", "virtualenv", env_path])
        print("Installing `jinja2` into bootstrap environment...")
        subprocess.check_call([join(bin_path, "pip"), "install", "jinja2"])
    python_executable = join(bin_path, "python")
    if not os.path.samefile(python_executable, sys.executable):
        print(f"Re-executing with: {python_executable}")
        os.execv(python_executable, [python_executable, __file__])

    import subprocess

    import jinja2

    jinja = jinja2.Environment(
        loader=jinja2.FileSystemLoader(join(base_path, "ci", "templates")),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    tox_environments = [
        line.strip()
        # WARNING: 'tox' must be installed globally or in the project's virtualenv
        for line in subprocess.check_output(
            ["tox", "--listenvs"], universal_newlines=True
        ).splitlines()
    ]
    tox_environments = [line for line in tox_environments if line.startswith("py")]

    for name in os.listdir(join("ci", "templates")):
        with open(join(base_path, name), "w") as fh:
            fh.write(jinja.get_template(name).render(tox_environments=tox_environments))
        print(f"Wrote {name}")
    print("DONE.")
