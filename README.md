# Inter Smart Group Loads tracking API

## Overview

The Intersmart Tracking API is a specialized fork of the original Intersmartgroup API, focused exclusively on car and freight tracking. It is designed for logistics operations that require real-time monitoring of transportation assets without additional cost calculation features.

This API is written in Python using Flask, with a strong emphasis on a powerful Telegram bot interface for managing fleets and tracking assets.

## Features

- **Real-Time Car & Freight Tracking**:
  - Track active shipments and vehicle in real-time.
  - View detailed data for each tracked vehicle.
  - Manage and update fleet data (CRUD operations) entirely through the Telegram bot.

- **Advanced Telegram Bot Functionality**:
  - Provides an interactive command interface for admins.
  - Allows real-time updates within the bot.
  - Supports inline queries and callback buttons for enhanced UX.

## Architecture

- **Backend**: Built with **Flask (Python)**.
- **Data Handling**: Uses lightweight file-based storage—no SQL database.
- **Telegram Bot**: Central to system functionality, using **python-telegram-bot** library.
- **Deployment**: Runs in production using **uWSGI**, with security best practices applied.

## Usage

To interact with the API:
1. **API Endpoint**:
   - `GET https://api.intersmartgroup.com/s2/loads/`: Fetch real-time location data of active shipments.
   - `GET https://api.intersmartgroup.com/s2/driver/?load_id=4214$auth_num=470129384701`: Fetch vehicle driver's details of selected shipment.
2. **Telegram Bot**:
   - The primary interface for tracking and management.
   - Support commands for querying fleet status, adding shipments, updating trip status, and more.

## Installation

To run the project locally:

1. Clone the repository
2. Install all the requirements
3. Prepare Bot using BotFather
4. You are ready to test
5. Install and set up uWSGI for production usage

# Contributing

We welcome suggestions and contributions! To contribute:

- Fork the repository.
- Create a new branch (git checkout -b feature-name).
- Commit your changes (git commit -am 'Add feature').
- Push to your branch (git push origin feature-name).
- Open a Pull Request.

Please report issues or suggest enhancements via the Issues tab.

# License

Licensed under the MIT License. See the LICENSE file for more details.

# Contact

For questions or collaboration, contact: ceasione@gmail.com