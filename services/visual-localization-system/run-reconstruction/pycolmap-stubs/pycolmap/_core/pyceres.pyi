from __future__ import annotations
import typing
__all__: list[str] = ['CallbackReturnType', 'DO_NOT_TAKE_OWNERSHIP', 'DenseLinearAlgebraLibraryType', 'DoglegType', 'DumpFormatType', 'IterationSummary', 'LineSearchDirectionType', 'LineSearchInterpolationType', 'LineSearchType', 'LinearSolverType', 'LoggingType', 'MinimizerType', 'NonlinearConjugateGradientType', 'Ownership', 'PreconditionerType', 'SolverOptions', 'SolverSummary', 'SparseLinearAlgebraLibraryType', 'TAKE_OWNERSHIP', 'TerminationType', 'TrustRegionStrategyType', 'VisibilityClusteringType']
class CallbackReturnType:
    """
    Members:
    
      SOLVER_CONTINUE
    
      SOLVER_ABORT
    
      SOLVER_TERMINATE_SUCCESSFULLY
    """
    SOLVER_ABORT: typing.ClassVar[CallbackReturnType]  # value = CallbackReturnType.SOLVER_ABORT
    SOLVER_CONTINUE: typing.ClassVar[CallbackReturnType]  # value = CallbackReturnType.SOLVER_CONTINUE
    SOLVER_TERMINATE_SUCCESSFULLY: typing.ClassVar[CallbackReturnType]  # value = CallbackReturnType.SOLVER_TERMINATE_SUCCESSFULLY
    __members__: typing.ClassVar[dict[str, CallbackReturnType]]  # value = {'SOLVER_CONTINUE': CallbackReturnType.SOLVER_CONTINUE, 'SOLVER_ABORT': CallbackReturnType.SOLVER_ABORT, 'SOLVER_TERMINATE_SUCCESSFULLY': CallbackReturnType.SOLVER_TERMINATE_SUCCESSFULLY}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class DenseLinearAlgebraLibraryType:
    """
    Members:
    
      EIGEN
    
      LAPACK
    
      CUDA
    """
    CUDA: typing.ClassVar[DenseLinearAlgebraLibraryType]  # value = DenseLinearAlgebraLibraryType.CUDA
    EIGEN: typing.ClassVar[DenseLinearAlgebraLibraryType]  # value = DenseLinearAlgebraLibraryType.EIGEN
    LAPACK: typing.ClassVar[DenseLinearAlgebraLibraryType]  # value = DenseLinearAlgebraLibraryType.LAPACK
    __members__: typing.ClassVar[dict[str, DenseLinearAlgebraLibraryType]]  # value = {'EIGEN': DenseLinearAlgebraLibraryType.EIGEN, 'LAPACK': DenseLinearAlgebraLibraryType.LAPACK, 'CUDA': DenseLinearAlgebraLibraryType.CUDA}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class DoglegType:
    """
    Members:
    
      TRADITIONAL_DOGLEG
    
      SUBSPACE_DOGLEG
    """
    SUBSPACE_DOGLEG: typing.ClassVar[DoglegType]  # value = DoglegType.SUBSPACE_DOGLEG
    TRADITIONAL_DOGLEG: typing.ClassVar[DoglegType]  # value = DoglegType.TRADITIONAL_DOGLEG
    __members__: typing.ClassVar[dict[str, DoglegType]]  # value = {'TRADITIONAL_DOGLEG': DoglegType.TRADITIONAL_DOGLEG, 'SUBSPACE_DOGLEG': DoglegType.SUBSPACE_DOGLEG}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class DumpFormatType:
    """
    Members:
    
      CONSOLE
    
      TEXTFILE
    """
    CONSOLE: typing.ClassVar[DumpFormatType]  # value = DumpFormatType.CONSOLE
    TEXTFILE: typing.ClassVar[DumpFormatType]  # value = DumpFormatType.TEXTFILE
    __members__: typing.ClassVar[dict[str, DumpFormatType]]  # value = {'CONSOLE': DumpFormatType.CONSOLE, 'TEXTFILE': DumpFormatType.TEXTFILE}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class IterationSummary:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: IterationSummary) -> None:
        ...
    @property
    def cost(self) -> float:
        ...
    @property
    def cost_change(self) -> float:
        ...
    @property
    def cumulative_time_in_seconds(self) -> float:
        ...
    @property
    def eta(self) -> float:
        ...
    @property
    def gradient_max_norm(self) -> float:
        ...
    @property
    def gradient_norm(self) -> float:
        ...
    @property
    def iteration(self) -> int:
        ...
    @property
    def iteration_time_in_seconds(self) -> float:
        ...
    @property
    def line_search_function_evaluations(self) -> int:
        ...
    @property
    def line_search_gradient_evaluations(self) -> int:
        ...
    @property
    def line_search_iterations(self) -> int:
        ...
    @property
    def linear_solver_iterations(self) -> int:
        ...
    @property
    def relative_decrease(self) -> float:
        ...
    @property
    def step_is_nonmonotonic(self) -> bool:
        ...
    @property
    def step_is_successful(self) -> bool:
        ...
    @property
    def step_is_valid(self) -> bool:
        ...
    @property
    def step_norm(self) -> float:
        ...
    @property
    def step_size(self) -> float:
        ...
    @property
    def step_solver_time_in_seconds(self) -> float:
        ...
    @property
    def trust_region_radius(self) -> float:
        ...
