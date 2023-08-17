# ML Engineering Portfolio Suite

This workspace contains five small, portfolio-ready projects. Together they cover the lifecycle around a practical machine-learning system: presenting work, validating data, tracking experiments, documenting models, and monitoring production inputs.

| Project | What it demonstrates | Location |
| --- | --- | --- |
| **Gitfolio Audit** | GitHub API integration, typed models, explainable scoring, multi-format CLI output | [root package](src/gitfolio_audit) |
| **Data Contract Checker** | Schema validation, type coercion, primary-key checks, CI exit codes | [projects/data-contract](projects/data-contract) |
| **Experiment Tracker Lite** | SQLite schema design, transactions, metric lineage, artifact hashing | [projects/experiment-tracker](projects/experiment-tracker) |
| **Model Card Generator** | Responsible ML documentation, validation, Markdown generation | [projects/model-card](projects/model-card) |
| **Data Drift Monitor** | PSI/TVD drift detection, missingness checks, operational thresholds | [projects/data-drift](projects/data-drift) |

## Verify everything

The root test command runs every project without network access:

```bash
python -m pytest
python -m compileall -q src projects
```

Each project can also be installed and run independently from its own directory. Their READMEs contain quickstarts and examples.

## Publishing strategy

For a GitHub portfolio, publish the strongest two or three projects as separate repositories after adding project-specific examples and screenshots. The suite can remain as a monorepo while the ideas mature; it is intentionally organized so each project can be extracted cleanly.
