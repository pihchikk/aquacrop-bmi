import os
from pathlib import Path
import json
import tempfile
import shutil
from aquacrop_bmi_babel._bmi import AquaCrop as FortranAquaCrop
from aquacrop_bmi_babel.bmi_aquacrop import BmiAquaCrop


class AquaCrop(FortranAquaCrop):
    """Fortran BMI with JSON preprocessing"""
    
    METADATA = "data/AquaCrop"
    
    def __init__(self):
        super().__init__()
        self._temp_dir = None
        self._data_root = None
        self._original_cwd = None
        self._finalized = False
    
    def initialize(self, config_file: str) -> None:
        """Initialize from JSON or PRO file"""
        # Save cwd at start
        try:
            self._original_cwd = Path(os.getcwd())
        except (FileNotFoundError, OSError):
            self._original_cwd = Path("/tmp")
        
        config_path = Path(config_file).resolve()
        
        if config_path.suffix == '.json':
            # Preprocess JSON → .PRO via BmiAquaCrop
            temp_cwd = Path(tempfile.mkdtemp(prefix="aquacrop_prep_"))
            
            try:
                prep = BmiAquaCrop(original_cwd=temp_cwd)
                prep.initialize(str(config_path))
                
                data_root = Path(prep._data_root)
                project_file = data_root / 'LIST' / 'project.PRO'
                
                if not project_file.exists():
                    raise FileNotFoundError(f"Preprocessing failed: {project_file}")
                
                # Close preprocessing Fortran BMI
                prep._fortran_bmi.finalize()
                del prep
                
                self._data_root = data_root
                print(f"Using preprocessed data: {data_root}")
                
            finally:
                shutil.rmtree(temp_cwd, ignore_errors=True)
            
            # Initialize main Fortran BMI with .PRO
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
            return  # Already finalized, skip
        
        # Change to data_root for Fortran's OUTP/AllDone.OUT
        if self._data_root and self._data_root.exists():
            try:
                os.chdir(self._data_root)
            except (FileNotFoundError, OSError):
                pass
        
        try:
            super().finalize()
        except Exception as e:
            print(f"Warning during finalize: {e}")
        
        # Return to original directory
        if self._original_cwd:
            try:
                os.chdir(self._original_cwd)
            except (FileNotFoundError, OSError):
                pass
        
        self._finalized = True


__all__ = ["AquaCrop"]