class LineSearchDirectionType:
    """
    Members:
    
      BFGS
    
      LBFGS
    
      NONLINEAR_CONJUGATE_GRADIENT
    
      STEEPEST_DESCENT
    """
    BFGS: typing.ClassVar[LineSearchDirectionType]  # value = LineSearchDirectionType.BFGS
    LBFGS: typing.ClassVar[LineSearchDirectionType]  # value = LineSearchDirectionType.LBFGS
    NONLINEAR_CONJUGATE_GRADIENT: typing.ClassVar[LineSearchDirectionType]  # value = LineSearchDirectionType.NONLINEAR_CONJUGATE_GRADIENT
    STEEPEST_DESCENT: typing.ClassVar[LineSearchDirectionType]  # value = LineSearchDirectionType.STEEPEST_DESCENT
    __members__: typing.ClassVar[dict[str, LineSearchDirectionType]]  # value = {'BFGS': LineSearchDirectionType.BFGS, 'LBFGS': LineSearchDirectionType.LBFGS, 'NONLINEAR_CONJUGATE_GRADIENT': LineSearchDirectionType.NONLINEAR_CONJUGATE_GRADIENT, 'STEEPEST_DESCENT': LineSearchDirectionType.STEEPEST_DESCENT}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class LineSearchInterpolationType:
    """
    Members:
    
      BISECTION
    
      CUBIC
    
      QUADRATIC
    """
    BISECTION: typing.ClassVar[LineSearchInterpolationType]  # value = LineSearchInterpolationType.BISECTION
    CUBIC: typing.ClassVar[LineSearchInterpolationType]  # value = LineSearchInterpolationType.CUBIC
    QUADRATIC: typing.ClassVar[LineSearchInterpolationType]  # value = LineSearchInterpolationType.QUADRATIC
    __members__: typing.ClassVar[dict[str, LineSearchInterpolationType]]  # value = {'BISECTION': LineSearchInterpolationType.BISECTION, 'CUBIC': LineSearchInterpolationType.CUBIC, 'QUADRATIC': LineSearchInterpolationType.QUADRATIC}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class LineSearchType:
    """
    Members:
    
      ARMIJO
    
      WOLFE
    """
    ARMIJO: typing.ClassVar[LineSearchType]  # value = LineSearchType.ARMIJO
    WOLFE: typing.ClassVar[LineSearchType]  # value = LineSearchType.WOLFE
    __members__: typing.ClassVar[dict[str, LineSearchType]]  # value = {'ARMIJO': LineSearchType.ARMIJO, 'WOLFE': LineSearchType.WOLFE}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class LinearSolverType:
    """
    Members:
    
      DENSE_NORMAL_CHOLESKY
    
      DENSE_QR
    
      SPARSE_NORMAL_CHOLESKY
    
      DENSE_SCHUR
    
      SPARSE_SCHUR
    
      ITERATIVE_SCHUR
    
      CGNR
    """
    CGNR: typing.ClassVar[LinearSolverType]  # value = LinearSolverType.CGNR
    DENSE_NORMAL_CHOLESKY: typing.ClassVar[LinearSolverType]  # value = LinearSolverType.DENSE_NORMAL_CHOLESKY
    DENSE_QR: typing.ClassVar[LinearSolverType]  # value = LinearSolverType.DENSE_QR
    DENSE_SCHUR: typing.ClassVar[LinearSolverType]  # value = LinearSolverType.DENSE_SCHUR
    ITERATIVE_SCHUR: typing.ClassVar[LinearSolverType]  # value = LinearSolverType.ITERATIVE_SCHUR
    SPARSE_NORMAL_CHOLESKY: typing.ClassVar[LinearSolverType]  # value = LinearSolverType.SPARSE_NORMAL_CHOLESKY
    SPARSE_SCHUR: typing.ClassVar[LinearSolverType]  # value = LinearSolverType.SPARSE_SCHUR
    __members__: typing.ClassVar[dict[str, LinearSolverType]]  # value = {'DENSE_NORMAL_CHOLESKY': LinearSolverType.DENSE_NORMAL_CHOLESKY, 'DENSE_QR': LinearSolverType.DENSE_QR, 'SPARSE_NORMAL_CHOLESKY': LinearSolverType.SPARSE_NORMAL_CHOLESKY, 'DENSE_SCHUR': LinearSolverType.DENSE_SCHUR, 'SPARSE_SCHUR': LinearSolverType.SPARSE_SCHUR, 'ITERATIVE_SCHUR': LinearSolverType.ITERATIVE_SCHUR, 'CGNR': LinearSolverType.CGNR}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class LoggingType:
    """
    Members:
    
      SILENT
    
      PER_MINIMIZER_ITERATION
    """
    PER_MINIMIZER_ITERATION: typing.ClassVar[LoggingType]  # value = LoggingType.PER_MINIMIZER_ITERATION
    SILENT: typing.ClassVar[LoggingType]  # value = LoggingType.SILENT
    __members__: typing.ClassVar[dict[str, LoggingType]]  # value = {'SILENT': LoggingType.SILENT, 'PER_MINIMIZER_ITERATION': LoggingType.PER_MINIMIZER_ITERATION}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class MinimizerType:
    """
    Members:
    
      LINE_SEARCH
    
      TRUST_REGION
    """
    LINE_SEARCH: typing.ClassVar[MinimizerType]  # value = MinimizerType.LINE_SEARCH
    TRUST_REGION: typing.ClassVar[MinimizerType]  # value = MinimizerType.TRUST_REGION
    __members__: typing.ClassVar[dict[str, MinimizerType]]  # value = {'LINE_SEARCH': MinimizerType.LINE_SEARCH, 'TRUST_REGION': MinimizerType.TRUST_REGION}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class NonlinearConjugateGradientType:
    """
    Members:
    
      FLETCHER_REEVES
    
      HESTENES_STIEFEL
    
      POLAK_RIBIERE
    """
    FLETCHER_REEVES: typing.ClassVar[NonlinearConjugateGradientType]  # value = NonlinearConjugateGradientType.FLETCHER_REEVES
    HESTENES_STIEFEL: typing.ClassVar[NonlinearConjugateGradientType]  # value = NonlinearConjugateGradientType.HESTENES_STIEFEL
    POLAK_RIBIERE: typing.ClassVar[NonlinearConjugateGradientType]  # value = NonlinearConjugateGradientType.POLAK_RIBIERE
    __members__: typing.ClassVar[dict[str, NonlinearConjugateGradientType]]  # value = {'FLETCHER_REEVES': NonlinearConjugateGradientType.FLETCHER_REEVES, 'HESTENES_STIEFEL': NonlinearConjugateGradientType.HESTENES_STIEFEL, 'POLAK_RIBIERE': NonlinearConjugateGradientType.POLAK_RIBIERE}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class Ownership:
    """
    Members:
    
      DO_NOT_TAKE_OWNERSHIP
    
      TAKE_OWNERSHIP
    """
    DO_NOT_TAKE_OWNERSHIP: typing.ClassVar[Ownership]  # value = Ownership.DO_NOT_TAKE_OWNERSHIP
    TAKE_OWNERSHIP: typing.ClassVar[Ownership]  # value = Ownership.TAKE_OWNERSHIP
    __members__: typing.ClassVar[dict[str, Ownership]]  # value = {'DO_NOT_TAKE_OWNERSHIP': Ownership.DO_NOT_TAKE_OWNERSHIP, 'TAKE_OWNERSHIP': Ownership.TAKE_OWNERSHIP}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class PreconditionerType:
    """
    Members:
    
      IDENTITY
    
      JACOBI
    
      SCHUR_JACOBI
    
      CLUSTER_JACOBI
    
      CLUSTER_TRIDIAGONAL
    """
    CLUSTER_JACOBI: typing.ClassVar[PreconditionerType]  # value = PreconditionerType.CLUSTER_JACOBI
    CLUSTER_TRIDIAGONAL: typing.ClassVar[PreconditionerType]  # value = PreconditionerType.CLUSTER_TRIDIAGONAL
    IDENTITY: typing.ClassVar[PreconditionerType]  # value = PreconditionerType.IDENTITY
    JACOBI: typing.ClassVar[PreconditionerType]  # value = PreconditionerType.JACOBI
    SCHUR_JACOBI: typing.ClassVar[PreconditionerType]  # value = PreconditionerType.SCHUR_JACOBI
    __members__: typing.ClassVar[dict[str, PreconditionerType]]  # value = {'IDENTITY': PreconditionerType.IDENTITY, 'JACOBI': PreconditionerType.JACOBI, 'SCHUR_JACOBI': PreconditionerType.SCHUR_JACOBI, 'CLUSTER_JACOBI': PreconditionerType.CLUSTER_JACOBI, 'CLUSTER_TRIDIAGONAL': PreconditionerType.CLUSTER_TRIDIAGONAL}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class SolverOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def IsValid(self, arg0: str) -> bool:
        ...
    def __copy__(self) -> SolverOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> SolverOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: SolverOptions) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def check_gradients(self) -> bool:
        """
         (bool, default: False)
        """
    @check_gradients.setter
    def check_gradients(self, arg0: bool) -> None:
        ...
    @property
    def dense_linear_algebra_library_type(self) -> DenseLinearAlgebraLibraryType:
        """
         (DenseLinearAlgebraLibraryType, default: DenseLinearAlgebraLibraryType.EIGEN)
        """
    @dense_linear_algebra_library_type.setter
    def dense_linear_algebra_library_type(self, arg0: DenseLinearAlgebraLibraryType) -> None:
        ...
    @property
    def dogleg_type(self) -> DoglegType:
        """
         (DoglegType, default: DoglegType.TRADITIONAL_DOGLEG)
        """
    @dogleg_type.setter
    def dogleg_type(self, arg0: DoglegType) -> None:
        ...
    @property
    def dynamic_sparsity(self) -> bool:
        """
         (bool, default: False)
        """
    @dynamic_sparsity.setter
    def dynamic_sparsity(self, arg0: bool) -> None:
        ...
    @property
    def eta(self) -> float:
        """
         (float, default: 0.1)
        """
    @eta.setter
    def eta(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def function_tolerance(self) -> float:
        """
         (float, default: 1e-06)
        """
    @function_tolerance.setter
    def function_tolerance(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def gradient_check_numeric_derivative_relative_step_size(self) -> float:
        """
         (float, default: 1e-06)
        """
    @gradient_check_numeric_derivative_relative_step_size.setter
    def gradient_check_numeric_derivative_relative_step_size(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def gradient_check_relative_precision(self) -> float:
        """
         (float, default: 1e-08)
        """
    @gradient_check_relative_precision.setter
    def gradient_check_relative_precision(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def gradient_tolerance(self) -> float:
        """
         (float, default: 1e-10)
        """
    @gradient_tolerance.setter
    def gradient_tolerance(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def initial_trust_region_radius(self) -> float:
        """
         (float, default: 10000.0)
        """
    @initial_trust_region_radius.setter
    def initial_trust_region_radius(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def inner_iteration_tolerance(self) -> float:
        """
         (float, default: 0.001)
        """
    @inner_iteration_tolerance.setter
    def inner_iteration_tolerance(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def jacobi_scaling(self) -> bool:
        """
         (bool, default: True)
        """
    @jacobi_scaling.setter
    def jacobi_scaling(self, arg0: bool) -> None:
        ...
    @property
    def line_search_direction_type(self) -> LineSearchDirectionType:
        """
         (LineSearchDirectionType, default: LineSearchDirectionType.LBFGS)
        """
    @line_search_direction_type.setter
    def line_search_direction_type(self, arg0: LineSearchDirectionType) -> None:
        ...
    @property
    def line_search_interpolation_type(self) -> LineSearchInterpolationType:
        """
         (LineSearchInterpolationType, default: LineSearchInterpolationType.CUBIC)
        """
    @line_search_interpolation_type.setter
    def line_search_interpolation_type(self, arg0: LineSearchInterpolationType) -> None:
        ...
    @property
    def line_search_sufficient_curvature_decrease(self) -> float:
        """
         (float, default: 0.9)
        """
    @line_search_sufficient_curvature_decrease.setter
    def line_search_sufficient_curvature_decrease(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def line_search_sufficient_function_decrease(self) -> float:
        """
         (float, default: 0.0001)
        """
    @line_search_sufficient_function_decrease.setter
    def line_search_sufficient_function_decrease(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def line_search_type(self) -> LineSearchType:
        """
         (LineSearchType, default: LineSearchType.WOLFE)
        """
    @line_search_type.setter
    def line_search_type(self, arg0: LineSearchType) -> None:
        ...
    @property
    def linear_solver_type(self) -> LinearSolverType:
        """
         (LinearSolverType, default: LinearSolverType.SPARSE_NORMAL_CHOLESKY)
        """
    @linear_solver_type.setter
    def linear_solver_type(self, arg0: LinearSolverType) -> None:
        ...
    @property
    def logging_type(self) -> LoggingType:
        """
         (LoggingType, default: LoggingType.PER_MINIMIZER_ITERATION)
        """
    @logging_type.setter
    def logging_type(self, arg0: LoggingType) -> None:
        ...
    @property
    def max_consecutive_nonmonotonic_steps(self) -> int:
        """
         (int, default: 5)
        """
    @max_consecutive_nonmonotonic_steps.setter
    def max_consecutive_nonmonotonic_steps(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_lbfgs_rank(self) -> int:
        """
         (int, default: 20)
        """
    @max_lbfgs_rank.setter
    def max_lbfgs_rank(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_line_search_step_contraction(self) -> float:
        """
         (float, default: 0.001)
        """
    @max_line_search_step_contraction.setter
    def max_line_search_step_contraction(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_line_search_step_expansion(self) -> float:
        """
         (float, default: 10.0)
        """
    @max_line_search_step_expansion.setter
    def max_line_search_step_expansion(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_linear_solver_iterations(self) -> int:
        """
         (int, default: 500)
        """
    @max_linear_solver_iterations.setter
    def max_linear_solver_iterations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_lm_diagonal(self) -> float:
        """
         (float, default: 1e+32)
        """
    @max_lm_diagonal.setter
    def max_lm_diagonal(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_num_consecutive_invalid_steps(self) -> int:
        """
         (int, default: 5)
        """
    @max_num_consecutive_invalid_steps.setter
    def max_num_consecutive_invalid_steps(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_num_iterations(self) -> int:
        """
         (int, default: 50)
        """
    @max_num_iterations.setter
    def max_num_iterations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_num_line_search_direction_restarts(self) -> int:
        """
         (int, default: 5)
        """
    @max_num_line_search_direction_restarts.setter
    def max_num_line_search_direction_restarts(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_num_line_search_step_size_iterations(self) -> int:
        """
         (int, default: 20)
        """
    @max_num_line_search_step_size_iterations.setter
    def max_num_line_search_step_size_iterations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_solver_time_in_seconds(self) -> float:
        """
         (float, default: 1000000000.0)
        """
    @max_solver_time_in_seconds.setter
    def max_solver_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_trust_region_radius(self) -> float:
        """
         (float, default: 1e+16)
        """
    @max_trust_region_radius.setter
    def max_trust_region_radius(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_line_search_step_contraction(self) -> float:
        """
         (float, default: 0.6)
        """
    @min_line_search_step_contraction.setter
    def min_line_search_step_contraction(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_line_search_step_size(self) -> float:
        """
         (float, default: 1e-09)
        """
    @min_line_search_step_size.setter
    def min_line_search_step_size(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_linear_solver_iterations(self) -> int:
        """
         (int, default: 0)
        """
    @min_linear_solver_iterations.setter
    def min_linear_solver_iterations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_lm_diagonal(self) -> float:
        """
         (float, default: 1e-06)
        """
    @min_lm_diagonal.setter
    def min_lm_diagonal(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_relative_decrease(self) -> float:
        """
         (float, default: 0.001)
        """
    @min_relative_decrease.setter
    def min_relative_decrease(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_trust_region_radius(self) -> float:
        """
         (float, default: 1e-32)
        """
    @min_trust_region_radius.setter
    def min_trust_region_radius(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def minimizer_progress_to_stdout(self) -> bool:
        """
         (bool, default: False)
        """
    @minimizer_progress_to_stdout.setter
    def minimizer_progress_to_stdout(self, arg0: bool) -> None:
        ...
    @property
    def minimizer_type(self) -> MinimizerType:
        """
         (MinimizerType, default: MinimizerType.TRUST_REGION)
        """
    @minimizer_type.setter
    def minimizer_type(self, arg0: MinimizerType) -> None:
        ...
    @property
    def nonlinear_conjugate_gradient_type(self) -> NonlinearConjugateGradientType:
        """
         (NonlinearConjugateGradientType, default: NonlinearConjugateGradientType.FLETCHER_REEVES)
        """
    @nonlinear_conjugate_gradient_type.setter
    def nonlinear_conjugate_gradient_type(self, arg0: NonlinearConjugateGradientType) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
         (int, default: 1)
        """
    @num_threads.setter
    def num_threads(self, arg1: typing.SupportsInt) -> None:
        ...
    @property
    def parameter_tolerance(self) -> float:
        """
         (float, default: 1e-08)
        """
    @parameter_tolerance.setter
    def parameter_tolerance(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def preconditioner_type(self) -> PreconditionerType:
        """
         (PreconditionerType, default: PreconditionerType.JACOBI)
        """
    @preconditioner_type.setter
    def preconditioner_type(self, arg0: PreconditionerType) -> None:
        ...
    @property
    def sparse_linear_algebra_library_type(self) -> SparseLinearAlgebraLibraryType:
        """
         (SparseLinearAlgebraLibraryType, default: SparseLinearAlgebraLibraryType.SUITE_SPARSE)
        """
    @sparse_linear_algebra_library_type.setter
    def sparse_linear_algebra_library_type(self, arg0: SparseLinearAlgebraLibraryType) -> None:
        ...
    @property
    def trust_region_problem_dump_directory(self) -> str:
        """
         (str, default: /tmp)
        """
    @trust_region_problem_dump_directory.setter
    def trust_region_problem_dump_directory(self, arg0: str) -> None:
        ...
    @property
    def trust_region_problem_dump_format_type(self) -> DumpFormatType:
        """
         (DumpFormatType, default: DumpFormatType.TEXTFILE)
        """
    @trust_region_problem_dump_format_type.setter
    def trust_region_problem_dump_format_type(self, arg0: DumpFormatType) -> None:
        ...
    @property
    def trust_region_strategy_type(self) -> TrustRegionStrategyType:
        """
         (TrustRegionStrategyType, default: TrustRegionStrategyType.LEVENBERG_MARQUARDT)
        """
    @trust_region_strategy_type.setter
    def trust_region_strategy_type(self, arg0: TrustRegionStrategyType) -> None:
        ...
    @property
    def update_state_every_iteration(self) -> bool:
        """
         (bool, default: False)
        """
    @update_state_every_iteration.setter
    def update_state_every_iteration(self, arg0: bool) -> None:
        ...
    @property
    def use_approximate_eigenvalue_bfgs_scaling(self) -> bool:
        """
         (bool, default: False)
        """
    @use_approximate_eigenvalue_bfgs_scaling.setter
    def use_approximate_eigenvalue_bfgs_scaling(self, arg0: bool) -> None:
        ...
    @property
    def use_explicit_schur_complement(self) -> bool:
        """
         (bool, default: False)
        """
    @use_explicit_schur_complement.setter
    def use_explicit_schur_complement(self, arg0: bool) -> None:
        ...
    @property
    def use_inner_iterations(self) -> bool:
        """
         (bool, default: False)
        """
    @use_inner_iterations.setter
    def use_inner_iterations(self, arg0: bool) -> None:
        ...
    @property
    def use_nonmonotonic_steps(self) -> bool:
        """
         (bool, default: False)
        """
    @use_nonmonotonic_steps.setter
    def use_nonmonotonic_steps(self, arg0: bool) -> None:
        ...
    @property
    def visibility_clustering_type(self) -> VisibilityClusteringType:
        """
         (VisibilityClusteringType, default: VisibilityClusteringType.CANONICAL_VIEWS)
        """
    @visibility_clustering_type.setter
    def visibility_clustering_type(self, arg0: VisibilityClusteringType) -> None:
        ...
class SolverSummary:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def BriefReport(self) -> str:
        ...
    def FullReport(self) -> str:
        ...
    def IsSolutionUsable(self) -> bool:
        ...
    def __copy__(self) -> SolverSummary:
        ...
    def __deepcopy__(self, arg0: dict) -> SolverSummary:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: SolverSummary) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def dense_linear_algebra_library_type(self) -> DenseLinearAlgebraLibraryType:
        """
         (DenseLinearAlgebraLibraryType, default: DenseLinearAlgebraLibraryType.EIGEN)
        """
    @dense_linear_algebra_library_type.setter
    def dense_linear_algebra_library_type(self, arg0: DenseLinearAlgebraLibraryType) -> None:
        ...
    @property
    def dogleg_type(self) -> DoglegType:
        """
         (DoglegType, default: DoglegType.TRADITIONAL_DOGLEG)
        """
    @dogleg_type.setter
    def dogleg_type(self, arg0: DoglegType) -> None:
        ...
    @property
    def final_cost(self) -> float:
        """
         (float, default: -1.0)
        """
    @final_cost.setter
    def final_cost(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def fixed_cost(self) -> float:
        """
         (float, default: -1.0)
        """
    @fixed_cost.setter
    def fixed_cost(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def initial_cost(self) -> float:
        """
         (float, default: -1.0)
        """
    @initial_cost.setter
    def initial_cost(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def inner_iteration_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @inner_iteration_time_in_seconds.setter
    def inner_iteration_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def inner_iterations_given(self) -> bool:
        """
         (bool, default: False)
        """
    @inner_iterations_given.setter
    def inner_iterations_given(self, arg0: bool) -> None:
        ...
    @property
    def inner_iterations_used(self) -> bool:
        """
         (bool, default: False)
        """
    @inner_iterations_used.setter
    def inner_iterations_used(self, arg0: bool) -> None:
        ...
    @property
    def is_constrained(self) -> bool:
        """
         (bool, default: False)
        """
    @is_constrained.setter
    def is_constrained(self, arg0: bool) -> None:
        ...
    @property
    def jacobian_evaluation_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @jacobian_evaluation_time_in_seconds.setter
    def jacobian_evaluation_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def line_search_cost_evaluation_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @line_search_cost_evaluation_time_in_seconds.setter
    def line_search_cost_evaluation_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def line_search_direction_type(self) -> LineSearchDirectionType:
        """
         (LineSearchDirectionType, default: LineSearchDirectionType.LBFGS)
        """
    @line_search_direction_type.setter
    def line_search_direction_type(self, arg0: LineSearchDirectionType) -> None:
        ...
    @property
    def line_search_gradient_evaluation_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @line_search_gradient_evaluation_time_in_seconds.setter
    def line_search_gradient_evaluation_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def line_search_interpolation_type(self) -> LineSearchInterpolationType:
        """
         (LineSearchInterpolationType, default: LineSearchInterpolationType.CUBIC)
        """
    @line_search_interpolation_type.setter
    def line_search_interpolation_type(self, arg0: LineSearchInterpolationType) -> None:
        ...
    @property
    def line_search_polynomial_minimization_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @line_search_polynomial_minimization_time_in_seconds.setter
    def line_search_polynomial_minimization_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def line_search_total_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @line_search_total_time_in_seconds.setter
    def line_search_total_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def line_search_type(self) -> LineSearchType:
        """
         (LineSearchType, default: LineSearchType.WOLFE)
        """
    @line_search_type.setter
    def line_search_type(self, arg0: LineSearchType) -> None:
        ...
    @property
    def linear_solver_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @linear_solver_time_in_seconds.setter
    def linear_solver_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def linear_solver_type_given(self) -> LinearSolverType:
        """
         (LinearSolverType, default: LinearSolverType.SPARSE_NORMAL_CHOLESKY)
        """
    @linear_solver_type_given.setter
    def linear_solver_type_given(self, arg0: LinearSolverType) -> None:
        ...
    @property
    def linear_solver_type_used(self) -> LinearSolverType:
        """
         (LinearSolverType, default: LinearSolverType.SPARSE_NORMAL_CHOLESKY)
        """
    @linear_solver_type_used.setter
    def linear_solver_type_used(self, arg0: LinearSolverType) -> None:
        ...
    @property
    def max_lbfgs_rank(self) -> int:
        """
         (int, default: -1)
        """
    @max_lbfgs_rank.setter
    def max_lbfgs_rank(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def message(self) -> str:
        """
         (str, default: ceres::Solve was not called.)
        """
    @message.setter
    def message(self, arg0: str) -> None:
        ...
    @property
    def minimizer_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @minimizer_time_in_seconds.setter
    def minimizer_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def minimizer_type(self) -> MinimizerType:
        """
         (MinimizerType, default: MinimizerType.TRUST_REGION)
        """
    @minimizer_type.setter
    def minimizer_type(self, arg0: MinimizerType) -> None:
        ...
    @property
    def nonlinear_conjugate_gradient_type(self) -> NonlinearConjugateGradientType:
        """
         (NonlinearConjugateGradientType, default: NonlinearConjugateGradientType.FLETCHER_REEVES)
        """
    @nonlinear_conjugate_gradient_type.setter
    def nonlinear_conjugate_gradient_type(self, arg0: NonlinearConjugateGradientType) -> None:
        ...
    @property
    def num_effective_parameters(self) -> int:
        """
         (int, default: -1)
        """
    @num_effective_parameters.setter
    def num_effective_parameters(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_effective_parameters_reduced(self) -> int:
        """
         (int, default: -1)
        """
    @num_effective_parameters_reduced.setter
    def num_effective_parameters_reduced(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_inner_iteration_steps(self) -> int:
        """
         (int, default: -1)
        """
    @num_inner_iteration_steps.setter
    def num_inner_iteration_steps(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_jacobian_evaluations(self) -> int:
        """
         (int, default: -1)
        """
    @num_jacobian_evaluations.setter
    def num_jacobian_evaluations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_line_search_steps(self) -> int:
        """
         (int, default: -1)
        """
    @num_line_search_steps.setter
    def num_line_search_steps(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_linear_solves(self) -> int:
        """
         (int, default: -1)
        """
    @num_linear_solves.setter
    def num_linear_solves(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_parameter_blocks(self) -> int:
        """
         (int, default: -1)
        """
    @num_parameter_blocks.setter
    def num_parameter_blocks(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_parameter_blocks_reduced(self) -> int:
        """
         (int, default: -1)
        """
    @num_parameter_blocks_reduced.setter
    def num_parameter_blocks_reduced(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_parameters(self) -> int:
        """
         (int, default: -1)
        """
    @num_parameters.setter
    def num_parameters(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_parameters_reduced(self) -> int:
        """
         (int, default: -1)
        """
    @num_parameters_reduced.setter
    def num_parameters_reduced(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_residual_blocks(self) -> int:
        """
         (int, default: -1)
        """
    @num_residual_blocks.setter
    def num_residual_blocks(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_residual_blocks_reduced(self) -> int:
        """
         (int, default: -1)
        """
    @num_residual_blocks_reduced.setter
    def num_residual_blocks_reduced(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_residual_evaluations(self) -> int:
        """
         (int, default: -1)
        """
    @num_residual_evaluations.setter
    def num_residual_evaluations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_residuals(self) -> int:
        """
         (int, default: -1)
        """
    @num_residuals.setter
    def num_residuals(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_residuals_reduced(self) -> int:
        """
         (int, default: -1)
        """
    @num_residuals_reduced.setter
    def num_residuals_reduced(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_successful_steps(self) -> int:
        """
         (int, default: -1)
        """
    @num_successful_steps.setter
    def num_successful_steps(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_threads_given(self) -> int:
        """
         (int, default: -1)
        """
    @num_threads_given.setter
    def num_threads_given(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_threads_used(self) -> int:
        """
         (int, default: -1)
        """
    @num_threads_used.setter
    def num_threads_used(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_unsuccessful_steps(self) -> int:
        """
         (int, default: -1)
        """
    @num_unsuccessful_steps.setter
    def num_unsuccessful_steps(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def postprocessor_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @postprocessor_time_in_seconds.setter
    def postprocessor_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def preconditioner_type_given(self) -> PreconditionerType:
        """
         (PreconditionerType, default: PreconditionerType.IDENTITY)
        """
    @preconditioner_type_given.setter
    def preconditioner_type_given(self, arg0: PreconditionerType) -> None:
        ...
    @property
    def preconditioner_type_used(self) -> PreconditionerType:
        """
         (PreconditionerType, default: PreconditionerType.IDENTITY)
        """
    @preconditioner_type_used.setter
    def preconditioner_type_used(self, arg0: PreconditionerType) -> None:
        ...
    @property
    def preprocessor_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @preprocessor_time_in_seconds.setter
    def preprocessor_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def residual_evaluation_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @residual_evaluation_time_in_seconds.setter
    def residual_evaluation_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def schur_structure_given(self) -> str:
        """
         (str, default: )
        """
    @schur_structure_given.setter
    def schur_structure_given(self, arg0: str) -> None:
        ...
    @property
    def schur_structure_used(self) -> str:
        """
         (str, default: )
        """
    @schur_structure_used.setter
    def schur_structure_used(self, arg0: str) -> None:
        ...
    @property
    def sparse_linear_algebra_library_type(self) -> SparseLinearAlgebraLibraryType:
        """
         (SparseLinearAlgebraLibraryType, default: SparseLinearAlgebraLibraryType.NO_SPARSE)
        """
    @sparse_linear_algebra_library_type.setter
    def sparse_linear_algebra_library_type(self, arg0: SparseLinearAlgebraLibraryType) -> None:
        ...
    @property
    def termination_type(self) -> TerminationType:
        """
         (TerminationType, default: TerminationType.FAILURE)
        """
    @termination_type.setter
    def termination_type(self, arg0: TerminationType) -> None:
        ...
    @property
    def total_time_in_seconds(self) -> float:
        """
         (float, default: -1.0)
        """
    @total_time_in_seconds.setter
    def total_time_in_seconds(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def trust_region_strategy_type(self) -> TrustRegionStrategyType:
        """
         (TrustRegionStrategyType, default: TrustRegionStrategyType.LEVENBERG_MARQUARDT)
        """
    @trust_region_strategy_type.setter
    def trust_region_strategy_type(self, arg0: TrustRegionStrategyType) -> None:
        ...
    @property
    def visibility_clustering_type(self) -> VisibilityClusteringType:
        """
         (VisibilityClusteringType, default: VisibilityClusteringType.CANONICAL_VIEWS)
        """
    @visibility_clustering_type.setter
    def visibility_clustering_type(self, arg0: VisibilityClusteringType) -> None:
        ...
class SparseLinearAlgebraLibraryType:
    """
    Members:
    
      SUITE_SPARSE
    
      EIGEN_SPARSE
    
      ACCELERATE_SPARSE
    
      NO_SPARSE
    """
    ACCELERATE_SPARSE: typing.ClassVar[SparseLinearAlgebraLibraryType]  # value = SparseLinearAlgebraLibraryType.ACCELERATE_SPARSE
    EIGEN_SPARSE: typing.ClassVar[SparseLinearAlgebraLibraryType]  # value = SparseLinearAlgebraLibraryType.EIGEN_SPARSE
    NO_SPARSE: typing.ClassVar[SparseLinearAlgebraLibraryType]  # value = SparseLinearAlgebraLibraryType.NO_SPARSE
    SUITE_SPARSE: typing.ClassVar[SparseLinearAlgebraLibraryType]  # value = SparseLinearAlgebraLibraryType.SUITE_SPARSE
    __members__: typing.ClassVar[dict[str, SparseLinearAlgebraLibraryType]]  # value = {'SUITE_SPARSE': SparseLinearAlgebraLibraryType.SUITE_SPARSE, 'EIGEN_SPARSE': SparseLinearAlgebraLibraryType.EIGEN_SPARSE, 'ACCELERATE_SPARSE': SparseLinearAlgebraLibraryType.ACCELERATE_SPARSE, 'NO_SPARSE': SparseLinearAlgebraLibraryType.NO_SPARSE}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class TerminationType:
    """
    Members:
    
      CONVERGENCE
    
      NO_CONVERGENCE
    
      FAILURE
    
      USER_SUCCESS
    
      USER_FAILURE
    """
    CONVERGENCE: typing.ClassVar[TerminationType]  # value = TerminationType.CONVERGENCE
    FAILURE: typing.ClassVar[TerminationType]  # value = TerminationType.FAILURE
    NO_CONVERGENCE: typing.ClassVar[TerminationType]  # value = TerminationType.NO_CONVERGENCE
    USER_FAILURE: typing.ClassVar[TerminationType]  # value = TerminationType.USER_FAILURE
    USER_SUCCESS: typing.ClassVar[TerminationType]  # value = TerminationType.USER_SUCCESS
    __members__: typing.ClassVar[dict[str, TerminationType]]  # value = {'CONVERGENCE': TerminationType.CONVERGENCE, 'NO_CONVERGENCE': TerminationType.NO_CONVERGENCE, 'FAILURE': TerminationType.FAILURE, 'USER_SUCCESS': TerminationType.USER_SUCCESS, 'USER_FAILURE': TerminationType.USER_FAILURE}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class TrustRegionStrategyType:
    """
    Members:
    
      LEVENBERG_MARQUARDT
    
      DOGLEG
    """
    DOGLEG: typing.ClassVar[TrustRegionStrategyType]  # value = TrustRegionStrategyType.DOGLEG
    LEVENBERG_MARQUARDT: typing.ClassVar[TrustRegionStrategyType]  # value = TrustRegionStrategyType.LEVENBERG_MARQUARDT
    __members__: typing.ClassVar[dict[str, TrustRegionStrategyType]]  # value = {'LEVENBERG_MARQUARDT': TrustRegionStrategyType.LEVENBERG_MARQUARDT, 'DOGLEG': TrustRegionStrategyType.DOGLEG}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class VisibilityClusteringType:
    """
    Members:
    
      CANONICAL_VIEWS
    
      SINGLE_LINKAGE
    """
    CANONICAL_VIEWS: typing.ClassVar[VisibilityClusteringType]  # value = VisibilityClusteringType.CANONICAL_VIEWS
    SINGLE_LINKAGE: typing.ClassVar[VisibilityClusteringType]  # value = VisibilityClusteringType.SINGLE_LINKAGE
    __members__: typing.ClassVar[dict[str, VisibilityClusteringType]]  # value = {'CANONICAL_VIEWS': VisibilityClusteringType.CANONICAL_VIEWS, 'SINGLE_LINKAGE': VisibilityClusteringType.SINGLE_LINKAGE}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
DO_NOT_TAKE_OWNERSHIP: Ownership  # value = Ownership.DO_NOT_TAKE_OWNERSHIP
TAKE_OWNERSHIP: Ownership  # value = Ownership.TAKE_OWNERSHIP
