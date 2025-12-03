import os
from pathlib import Path
import json
import tempfile
import shutil
from aquacrop_bmi_babel._bmi import AquaCrop as FortranAquaCrop
from aquacrop_bmi_babel.bmi_aquacrop import BmiAquaCrop


class AquaCrop(FortranAquaCrop):
    
    METADATA = "data/AquaCrop"
    
    def __init__(self):
        super().__init__()
        self._temp_dir = None
        self._data_root = None
        self._original_cwd = None
        self._finalized = False
    
    def initialize_from_json(self, json_str: str) -> None:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_str)
            temp_json_path = f.name
        
        try:
            self.initialize(temp_json_path)
        finally:
            try:
                os.unlink(temp_json_path)
            except:
                pass
    
    def initialize_from_dict(self, config: dict) -> None:
        self.initialize_from_json(json.dumps(config, indent=2))
    
    def initialize(self, config_file: str) -> None:
        try:
            self._original_cwd = Path(os.getcwd())
        except (FileNotFoundError, OSError):
            self._original_cwd = Path("/tmp")
        
        config_path = Path(config_file).resolve()
        
        if config_path.suffix == '.json':
            temp_cwd = Path(tempfile.mkdtemp(prefix="aquacrop_prep_"))
            data_root = None 
            
            try:
                prep = BmiAquaCrop(original_cwd=self._original_cwd)
                prep.initialize(str(config_path))
                
                if getattr(prep, '_calibration_only', False):
                    print("Note: Calibration completed. BMI not initialized for simulation.")
                    print("      Create a new instance with the generated scenarios file to run simulation.")
                    self._data_root = prep._data_root if hasattr(prep, '_data_root') else None
                    self._finalized = True  
                    return
                
                data_root = Path(prep._data_root)
                project_file = data_root / 'LIST' / 'project.PRO'
                
                if not project_file.exists():
                    raise FileNotFoundError(f"Preprocessing failed: {project_file}")
                
                permanent_location = self._original_cwd / "outputs" / data_root.name
                
                if data_root != permanent_location and not data_root.is_relative_to(self._original_cwd):
                    permanent_location.parent.mkdir(parents=True, exist_ok=True)
                    
                    if permanent_location.exists():
                        shutil.rmtree(permanent_location)
                    shutil.move(str(data_root), str(permanent_location))
                    
                    data_root = permanent_location
                    project_file = data_root / 'LIST' / 'project.PRO'
                else:
                    pass
                
                try:
                    os.chdir(data_root)
                    prep._fortran_bmi.finalize()
                except Exception as e:
                    print(f"Warning: prep finalize failed: {e}")
                finally:
                    try:
                        os.chdir(self._original_cwd)
                    except:
                        pass
                
                del prep
                
                self._data_root = data_root
                print(f"Using preprocessed data: {data_root}")
                
            finally:
                if data_root and not data_root.is_relative_to(temp_cwd):
                    shutil.rmtree(temp_cwd, ignore_errors=True)
            
            super().initialize(str(project_file))
        else:
            super().initialize(config_file)
        
        self._finalized = False
    
    def update(self) -> None:
        if self._finalized:
            raise RuntimeError("Cannot update: model already finalized")
        super().update()
    
    def update_until(self, time: float) -> None:
        if self._finalized:
            raise RuntimeError("Cannot update_until: model already finalized")
        super().update_until(time)
    
    def finalize(self) -> None:
        if self._finalized:
            return 
        
        if self._data_root and self._data_root.exists():
            try:
                os.chdir(self._data_root)
            except (FileNotFoundError, OSError):
                pass
        
        try:
            super().finalize()
        except Exception as e:
            print(f"Warning during finalize: {e}")
        
        if self._original_cwd:
            try:
                os.chdir(self._original_cwd)
            except (FileNotFoundError, OSError):
                pass
        
        self._finalized = True


__all__ = ["AquaCrop"]