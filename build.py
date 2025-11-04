from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from shutil import copyfile, copystat, which
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from pymake import pymake
from pymake.rules import RuleDB
from pymake.symtable import SymbolTable



class CustomBuildHook(BuildHookInterface):
    def initialize(self, _version: str, build_data: dict[str, Any]) -> None:
        root = Path(self.root)
        ac_source_path = _build_ac(root)

        ac_target_dir = root.joinpath('src', 'aquacrop_bmi', 'wrapper')  # Note: added 'src'
        ac_target_dir.mkdir(parents=True, exist_ok=True)
        ac_target_path = ac_target_dir / ac_source_path.name

        copyfile(ac_source_path, ac_target_path)
        copystat(ac_source_path, ac_target_path)

        if strip := which('strip'):
            subprocess.check_call([strip, ac_target_path.as_posix()])  # noqa: S603

        build_data['infer_tag'] = True


def _build_ac(root: Path) -> Path:
    ac_dir = root / 'aquacrop'
    cwd = Path.cwd()
    os.chdir(ac_dir)

    target = 'aquacrop'
    makefile = pymake.parse_makefile('Makefile')
    rulesdb = RuleDB()
    symtable = SymbolTable()
    pymake.execute_statement_list(makefile.token_list, [target], rulesdb, symtable)
    args = argparse.Namespace(silent=False, dry_run=False)
    for rule in rulesdb.walk_tree(target):
        if rule.assignment_list:
            symtable.push_layer()
            for asn in rule.assignment_list:
                asn.eval(symtable)
        for recipe in rule.recipe_list:
            pymake.execute_recipe(rule, recipe, symtable, args)
        if rule.assignment_list:
            symtable.pop_layer()

    os.chdir(cwd)

    return ac_dir / target
