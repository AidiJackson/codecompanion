# Architecture Overview

## Project Structure

This document provides a high-level overview of the project architecture.

## Planned Phases

1. Setup
2. Core Implementation
3. Testing

## Architecture Notes

No additional notes.

## Components

### Core Components

- **Orchestrator**: Manages agent workflow and state
- **Architect**: Generates architecture documentation
- **CLI**: Command-line interface for CodeCompanion

### Data Flow

1. User initiates command via CLI
2. Orchestrator loads current state
3. Architect generates documentation
4. State is updated and persisted
5. Results returned to user

