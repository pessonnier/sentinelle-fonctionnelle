"""Cas d'usage de l'application de conception."""

from .deployment_demo import build_deployment_demo
from .hierarchy_demo import build_hierarchy_demo
from .persistence_demo import build_persistence_demo
from .projects import (
    ApplicationMode,
    AuthenticatedIdentity,
    AuthenticationRequired,
    AuthorizationDenied,
    ConcurrentProjectUpdate,
    ProjectApplication,
    ProjectNotFound,
    ProjectRole,
)
from .code_generation import (
    CodeGenerationError,
    GeneratedCodeArtifact,
    generate_python_playwright,
    generate_python_playwright_file,
)
from .code_customization import (
    CodeCustomizationError,
    CustomizationMerge,
    ProtectedCodeRegion,
    merge_customized_source,
    protected_regions,
    validate_customized_source,
)
from .code_generation_prompt import (
    CODE_GENERATION_SKILLS,
    CodeGenerationPromptArtifact,
    CodeGenerationPromptError,
    LLMCodeCandidate,
    LLMGeneratedFile,
    build_code_generation_prompt,
    generation_skill_documents,
    validate_code_generation_response,
)
from .execution_runner import (
    ExecutionReport,
    ExecutionRunnerError,
    run_generated_playwright,
)
from .candidate_lifecycle import CandidateLifecycleApplication
from .bundle_export import (
    BUNDLE_FORMAT_VERSION,
    BundleArtifact,
    BundleExportError,
    export_approved_candidate,
)
from .bundle_runner import (
    BundleRunReport,
    BundleRunnerError,
    run_bundle,
    validate_bundle,
)
from .rendered_page_analysis import (
    CatalogApplicationResult,
    RenderedPageAnalysisError,
    RenderedPageCatalogArtifact,
    analyze_rendered_page,
    analyze_rendered_page_file,
    apply_rendered_catalog_file,
    parse_exploration_plan,
)
from .precondition_readiness import (
    ReadinessCheck,
    ReadinessStatus,
    WorkflowReadiness,
    assess_workflow_readiness,
)
from .retention import RetentionError, RetentionResult, apply_artifact_retention
from .hr_demo_seed import HrDemoSeedResult, seed_hr_demo_project
from .orders_demo_seed import OrdersDemoSeedResult, seed_orders_demo_project

__all__ = [
    "CandidateLifecycleApplication",
    "BUNDLE_FORMAT_VERSION",
    "BundleArtifact",
    "BundleExportError",
    "export_approved_candidate",
    "BundleRunReport",
    "BundleRunnerError",
    "run_bundle",
    "validate_bundle",
    "CodeGenerationError",
    "CodeCustomizationError",
    "CustomizationMerge",
    "ProtectedCodeRegion",
    "merge_customized_source",
    "protected_regions",
    "validate_customized_source",
    "GeneratedCodeArtifact",
    "generate_python_playwright",
    "generate_python_playwright_file",
    "CODE_GENERATION_SKILLS",
    "CodeGenerationPromptArtifact",
    "CodeGenerationPromptError",
    "LLMCodeCandidate",
    "LLMGeneratedFile",
    "build_code_generation_prompt",
    "generation_skill_documents",
    "validate_code_generation_response",
    "ExecutionReport",
    "ExecutionRunnerError",
    "run_generated_playwright",
    "CatalogApplicationResult",
    "RenderedPageAnalysisError",
    "RenderedPageCatalogArtifact",
    "analyze_rendered_page",
    "analyze_rendered_page_file",
    "apply_rendered_catalog_file",
    "parse_exploration_plan",
    "ReadinessCheck",
    "ReadinessStatus",
    "WorkflowReadiness",
    "assess_workflow_readiness",
    "RetentionError",
    "RetentionResult",
    "apply_artifact_retention",
    "HrDemoSeedResult",
    "seed_hr_demo_project",
    "OrdersDemoSeedResult",
    "seed_orders_demo_project",
    "ApplicationMode",
    "AuthenticatedIdentity",
    "AuthenticationRequired",
    "AuthorizationDenied",
    "ConcurrentProjectUpdate",
    "ProjectApplication",
    "ProjectNotFound",
    "ProjectRole",
    "build_deployment_demo",
    "build_hierarchy_demo",
    "build_persistence_demo",
]
