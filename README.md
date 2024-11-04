# Pyodide AWS CDK App Template

This repository contains an AWS CDK app template for deploying and experimenting with Pyodide-based applications on AWS.

## Overview

This template sets up a single AWS Lambda function that serves:

- Two HTML examples demonstrating Pyodide in action
- A simple Flet app
- A Streamlit app

Each example leverages Pyodide, allowing Python to run directly in the browser.

The CDK app also provisions a DynamoDB table with a general-purpose schema. This schema is compatible with
my `simplesingletable` tool, enabling low-cost storage and efficient querying.
