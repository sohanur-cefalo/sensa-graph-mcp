# RnD Knowledge Graph Structure

## Overview

This document describes a layered knowledge graph structure with nodes
and edges. Each node includes standard metadata fields and vector
embeddings. Edges include validity periods for version control and
temporal modeling.

------------------------------------------------------------------------

## Standard Node Fields (All Layers)

-   Unique ID (no need to be human readable)
-   Fingerprint (delivered in handover document)
-   Description (delivered in handover document)
-   Vector embedding

------------------------------------------------------------------------

# Layer 0 --- CATEGORY

All nodes in this layer should have the layer label.

## SITE

Fields: - Unique ID - Fingerprint - Description - Vector embedding

## PLANT

Fields: - Unique ID - Fingerprint - Description - Vector embedding

## SECTION

Fields: - Unique ID - Fingerprint - Description - Vector embedding

## SUB-SECTION

Fields: - Unique ID - Fingerprint - Description - Vector embedding

### Edges (Layer 0)

-   Descriptive Name (e.g., IS_CATEGORY) --- Not delivered by CS
-   Validity from (provided by CS)
-   Validity to (infinity as default, provided by CS)

------------------------------------------------------------------------

# Layer 1 --- CONTEXT

All nodes in this layer should have the layer label.

## Dimension: Location

### Hall 01

### Tank Area 1

### Aardal

Each includes: - Unique ID - Fingerprint - Description - Vector
embedding

### Edges

-   Descriptive Name (e.g., LOCATED_IN) --- Not delivered by CS
-   Validity from (provided by CS)
-   Validity to (infinity as default, provided by CS)

------------------------------------------------------------------------

## Dimension: System

### Feeding System

Fields: - Unique ID - Fingerprint - Description - Vector embedding

### Edges

-   Descriptive Name --- Not delivered by CS
-   Validity from (provided by CS)
-   Validity to (infinity as default, provided by CS)

------------------------------------------------------------------------

## Dimension: Measuring Unit

### MEASURING UNIT

### km/h

Fields: - Unique ID - Fingerprint - Description - Vector embedding

------------------------------------------------------------------------

# Layer 2 --- ASSET

All nodes in this layer should have the layer label.

## Oxygen Sensor

Fields: - Unique ID - Fingerprint - Description - Vector embedding

### Edges

-   Descriptive Name (e.g., LOCATED_IN) --- Not delivered by CS
-   Validity from (provided by CS)
-   Validity to (infinity as default, provided by CS)

------------------------------------------------------------------------

# Layer 3 --- SIGNAL

All time series are unique nodes. When a version changes: - Add a new
node - Modify validity of edges - GUID of node is one-to-one with Influx
GUID

## Flow_RAW

## Flow_1\_min_AVG_CLEAN

## Flow_1\_hour_AVG_CLEAN

## Flow_1\_day_AVG_CLEAN

Each includes: - Unique ID - Fingerprint - Description - Vector
embedding - Other fields defining how to access data in InfluxDB

### Edges

-   Descriptive Name --- Not delivered by CS
-   Validity from (provided by CS)
-   Validity to (infinity as default, provided by CS)

------------------------------------------------------------------------

# Key Concepts

-   All layers use vector embeddings for semantic capabilities.
-   Edges contain temporal validity for version control.
-   Signal nodes map directly to InfluxDB GUIDs.
-   Versioning is handled via node creation and edge validity updates.
