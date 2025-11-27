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
            data_root = None  # Initialize before try
            
            try:
                # Pass REAL original_cwd, not temp_cwd!
                prep = BmiAquaCrop(original_cwd=self._original_cwd)
                prep.initialize(str(config_path))
                
                # Check if calibration returned early
                if getattr(prep, '_calibration_only', False):
                    print("Note: Calibration completed. BMI not initialized for simulation.")
                    print("      Create a new instance with the generated scenarios file to run simulation.")
                    self._data_root = prep._data_root if hasattr(prep, '_data_root') else None
                    self._finalized = True  # Mark as "done" since we won't run simulation
                    return
                
                data_root = Path(prep._data_root)
                project_file = data_root / 'LIST' / 'project.PRO'
                
                if not project_file.exists():
                    raise FileNotFoundError(f"Preprocessing failed: {project_file}")
                
                # Check if data is already in permanent location or needs moving
                permanent_location = self._original_cwd / "outputs" / data_root.name
                
                if data_root != permanent_location and not data_root.is_relative_to(self._original_cwd):
                    # Data is in temp_cwd, need to move to permanent location
                    permanent_location.parent.mkdir(parents=True, exist_ok=True)
                    
                    if permanent_location.exists():
                        shutil.rmtree(permanent_location)
                    shutil.move(str(data_root), str(permanent_location))
                    
                    # Update paths to permanent location
                    data_root = permanent_location
                    project_file = data_root / 'LIST' / 'project.PRO'
                else:
                    # Data already in permanent location, no move needed
                    pass
                
                # Change back to data_root before finalizing (for OUTP/AllDone.OUT)
                try:
                    os.chdir(data_root)
                    prep._fortran_bmi.finalize()
                except Exception as e:
                    print(f"Warning: prep finalize failed: {e}")
                finally:
                    # Return to original cwd
                    try:
                        os.chdir(self._original_cwd)
                    except:
                        pass
                
                del prep
                
                self._data_root = data_root
                print(f"Using preprocessed data: {data_root}")
                
            finally:
                # Only delete temp_cwd if data_root is NOT inside it
                if data_root and not data_root.is_relative_to(temp_cwd):
                    shutil.rmtree(temp_cwd, ignore_errors=True)
                # else: data is still in temp_cwd, don't delete yet
            
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