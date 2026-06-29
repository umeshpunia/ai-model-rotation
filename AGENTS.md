# AI Gateway Pro — Engineering Instructions for AI Coding Agents

## Mission

You are an expert Senior Software Architect and Principal Engineer.

Your responsibility is to design and implement **AI Gateway Pro**, a production-grade desktop application for managing AI providers, API keys, routing, monitoring, and failover.

The resulting codebase must be suitable for production use and extensible without major refactoring.

---

# General Rules

Never generate placeholder code.

Never generate mock implementations unless explicitly requested.

Every feature must be fully implemented.

Every file must compile.

Every endpoint must work.

Every UI element must function.

Every setting must persist.

Never leave TODO comments.

Never skip requested functionality.

---

# Development Philosophy

Always prefer

Maintainability

Scalability

Performance

Security

Extensibility

Clean code

Avoid quick fixes.

Avoid hacks.

Avoid duplicated logic.

Always refactor when necessary.

---

# Architecture

Use Clean Architecture.

Separate

Presentation

Business Logic

Infrastructure

Persistence

Never mix concerns.

---

# Backend

Python

FastAPI

Async-first architecture.

Use dependency injection.

Use repository pattern.

Use service layer.

Business logic must never exist inside API routes.

---

# Frontend

React

TypeScript

Tailwind

shadcn/ui

React Query

React Router

Zustand or Context API for application state.

Avoid unnecessary re-renders.

---

# Database

Default

SQLite

Optional

PostgreSQL

Support automatic migrations.

Never hardcode IDs.

---

# Configuration

No hardcoded providers.

No hardcoded models.

No hardcoded URLs.

Everything configurable.

Support

JSON

Environment Variables

Database Settings

Configuration changes should apply without requiring application restart where feasible.

---

# Provider System

Providers must behave like plugins.

Each provider implements a common interface.

Adding a provider should not require modification of existing provider implementations.

The routing engine should discover providers dynamically.

---

# API Keys

Support unlimited API keys.

Each key stores

Provider

Status

Priority

Usage

Failures

Cooldown

Latency

Health

Statistics

Encryption

---

# Key Rotation

Automatically rotate keys when

401

403

429

Timeout

Server Error

Retry another key.

Retry another provider.

Never stop processing unless all providers fail.

Do not implement functionality intended to bypass provider policies; use rotation for resilience and high availability only.

---

# Provider Failover

Support

Priority

Round Robin

Least Used

Fastest

Lowest Cost

Highest Success

Random

AI Optimized

Routing strategy must be configurable.

---

# Health Monitoring

Run background jobs.

Monitor

Provider availability

API key validity

Latency

Authentication failures

Timeouts

Quota/rate-limit responses

Recover automatically when appropriate.

---

# Scheduler

Background scheduler must continue working while application is running.

Should support

Health Checks

Statistics

Cleanup

Recovery

Backups

Notification jobs

---

# REST API

REST API must remain available even when UI is closed, provided the background service is running.

API versioning required.

Support

JSON

Streaming

Authentication

Pagination

Filtering

Validation

---

# Error Handling

Never crash.

Catch every exception.

Log every error.

Return meaningful API responses.

Automatically retry recoverable failures.

---

# Logging

Structured logging.

Separate

Application Logs

Gateway Logs

Provider Logs

Request Logs

Health Logs

Support log rotation.

---

# Security

Encrypt API keys at rest.

Mask API keys in UI.

Mask API keys in logs.

Support master password.

Support JWT.

Never expose secrets.

---

# Desktop Application

Application must

Install normally

Create desktop shortcut

Create Start Menu shortcut

Run in background

Minimize to tray

Restore from tray

Exit safely

Support auto-start with Windows

Generate

Installer

Portable version

Uninstaller

---

# UI

Professional.

Responsive.

Dark Mode.

Light Mode.

Modern animations.

Accessible.

No broken layouts.

---

# Performance

Use asynchronous networking.

Avoid blocking operations.

Cache frequently used data.

Avoid unnecessary database queries.

Optimize rendering.

---

# Code Quality

Use

Type hints

Docstrings

Linting

Formatting

Modular structure

Reusable components

SOLID principles

DRY principles

KISS where appropriate

No duplicated code.

---

# Testing

Generate

Unit Tests

Integration Tests

Provider Tests

API Tests

Service Tests

Health Check Tests

Installer Smoke Tests

---

# Documentation

Generate

README

Installation Guide

Developer Guide

API Documentation

Architecture Documentation

Deployment Guide

Troubleshooting Guide

Release Notes

---

# Completion Rules

Do not mark any task complete until

The feature is fully implemented.

The project builds successfully.

The backend starts successfully.

The frontend starts successfully.

The installer can be generated.

The portable build can be generated.

No compile errors remain.

No runtime errors remain.

No placeholder implementations remain.

---

# Final Goal

Produce a professional, production-ready AI Gateway desktop application that:

* Manages unlimited AI providers.
* Manages unlimited API keys.
* Provides intelligent routing and configurable failover.
* Monitors provider and key health continuously.
* Encrypts and securely stores credentials.
* Runs as a background desktop service with a system tray icon.
* Exposes a stable local REST API for client applications.
* Supports installer generation, portable builds, and future extensibility with minimal code changes.
