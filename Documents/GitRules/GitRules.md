# Project Git Rules

This document defines the Git branching and workflow rules for this project.

## 1. Branch Types

- **main**  
  - Always points to the **latest released** stable version.

- **release/{MAJOR.MINOR.PATCH}**  
  - Created from `main` as a **release branch** for a specific version.  
  - Used to track the exact state of each released version.

- **dev/{MAJOR.MINOR}/main**  
  - Base development branch for a new major/minor version series.  
  - All component development branches for that version are created from this branch.

- **dev/{MAJOR.MINOR}/{component-name}**  
  - Development branches for each component.  
  - Engineers implement new features and changes on these branches.

- **fix/{MAJOR.MINOR.PATCH}/main**
  - Fix branch for a specific patch version.  
  - Used when applying bug fixes to an already released version.

- **fix/{MAJOR.MINOR.PATCH}/{component-name}**  
  - Component-level fix branches when multiple patches are developed in parallel.  
  - Used to divide the work per component.

## 2. Development of New Releases

### 2.1 Starting to Develop New Features

1. Create a new branch `dev/{MAJOR.MINOR}/main` from `main`.
2. Create new branches `dev/{MAJOR.MINOR}/{component-name}` from `dev/{MAJOR.MINOR}/main` for each component to be developed.

### 2.2 Commit Rules

1. Engineers develop in each component branch (`dev/{MAJOR.MINOR}/{component-name}`).
2. Engineers commit only to the corresponding component branch.

### 2.3 Merge Rules

1. When at least one task in a component is completed, the engineer sends a pull request from the corresponding component branch to `dev/{MAJOR.MINOR}/main`.
2. The Lead Engineer reviews the pull request and, if acceptable, merges it into `dev/{MAJOR.MINOR}/main`.

### 2.4 Release Flow

1. When all planned components for the version are developed and well tested, conduct integration testing on `dev/{MAJOR.MINOR}/main`.
2. If the product passes integration testing, merge `dev/{MAJOR.MINOR}/main` into `main` as the latest release.
3. From `main`, create `release/{MAJOR.MINOR.PATCH}` to record the released state.

## 3. Development of Patches

The development workflow for patches follows the same basic steps as **Development of New Releases**, with the following points:

1. For a bug fix on an existing release, create a branch `fix/{MAJOR.MINOR.PATCH}/main` from `main` or from the corresponding `release/{MAJOR.MINOR.PATCH}`.
2. If multiple components need fixes in parallel, create `fix/{MAJOR.MINOR.PATCH}/{component-name}` branches from `fix/{MAJOR.MINOR.PATCH}/main`.
3. After development and testing on fix branches, merge them back into `fix/{MAJOR.MINOR.PATCH}/main`, then into `main`, and also into the relevant `dev/{MAJOR.MINOR}/main` branch so that future versions include the same fix.
