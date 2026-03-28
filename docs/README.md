# Documentation

## Overview

Feed is a monorepo of small web apps that combine free public data feeds in novel ways. Each app is a self-contained Python/FastAPI application backed by free government and community APIs, with shared infrastructure for common patterns like caching, rate limiting, and template rendering.

This documentation covers the architecture, individual apps, development workflow, and data sources.

## Documentation Structure

### [01. Architecture](01-architecture/README.md)

System design, shared infrastructure, and recurring patterns across all apps.

### [02. Apps](02-apps/README.md)

Catalog of all 11 apps with descriptions, ports, data sources, and viability assessments.

### [03. Development](03-development/README.md)

Getting started, creating new apps, and troubleshooting.

### [04. Data Sources](04-data-sources/README.md)

Comprehensive reference for all free public APIs used, API key requirements, and known data gaps.

## Quick Start

New to the project? Start with [Getting Started](03-development/01-getting-started.md).

## Finding Information

- **How it works**: Check the [Architecture](01-architecture/README.md) section
- **What apps exist**: Check the [App Catalog](02-apps/01-app-catalog.md)
- **How to run things**: Check [Getting Started](03-development/01-getting-started.md)
- **API reference**: Check [Data Sources](04-data-sources/README.md)
