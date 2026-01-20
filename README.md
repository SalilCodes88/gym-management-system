# Gym Management System (Python, OOP)

A fully object-oriented gym management system built in Python, designed to demonstrate clean architecture, domain-driven design, and real-world application structure.

## Features
- Member & Trainer management
- Membership plans with pricing strategies (NoDiscount, PercentOff, FixedPrice)
- Payment processing with ledger tracking
- Workout plans and exercise catalogs
- Persistent storage using JSON serialization
- Command-line interface (CLI)

## Architecture
- `gym/` – Core domain logic (members, memberships, workouts, payments)
- `storage.py` – Serialization / deserialization layer
- `main.py` – CLI interface
- `data/` – Runtime storage (ignored by git)

## Key Concepts Demonstrated
- Abstract Base Classes (ABC)
- Composition over inheritance
- Strategy pattern (pricing policies, payment processors)
- Dataclasses (mutable & frozen)
- Domain validation and custom exceptions
- Separation of domain, storage, and interface layers

## How to Run
```bash
python main.py
