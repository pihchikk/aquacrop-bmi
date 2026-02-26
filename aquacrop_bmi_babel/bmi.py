import os
from pathlib import Path
import json
import tempfile
import shutil
from aquacrop_bmi_babel._bmi import AquaCrop as FortranAquaCrop
from aquacrop_bmi_babel.bmi_aquacrop import BmiAquaCrop, suppress_fortran_output


class AquaCrop(FortranAquaCrop):
    """
    BMI wrapper for AquaCrop with robust working directory management.

    This class ensures that the working directory is always restored to its
    original state, even when errors occur during initialization or finalization.

    Parameters
    ----------
    verbose : bool, optional
        If True, print Fortran debug output during initialization.
        Default is False (output suppressed).
    """

    METADATA = "data/AquaCrop"

    def __init__(self, verbose: bool = False):
        super().__init__()
        self._temp_dir = None
        self._data_root = None
        self._finalized = False
        self._verbose = verbose

        # Save original working directory ONCE in __init__
        # This prevents overwriting with wrong path on subsequent calls
        try:
            self._original_cwd = Path(os.getcwd())
        except (FileNotFoundError, OSError):
            # Fallback if cwd is deleted or inaccessible
            try:
                self._original_cwd = Path.home()
            except:
                self._original_cwd = Path("/tmp")
    
    def __enter__(self):
        """Context manager entry - allows 'with AquaCrop() as model:'"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures finalize() is always called"""
        self.finalize()
        return False  # Don't suppress exceptions
    
    def initialize_from_json(self, json_str: str) -> None:
        """Initialize from JSON string instead of file"""
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
        """Initialize from Python dict instead of file"""
        self.initialize_from_json(json.dumps(config, indent=2))
    
    def initialize(self, config_file: str) -> None:
        """
        Initialize model from configuration file.
        
        Working directory is guaranteed to be restored even if initialization fails.
        """
        config_path = Path(config_file)
        
        # Make path absolute relative to original_cwd (not current potentially changed cwd)
        if not config_path.is_absolute():
            config_path = (self._original_cwd / config_path).resolve()
        else:
            config_path = config_path.resolve()
        
        if config_path.suffix == '.json':
            temp_cwd = Path(tempfile.mkdtemp(prefix="aquacrop_prep_"))
            data_root = None
            
            try:
                # Always ensure we're in original_cwd before starting
                os.chdir(self._original_cwd)

                # Use BmiAquaCrop for data generation only (init_fortran=False)
                # This avoids initializing + finalizing a temporary Fortran instance
                # which would destroy global Fortran state needed by self.
                prep = BmiAquaCrop(original_cwd=self._original_cwd, init_fortran=False)

                try:
                    prep.initialize(str(config_path))
                except Exception as e:
                    # Restore cwd even if prep.initialize fails
                    os.chdir(self._original_cwd)
                    raise

                # Check if this was calibration-only mode
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

                # Move data to permanent location under outputs/
                permanent_location = self._original_cwd / "outputs" / data_root.name

                if data_root != permanent_location and not data_root.is_relative_to(self._original_cwd):
                    permanent_location.parent.mkdir(parents=True, exist_ok=True)

                    if permanent_location.exists():
                        shutil.rmtree(permanent_location)
                    shutil.move(str(data_root), str(permanent_location))

                    data_root = permanent_location
                    project_file = data_root / 'LIST' / 'project.PRO'

                del prep

                self._data_root = data_root
                print(f"Using preprocessed data: {data_root}")

            finally:
                # Cleanup temp directory
                if data_root and not data_root.is_relative_to(temp_cwd):
                    shutil.rmtree(temp_cwd, ignore_errors=True)

                # CRITICAL: Always restore cwd, even if exception occurred
                os.chdir(self._original_cwd)
            
            # Initialize Fortran BMI with project file
            # Note: Fortran changes cwd to data_root - we restore it immediately
            if self._verbose:
                super().initialize(str(project_file))
            else:
                with suppress_fortran_output():
                    super().initialize(str(project_file))
            os.chdir(self._original_cwd)  # Restore cwd after Fortran init

        else:
            # Direct .PRO file initialization
            if self._verbose:
                super().initialize(str(config_path))
            else:
                with suppress_fortran_output():
                    super().initialize(str(config_path))
            os.chdir(self._original_cwd)  # Restore cwd after Fortran init
        
        self._finalized = False
    
    def update(self) -> None:
        """Advance model by one time step"""
        if self._finalized:
            raise RuntimeError("Cannot update: model already finalized")
        super().update()
    
    def update_until(self, time: float) -> None:
        """Advance model to specified time"""
        if self._finalized:
            raise RuntimeError("Cannot update_until: model already finalized")
        super().update_until(time)
    
    def finalize(self) -> None:
        """
        Finalize model and restore working directory.
        
        This method is safe to call multiple times.
        Working directory is always restored to original location.
        """
        if self._finalized:
            return
        
        # Change to data_root if it exists (Fortran needs to be there to write outputs)
        if self._data_root and self._data_root.exists():
            try:
                os.chdir(self._data_root)
            except (FileNotFoundError, OSError):
                pass
        
        # Call Fortran finalize
        try:
            super().finalize()
        except Exception as e:
            print(f"Warning during finalize: {e}")
        
        # CRITICAL: Always restore cwd to original location
        if self._original_cwd:
            try:
                os.chdir(self._original_cwd)
            except (FileNotFoundError, OSError):
                # If original_cwd was deleted, go to home
                try:
                    os.chdir(Path.home())
                except:
                    os.chdir("/tmp")
        
        self._finalized = True


__all__ = ["AquaCrop"]