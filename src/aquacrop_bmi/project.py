from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Self

from aquacrop_bmi.data import DEFAULT_DATA_DIR, specs, templates
from aquacrop_bmi.soil_texture import SoilLayerParams, curve_number_calc, rew_calc
from aquacrop_bmi.util import dump_crop_file, elapse_date
from aquacrop_bmi.wrapper import AQUACROP_EXE



if TYPE_CHECKING:
    import numpy as np

    from aquacrop_bmi.models import Season



class AquacropProject:
    default_files = tuple((p, p.relative_to(DEFAULT_DATA_DIR))
        for p in DEFAULT_DATA_DIR.glob('**/*')
        if p.is_file())


    def __init__(self, copy_from: Path | None = None, *, with_default: bool = True) -> None:
        self._tmp = TemporaryDirectory()
        self._copy_from = copy_from
        self._with_default = with_default


    def __enter__(self) -> Self:
        root = Path(self._tmp.__enter__())
        self.root = root
        self.list = root / 'LIST'
        self.outp = root / 'OUTP'
        self.simul = root / 'SIMUL'
        
        for dir_ in self.list, self.outp, self.simul:
            dir_.mkdir()

        if self._with_default:
            for src_path, rel_path in self.default_files:
                root.joinpath(rel_path).write_bytes(src_path.read_bytes())

        if copy_from := self._copy_from:
            for src_path in copy_from.glob('**/*'):
                if src_path.is_file():
                    rel_path = src_path.relative_to(copy_from)
                    root.joinpath(rel_path).symlink_to(src_path)

        return self


    def __exit__(self, *exc_info) -> None:
        self._tmp.__exit__(*exc_info)


    def run_aquacrop(self) -> int:
        return subprocess.call(AQUACROP_EXE, cwd=self.root)  # noqa: S603


    def write_climate_files(
        self,
        start: date,
        data: np.recarray,
    ) -> None:
        header_template = templates.CLI_SUB_HEADER.format(
            first_day=start.day,
            first_month=start.month,
            first_year=start.year,
        )

        with (
            self.root.joinpath('project.Tnx').open('w', encoding='utf-8') as tnx,
            self.root.joinpath('project.PLU').open('w', encoding='utf-8') as plu,
            self.root.joinpath('project.ETo').open('w', encoding='utf-8') as et0,
        ):
            tnx.write(header_template.format(columns='Tmin (C)   TMax (C)'))
            plu.write(header_template.format(columns='Total Rain (mm)'))
            et0.write(header_template.format(columns='Average ETo (mm/day)'))
            for row in data:
                tnx.write(f'{row.tn:.1f}\t{row.tx:.1f}\n')
                plu.write(f'{row.pr:.1f}\n')
                et0.write(f'{row.et0:.1f}\n')


    def write_soil_file(
        self,
        soil: list[SoilLayerParams],
    ) -> None:
        first = soil[0]
        curve_number = curve_number_calc(first.ksat)
        rew = rew_calc(fc=first.fc, air=first.wp / 2)
        horizon_count = len(soil)

        with self.root.joinpath('project.SOL').open('w', encoding='utf-8') as f:
            f.write(templates.SOL_CONTENT.format(
                curve_number=curve_number,
                rew=rew,
                horizon_count=horizon_count,
            ))
            for hor in soil:
                ksat = hor.ksat
                f.write(
                    f'  {hor.thickness:^7.2f}   {hor.sat:>4.1f}  {hor.fc:>4.1f}'
                    f'  {hor.wp:>4.1f}  {ksat:^8.1f} {hor.penetrability:^13.0f}'
                    f'  {hor.gravel:^6.0f}  {hor.cr_a:^9.6f}  {hor.cr_b:^9.6f}'
                    f'   {hor.texture_class.name}\n',
                )


    def write_sw0_file(
        self,
        soil: list[SoilLayerParams],
    ) -> None:
        with self.root.joinpath('project.SW0').open('w', encoding='utf-8') as f:
            f.write(templates.SW0_CONTENT.format(
                horizon_count=len(soil),
            ))
            for hor in soil:
                f.write(f'         {hor.thickness:.2f}                {hor.wc:.2f}                  {hor.ec:.2f}\n')  # noqa: E501


    def write_gwt_file(
        self,
        *,
        depth: float = 2.0,
        ec: float = 0.0,
    ) -> None:
        self.root.joinpath('project.GWT').write_text(templates.GWT_CONTENT.format(
            depth=depth,
            ec=ec,
        ))


    def write_calendar_file(
        self,
        simulation: Season,
    ) -> None:
        growing_season_start_doy = simulation.growing_season_start.timetuple().tm_yday
        self.root.joinpath('project.CAL').write_text(templates.CAL_CONTENT.format(
            growing_season_start_doy=growing_season_start_doy,
        ))


    def write_crop_file(
        self,
        crop_index: tuple[str, ...],
        crop_params: dict[str, int | float],
    ) -> None:
        with self.root.joinpath('project.CRO').open('w', encoding='utf-8') as f:
            dump_crop_file(f, crop_index, crop_params)


    def write_fertility_management_file(
        self,
        fertility_stress: float,
    ) -> None:
        self.root.joinpath('project.MAN').write_text(templates.MAN_CONTENT.format(
            fertility_stress=fertility_stress,
        ))


    def write_project_file(
        self,
        simulation: Season,
    ) -> None:
        self.list.joinpath('project.PRO').write_text(templates.PRO_CONTENT.format(
            simulation_start=elapse_date(simulation.simulation_start),
            simulation_end=elapse_date(simulation.simulation_end),
            growing_season_start=elapse_date(simulation.growing_season_start),
            growing_season_end=elapse_date(simulation.growing_season_end),
        ))


    def write_daily_out_config(self) -> None:
        self.simul.joinpath('DailyResults.SIM').write_text(templates.OUT_DAILY_CONTENT)


    def read_final_yield(self) -> float:
        with self.outp.joinpath('projectPROseason.OUT').open() as f:
            for _ in range(4):
                next(f)
            line = next(f)
        return float(line[294:303])


    def read_daily_out(self) -> list[tuple[date, *tuple[int | float | str, ...]]]:
        return list(_read_daily_out(self.outp))



def _read_daily_out(root: Path):
    with root.joinpath('projectPROday.OUT').open() as f:
        for _ in range(4):
            next(f)
        for line in f:
            if line:
                values = _parse_daily_out_line(line)
                day = next(values)
                month = next(values)
                year = next(values)
                yield date(year, month, day), *values



def _parse_daily_out_line(line: str):
    beg = 0
    for end in specs.DAILY_OUT_WIDTHS:
        val = line[beg:end].strip()
        try:
            yield int(val)
        except ValueError:
            try:
                yield float(val)
            except ValueError:
                yield val
        beg = end
